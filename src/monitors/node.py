import logging
from datetime import datetime, timedelta
from typing import Optional, List
import dateutil

from src.alerters.reactive.node import Node
from src.alerts.alerts import FoundLiveArchiveNodeAgainAlert
from src.channels.channel import ChannelSet
from src.monitors.monitor import Monitor
from src.store.store_keys import Keys
from src.utils.config_parsers.internal import InternalConfig
from src.utils.config_parsers.internal_parsed import InternalConf
from src.utils.data_wrapper.oasis_api import OasisApiWrapper
from src.utils.exceptions import \
    NoLiveNodeConnectedWithAnApiServerException, \
    NoLiveArchiveNodeConnectedWithAnApiServerException
from src.utils.parsing import parse_int_from_string
from src.store.redis.redis_api import RedisApi
from src.utils.types import NONE


class NodeMonitor(Monitor):

    def __init__(self, monitor_name: str, channels: ChannelSet,
                 logger: logging.Logger, node_monitor_max_catch_up_blocks: int,
                 redis: Optional[RedisApi], node: Node,
                 archive_alerts_disabled: bool, data_sources: List[Node],
                 internal_conf: InternalConfig = InternalConf):
        super().__init__(monitor_name, channels, logger, redis, internal_conf)

        self._node = node
        self._data_wrapper = OasisApiWrapper(logger)
        self._node_monitor_max_catch_up_blocks = \
            node_monitor_max_catch_up_blocks

        self._redis_alive_key_timeout = \
            self._internal_conf.redis_node_monitor_alive_key_timeout

        self._redis_last_height_key_timeout = \
            self._internal_conf.redis_node_monitor_last_height_key_timeout

        # The data sources for indirect monitoring are all nodes from the same
        # chain which have been set as a data source in the config.
        self._indirect_monitoring_data_sources = data_sources

        # The data sources for archive monitoring are all archive nodes from
        # the same chain that have been set as data source in the config.
        self._archive_monitoring_data_sources = [node for node in data_sources
                                                 if node.is_archive_node]
        self.last_data_source_used = None
        self._last_height_checked = NONE
        self._monitor_is_catching_up = False
        self._indirect_monitoring_disabled = len(data_sources) == 0
        self._no_live_archive_node_alert_sent = False
        self._archive_alerts_disabled = archive_alerts_disabled

        self.load_state()

    def is_catching_up(self) -> bool:
        return self._monitor_is_catching_up

    @property
    def indirect_monitoring_disabled(self) -> bool:
        return self._indirect_monitoring_disabled

    @property
    def node(self) -> Node:
        return self._node

    @property
    def last_height_checked(self) -> int:
        return self._last_height_checked

    @property
    def no_live_archive_node_alert_sent(self) -> bool:
        return self._no_live_archive_node_alert_sent

    @property
    def data_wrapper(self) -> OasisApiWrapper:
        return self._data_wrapper

    @property
    def indirect_monitoring_data_sources(self) -> List[Node]:
        return self._indirect_monitoring_data_sources

    @property
    def archive_monitoring_data_sources(self) -> List[Node]:
        return self._archive_monitoring_data_sources

    # The data_source_indirect function returns a node for the indirect
    # monitoring. Since indirect monitoring does not require data from past
    # chain state, the data_source_indirect function may return a node which is
    # not an archive node.
    @property
    def data_source_indirect(self) -> Node:
        # Get one of the nodes to use as data source
        for n in self._indirect_monitoring_data_sources:
            nodes_connected_to_an_api = \
                self.data_wrapper.get_web_sockets_connected_to_an_api(
                    n.api_url)
            if n.name in nodes_connected_to_an_api and not n.is_down:
                self.last_data_source_used = n
                self._data_wrapper.ping_node(n.api_url, n.name)
                return n
        raise NoLiveNodeConnectedWithAnApiServerException()

    # The data_source_archive function returns a node for archive monitoring.
    # Since archive monitoring requires data from past chain state, the
    # data_source_archive function returns only nodes which are archive nodes.
    @property
    def data_source_archive(self) -> Node:
        # Get one of the archive nodes to use as data source
        for n in self._archive_monitoring_data_sources:
            nodes_connected_to_an_api = \
                self.data_wrapper.get_web_sockets_connected_to_an_api(
                    n.api_url)
            if n.name in nodes_connected_to_an_api and not n.is_down:
                self.last_data_source_used = n
                self._data_wrapper.ping_node(n.api_url, n.name)
                return n
        raise NoLiveArchiveNodeConnectedWithAnApiServerException()

    def load_state(self) -> None:

        # If Redis is enabled, load any previously stored state
        if self.redis_enabled:
            key_lh = Keys.get_node_monitor_last_height_checked(
                self.monitor_name)
            self._last_height_checked = self.redis.get_int(key_lh, NONE)

            self.logger.debug(
                'Restored %s state: %s=%s', self._monitor_name,
                key_lh, self._last_height_checked)

    def save_state(self) -> None:
        # If Redis is enabled, save the current time, indicating that the node
        # monitor was alive at this time, the current session index,
        # and the last height checked.
        if self.redis_enabled:
            key_lh = Keys.get_node_monitor_last_height_checked(
                self.monitor_name)
            key_alive = Keys.get_node_monitor_alive(self.monitor_name)

            self.logger.debug(
                'Saving node monitor state: %s=%s', self._monitor_name,
                key_lh, self._last_height_checked)

            # Set last height checked key
            until = timedelta(seconds=self._redis_last_height_key_timeout)
            self.redis.set_for(key_lh, self._last_height_checked, until)

            # Set alive key (to be able to query latest update from Telegram)
            until = timedelta(seconds=self._redis_alive_key_timeout)
            self.redis.set_for(
                key_alive, str(datetime.now().timestamp()), until
            )
    def status(self) -> str:

        if self._node.is_validator:
            return self._node.status() + \
                ', last_height_checked={}' \
                       .format(self._last_height_checked)
        else:
            return self._node.status()

    def monitor_direct(self) -> None:

        # Check if node is accessible
        self._logger.debug('Checking if %s is alive', self._node)
        self._data_wrapper.ping_node(self._node.api_url, self._node.name)
        self._node.set_as_up(self.channels, self.logger)

        # Get isSyncing Status
        is_syncing = not self.data_wrapper.get_is_syncing(self._node.api_url,
                                                        self._node.name)
        self._logger.debug('%s is syncing: %s', self._node, is_syncing)
        self._node.set_is_syncing(is_syncing, self.channels, self.logger)

        # Set number of peers
        no_of_peers = self.data_wrapper.get_prometheus_gauge(self._node.api_url,
        self._node.name, "tendermint_p2p_peers")
        self._logger.debug('%s no. of peers: %s', self._node, no_of_peers)
        self._node.set_no_of_peers(int(float(no_of_peers)), self.channels,
                                    self.logger)

        # Update finalized block height
        finalized_block_header = self.data_wrapper.get_block_header(
            self._node.api_url, self._node.name)

        # Update finalized block
        finalized_block_height = parse_int_from_string(
            str(finalized_block_header['height']))

        self._logger.debug('%s finalized_block_height: %s', self._node,
                            finalized_block_height)

        self._node.update_finalized_block_height(finalized_block_height,
                                                 self.logger, self.channels)

        # Set API as up, and declare that node was connected to the API
        self.data_wrapper.set_api_as_up(self.monitor_name, self.channels)
        self.node.connect_with_api(self.channels, self.logger)

    def _monitor_archive_state(self) -> None:

        # Data source must be saved to avoid situations where
        # last_height_to_check < finalized_block_height
        archive_node = self.data_source_archive
        last_height_to_check = archive_node.finalized_block_height
        
        if self._last_height_checked == NONE:
            self._last_height_checked = last_height_to_check - 1

        height_to_check = self._last_height_checked

        # If the data source node's finalized height is less than the height
        # already checked, there is no need to check that block.
        if last_height_to_check < height_to_check:
            pass
        elif last_height_to_check - self._last_height_checked > \
                self._node_monitor_max_catch_up_blocks:
            height_to_check = last_height_to_check - \
                self._node_monitor_max_catch_up_blocks
            self._check_events(height_to_check, archive_node)
            self._last_height_checked = height_to_check
        elif height_to_check <= last_height_to_check:
            self._check_events(height_to_check, archive_node)
            self._last_height_checked = height_to_check

        if last_height_to_check - self._last_height_checked > 2:
            self._monitor_is_catching_up = True
        else:
            self._monitor_is_catching_up = False

        # Unset, so that if in the next monitoring round an archive node is not
        # found, the operator is informed accordingly.
        if self._no_live_archive_node_alert_sent:
            self._no_live_archive_node_alert_sent = False
            self.channels.alert_info(FoundLiveArchiveNodeAgainAlert(
                self.monitor_name))

    def _monitor_indirect_validator(self) -> None:

        # Get dictionary of validators at current block height
        session_validators = self.data_wrapper.get_session_validators(
            self.data_source_indirect.api_url, self.data_source_indirect.name)

        # Attempt to return validator from list of session_validators
        validator_data = list(filter(
            lambda validator: validator['id'] == self._node.node_public_key,
            session_validators))

        is_active = False if len(validator_data) == 0 else True
        self._logger.debug('%s active: %s', self._node, is_active)
        self.node.set_active(is_active, self.channels, self.logger)

        voting_power = 0 if is_active == False  \
            else validator_data[0]['voting_power']

        self._logger.debug('%s voting power: %s', self.node, voting_power)
        self.node.set_voting_power(int(voting_power), self.channels,
                                    self.logger)

        # Get node status and from that the last height to be checked
        latestblock = self.data_wrapper.get_consensus_block(
            self.data_source_indirect.api_url, self.data_source_indirect.name)

        # The Precommits(Signatures) are of the block before
        last_height_to_check = int(latestblock['height'])

        # If the chain has not started, return as there are no blocks to get
        if last_height_to_check == 0:
            return

        # If this is the first height being checked, ignore previous heights
        if self._last_height_checked == NONE:
            self._last_height_checked = last_height_to_check - 1

        # Consider any height that is after the previous last height
        height = self._last_height_checked
        if last_height_to_check - self._last_height_checked > \
                self._node_monitor_max_catch_up_blocks:
            height = last_height_to_check - \
                self._node_monitor_max_catch_up_blocks
            self._check_block(height)
            self._check_events(height, None)
            self._last_height_checked = height
        elif height <= last_height_to_check:
            self._check_block(height)
            self._check_events(height, None)
            self._last_height_checked = height

        if last_height_to_check - self._last_height_checked > 2:
            self._monitor_is_catching_up = True
        else:
            self._monitor_is_catching_up = False

        # Retrieve the bonding balance and set it
        staking_account = self.data_wrapper.get_staking_account(
            self.data_source_indirect.api_url, self.data_source_indirect.name,
            self._node.staking_address)

        bonded_balance = parse_int_from_string(
            str(staking_account['escrow']['active']['balance']))
        self._logger.debug('%s bonded_balance: %s', self._node, bonded_balance)
        self._node.set_bonded_balance(bonded_balance, self.channels,
                                      self.logger)

        debonding_balance = parse_int_from_string(
            str(staking_account['escrow']['debonding']['balance']))
        self._logger.debug('%s debonding_balance: %s', self._node,
                           debonding_balance)
        self._node.set_debonding_balance(debonding_balance, self.channels,
                                         self.logger)

        # Staking Delegations for self Entity ID
        staking_delegations = self.data_wrapper.get_staking_delegations(
            self.data_source_indirect.api_url, self.data_source_indirect.name,
            self._node.staking_address
        )

        shares = 0
        for i, j in enumerate(staking_delegations):
            shares += int(staking_delegations[j]['shares'])

        # Set shares balance
        self._logger.debug('%s shares balance: %s', self._node, shares)
        self._node.set_shares_balance(shares, self.channels, self.logger)

        if not self._archive_alerts_disabled:
            self._monitor_archive_state()

        self._last_height_checked += 1
        

    def _monitor_indirect_full_node(self) -> None:
        # These are not needed for full nodes, and thus must be given a
        # dummy value since NoneTypes cannot be saved in redis.

        # Set bonded balance
        balance = 0
        self._logger.debug('%s bonded balance: %s', self._node, balance)
        self._node.set_bonded_balance(balance, self.channels, self.logger)

        # Set debonding balance
        self._logger.debug('%s debonding balance: %s', self._node, balance)
        self._node.set_debonding_balance(balance, self.channels, self.logger)

        # Set shares balance
        self._logger.debug('%s shares balance: %s', self._node, balance)
        self._node.set_shares_balance(balance, self.channels, self.logger)

        # Set active
        self._logger.debug('%s is active: %s', self._node, False)
        self._node.set_active(False, self.channels, self.logger)

    def monitor_indirect(self) -> None:
        if self._node.is_validator:
            self._monitor_indirect_validator()

            # Set API as up and declare that used node is connected with the API
            self.data_wrapper.set_api_as_up(self.monitor_name, self.channels)
            self.last_data_source_used.connect_with_api(
                self.channels, self.logger)
        else:
            self._monitor_indirect_full_node()

    def monitor(self) -> None:
        # Monitor part of the node state by querying the node directly
        self.monitor_direct()
        # Monitor part of the node state by querying the node indirectly if
        # indirect monitoring is enabled.
        if not self.indirect_monitoring_disabled:
            self.monitor_indirect()

        # Output status
        self._logger.info('%s status: %s', self._node, self.status())

    def _check_events(self, height: int, archive_node: Optional[Node]) -> None:
        self._logger.info('%s obtaining data at height %s', self._monitor_name,
                          height)

        if archive_node == None:
            events = self.data_wrapper.get_events_by_height(
                self.data_source_indirect.api_url,
                self.data_source_indirect.name,
                str(height))
        else:
            events = self.data_wrapper.get_events_by_height(
                archive_node.api_url,
                archive_node.name,
                str(height))

        if events != None:
            self._logger.debug('Events found at block height : '+str(height))
            # Iterate through the list of events
            for event in events:
                # Call method based on whether block missed or not
                for v in self._indirect_monitoring_data_sources:
                    v.process_event(
                        str(height), event, self.channels, self.logger)

            self._logger.debug('Finished processing events.')

    def _check_block(self, height: int) -> None:
        self._logger.info('%s obtaining data at height %s',
                          self._monitor_name, height)

        # Get PreCommits of the last block
        signed_blocked = self.data_wrapper.get_signed_blocks(
            self.data_source_indirect.api_url, self.data_source_indirect.name,
            str(height))

        # Get validators participating in the signatures of last commit
        block_precommits = signed_blocked['signatures']
        non_null_precommits = filter(lambda p: p, block_precommits)

        block_precommits_validators = set(
            map(lambda p: p['validator_address'], non_null_precommits))

        total_no_of_missing_validators = \
            len(block_precommits) - len(block_precommits_validators)

        self._logger.debug('Precommit validators: %s',
                           block_precommits_validators)

        self._logger.debug('Total missing validators: %s',
                           total_no_of_missing_validators)

        block_header = self.data_wrapper.get_block_header_height(
            self.data_source_indirect.api_url, self.data_source_indirect.name,
            str(height))

        # Call method based on whether block missed or not
        for v in self._indirect_monitoring_data_sources:
            if v.is_validator and v.tendermint_address_key not in \
                block_precommits_validators:
                block_time = block_header['time']
                v.add_missed_block(
                    height - 1,  # '- 1' since it's actually previous height
                    dateutil.parser.parse(block_time, ignoretz=True),
                    total_no_of_missing_validators, self.channels,
                    self.logger)
            else:
                v.clear_missed_blocks(self.channels, self.logger)

        self._logger.debug('Moving to next height.')
