/* eslint-disable no-console */
const https = require('https');
const crypto = require('crypto');
const express = require('express');
const path = require('path');
const axios = require('axios');
const nodemailer = require('nodemailer');
const twilio = require('twilio');
const mongoClient = require('mongodb').MongoClient;
const session = require('express-session');
const FileStore = require('session-file-store')(session);
const utils = require('./server/utils');
const cfg = require('./server/configs');
const redis = require('./server/redis');
const mongo = require('./server/mongo');
const msg = require('./server/msgs');
const files = require('./server/files');
const filters = require('./server/filters');
const error = require('./server/error');

const httpsKey = files.readCertificateFile(
  path.join(__dirname, 'certificates', 'key.pem'),
);
const httpsCert = files.readCertificateFile(
  path.join(__dirname, 'certificates', 'cert.pem'),
);
const httpsOptions = {
  key: httpsKey,
  cert: httpsCert,
};

const app = express();
app.disable('x-powered-by');
app.use(express.json());
app.use(express.static(path.join(__dirname, 'build')));

// ---------------------------------------- Info from config files

let alerterID;
let redisDB;
let chainNodesMap = {};
let repoNameList = [];
let mongoInfo;
let redisInfo;
let authUsername;
let hashedPassword;
let salt;
let cookieSecret;

function resetInfoFromUserConfigMain() {
  alerterID = undefined;
  mongoInfo = undefined;
  redisInfo = undefined;
  console.debug('Set main user config values to default.');
}

function resetInfoFromUserNodesConfig() {
  chainNodesMap = {};
  console.debug('Set nodes user config values to default.');
}

function resetInfoFromUserReposConfig() {
  repoNameList = {};
  console.debug('Set repos user config values to default.');
}

function resetInfoFromInternalMainConfig() {
  redisDB = undefined;
  console.debug('Set main internal config values to default.');
}

function loadInfoFromUserConfigMain() {
  const configName = cfg.USER_CONFIG_MAIN;
  try {
    const config = cfg.readConfig(configName);

    // Get unique alerter identifier
    if (config.general && config.general.unique_alerter_identifier) {
      alerterID = config.general.unique_alerter_identifier;
      console.debug('Set alerter ID to %s', alerterID);
    } else {
      console.error('Missing alerter ID from %s. Using %s',
        configName, alerterID);
    }

    // Get whole mongo info section
    if (config.mongo) {
      mongoInfo = config.mongo;
      console.debug('Set mongo info to %s', JSON.stringify(mongoInfo));
    } else {
      console.error('Missing mongo info from %s. Using %s',
        configName, mongoInfo);
    }

    // Get whole redis info section
    if (config.redis) {
      redisInfo = config.redis;
      console.debug('Set redis info to %s', JSON.stringify(redisInfo));
    } else {
      console.error('Missing redis info from %s. Using %s',
        configName, redisInfo);
    }
  } catch (err) {
    if (err.code === 'ENOENT') {
      console.error('Config %s not found. Using alerterID=%s, mongoInfo=%s, '
        + 'redisInfo=%s', configName, alerterID, mongoInfo, redisInfo);
    } else {
      throw err;
    }
  }
}

function loadInfoFromUserNodesConfig() {
  const configName = cfg.USER_CONFIG_NODES;
  try {
    const nodes = cfg.readConfig(configName);
    const cnMap = {}; // node-chain-system map
    // Form map of chain names to node names by iterating over nodes
    Object.values(nodes)
      .forEach((n) => {
        if (n.node_name) {
          if (!cnMap[n.chain_name]) {
            cnMap[n.chain_name] = {};
          }
          cnMap[n.chain_name][n.node_name] = n;
        } else {
          console.error('Skipping node %s with no chain_name or node_name.', n);
        }
      });

    chainNodesMap = cnMap;
    console.debug('Set chain nodes map to %s', chainNodesMap);
  } catch (err) {
    if (err.code === 'ENOENT') {
      console.error('Config %s not found. Using nodes list "%s".',
        configName, chainNodesMap);
    } else {
      throw err;
    }
  }
}

