const utils = require('./utils');

const getMonitoredChains = (chainNodesMap) => {
  const filter = n => utils.toBool(n.use_as_data_source);
  return Object.keys(chainNodesMap)
    .filter(c => Object.keys(chainNodesMap[c])
      .some(n => filter(chainNodesMap[c][n])));
};

const getMonitoredChainsConsideringNodes = (chainNodesMap) => {
  const filter = n => utils.toBool(n.monitor_node)
    || utils.toBool(n.use_as_data_source);
  return Object.keys(chainNodesMap)
    .filter(c => Object.keys(chainNodesMap[c])
      .some(n => filter(chainNodesMap[c][n])));
};

function isNotEmpty(str) {
  return !(!str || str.length === 0);
}

const getMonitoredChainsConsideringSystems = (chainNodesMap) => {
  const filter = n => isNotEmpty(n.node_exporter_url);
  return Object.keys(chainNodesMap)
    .filter(c => Object.keys(chainNodesMap[c])
      .some(n => filter(chainNodesMap[c][n])));
};

const getMonitoredNodes = (chainNodesMap) => {
  // Filter chains and reconstruct map with remaining chains
  const cnMap = {};
  getMonitoredChainsConsideringNodes(chainNodesMap)
    .forEach((c) => {
      cnMap[c] = chainNodesMap[c];
    });

  // Filter nodes and reconstruct chain with remaining nodes
  const filter = n => utils.toBool(n.monitor_node);
  Object.keys(cnMap)
    .forEach((c) => {
      cnMap[c] = {};
      Object.keys(chainNodesMap[c])
        .filter(n => filter(chainNodesMap[c][n]))
        .forEach((n) => {
          cnMap[c][n] = chainNodesMap[c][n];
        });
    });

  return cnMap;
};

const getMonitoredSystems = (chainNodesMap) => {
  // Filter chains and nodes and reconstruct map with remaining chains and nodes
  const cnMap = {};
  getMonitoredChainsConsideringSystems(chainNodesMap)
    .forEach((c) => {
      cnMap[c] = chainNodesMap[c];
    });

  // Filter nodes and reconstruct chain with remaining nodes
  const filter = n => isNotEmpty(n.node_exporter_url);
  Object.keys(cnMap)
    .forEach((c) => {
      cnMap[c] = {};
      Object.keys(chainNodesMap[c])
        .filter(n => filter(chainNodesMap[c][n]))
        .forEach((n) => {
          cnMap[c][n] = chainNodesMap[c][n];
        });
    });

  return cnMap;
};

module.exports = {
  getMonitoredChains,
  getMonitoredChainsConsideringNodes,
  getMonitoredNodes,
  getMonitoredSystems,
};
