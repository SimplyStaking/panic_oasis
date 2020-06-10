import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { forbidExtraProps } from 'airbnb-prop-types';
import PropTypes from 'prop-types';
import moment from 'moment';
import { createActiveNodeStats } from '../utils/dashboard';
import DataCard from './cards';
import {NODE_TYPE } from '../utils/constants';
import TooltipOverlay from './overlays';
import '../style/style.css';

function SingleRowMultipleColumnsGrid({
  content, xs, sm, md, lg,
}) {
  const columns = [];
  for (let i = 0; i < content.length; i += 1) {
    columns.push(<Col xs={xs} sm={sm} md={md} lg={lg} key={i}>{content[i]}</Col>);
  }
  return <div className="grid-container-style"><Row md>{columns}</Row></div>;
}


function NodeDataGrid({ node }) {
  const activeNodeStats = createActiveNodeStats(node);

  const cards = [
    <DataCard
      title="Peers"
      data={activeNodeStats.noOfPeers}
      key="peers-card"
    />,
    node.lastHeightUpdate === -1
      ? (
        <DataCard
          title="Latest Block Height Update"
          data={activeNodeStats.lastHeightUpdate}
          key="height-update-card"
        />
      )
      : (
        <TooltipOverlay
          identifier="height-update"
          placement="top"
          tooltipText={moment.unix(
            activeNodeStats.lastHeightUpdate,
          ).format('DD-MM-YYYY HH:mm:ss')}
          component={(
            <div>
              <DataCard
                title="Latest Block Height Update"
                data={moment.unix(activeNodeStats.lastHeightUpdate).fromNow()}
                key="height-update-card"
              />
            </div>
          )}
        />
      ),
    <DataCard
      title="Latest Block Height"
      data={activeNodeStats.height}
      key="height-card"
    />,
  ];

  if (node.isDown) {
    cards.push(
      <TooltipOverlay
        identifier="down-since"
        placement="top"
        tooltipText={moment.unix(
          activeNodeStats.wentDownAt,
        ).format('DD-MM-YYYY HH:mm:ss')}
        component={(
          <div>
            <DataCard
              title="Down Since"
              data={moment.unix(activeNodeStats.wentDownAt).fromNow()}
              key="down-since-card"
            />
          </div>
        )}
      />,
    );
  }

  if (node.isValidator) {
    cards.push(
      <DataCard
        title="Bonded Balance"
        data={activeNodeStats.bondedBalance}
        key="bonded-balance-card"
      />,
    );
    cards.push(
      <DataCard
        title="Debonding Balance"
        data={activeNodeStats.debondingBalance}
        key="debonding-balance-card"
      />,
    );
    cards.push(
      <DataCard
        title="Shares Balance"
        data={activeNodeStats.sharesBalance}
        key="shares-balance-card"
      />,
    );
    cards.push(
      <DataCard
        title="Voting Power"
        data={activeNodeStats.votingPower}
        key="voting-power-balance-card"
      />,
    );
    cards.push(
      <DataCard
        title="Consecutive Blocks Missed"
        data={activeNodeStats.consecutiveBlocksMissed}
        key="consecutive-blocks-missed-card"
      />,
    );
  }

  return <SingleRowMultipleColumnsGrid content={cards} xs={6} sm={6} md={4} lg={4} />;
}

NodeDataGrid.propTypes = forbidExtraProps({
  node: NODE_TYPE.isRequired,
});

SingleRowMultipleColumnsGrid.propTypes = forbidExtraProps({
  content: PropTypes.arrayOf(PropTypes.oneOfType([
    PropTypes.symbol, PropTypes.object,
  ])).isRequired,
  xs: PropTypes.number.isRequired,
  sm: PropTypes.number.isRequired,
  lg: PropTypes.number.isRequired,
  md: PropTypes.number.isRequired,
});

export { SingleRowMultipleColumnsGrid, NodeDataGrid };