function loadInfoFromUserReposConfig() {
  const configName = cfg.USER_CONFIG_REPOS;
  try {
    const repos = cfg.readConfig(configName);
    const repoNames = new Set();

    // Form list of repo names by iterating over repos
    Object.values(repos)
      .forEach((r) => {
        if (r.repo_name) {
          repoNames.add(r.repo_name);
        } else {
          console.error('Skipping repo %s with no repo_name field.', r);
        }
      });

    repoNameList = Array.from(repoNames);
    console.debug('Set repo list to %s', repoNameList);
  } catch (err) {
    if (err.code === 'ENOENT') {
      console.error('Config %s not found. Using repos list "%s".',
        configName, repoNameList);
    } else {
      throw err;
    }
  }
}

function loadSystemBoundariesfromInternalMainConfig() {
  const configName = cfg.INTERNAL_CONFIG_MAIN;
  const emptyConfig = {
    validator_process_memory_usage_danger_boundary: null,
    validator_process_memory_usage_safe_boundary: null,
    validator_open_file_descriptors_danger_boundary: null,
    validator_open_file_descriptors_safe_boundary: null,
    validator_system_cpu_usage_danger_boundary: null,
    validator_system_cpu_usage_safe_boundary: null,
    validator_system_ram_usage_danger_boundary: null,
    validator_system_ram_usage_safe_boundary: null,
    validator_system_storage_usage_danger_boundary: null,
    validator_system_storage_usage_safe_boundary: null,
    node_process_memory_usage_danger_boundary: null,
    node_process_memory_usage_safe_boundary: null,
    node_open_file_descriptors_danger_boundary: null,
    node_open_file_descriptors_safe_boundary: null,
    node_system_cpu_usage_danger_boundary: null,
    node_system_cpu_usage_safe_boundary: null,
    node_system_ram_usage_danger_boundary: null,
    node_system_ram_usage_safe_boundary: null,
    node_system_storage_usage_danger_boundary: null,
    node_system_storage_usage_safe_boundary: null,
  };
  try {
    const config = cfg.readConfig(configName);
    if (config.system_intervals_and_limits) {
      Object.entries(emptyConfig).forEach(([key, _]) => {
        if (!config.system_intervals_and_limits[key]) {
          config.system_intervals_and_limits[key] = null;       
        }
      });
      return config.system_intervals_and_limits;
    }
    return emptyConfig;
  } catch (err) {
    console.error('Error occured: %s ', err);
    return emptyConfig;
  }
}

function loadInfoFromInternalMainConfig() {
  const configName = cfg.INTERNAL_CONFIG_MAIN;
  try {
    const config = cfg.readConfig(configName);
    // Get redis database
    if (config.redis && config.redis.redis_database) {
      redisDB = config.redis.redis_database;
      console.debug('Set redis DB to %s', redisDB);
    } else {
      console.error('Missing redis.redis_database from %s. Using %s',
        configName, redisDB);
    }
  } catch (err) {
    if (err.code === 'ENOENT') {
      console.error('Config %s not found. Using redis DB "%s".',
        configName, redisDB);
    } else {
      throw err;
    }
  }
}

