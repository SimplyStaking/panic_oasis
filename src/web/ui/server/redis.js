const redis = require('redis');
const msg = require('./msgs');

// Hashes
const getHashes = () => ({
  blockchain: 'hash_bc1',
});

// nX_<node_name>
const getKeysNode = () => ({
  went_down_at: 'n1',
  bonded_balance: 'n2',
  is_syncing: 'n3',
  no_of_peers: 'n4',
  active: 'n5',
  is_missing_blocks: 'n6',
  time_of_last_height_check_activity: 'n7',
  time_of_last_height_change: 'n8',
  finalized_block_height: 'n9',
  no_change_in_height_warning_sent: 'n10',
  voting_power: 'n11',
  consecutive_blocks_missed: 'n12',
  debonding_balance: 'n13',
  shares_balance: 'n14',
});

// nmX_<monitor_name>
const getKeysNodeMonitor = () => ({
  alive: 'nm1',
  last_height_checked: 'nm2',
});

module.exports = {
  getRedisClient: (host, port, password) => {
    const redisClient = redis.createClient({
      host,
      port,
      password: password || undefined,
      no_ready_check: true,
      retry_strategy: (options) => {
        if (options.error && options.error.code === 'ECONNREFUSED') {
          // End reconnecting on a specific error and flush all commands with
          // a individual error
          return new Error(msg.MSG_NO_CONNECTION);
        }
        if (options.total_retry_time > 1000 * 60 * 60) {
          // End reconnecting after a specific timeout and flush all commands
          // with a individual error
          return new Error(msg.MSG_RETRY_TIME_EXCEEDED);
        }
        if (options.attempt > 10) {
          // End reconnecting with built in error
          return undefined;
        }
        // reconnect after
        return Math.min(options.attempt * 100, 3000);
      },
      connect_timeout: 10000, // 10 * 1000 ms
    });
    redisClient.on('error', (error) => {
      console.error(error);
    });
    redisClient.on('reconnecting', () => {
      console.log(msg.MSG_REDIS_RECONNECTING);
    });
    redisClient.on('ready', () => {
      console.debug(msg.MSG_REDIS_CONNECTED);
    });
    return redisClient;
  },

  addPrefixToDictValues: (dict, prefix) => {
    const newDict = {};
    Object.keys(dict)
      .forEach((key) => {
        newDict[key] = `${prefix}${dict[key]}`;
      });
    return newDict;
  },

  addPostfixToDictValues: (dict, postfix) => {
    const newDict = {};
    Object.keys(dict)
      .forEach((key) => {
        newDict[key] = `${dict[key]}${postfix}`;
      });
    return newDict;
  },

  DUMMY_KEY: '_dummy_key_',

  getHashes,
  getKeysNode,
  getKeysNodeMonitor,
};
