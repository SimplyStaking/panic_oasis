import React, { Component } from 'react';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Table from 'react-bootstrap/Table';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import { ToastsStore } from 'react-toasts';
import moment from 'moment';
import { getAllChainInfo, getChainNames } from '../utils/data';
import {
  MONITOR_TYPES, MONITOR_TYPE, NODE_TYPE, SYSTEM_TYPE,
} from '../utils/constants';
import {
  createMonitorStats, createMonitorTypeFromJson, createNodesFromJson,
  createSystemsFromJson,
} from '../utils/dashboard';
import Page from '../components/page';
import ChainsDropDown from '../components/dropdowns';
import { SystemBadges, NodeBadges } from '../components/badges';
import { SystemSelectionTabs, NodeSelectionTabs } from '../components/tabs';
import TooltipOverlay from '../components/overlays';
import '../style/style.css';

moment.locale('en');
moment.updateLocale('en', {
  relativeTime: {
    future: 'Just now',
    s: '%d seconds',
    ss: '%d seconds',
  },
});

// obtained from here: https://github.com/moment/moment/issues/1968
moment.relativeTimeThreshold('s', 59);
moment.relativeTimeThreshold('m', 60);
moment.relativeTimeThreshold('h', 24);
moment.relativeTimeThreshold('d', 28);
moment.relativeTimeThreshold('M', 12);
moment.relativeTimeThreshold('ss', 59);
moment.relativeTimeThreshold('mm', 60);
moment.relativeTimeThreshold('hh', 24);
moment.relativeTimeThreshold('dd', 28);
moment.relativeTimeThreshold('MM', 12);
moment.relativeTimeRounding(Math.floor);

function MoreDetailsNode({
  nodes, activeNodeIndex, activeChain, handleSelectNode,
}) {
  return (
    <div>
      <h1 className="heading-style-2">More Details</h1>
      <NodeSelectionTabs
        nodes={nodes}
        activeNodeIndex={activeNodeIndex}
        activeChain={activeChain}
        handleSelectNode={handleSelectNode}
      />
    </div>
  );
}

function MoreDetailsSystem({
  systems, activeSystemIndex, activeChain, handleSelectSystem,
}) {
  return (
    <div>
      <h1 className="heading-style-2">More Details</h1>
      <SystemSelectionTabs
        systems={systems}
        activeSystemIndex={activeSystemIndex}
        activeChain={activeChain}
        handleSelectSystem={handleSelectSystem}
      />
    </div>
  );
}

function NodesOverviewTableContent({ nodes, activeChain }) {
  const content = [];
  for (let i = 0; i < nodes.length; i += 1) {
    if (nodes[i].chain === activeChain) {
      content.push(
        <tr key={nodes[i].name}>
          <td>{nodes[i].name}</td>
          <td><NodeBadges node={nodes[i]} /></td>
        </tr>,
      );
    }
  }
  return content;
}

function SystemsOverviewTableContent({
  systems, activeChain, activeChainJson,
}) {
  const content = [];
  for (let i = 0; i < systems.length; i += 1) {
    if (systems[i].chain === activeChain) {
      content.push(
        <tr key={systems[i].name}>
          <td>{systems[i].name}</td>
          <td>
            <SystemBadges
              system={systems[i]}
              activeChainJson={activeChainJson}
              systemHasValidator={systems[i].systemHasValidator}
            />
          </td>
        </tr>,
      );
    }
  }
  return content;
}

function NodesOverviewTable({ nodes, activeChain }) {
  return (
    <Table responsive className="tables-style-3">
      <thead>
        <tr>
          <th>Node</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <NodesOverviewTableContent nodes={nodes} activeChain={activeChain} />
      </tbody>
    </Table>
  );
}

function SystemsOverviewTable({ systems, activeChain, activeChainJson }) {
  return (
    <Table responsive className="tables-style-3">
      <thead>
        <tr>
          <th>Systems</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <SystemsOverviewTableContent
          systems={systems}
          activeChain={activeChain}
          activeChainJson={activeChainJson}
        />
      </tbody>
    </Table>
  );
}