function loadInfoFromUserUIConfig() {
  const configName = cfg.USER_CONFIG_UI;
  try {
    const config = cfg.readConfig(configName);

    // - If the considered auth detail is in the config, read and store it.
    // - If not in the config file, check if it has already been stored.
    // - Otherwise, UI authentication has not been set up, so shut UI down.

    if (config.authentication && config.authentication.username) {
      authUsername = config.authentication.username;
      console.debug('Set authentication username to %s.', authUsername);
    } else if (authUsername) {
      console.error('Missing authentication.username from %s. Using %s.',
        configName, authUsername);
    } else {
      console.error('Missing authentication.username from %s. Please run the '
        + 'panic_oasis/run_ui_setup.py script to setup authentication for '
        + 'the UI before proceeding further.', configName);
      throw new Error(error.INVALID_UI_CONFIG.message);
    }

    if (config.authentication && config.authentication.hashed_password) {
      hashedPassword = config.authentication.hashed_password.slice(64, 128);
      salt = config.authentication.hashed_password.slice(0, 64);
      console.debug('Set authentication password corresponding to hash %s.',
        hashedPassword);
      console.debug('Set salt to %s.', salt);
    } else if (hashedPassword) {
      console.error('Missing authentication.hashed_password from %s. Using the '
        + 'password corresponding to hash %s, and salt %s.',
      configName, hashedPassword, salt);
    } else {
      console.error('Missing authentication.hashed_password from %s. Please '
        + 'run the panic_oasis/run_ui_setup.py script to setup '
        + 'authentication for the UI before proceeding further.',
      configName);
      throw new Error(error.INVALID_UI_CONFIG.message);
    }

    if (config.authentication && config.authentication.cookie_secret) {
      cookieSecret = config.authentication.cookie_secret;
      console.debug('Set cookie secret to %s. Note, the server needs to be '
        + 'restarted if the cookie secret has been modified, as the session '
        + 'would need to be re-initialized. Ignore warning if this is not the '
        + 'case.', cookieSecret);
    } else if (cookieSecret) {
      console.error('Missing authentication.cookie_secret from %s. Using %s.',
        configName, cookieSecret);
    } else {
      console.error('Missing authentication.cookie_secret from %s. Please '
        + 'run the panic_oasis/run_ui_setup.py script to setup '
        + 'authentication for the UI before proceeding further.',
      configName);
      throw new Error(error.INVALID_UI_CONFIG.message);
    }
  } catch (err) {
    if (err.code === 'ENOENT') {
      if (cookieSecret && hashedPassword && authUsername && salt) {
        console.error('Config %s not found. Using authUsername=%s,'
          + 'hashedPassword=%s, cookieSecret=%s, salt=%s.', configName,
        authUsername, hashedPassword, cookieSecret, salt);
      } else {
        console.error('Config  %s not found. Please run the '
          + 'panic_oasis/run_ui_setup.py script to setup '
          + 'authentication for the UI before proceeding further.', configName);
        throw new Error(error.INVALID_UI_CONFIG.message);
      }
    } else {
      throw err;
    }
  }
}

function authDetailsValid(username, password) {
  return authUsername === username && hashedPassword === password;
}

function checkAndFixAuthenticated(req) {
  req.session.authenticated = authDetailsValid(
    req.session.username, req.session.password,
  );
}

// Get data from config to initialize a session
loadInfoFromUserUIConfig();

// Initialize session
app.use(session({
  name: 'session-cookie',
  secret: cookieSecret,
  saveUninitialized: false,
  resave: false,
  store: new FileStore({ path: `${__dirname}/sessions` }),
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: true,
    maxAge: 60 * 60 * 1000 * 24,
  },
}));

// ---------------------------------------- Authentication

app.post('/server/authenticate', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { username, password } = req.body;

  if (!(username && password)) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  req.session.username = username;
  const inputHashedPass = crypto.pbkdf2Sync(Buffer.from(password),
    Buffer.from(salt, 'hex'), 100000, 32, 'sha256').toString('hex');
  req.session.password = inputHashedPass;

  if (authDetailsValid(username, inputHashedPass)) {
    req.session.authenticated = true;
    res.status(utils.SUCCESS_STATUS)
      .send(utils.resultJson({ authenticated: true }));
  } else {
    req.session.authenticated = false;
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_INVALID_AUTH));
  }
});

app.get('/server/get_authentication_status', (req, res) => {
  console.log('Received GET request for %s', req.url);
  checkAndFixAuthenticated(req);
  res.status(utils.SUCCESS_STATUS)
    .send(utils.resultJson({ authenticated: req.session.authenticated }));
});

app.post('/server/terminate_session', (req, res) => {
  console.log('Received POST request for %s', req.url);
  req.session.destroy();
  res.status(utils.SUCCESS_STATUS).clearCookie('session-cookie', {
    httpOnly: true,
    secure: true,
    sameSite: true,
  }).end();
});


// ---------------------------------------- Config get

app.get('/server/config', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const { file } = req.query;

  if (!file) {
    return res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
  }

  if (cfg.ALL_CONFIG_FILES.includes(file)) {
    try {
      const data = cfg.readConfig(file);
      return res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(data));
    } catch (err) {
      if (err.code === 'ENOENT') {
        return res.status(utils.SUCCESS_STATUS)
          .send(utils.errorJson(msg.MSG_CONFIG_NOT_FOUND));
      }
      throw err;
    }
  }
  return res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_CONFIG_UNRECOGNIZED));
});

// ---------------------------------------- Config post

app.post('/server/config', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { file } = req.query;
  const { config } = req.body;

  if (!(file && config)) {
    return res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
  }

  if (cfg.ALL_CONFIG_FILES.includes(file)) {
    cfg.writeConfig(file, config);
    loadInfoFromUserConfigMain();
    return res.status(utils.SUCCESS_STATUS)
      .send(utils.resultJson(msg.MSG_CONFIG_SUBMITTED));
  }
  return res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_CONFIG_UNRECOGNIZED));
});

