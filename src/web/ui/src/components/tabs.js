import React from 'react';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';
import { forbidExtraProps } from 'airbnb-prop-types';
import PropTypes from 'prop-types';
import { NODE_TYPE, SYSTEM_TYPE } from '../utils/constants';
import '../style/style.css';
import { NodeDataGrid, SystemDataGrid } from './grid';

function createNodeTabs(nodes, activeChain) {
  const tabs = [];
  for (let i = 0; i < nodes.length; i += 1) {
    if (nodes[i].chain === activeChain) {
      tabs.push(
        <Tab eventKey={i} title={nodes[i].name} key={nodes[i].name}>
          <NodeDataGrid node={nodes[i]} />
        </Tab>,
      );
    }
  }
  return tabs;
}

function createSystemTabs(systems, activeChain) {
  const tabs = [];
  for (let i = 0; i < systems.length; i += 1) {
    if (systems[i].chain === activeChain) {
      tabs.push(
        <Tab eventKey={i} title={systems[i].name} key={systems[i].name}>
          <SystemDataGrid system={systems[i]} />
        </Tab>,
      );
    }
  }
  return tabs;
}

function NodeSelectionTabs({
  nodes, activeNodeIndex, activeChain, handleSelectNode,
}) {
  return (
    <Tabs
      id="nodes-tabs"
      activeKey={activeNodeIndex}
      onSelect={handleSelectNode}
      className="tabs-style"
    >
      {createNodeTabs(nodes, activeChain)}
    </Tabs>
  );
}

function SystemSelectionTabs({
  systems, activeSystemIndex, activeChain, handleSelectSystem,
}) {
  return (
    <Tabs
      id="systems-tabs"
      activeKey={activeSystemIndex}
      onSelect={handleSelectSystem}
      className="tabs-style"
    >
      {createSystemTabs(systems, activeChain)}
    </Tabs>
  );
}

NodeSelectionTabs.propTypes = forbidExtraProps({
  nodes: PropTypes.arrayOf(NODE_TYPE).isRequired,
  activeNodeIndex: PropTypes.number.isRequired,
  activeChain: PropTypes.string.isRequired,
  handleSelectNode: PropTypes.func.isRequired,
});

SystemSelectionTabs.propTypes = forbidExtraProps({
  systems: PropTypes.arrayOf(SYSTEM_TYPE).isRequired,
  activeSystemIndex: PropTypes.number.isRequired,
  activeChain: PropTypes.string.isRequired,
  handleSelectSystem: PropTypes.func.isRequired,
});

export { NodeSelectionTabs, SystemSelectionTabs };