function NodesOverview({
  nodes, activeChain, activeNodeIndex, handleSelectNode,
}) {
  return (
    <Container>
      <h1 className="heading-style-1">Nodes Overview</h1>
      <NodesOverviewTable nodes={nodes} activeChain={activeChain} />
      <MoreDetailsNode
        nodes={nodes}
        activeNodeIndex={activeNodeIndex}
        activeChain={activeChain}
        handleSelectNode={handleSelectNode}
      />
    </Container>
  );
}

function SystemsOverview({
  systems, activeChain, activeSystemIndex, handleSelectSystem, activeChainJson,
}) {
  return (
    <Container>
      <h1 className="heading-style-1">Systems Overview</h1>
      <SystemsOverviewTable
        systems={systems}
        activeChain={activeChain}
        activeChainJson={activeChainJson}
      />
      <MoreDetailsSystem
        systems={systems}
        activeSystemIndex={activeSystemIndex}
        activeChain={activeChain}
        handleSelectSystem={handleSelectSystem}
      />
    </Container>
  );
}

function MonitorsStatusTableContent({ monitors }) {
  const content = [];

  for (let i = 0; i < monitors.length; i += 1) {
    const monitor = monitors[i];
    const monitorStats = createMonitorStats(monitor);
    content.push(
      <tr key={monitor.name + monitor.type}>
        <td>{monitor.name}</td>
        <td>{monitor.type}</td>
        {
          monitor.lastUpdate === -1
            ? <td className="time-style">{monitorStats.lastUpdate}</td>
            : (
              <TooltipOverlay
                identifier="tooltip-top"
                placement="top"
                tooltipText={moment.unix(monitorStats.lastUpdate).format(
                  'DD-MM-YYYY HH:mm:ss',
                )}
                component={(
                  <td className="time-style">
                    {moment.unix(monitorStats.lastUpdate).fromNow()}
                  </td>
                )}
              />
            )
          }
      </tr>,
    );
  }
  return content;
}

function MonitorsStatusTable({ monitors }) {
  return (
    <Table responsive className="tables-style-3">
      <thead>
        <tr>
          <th style={{ minWidth: '200px' }}>Monitor</th>
          <th style={{ minWidth: '200px' }}>Type</th>
          <th
            className="column-style"
            style={{ minWidth: '200px' }}
          >
            Last Update
          </th>
        </tr>
      </thead>
      <tbody>
        <MonitorsStatusTableContent monitors={monitors} />
      </tbody>
    </Table>
  );
}

function MonitorsStatus({ monitors }) {
  return (
    <Container>
      <h1 className="heading-style-1">Monitors Status</h1>
      <MonitorsStatusTable monitors={monitors} />
    </Container>
  );
}

class Dashboard extends Component {
  constructor(props) {
    super(props);
    this.dataTimer = null;
    this.clock = null;
    this.state = {
      chainNames: [],
      activeChain: null,
      activeChainJson: {},
      isFetchingData: true,
      // By default select the first chain
      activeChainIndex: 0,
      nodes: [],
      // By default select the first node of the active chain
      activeNodeIndex: 0,
      systems: [],
      // By default select the first system of the active chain
      activeSystemIndex: 0,
      monitors: [],
      updateClock: false,
      redisErrorOnChainChange: false,
    };
  }

  componentDidMount() {
    const { state } = this;
    this.fetchData();
    this.dataTimer = setInterval(this.fetchData.bind(this), 5000);
    this.clock = setInterval(() => this.setState({
      updateClock: !state.updateClock,
    }), 500);
  }

  componentWillUnmount() {
    clearInterval(this.dataTimer);
    clearInterval(this.clock);
    this.dataTimer = null;
    this.clock = null;
  }

  async fetchData() {
    const response = await this.fetchAlerterObjects();
    if (response === 0) {
      return 0;
    }
    return -1;
  }