// ---------------------------------------- Redis

function getRedisKeyPrefix() {
  return `${alerterID}:`;
}

// ---------------------------------------- Alerts log

app.get('/server/alerts', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const { pageNo, size } = req.query;

  if (!(pageNo && size)) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  if (!mongoInfo || (mongoInfo.enabled && !utils.toBool(mongoInfo.enabled))) {
    console.error(msg.MSG_MONGO_NOT_SET_UP_LONG);
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MONGO_NOT_SET_UP));
    return;
  }

  const parsedPageNo = parseInt(pageNo, 10);
  const parsedSize = parseInt(size, 10);
  if (parsedPageNo <= 0) {
    const errMsg = 'invalid page number; should be greater than 0';
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(errMsg));
    return;
  }
  if (parsedSize <= 0) {
    const errMsg = 'invalid page size; should be greater than 0';
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(errMsg));
    return;
  }

  const query = {};
  query.skip = parsedSize * (parsedPageNo - 1);
  query.limit = parsedSize;
  query.sort = { $natural: -1 };

  const authPass = mongoInfo.pass ? `:${mongoInfo.pass}` : '';
  const authFull = mongoInfo.user ? `${mongoInfo.user}${authPass}@` : '';
  const url = `mongodb://${authFull}${mongoInfo.host}:${mongoInfo.port}`;
  await mongoClient.connect(url, mongo.options, (err, client) => {
    if (err != null) {
      res.status(utils.ERR_STATUS)
        .send(utils.errorJson(msg.MSG_MONGO_ERROR));
      return;
    }

    const db = client.db(mongoInfo.db_name);
    const colName = `alerts_${alerterID}`;
    mongo.findDocuments(db, colName, query, (totalCount, alerts) => {
      client.close();
      const totalPages = (
        parsedSize > 0 ? Math.ceil(totalCount / parsedSize) : 1);
      res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson({
          total_pages: totalPages,
          alerts,
        }));
    });
  });
});

// ---------------------------------------- Chains and Nodes

app.get('/server/chains', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const onlyIfMonitored = req.query.onlyIfMonitored || '';

  // Apply filter if we only want chains for
  // which the nodes are involved in monitoring
  if (utils.toBool(onlyIfMonitored)) {
    const chains = filters.getMonitoredChainsConsideringNodes(chainNodesMap);
    res.status(utils.SUCCESS_STATUS)
      .send(utils.resultJson(chains));
    return;
  }
  res.status(utils.SUCCESS_STATUS)
    .send(utils.resultJson(Object.keys(chainNodesMap)));
});

app.get('/server/chain_nodes_map', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const onlyIfMonitored = req.query.onlyIfMonitored || '';

  // Apply filter if we only want chains for
  // which the nodes are involved in monitoring
  if (utils.toBool(onlyIfMonitored)) {
    res.status(utils.SUCCESS_STATUS)
      .send(utils.resultJson(filters.getMonitoredNodes(chainNodesMap)));
    return;
  }
  res.status(utils.SUCCESS_STATUS)
    .send(utils.resultJson(chainNodesMap));
});

