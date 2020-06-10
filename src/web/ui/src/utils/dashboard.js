import React from 'react';
import Badge from 'react-bootstrap/Badge';
import NavDropdown from 'react-bootstrap/NavDropdown';
import Node from '../components/node';
import Monitor from '../components/monitor';
import { MONITOR_TYPES } from './constants';
import scaleToNano from './scaling';
import '../style/style.css';

function createNodesFromJson(activeChain, nodesJson) {
  const nodes = [];
  Object.entries(nodesJson).forEach(([node, data]) => {
    const chain = activeChain;
    const isDown = data.went_down_at === null ? false
      : data.went_down_at !== 'None';
    const isValidator = data.is_validator === null ? -1
      : data.is_validator.toLowerCase() === 'true';
    const wentDownAt = data.went_down_at === null ? -1
      : parseFloat(data.went_down_at);
    const isSyncing = data.is_syncing === null ? -1
      : data.is_syncing.toLowerCase() === 'true';
    const noOfPeers = data.no_of_peers === null
    || data.no_of_peers === 'None' ? -1 : parseInt(data.no_of_peers, 10);
    const timeOfLastHeightChange = data.time_of_last_height_change === null
      ? -1 : parseFloat(data.time_of_last_height_change);
    const finalizedBlockHeight = data.finalized_block_height === null ? -1
      : parseInt(data.finalized_block_height, 10);
    const bondedBalance = data.bonded_balance === null
    || data.bonded_balance === 'None' ? -1
      : parseInt(data.bonded_balance, 10);
    const debondingBalance = data.debonding_balance === null
      || data.debonding_balance === 'None' ? -1
        : parseInt(data.debonding_balance, 10);
    const sharesBalance = data.shares_balance === null
        || data.shares_balance === 'None' ? -1
          : parseInt(data.shares_balance, 10);
    const votingPower = data.voting_power === null
          || data.voting_power === 'None' ? -1
            : parseInt(data.voting_power, 10);
    const active = data.active === null || data.active === 'None' ? -1
      : data.active.toLowerCase() === 'true';
    const isMissingBlocks = data.is_missing_blocks === null ? -1
      : data.is_missing_blocks.toLowerCase() === 'true';
    const consecutiveBlocksMissed = data.consecutive_blocks_missed === null ? -1
      : parseInt(data.consecutive_blocks_missed, 10);

    nodes.push(
      new Node(node, chain, isValidator, wentDownAt, isDown, isSyncing,
        noOfPeers, timeOfLastHeightChange, finalizedBlockHeight,
        bondedBalance, active, isMissingBlocks, debondingBalance,
        sharesBalance, votingPower, consecutiveBlocksMissed),
    );
  });

  return nodes;
}

function createMonitorTypeFromJson(activeChain, monitorsJson, monitorType) {
  const monitors = [];
  let monitorTypeJson;

  if (monitorType === MONITOR_TYPES.node_monitor) {
    monitorTypeJson = monitorsJson.node;
  }else {
    return monitors;
  }
  Object.entries(monitorTypeJson).forEach(([monitor, data]) => {
    const chain = activeChain;
    const monitorName = `${monitor}`;
    const lastUpdate = data.alive === null ? -1 : parseFloat(data.alive);
    monitors.push(new Monitor(monitorName, chain, lastUpdate, monitorType));
  });

  return monitors;
}
function createActiveNodeStats(node) {
  const noOfPeers = node.noOfPeers === -1 ? 'N/a' : node.noOfPeers;
  const height = node.height === -1 ? 'N/a' : node.height;
  const bondedBalance = node.bondedBalance === -1
    ? 'N/a' : scaleToNano(node.bondedBalance);
  const debondingBalance = node.debondingBalance === -1
    ? 'N/a' : scaleToNano(node.debondingBalance);
  const sharesBalance = node.sharesBalance === -1
    ? 'N/a' : scaleToNano(node.sharesBalance);
  const votingPower = node.votingPower === -1
  ? 'N/a' : node.votingPower;
  const consecutiveBlocksMissed = node.consecutiveBlocksMissed === -1
    ? 'N/a' : node.consecutiveBlocksMissed;
  const wentDownAt = node.wentDownAt === -1 ? 'N/a' : node.wentDownAt;
  const lastHeightUpdate = node.lastHeightUpdate === -1
    ? 'no update' : node.lastHeightUpdate;

  return {
    noOfPeers,
    height,
    bondedBalance,
    debondingBalance,
    sharesBalance,
    votingPower,
    consecutiveBlocksMissed,
    wentDownAt,
    lastHeightUpdate,
  };
}

function createMonitorStats(monitor) {
  const lastUpdate = monitor.lastUpdate === -1
    ? 'no recent update' : monitor.lastUpdate;

  return { lastUpdate };
}

function createBadge(name, variant, key) {
  return (
    <Badge variant={variant} className="badges-style" key={key}>
      {name}
    </Badge>
  );
}

function createChainDropDownItems(elements, activeChainIndex) {
  const items = [];
  if (elements.length === 1){
    items.push(
      <NavDropdown.Item
        key="no-option-key"
        style={{'font-size': '15px'}}
        disabled
      >
      -- No other option --
      </NavDropdown.Item>
    )
  }
  for (let i = 0; i < elements.length; i += 1) {
    if (i !== activeChainIndex) {
      items.push(
        <NavDropdown.Item
          eventKey={i}
          className="navbar-item"
          key={elements[i]}
        >
          {elements[i]}
        </NavDropdown.Item>,
      );
    }
  }
  return items;
}

export {
  createNodesFromJson, createMonitorTypeFromJson, createActiveNodeStats,
  createMonitorStats, createBadge, createChainDropDownItems,
};