  async fetchAlerterObjects() {
    const response = await this.fetchChains();
    if (response === 0) {
      this.fetchNodes();
      this.fetchSystems();
      this.fetchMonitors();
      this.setState({ isFetchingData: false });
      return 0;
    }
    this.setState({ isFetchingData: false });
    return -1;
  }

  async fetchChains() {
    const { state } = this;
    let response;

    try {
      response = await getChainNames();
    } catch (e) {
      if (e.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        ToastsStore.error(`Error: ${e.response.data.error}`, 5000);
      } else {
        // Something happened in setting up the request that triggered an Error
        ToastsStore.error(`Error: ${e.message}`, 5000);
      }
      return -1;
    }
    const chainNames = response.data.result;

    // If chainNames is empty, the config is deleted/emptied/not filled yet.
    // Therefore, no new data to display, hence return. If dashboard data is
    // already loaded, give an error message to the user.
    if (chainNames.length === 0) {
      if (state.chainNames.length !== 0) {
        ToastsStore.error('The user_config_nodes.ini file must be '
          + 'mis-configured as PANIC has no blockchains/nodes to '
          + 'monitor. Please solve this using the Settings->Nodes page and '
          + '(re)start PANIC if you want to continue using the dashboard',
        5000);
      }
      return -1;
    }
    const { activeChainIndex } = state;
    const activeChainName = chainNames[activeChainIndex];
    try {
      response = await getAllChainInfo(activeChainName);
    } catch (e) {
      if (state.chainNames.length !== 0) {
        if (e.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          ToastsStore.error(`Error: ${e.response.data.error}`, 5000);
        } else {
          // Something happened in setting up the request that triggered an
          // error
          ToastsStore.error(`Error: ${e.message}`, 5000);
        }
      }
      return -1;
    }
    const chainInfo = response.data.result;
    this.setState({
      chainNames,
      activeChain: activeChainName,
      activeChainJson: chainInfo,
      redisErrorOnChainChange: false,
    });
    return 0;
  }

  fetchNodes() {
    const { state } = this;
    const nodesJson = state.activeChainJson.nodes;
    const nodes = createNodesFromJson(state.activeChain, nodesJson);
    this.setState({ nodes });
  }

  fetchSystems() {
    const { state } = this;
    const systemsJson = state.activeChainJson.systems;
    const systems = createSystemsFromJson(state.activeChain, systemsJson);
    this.setState({ systems });
  }

  fetchMonitors() {
    const { state } = this;
    const nodeMonitors = createMonitorTypeFromJson(
      state.activeChain,
      state.activeChainJson.monitors,
      MONITOR_TYPES.node_monitor,
    );
    const systemMonitors = createMonitorTypeFromJson(
      state.activeChain,
      state.activeChainJson.monitors,
      MONITOR_TYPES.system_monitor,
    );
    const monitors = nodeMonitors.concat(systemMonitors);
    this.setState({ monitors });
  }

  handleSelectChain(selectedChain) {
    // This must be done because the 'selectedChain' value is passed as string.
    const selectedChainParsed = parseInt(selectedChain, 10);

    // Set the active node and the active system to the first node and system
    // of the selected chain and fetch it's data
    this.setState({
      isFetchingData: true,
      activeChainIndex: selectedChainParsed,
      activeNodeIndex: 0,
      activeSystemIndex: 0,
    }, async () => {
      const response = await this.fetchData();
      if (response === -1) {
        this.setState({ redisErrorOnChainChange: true });
      }
    });
  }

  handleSelectNode(selectedNode) {
    this.setState({ activeNodeIndex: parseInt(selectedNode, 10) });
  }

  handleSelectSystem(selectedSystem) {
    this.setState({ activeSystemIndex: parseInt(selectedSystem, 10) });
  }