app.get('/server/all_chain_info', async (req, res) => {
  console.log('Received GET request for %s', req.url);

  if (!redisInfo || (redisInfo.enabled && !utils.toBool(redisInfo.enabled))) {
    console.error(msg.MSG_REDIS_NOT_SET_UP_LONG);
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_REDIS_NOT_SET_UP));
    return;
  }

  const { chainName } = req.query;
  if (!chainName) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  // Filter map and get nodes list
  const filteredCNMap = filters.getMonitoredNodes(chainNodesMap);
  const nodesList = filteredCNMap[chainName] || [];

  // Filter map and get systems list
  const filteredCNSMap = filters.getMonitoredSystems(chainNodesMap);
  const systemsList = filteredCNSMap[chainName] || [];

  // Check that chain is recognized
  if (!filteredCNMap[chainName]) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_CHAIN_NOT_FOUND));
    return;
  }

  // Initialise allInfo with general template
  const allInfo = {
    nodes: {},
    systems: {},
    systemBoundaries: {},
    monitors: {
      node: {},
      system: {},
    },
  };

  // List of values to get from Redis
  const valuesToGetNormally = []; // mget to be used
  const valuesToGetFromHash = []; // hmget to be used

  // ----------------------------- Nodes

  Object.keys(nodesList)
    .forEach((n) => {
      // Create redis keys for node
      let keysNode = redis.getKeysNode();
      keysNode = redis.addPostfixToDictValues(keysNode, `_${n}`);
      // Add keys to the values-to-get list
      Object.keys(keysNode)
        .forEach((k) => {
          valuesToGetFromHash.push(keysNode[k]);
        });

      // Create redis keys for node monitor
      let keysNodeMonitor = redis.getKeysNodeMonitor();
      keysNodeMonitor = redis.addPrefixToDictValues(keysNodeMonitor,
        getRedisKeyPrefix()); // Add prefix
      keysNodeMonitor = redis.addPostfixToDictValues(keysNodeMonitor,
        `_Node monitor (${n})`); // Add postfix

      // Add keys to the values-to-get list
      Object.keys(keysNodeMonitor)
        .forEach((k) => {
          valuesToGetNormally.push(keysNodeMonitor[k]);
        });

      // Create node and node monitor sections
      allInfo.nodes[n] = keysNode;
      allInfo.monitors.node[n] = keysNodeMonitor;
    });

  // ----------------------------- Systems

  Object.keys(systemsList)
    .forEach((n) => {
      if (systemsList[n].node_exporter_url) {
        let keysSystem = redis.getKeysSystem();
        keysSystem = redis.addPostfixToDictValues(keysSystem, `_${n}`);

        Object.keys(keysSystem)
          .forEach((k) => {
            valuesToGetFromHash.push(keysSystem[k]);
          });

        // Create redis keys for system monitor
        let keysSystemMonitor = redis.getKeysSystemMonitor();
        keysSystemMonitor = redis.addPrefixToDictValues(keysSystemMonitor,
          getRedisKeyPrefix()); // Add prefix
        keysSystemMonitor = redis.addPostfixToDictValues(keysSystemMonitor,
          `_System monitor (${n})`); // Add postfix

        //  Add keys to the values-to-get list
        Object.keys(keysSystemMonitor)
          .forEach((k) => {
            valuesToGetNormally.push(keysSystemMonitor[k]);
          });

        // Create system and system monitor sections
        allInfo.systems[n] = keysSystem;
        allInfo.systems[n].system_has_validator = systemsList[n]
          .node_is_validator;
        allInfo.monitors.system[n] = keysSystemMonitor;
      }
    });

  // ----------------------------- System Boundaries

  allInfo.systemBoundaries = loadSystemBoundariesfromInternalMainConfig();

  // ----------------------------- Get values

  const bcHash = redis.getHashes().blockchain;
  const hash = `${getRedisKeyPrefix()}${bcHash}_${chainName}`;
  const valuesDict = {};

  const redisClient = redis.getRedisClient(
    redisInfo.host, redisInfo.port, redisInfo.password,
  );
  redisClient.select(redisDB, (err, _) => {
    if (err != null) {
      redisClient.quit();
      console.error(err);
      const errMsg = err.code === 'NOAUTH'
        ? msg.MSG_REDIS_AUTH_INCORRECT : msg.MSG_REDIS_ERROR;
      res.status(utils.ERR_STATUS)
        .send(utils.errorJson(errMsg));
      return;
    }

    redisClient
      .multi()
      .mget(valuesToGetNormally, (err1, values) => {
        valuesToGetNormally.forEach((key, i) => {
          valuesDict[key] = values[i];
        });
      })
      .hmget(hash, valuesToGetFromHash, (err2, values) => {
        valuesToGetFromHash.forEach((key, i) => {
          valuesDict[key] = values[i];
        });
      })
      // eslint-disable-next-line no-unused-vars
      .exec((err3, replies) => {
        if (err3 != null) {
          res.status(utils.ERR_STATUS)
            .send(utils.errorJson(msg.MSG_REDIS_ERROR));
          return;
        }

        // Replace keys in node sections with value in valuesDict
        Object.keys(allInfo.nodes)
          .forEach((n) => {
            Object.keys(allInfo.nodes[n])
              .forEach((k) => {
                allInfo.nodes[n][k] = valuesDict[allInfo.nodes[n][k]];
              });
          });

        // Replace keys in system sections with value in valuesDict
        Object.keys(allInfo.systems)
          .forEach((n) => {
            Object.keys(allInfo.systems[n])
              .forEach((k) => {
                if (k !== 'system_has_validator') {
                  allInfo.systems[n][k] = valuesDict[allInfo.systems[n][k]];
                }
              });
          });

        // Replace keys in node monitor sections with value in valuesDict
        Object.keys(allInfo.monitors.node)
          .forEach((n) => {
            Object.keys(allInfo.monitors.node[n])
              .forEach((k) => {
                allInfo.monitors.node[n][k] = valuesDict[
                  allInfo.monitors.node[n][k]];
              });
          });
        // Replace keys in system monitor sections with value in valuesDict
        Object.keys(allInfo.monitors.system)
          .forEach((n) => {
            Object.keys(allInfo.monitors.system[n])
              .forEach((k) => {
                allInfo.monitors.system[n][k] = valuesDict[
                  allInfo.monitors.system[n][k]];
              });
          });
        // Add extra information to each node (is_validator)
        Object.keys(nodesList)
          .forEach((n) => {
            if (nodesList[n] && nodesList[n].node_is_validator) {
              allInfo.nodes[n].is_validator = nodesList[n].node_is_validator;
            } else {
              console.error('Missing node_is_validator for node %s. '
                + 'Defaulting to False.', n);
              allInfo.nodes[n].is_validator = false.toString();
            }
          });

        redisClient.quit();
        res.status(utils.SUCCESS_STATUS)
          .send(utils.resultJson(allInfo));
      });
  });
});

// ---------------------------------------- Repos

app.get('/server/repos', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  const repos = Array.from(repoNameList);
  return res.status(utils.SUCCESS_STATUS)
    .send(utils.resultJson(repos));
});

// ---------------------------------------- Pings and Tests

app.post('/server/ping_server', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  try {
    return res.status(utils.SUCCESS_STATUS)
      .send(utils.resultJson(msg.MSG_PONG));
  } catch (err) {
    return res.status(utils.ERR_STATUS)
      .send(utils.errorJson(err));
  }
});

app.post('/server/ping_redis', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { host, port, password } = req.body;

  if (!(host && port)) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  const redisClient = redis.getRedisClient(host, port, password);
  redisClient.ping((err, result) => {
    redisClient.quit();

    if (err == null && result.toLowerCase() === 'pong') {
      res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(msg.MSG_PONG));
      return;
    }

    if (err == null) {
      console.log('Unexpected Redis ping result: %s', result);
      res.status(utils.ERR_STATUS)
        .send(utils.errorJson(msg.MSG_REDIS_ERROR));
      return;
    }

    console.error(err);
    const errMsg = err.code === 'NOAUTH'
      ? msg.MSG_REDIS_AUTH_INCORRECT : msg.MSG_REDIS_ERROR;
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(errMsg));
  });
});

app.post('/server/ping_mongo', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    host, port, user, pass,
  } = req.body;

  if (!(host && port)) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  const authPass = pass ? `:${pass}` : '';
  const authFull = user ? `${user}${authPass}@` : '';
  const url = `mongodb://${authFull}${host}:${port}`;
  await mongoClient.connect(url, mongo.options, (err, _) => {
    if (err == null) {
      res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(msg.MSG_PONG));
      return;
    }
    console.error(err);
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_NO_CONNECTION));
  });
});

app.post('/server/oasis_api_server/ping_api', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { endpoint } = req.body;

  if (!endpoint) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  const url = `${endpoint}/api/ping`;
  axios.get(url)
    .then((_) => {
      res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(msg.MSG_PONG));
    })
    .catch((err) => {
      console.error(err);
      if (err.code === 'ECONNREFUSED') {
        res.status(utils.ERR_STATUS)
          .send(utils.errorJson(msg.MSG_NO_CONNECTION));
      } else {
        // Connection made but error occurred
        res.status(utils.ERR_STATUS)
          .send(utils.errorJson(msg.MSG_OASIS_API_SERVER_ERROR));
      }
    });
});