  render() {
    const { state } = this;
    return (
      <Page
        spinnerCondition={state.isFetchingData || state.redisErrorOnChainChange}
        component={(
          <div>
            {state.chainNames.length > 0
              ? (
                <div>
                  <ChainsDropDown
                    chainNames={state.chainNames}
                    activeChainIndex={state.activeChainIndex}
                    handleSelectChain={chain => this.handleSelectChain(chain)}
                  />
                  { state.nodes.length > 0
                  && (
                    <NodesOverview
                      nodes={state.nodes}
                      activeChain={state.activeChain}
                      activeNodeIndex={state.activeNodeIndex}
                      handleSelectNode={node => this.handleSelectNode(node)}
                    />
                  )
                  }
                  { state.systems.length > 0
                  && (
                    <SystemsOverview
                      systems={state.systems}
                      activeChain={state.activeChain}
                      activeSystemIndex={state.activeSystemIndex}
                      handleSelectSystem={
                        system => this.handleSelectSystem(system)
                      }
                      activeChainJson={state.activeChainJson}
                    />
                  )
                  }
                  <MonitorsStatus monitors={state.monitors} />
                </div>
              )
              : (
                <Container
                  className="my-auto text-center error d-flex
                    align-items-center"
                >
                  <Row className="m-auto justify-content-center
                    align-items-center"
                  >
                    <Col xs="auto">
                      <p className="lead">
                        The nodes&apos; user config or Redis must be
                        mis-configured. Please set up PANIC and Redis using
                        the Settings pages and do not forget to (re)start
                        PANIC afterwards! Also please make sure that Redis is
                        running.
                      </p>
                    </Col>
                  </Row>
                </Container>
              )
            }
          </div>
        )}
      />
    );
  }
}

ChainsDropDown.propTypes = forbidExtraProps({
  chainNames: PropTypes.arrayOf(PropTypes.string).isRequired,
  activeChainIndex: PropTypes.number.isRequired,
  handleSelectChain: PropTypes.func.isRequired,
});

MoreDetailsNode.propTypes = forbidExtraProps({
  nodes: PropTypes.arrayOf(NODE_TYPE).isRequired,
  activeNodeIndex: PropTypes.number.isRequired,
  handleSelectNode: PropTypes.func.isRequired,
  activeChain: PropTypes.string.isRequired,
});

NodesOverviewTable.propTypes = forbidExtraProps({
  nodes: PropTypes.arrayOf(NODE_TYPE).isRequired,
  activeChain: PropTypes.string.isRequired,
});

NodesOverview.propTypes = forbidExtraProps({
  nodes: PropTypes.arrayOf(NODE_TYPE).isRequired,
  activeNodeIndex: PropTypes.number.isRequired,
  handleSelectNode: PropTypes.func.isRequired,
  activeChain: PropTypes.string.isRequired,
});


MonitorsStatusTable.propTypes = forbidExtraProps({
  monitors: PropTypes.arrayOf(MONITOR_TYPE).isRequired,
});

MonitorsStatus.propTypes = forbidExtraProps({
  monitors: PropTypes.arrayOf(MONITOR_TYPE).isRequired,
});

SystemsOverviewTable.propTypes = forbidExtraProps({
  systems: PropTypes.arrayOf(SYSTEM_TYPE).isRequired,
  activeChain: PropTypes.string.isRequired,
  activeChainJson: PropTypes.objectOf(PropTypes.object).isRequired,
});

SystemsOverview.propTypes = forbidExtraProps({
  systems: PropTypes.arrayOf(SYSTEM_TYPE).isRequired,
  activeChain: PropTypes.string.isRequired,
  activeChainJson: PropTypes.objectOf(PropTypes.object).isRequired,
  activeSystemIndex: PropTypes.number.isRequired,
  handleSelectSystem: PropTypes.func.isRequired,
});

MoreDetailsSystem.propTypes = forbidExtraProps({
  systems: PropTypes.arrayOf(SYSTEM_TYPE).isRequired,
  activeChain: PropTypes.string.isRequired,
  activeSystemIndex: PropTypes.number.isRequired,
  handleSelectSystem: PropTypes.func.isRequired,
});

export default Dashboard;