app.post('/server/oasis_api_server/ping_node', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const { apiUrl, nodeName } = req.body;

  if (!(apiUrl && nodeName)) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  const url = `${apiUrl}/api/pingnode`;

  axios.get(url, { params: { name: nodeName } })
    .then((_) => {
      res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(msg.MSG_PONG));
    })
    .catch((err) => {
      console.error(err);
      if (err.code === 'ECONNREFUSED') {
        res.status(utils.ERR_STATUS)
          .send(utils.errorJson(msg.MSG_NO_CONNECTION));
      } else {
        // Connection made but error occurred (typically means node is missing)
        res.status(utils.ERR_STATUS)
          .send(utils.errorJson(msg.MSG_OASIS_API_SERVER_ERROR));
      }
    });
});

app.post('/server/test_twilio', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    accountSid, authToken,
    twilioPhoneNumber, phoneNumberToDial,
  } = req.body;

  if (!(accountSid && authToken && twilioPhoneNumber && phoneNumberToDial)) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  const twilioClient = twilio(accountSid, authToken);
  twilioClient.calls
    .create({
      twiml: '<Response><Reject /></Response>',
      to: phoneNumberToDial,
      from: twilioPhoneNumber,
    })
    .then(() => res.status(utils.SUCCESS_STATUS)
      .send(utils.resultJson(msg.MSG_PONG)))
    .catch((err) => {
      console.error(err);
      res.status(utils.ERR_STATUS)
        .send(utils.errorJson(msg.MSG_TWILIO_ERROR));
    });
});

app.post('/server/test_email', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  const {
    smtp, from, to, user, pass,
  } = req.body;

  if (!(smtp && from && to)) {
    res.status(utils.ERR_STATUS)
      .send(utils.errorJson(msg.MSG_MISSING_ARGUMENTS));
    return;
  }

  const transport = nodemailer.createTransport({
    host: smtp,
    auth: (user && pass) ? {
      user,
      pass,
    } : undefined,
  });

  transport.verify((err, _) => {
    if (err) {
      console.log(err);
      res.status(utils.ERR_STATUS)
        .send(utils.errorJson(msg.MSG_SMTP_ERROR));
      return;
    }

    const message = {
      from,
      to,
      subject: 'Test Email from PANIC',
      text: 'Test Email from PANIC',
    };

    transport.sendMail(message, (err2, info) => {
      if (err2) {
        console.log(err2);
        res.status(utils.ERR_STATUS)
          .send(utils.errorJson(msg.MSG_SMTP_ERROR));
        return;
      }
      console.debug(info);
      res.status(utils.SUCCESS_STATUS)
        .send(utils.resultJson(msg.MSG_PONG));
    });
  });
});

// ---------------------------------------- Server default

app.get('/server/*', async (req, res) => {
  console.log('Received GET request for %s', req.url);
  res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_INVALID_ENDPOINT));
});

app.post('/server/*', async (req, res) => {
  console.log('Received POST request for %s', req.url);
  res.status(utils.ERR_STATUS)
    .send(utils.errorJson(msg.MSG_INVALID_ENDPOINT));
});

// ---------------------------------------- PANIC UI

app.get('/*', (req, res) => {
  console.log('Received GET request for %s', req.url);
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// ---------------------------------------- Start info-from-config loaders

// First batch of data loads
loadInfoFromUserConfigMain();
loadInfoFromUserNodesConfig();
loadInfoFromUserReposConfig();
loadInfoFromInternalMainConfig();

// Asynchronous data loads
files.listenFileChanges(cfg.toConfigPath(cfg.USER_CONFIG_MAIN),
  loadInfoFromUserConfigMain, resetInfoFromUserConfigMain);
files.listenFileChanges(cfg.toConfigPath(cfg.USER_CONFIG_NODES),
  loadInfoFromUserNodesConfig, resetInfoFromUserNodesConfig);
files.listenFileChanges(cfg.toConfigPath(cfg.USER_CONFIG_REPOS),
  loadInfoFromUserReposConfig, resetInfoFromUserReposConfig);
files.listenFileChanges(cfg.toConfigPath(cfg.USER_CONFIG_UI),
  loadInfoFromUserUIConfig, () => {});
files.listenFileChanges(cfg.toConfigPath(cfg.INTERNAL_CONFIG_MAIN),
  loadInfoFromInternalMainConfig, resetInfoFromInternalMainConfig);

// ---------------------------------------- Start listen

const port = process.env.PORT || 9000;
const server = https.createServer(httpsOptions, app);
server.listen(port, () => {
  console.log('Listening on %s', port);
});
