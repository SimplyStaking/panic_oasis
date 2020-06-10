import logging
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock

from redis import ConnectionError as RedisConnectionError

from src.alerters.reactive.node import Node, NodeType
from src.alerts.alerts import FoundLiveArchiveNodeAgainAlert
from src.channels.channel import ChannelSet
from src.monitors.node import NodeMonitor
from src.store.store_keys import Keys
from src.utils.exceptions import \
    NoLiveNodeConnectedWithAnApiServerException, \
    NoLiveArchiveNodeConnectedWithAnApiServerException
from src.store.redis.redis_api import RedisApi
from src.utils.scaling import scale_to_giga
from src.utils.types import NONE
from test import TestInternalConf, TestUserConf
from test.test_helpers import CounterChannel

GET_WEB_SOCKETS_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.' \
    'get_web_sockets_connected_to_an_api'

PING_NODE_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.ping_node'

PING_API_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.ping_api'

GET_REGISTRY_NODE_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_node'

GET_CONSENSUS_GENESIS_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_consensus_genesis'

GET_PEERS_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_prometheus_gauge'

GET_SYNCING_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_is_syncing'

GET_CONSENSUS_BLOCK_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_consensus_block'

GET_FINALIZED_HEAD_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_block_header'

GET_BLOCK_HEADER_AT_HEIGHT_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_block_header_height'

GET_HEADER_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_block_header'

GET_SESSION_VALIDATORS_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_session_validators'

GET_SIGNED_BLOCKS_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_signed_blocks'

GET_TENDERMINT_ADDRESSS_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_tendermint_address'

GET_REGISTRY_NODES_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_registry_node'

GET_STAKING_ACCOUNT_INFO_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_staking_account_info'

GET_STAKING_DELEGATIONS_INFO_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_staking_delegations'

GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION = \
    'src.monitors.node.OasisApiWrapper.get_events_by_height'

DATA_SOURCE_INDIRECT_PATH = \
    'src.monitors.node.NodeMonitor.data_source_indirect'

DATA_SOURCE_ARCHIVE_PATH = \
    'src.monitors.node.NodeMonitor.data_source_archive'

# @unittest.skip("Skipping Test Node Monitor Without Redis")
# noinspection PyUnresolvedReferences
class TestNodeMonitorWithoutRedis(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = logging.getLogger('dummy')
        self.logger_events = logging.getLogger('dummy_events')
        self.monitor_name = 'testnodemonitor'
        self.counter_channel = CounterChannel(self.logger)
        self.channel_set = ChannelSet([self.counter_channel], TestInternalConf)
        self.node_monitor_max_catch_up_blocks = \
            TestInternalConf.node_monitor_max_catch_up_blocks
        self.redis = None
        self.archive_alerts_disabled = False
        self.data_sources = []
        self.chain = 'testchain'

        self.full_node_name = 'testfullnode'
        self.full_node_api_url = '123.123.123.11:9944'
        self.full_node_consensus_key = "ANDSAdisadjasdaANDAsa"
        self.full_node_tendermint_key = "ASFLNAFIISDANNSDAKKS2313AA"
        self.full_node_entity_public_key="a98dabsfkjabfkjabsf9j",

        self.full_node = Node(self.full_node_name, self.full_node_api_url,
                              NodeType.NON_VALIDATOR_FULL_NODE, '', self.chain,
                              None, True, self.full_node_consensus_key,
                              self.full_node_tendermint_key, 
                              self.full_node_entity_public_key,
                              TestInternalConf)

        self.full_node_monitor = NodeMonitor(
            self.monitor_name, self.channel_set, self.logger, 
            self.node_monitor_max_catch_up_blocks, 
            self.redis, self.full_node, self.archive_alerts_disabled, 
            self.data_sources, TestInternalConf)

        self.validator_name = 'testvalidator'
        self.validator_api_url = '13.13.14.11:9944'
        self.validator_consensus_key = "KASDB01923udlakd19sad"
        self.validator_tendermint_key = "ALSFNF9)901jjelakNALKNDLKA"
        self.validator_node_public_key = "DFJGDF8G898fdghb98dg9wetg9we00w"
        self.validator_node_entity_public_key="s12adsdghas9as0sa9dhnaskdlan",

        self.validator = Node(self.validator_name, self.validator_api_url,
                              NodeType.VALIDATOR_FULL_NODE,
                              self.validator_node_public_key, self.chain,
                              None, True, self.validator_consensus_key,
                              self.validator_tendermint_key, 
                              self.validator_node_entity_public_key,
                              TestInternalConf)

        self.validator_monitor = NodeMonitor(
            self.monitor_name, self.channel_set, self.logger, 
            self.node_monitor_max_catch_up_blocks, 
            self.redis, self.validator, self.archive_alerts_disabled, 
            self.data_sources, TestInternalConf)

        self.dummy_last_height_checked = 1000
        self.dummy_bonded_balance = scale_to_giga(5)
        self.dummy_debonding_balance = scale_to_giga(5)
        self.dummy_shares_balance = scale_to_giga(5)
        self.dummy_height_to_check = 1000
        self.dummy_no_of_peers = 100
        self.dummy_is_missing_blocks = False
        self.dummy_active = True
        self.dummy_finalized_block_height = 34535
        self.dummy_api_url_1 = "11.22.33.11:9944"
        self.dummy_api_url_2 = "11.22.33.12:9944"
        self.dummy_api_url_3 = "11.22.33.13:9944"
        self.dummy_api_url_4 = "11.22.33.14:9944"
        self.dummy_api_url_5 = "11.22.33.15:9944"
        self.dummy_node_name_1 = "testnode1"
        self.dummy_node_name_2 = "testnode2"
        self.dummy_node_name_3 = "testnode3"
        self.dummy_node_name_4 = "testnode4"
        self.dummy_node_name_5 = "testnode5"
        self.dummy_validator_node_name_2 = "testvalidatornode2"
        self.dummy_validator_node_name_3 = "testvalidatornode3"
        self.dummy_node_consensus_key_1 = "consensus_key_1"
        self.dummy_node_consensus_key_2 = "consensus_key_2"
        self.dummy_node_consensus_key_3 = "consensus_key_3"
        self.dummy_node_tendermint_key_1 = "consensus_key_1"
        self.dummy_node_tendermint_key_2 = "consensus_key_2"
        self.dummy_node_tendermint_key_3 = "consensus_key_3"
        self.dummy_node_entity_public_key_1 = "entity_key_1"
        self.dummy_node_entity_public_key_2 = "entity_key_2"
        self.dummy_node_entity_public_key_3 = "entity_key_3"
        self.dummy_full_node_1 = Node(name=self.dummy_node_name_1,
                                      api_url=self.dummy_api_url_1,
                                      node_type=NodeType.NON_VALIDATOR_FULL_NODE,
                                      node_public_key='',
                                      chain=self.chain, redis=None,
                                      is_archive_node=True,
                                      consensus_public_key='',
                                      tendermint_address_key='',
                                      entity_public_key='',
                                      internal_conf=TestInternalConf)
        self.dummy_full_node_2 = Node(name=self.dummy_node_name_2,
                                      api_url=self.dummy_api_url_2,
                                      node_type=NodeType.NON_VALIDATOR_FULL_NODE,
                                      node_public_key='',
                                      chain=self.chain, redis=None,
                                      is_archive_node=True,
                                      consensus_public_key='',
                                      tendermint_address_key='',
                                      entity_public_key='',
                                      internal_conf=TestInternalConf)
        self.dummy_full_node_3 = Node(name=self.dummy_node_name_3,
                                      api_url=self.dummy_api_url_3,
                                      node_type=NodeType.NON_VALIDATOR_FULL_NODE,
                                      node_public_key='',
                                      chain=self.chain, redis=None,
                                      is_archive_node=True,
                                      consensus_public_key='',
                                      tendermint_address_key='',
                                      entity_public_key='',
                                      internal_conf=TestInternalConf)
        self.dummy_full_node_4 = Node(name=self.dummy_node_name_5,
                                      api_url=self.dummy_api_url_5,
                                      node_type=NodeType.NON_VALIDATOR_FULL_NODE,
                                      node_public_key='',
                                      chain=self.chain, redis=None,
                                      is_archive_node=False,
                                      consensus_public_key='',
                                      tendermint_address_key='',
                                      entity_public_key='',
                                      internal_conf=TestInternalConf)

        self.dummy_take_event_owner = {"escrow" : {"take": 
            {"owner" : self.dummy_node_entity_public_key_1, 
             "tokens": "2000000000"}}}

        self.dummy_validator_node_1 = Node(
            name=self.dummy_node_name_4, api_url=self.dummy_api_url_4,
            node_type=NodeType.VALIDATOR_FULL_NODE,
            node_public_key=self.validator_node_public_key,
            chain=self.chain, redis=None, is_archive_node=True,
            consensus_public_key=self.dummy_node_consensus_key_1,
            tendermint_address_key=self.dummy_node_tendermint_key_1,
            entity_public_key=self.dummy_node_entity_public_key_1,
            internal_conf=TestInternalConf)

        self.dummy_validator_node_2 = Node(
            name=self.dummy_validator_node_name_2, api_url=self.dummy_api_url_4,
            node_type=NodeType.VALIDATOR_FULL_NODE,
            node_public_key=self.validator_node_public_key,
            chain=self.chain, redis=None, is_archive_node=True,
            consensus_public_key=self.dummy_node_consensus_key_2,
            tendermint_address_key=self.dummy_node_tendermint_key_2,
            entity_public_key=self.dummy_node_entity_public_key_2,
            internal_conf=TestInternalConf)

        self.dummy_validator_node_3 = Node(
            name=self.dummy_validator_node_name_3, api_url=self.dummy_api_url_4,
            node_type=NodeType.VALIDATOR_FULL_NODE,
            node_public_key=self.validator_node_public_key,
            chain=self.chain, redis=None, is_archive_node=True,
            consensus_public_key=self.dummy_node_consensus_key_3,
            tendermint_address_key=self.dummy_node_tendermint_key_3,
            entity_public_key=self.dummy_node_entity_public_key_3,
            internal_conf=TestInternalConf)

    def test_indirect_monitoring_data_sources_field_set_correctly(self) -> None:
        self.data_sources = [
            self.dummy_full_node_1, self.dummy_full_node_2,
            self.dummy_full_node_3, self.dummy_full_node_4,
            self.dummy_validator_node_1
        ]
        test_monitor = NodeMonitor(
            self.monitor_name, self.channel_set, self.logger,
            self.node_monitor_max_catch_up_blocks, 
            self.redis, self.validator, self.archive_alerts_disabled, 
            self.data_sources, TestInternalConf)

        self.assertEqual(test_monitor.indirect_monitoring_data_sources,
                         self.data_sources)

    def test_archive_monitoring_data_sources_field_set_correctly(self) -> None:
        self.data_sources = [
            self.dummy_full_node_1, self.dummy_full_node_2,
            self.dummy_full_node_3, self.dummy_full_node_4,
            self.dummy_validator_node_1
        ]
        test_monitor = NodeMonitor(
            self.monitor_name, self.channel_set, self.logger,
            self.node_monitor_max_catch_up_blocks, 
            self.redis, self.validator, self.archive_alerts_disabled, 
            self.data_sources, TestInternalConf)
        expected_result = [self.dummy_full_node_1, self.dummy_full_node_2,
                           self.dummy_full_node_3, self.dummy_validator_node_1]

        self.assertEqual(test_monitor.archive_monitoring_data_sources,
                         expected_result)

    def test_is_catching_up_false_by_default(self) -> None:
        self.assertFalse(self.validator_monitor.is_catching_up())

    def test_is_indirect_monitoring_disabled_true_if_no_data_sources(
            self) -> None:
        self.assertTrue(self.validator_monitor.indirect_monitoring_disabled)

    def test_is_indirect_monitoring_disabled_false_if_data_sources_given(
            self) -> None:
        self.data_sources = [
            self.dummy_full_node_1, self.dummy_full_node_2
        ]
        test_monitor = NodeMonitor(
            self.monitor_name, self.channel_set, self.logger,
            self.node_monitor_max_catch_up_blocks, 
            self.redis, self.validator, self.archive_alerts_disabled, 
            self.data_sources, TestInternalConf)

        self.assertFalse(test_monitor.indirect_monitoring_disabled)

    def test_last_height_checked_NONE_by_default(self) -> None:
        self.assertEqual(NONE, self.validator_monitor.last_height_checked)

    def test_no_live_archive_node_alert_sent_false_by_default(self) -> None:
        self.assertFalse(self.validator_monitor.no_live_archive_node_alert_sent)

    @patch(PING_NODE_FUNCTION, return_value=None)
    @patch(GET_WEB_SOCKETS_FUNCTION, return_value= [
        "testnode1",
        "testnode2",
        "testnode3",
        "testnode4"
    ])
    def test_data_source_chooses_an_online_full_node_connected_to_the_API(
            self, mock_get_web_sockets, _) -> None:
        self.dummy_full_node_1.set_as_down(self.channel_set, self.logger)
        self.dummy_validator_node_1.set_as_down(self.channel_set, self.logger)
        self.validator_monitor._indirect_monitoring_data_sources = [
            self.dummy_full_node_1, self.dummy_validator_node_1,
            self.dummy_full_node_2, self.dummy_full_node_3]

        mock_get_web_sockets.return_value = [
            self.dummy_node_name_1,
            self.dummy_node_name_4,
            self.dummy_node_name_3,
            self.dummy_node_name_5]

        node = self.validator_monitor.data_source_indirect

        self.assertEqual(node.name, self.dummy_node_name_3)

    @patch(PING_NODE_FUNCTION, return_value=None)
    @patch(GET_WEB_SOCKETS_FUNCTION, return_value= [
        "testnode1",
        "testnode2",
        "testnode3",
        "testnode4"
    ])
    def test_data_source_chooses_an_online_validator_node_connected_to_the_API(
            self, mock_get_web_sockets, _) -> None:

        self.dummy_full_node_1.set_as_down(self.channel_set, self.logger)
        self.dummy_full_node_2.set_as_down(self.channel_set, self.logger)
        
        self.validator_monitor._indirect_monitoring_data_sources = [
            self.dummy_full_node_1, self.dummy_validator_node_1,
            self.dummy_full_node_2, self.dummy_full_node_3]
        
        mock_get_web_sockets.return_value = [
            self.dummy_node_name_1,
            self.dummy_node_name_4,
            self.dummy_node_name_3,
            self.dummy_node_name_5]

        node = self.validator_monitor.data_source_indirect

        self.assertEqual(node.name, self.dummy_node_name_4)

    @patch(GET_WEB_SOCKETS_FUNCTION)
    def test_data_source_indirect_raises_exception_if_no_node_is_eligible_for_choosing(
            self, mock_get_web_sockets) -> None:
        self.dummy_full_node_1.set_as_down(self.channel_set, self.logger)
        self.dummy_full_node_3.set_as_down(self.channel_set, self.logger)

        self.validator_monitor._indirect_monitoring_data_sources = [
            self.dummy_full_node_1,
            self.dummy_full_node_2,
            self.dummy_full_node_3,
            self.dummy_validator_node_1]

        mock_get_web_sockets.return_value = [self.dummy_api_url_1]

        try:
            _ = self.validator_monitor.data_source_indirect
            self.fail('Expected NoLiveNodeConnectedWithAnApiServerException'
                      ' exception to be thrown.')
        except NoLiveNodeConnectedWithAnApiServerException:
            pass

    @patch(PING_NODE_FUNCTION, return_value=None)
    @patch(GET_WEB_SOCKETS_FUNCTION, return_value= [
        "testnode1",
        "testnode5"
    ])
    def test_data_source_archive_chooses_an_online_archive_full_node_connected_to_the_API(
            self, mock_get_web_sockets, _) -> None:
        self.dummy_full_node_1.set_as_down(self.channel_set, self.logger)
        self.dummy_full_node_3.set_as_down(self.channel_set, self.logger)
        self.validator_monitor._archive_monitoring_data_sources = [
            self.dummy_full_node_1, self.dummy_full_node_2,
            self.dummy_full_node_3, self.dummy_validator_node_1,
            self.dummy_full_node_4]

        mock_get_web_sockets.return_value = [self.dummy_node_name_1,
                                             self.dummy_node_name_5]
        node = self.validator_monitor.data_source_archive

        self.assertEqual(node.name, self.dummy_node_name_5)

    @patch(PING_NODE_FUNCTION, return_value=None)
    @patch(GET_WEB_SOCKETS_FUNCTION, return_value= [
        "testnode1",
        "testnode4",
        "testnode5"
    ])
    def test_data_source_archive_chooses_an_online_archive_validator_node_connected_to_the_API(
            self, mock_get_web_sockets, _) -> None:

        self.dummy_full_node_1.set_as_down(self.channel_set, self.logger)
        self.dummy_full_node_3.set_as_down(self.channel_set, self.logger)
        self.dummy_full_node_2.set_as_down(self.channel_set, self.logger)

        self.validator_monitor._archive_monitoring_data_sources = [
            self.dummy_full_node_1, self.dummy_full_node_2,
            self.dummy_full_node_3, self.dummy_validator_node_1,
            self.dummy_full_node_4]
        
        mock_get_web_sockets.return_value = [self.dummy_node_name_1,
                                             self.dummy_node_name_4,
                                             self.dummy_node_name_5]

        node = self.validator_monitor.data_source_archive

        self.assertEqual(node.name, self.dummy_node_name_4)

    @patch(GET_FINALIZED_HEAD_FUNCTION, return_value={
        "height":"523686"
    })
    @patch(PING_NODE_FUNCTION, return_value="pong")
    @patch(GET_SYNCING_FUNCTION, return_value="true")
    @patch(GET_PEERS_FUNCTION, return_value="92")
    def test_monitor_direct_sets_node_state_to_retrieved_data(
            self, _1, _2, _3, _4) -> None:
        self.validator_monitor.monitor_direct()

        self.assertFalse(self.validator.is_down)
        self.assertFalse(self.validator.is_syncing)
        self.assertEqual(self.validator.no_of_peers, 92)
        self.assertEqual(self.validator.finalized_block_height, 523686)

    @patch(GET_FINALIZED_HEAD_FUNCTION, return_value={
        "height":"523686"
    })
    @patch(PING_NODE_FUNCTION, return_value="pong")
    @patch(GET_SYNCING_FUNCTION, return_value="true")
    @patch(GET_PEERS_FUNCTION, return_value="92")
    @patch(PING_NODE_FUNCTION, return_value=None)
    def test_monitor_direct_connects_node_to_api_if_monitoring_successful(
            self, _1, _2, _3_, _4, _5) -> None:
        self.validator.disconnect_from_api(self.channel_set, self.logger)
        self.assertFalse(self.validator.is_connected_to_api_server)
        self.counter_channel.reset()
        self.validator_monitor.monitor_direct()

        self.assertTrue(self.validator.is_connected_to_api_server)

    @patch(GET_WEB_SOCKETS_FUNCTION)
    def test_data_source_archive_raises_exception_if_no_archive_node_is_eligible_for_choosing(
            self, mock_get_web_sockets) -> None:
        self.dummy_full_node_1.set_as_down(self.channel_set, self.logger)
        self.dummy_full_node_3.set_as_down(self.channel_set, self.logger)
        self.dummy_validator_node_1.set_as_down(self.channel_set, self.logger)
        self.validator_monitor._archive_monitoring_data_sources = [
            self.dummy_full_node_1, self.dummy_full_node_2,
            self.dummy_full_node_3, self.dummy_validator_node_1]
        mock_get_web_sockets.return_value = [self.dummy_api_url_1,
                                             self.dummy_api_url_5]

        try:
            _ = self.validator_monitor.data_source_archive
            self.fail('Expected '
                      'NoLiveArchiveNodeConnectedWithAnApiServerException'
                      ' exception to be thrown.')
        except NoLiveArchiveNodeConnectedWithAnApiServerException:
            pass

    def test_status_returns_as_expected_for_validator_monitor(self) -> None:
        self.validator_monitor._last_height_checked = \
            self.dummy_last_height_checked
        self.validator._bonded_balance = self.dummy_bonded_balance
        self.validator._debonding_balance = self.dummy_debonding_balance
        self.validator._shares_balance = self.dummy_shares_balance
        self.validator._no_of_peers = self.dummy_no_of_peers
        self.validator._active = self.dummy_active
        self.validator._finalized_block_height = \
            self.dummy_finalized_block_height
        self.validator._is_missing_blocks = self.dummy_is_missing_blocks

        expected_output = "bonded_balance={}, debonding_balance={}, " \
                          "shares_balance={}, "\
                          "is_syncing=False, " \
                          "no_of_peers={}, active={}, " \
                          "finalized_block_height={}, " \
                          "is_missing_blocks={}, " \
                          "last_height_checked={}".format(
            self.dummy_bonded_balance,
            self.dummy_debonding_balance,
            self.dummy_shares_balance,
            self.dummy_no_of_peers,
            self.dummy_active,
            self.dummy_finalized_block_height,
            self.dummy_is_missing_blocks,
            self.dummy_last_height_checked)
        self.assertEqual(expected_output, self.validator_monitor.status())

    def test_status_returns_as_expected_for_full_node_monitor(self) -> None:
        self.full_node._no_of_peers = self.dummy_no_of_peers
        self.full_node._finalized_block_height = \
            self.dummy_finalized_block_height

        expected_output = "bonded_balance={}, debonding_balance={}, " \
                          "shares_balance={}, " \
                          "is_syncing=False, " \
                          "no_of_peers={}, active={}, " \
                          "finalized_block_height={}, " \
                          "is_missing_blocks=False" \
                          .format(
            None, None, None, self.dummy_no_of_peers, None,
            self.dummy_finalized_block_height)

        self.assertEqual(expected_output, self.full_node_monitor.status())

    @patch(GET_FINALIZED_HEAD_FUNCTION, return_value={
        "height":"523686"
    })
    @patch(PING_NODE_FUNCTION, return_value="pong")
    @patch(GET_SYNCING_FUNCTION, return_value="true")
    @patch(GET_PEERS_FUNCTION, return_value="92")
    def test_monitor_direct_sets_node_state_to_retrieved_data(
            self, _1, _2, _3, _4) -> None:
        self.validator_monitor.monitor_direct()

        self.assertFalse(self.validator.is_down)
        self.assertFalse(self.validator.is_syncing)
        self.assertEqual(self.validator.no_of_peers, 92)
        self.assertEqual(self.validator.finalized_block_height, 523686)

    @patch(GET_FINALIZED_HEAD_FUNCTION, return_value={
        "height":"523686"
    })
    @patch(PING_NODE_FUNCTION, return_value="pong")
    @patch(GET_SYNCING_FUNCTION, return_value="true")
    @patch(GET_PEERS_FUNCTION, return_value="92")
    def test_monitor_direct_sets_API_as_up_if_monitoring_successful(
            self, _1, _2, _3, _4) -> None:
        self.validator_monitor.monitor_direct()

        self.assertFalse(self.validator_monitor.data_wrapper.is_api_down)


    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    @patch(GET_STAKING_ACCOUNT_INFO_FUNCTION, return_value={
        "escrow": {
            "active":{
                "balance" : "9999999999993"
            },
            "debonding":{
                "balance" : "9999999999993"
            }
        }
    })
    @patch(GET_SIGNED_BLOCKS_FUNCTION, return_value={
        "signatures" : [
            {"validator_address" : "06140E5B1FE5D72BAA12AED7815A7E19BC7BDABA"},
            {"validator_address" : "7C87340EFE4BE695E80099AE3B0CAE545381925D"},
            {"validator_address" : "0D73013810841C092B8ACB1A9646F412B62EE14C"},
        ]
    })
    @patch(GET_BLOCK_HEADER_AT_HEIGHT_FUNCTION, return_value={
        "height":"55666"
    })
    @patch(GET_CONSENSUS_BLOCK_FUNCTION, return_value={"height":"55666", \
    "meta": "asndiasbdiabsidjbasjiaslnlasndlkandlkasldknasdlknaskbda"})
    @patch(GET_SESSION_VALIDATORS_FUNCTION, return_value=[])
    @patch(GET_STAKING_DELEGATIONS_INFO_FUNCTION, return_value={
        "Xq2d4D43YmBdUAOd3q6A0n1kaHUY766RE24xznk1Sgc=": {
            "shares": "27681494143232"
        }
    })
    def test_monitor_indirect_sets_API_up_when_validator_indirect_monitoring_succesfull(
            self, _1, _2, _3, _4, _5, _6, _7) -> None:
        with mock.patch(DATA_SOURCE_INDIRECT_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1
            self.validator_monitor.last_data_source_used = \
                self.dummy_full_node_1

            self.validator_monitor._archive_alerts_disabled = True
            self.validator_monitor.monitor_indirect()
            self.assertFalse(self.validator_monitor.data_wrapper.is_api_down)

    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    @patch(GET_STAKING_ACCOUNT_INFO_FUNCTION, return_value={
        "escrow": {
            "active":{
                "balance" : "9999999999993"
            },
            "debonding":{
                "balance" : "9999999999993"
            }
        }
    })
    @patch(GET_SIGNED_BLOCKS_FUNCTION, return_value={
        "signatures" : [
            {"validator_address" : "06140E5B1FE5D72BAA12AED7815A7E19BC7BDABA"},
            {"validator_address" : "7C87340EFE4BE695E80099AE3B0CAE545381925D"},
            {"validator_address" : "0D73013810841C092B8ACB1A9646F412B62EE14C"},
        ]
    })
    @patch(GET_BLOCK_HEADER_AT_HEIGHT_FUNCTION, return_value={
        "height":"55666"
    })
    @patch(GET_CONSENSUS_BLOCK_FUNCTION, return_value={"height":"55666", \
    "meta": "asndiasbdiabsidjbasjiaslnlasndlkandlkasldknasdlknaskbda"})
    @patch(GET_SESSION_VALIDATORS_FUNCTION, return_value=[])
    @patch(GET_STAKING_DELEGATIONS_INFO_FUNCTION, return_value={
        "Xq2d4D43YmBdUAOd3q6A0n1kaHUY766RE24xznk1Sgc=": {
            "shares": "27681494143232"
        }
    })
    def test_monitor_indirect_connects_data_source_with_api_if_monitoring_succesfull(
            self, _1, _2, _3, _4, _5, _6, _7) -> None:
        with mock.patch(DATA_SOURCE_INDIRECT_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1
            self.validator_monitor.last_data_source_used = \
                self.dummy_full_node_1
            self.validator_monitor.last_data_source_used.disconnect_from_api(
                self.channel_set, self.logger)

            self.validator_monitor._archive_alerts_disabled = True
            self.validator_monitor.monitor_indirect()
            self.assertTrue(self.validator_monitor.last_data_source_used.
                            is_connected_to_api_server)

    def test_monitor_indirect_full_node_sets_values_as_expected(self) -> None:
        self.full_node_monitor.monitor_indirect()
        
        self.assertEqual(self.full_node_monitor.node.bonded_balance, 0)
        self.assertFalse(self.full_node_monitor.node.is_active)

    @patch(GET_STAKING_DELEGATIONS_INFO_FUNCTION, return_value={
        "Xq2d4D43YmBdUAOd3q6A0n1kaHUY766RE24xznk1Sgc=": {
            "shares": "27681494143232"
        }
    })
    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    @patch(GET_STAKING_ACCOUNT_INFO_FUNCTION, return_value={
        "escrow": {
            "active":{
                "balance" : "9999999999993"
            },
            "debonding":{
                "balance" : "9999999999993"
            }
        }
    })
    @patch(GET_SIGNED_BLOCKS_FUNCTION, return_value={
        "signatures" : [
            {"validator_address" : "06140E5B1FE5D72BAA12AED7815A7E19BC7BDABA"},
            {"validator_address" : "7C87340EFE4BE695E80099AE3B0CAE545381925D"},
            {"validator_address" : "0D73013810841C092B8ACB1A9646F412B62EE14C"},
        ]
    })
    @patch(GET_BLOCK_HEADER_AT_HEIGHT_FUNCTION, return_value={
        "height":"55666"
    })
    @patch(GET_CONSENSUS_BLOCK_FUNCTION, return_value={"height":"55666", \
    "meta": "asndiasbdiabsidjbasjiaslnlasndlkandlkasldknasdlknaskbda"})
    @patch(GET_SESSION_VALIDATORS_FUNCTION, return_value=[])
    def test_monitor_indirect_validator_calls_monitor_archive_if_not_disabled(
            self, _1, _2, _3, _4, _5, _6, _7) -> None:
        with mock.patch(DATA_SOURCE_INDIRECT_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1
            self.validator_monitor._monitor_archive_state = MagicMock()

            self.validator_monitor._monitor_indirect_validator()
            self.assertEqual(
                self.validator_monitor._monitor_archive_state.call_count, 1)
    
    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    def test_monitor_archive_sets_catching_up_true_if_more_than_2_blocks_late(
            self, _1) -> None:
        with mock.patch(DATA_SOURCE_ARCHIVE_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1

            # To make the monitor catch up
            archive_node_height = self.dummy_finalized_block_height + 4

            self.dummy_full_node_1.update_finalized_block_height(
                archive_node_height, self.logger, self.channel_set)
            self.validator_monitor._last_height_checked = \
                self.dummy_finalized_block_height
            self.validator_monitor._monitor_archive_state()

            self.assertTrue(self.validator_monitor._monitor_is_catching_up)

    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    def test_monitor_archive_sets_catching_up_false_if_less_than_2_blocks_late(
            self, _1) -> None:
        with mock.patch(DATA_SOURCE_ARCHIVE_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1
            self.dummy_full_node_1.update_finalized_block_height(
                self.dummy_finalized_block_height, self.logger,
                self.channel_set)

            self.validator_monitor._monitor_archive_state()
            self.assertFalse(self.validator_monitor._monitor_is_catching_up)

    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    def test_monitor_archive_sets_catching_up_false_if_2_blocks_late(
            self,_1) -> None:
        with mock.patch(DATA_SOURCE_ARCHIVE_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1
            self.dummy_full_node_1.update_finalized_block_height(
                self.dummy_finalized_block_height, self.logger,
                self.channel_set)
            self.validator_monitor._last_height_checked = \
                self.dummy_finalized_block_height - 2
            self.validator_monitor._monitor_archive_state()

            self.assertFalse(self.validator_monitor._monitor_is_catching_up)

    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    def test_monitor_archive_raises_info_alert_if_monitoring_round_successful_and_error_alert_sent(
            self, _1) -> None:
        with mock.patch(DATA_SOURCE_ARCHIVE_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1

            self.validator_monitor._no_live_archive_node_alert_sent = True
            self.validator_monitor._monitor_archive_state()

            self.assertEqual(self.counter_channel.info_count, 1)
            self.assertFalse(
                self.validator_monitor._no_live_archive_node_alert_sent)
            self.assertIsInstance(self.counter_channel.latest_alert,
                                  FoundLiveArchiveNodeAgainAlert)

    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value=None)
    def test_monitor_archive_no_alerts_if_monitoring_round_successful_error_alert_not_sent_previously(
            self, _1) -> None:
        with mock.patch(DATA_SOURCE_ARCHIVE_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1

            self.validator_monitor._monitor_archive_state()

            self.assertTrue(self.counter_channel.no_alerts())
            self.assertFalse(
                self.validator_monitor._no_live_archive_node_alert_sent)

    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value= \
            [{"escrow" : {"take" :  
            {"owner" : "entity_key_1", 
             "tokens": "2000000000"}}}])
    def test_monitor_archive_if_a_slashing_event_occurs_for_1_node(
            self, _1) -> None:
        with mock.patch(DATA_SOURCE_ARCHIVE_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1

            self.data_sources = [self.dummy_validator_node_1]

            test_monitor = NodeMonitor(
                self.monitor_name, self.channel_set, self.logger,
                self.node_monitor_max_catch_up_blocks, 
                self.redis, self.validator, self.archive_alerts_disabled, 
                self.data_sources, TestInternalConf)
                
            # To make the monitor catch up 
            archive_node_height = self.dummy_finalized_block_height + 4

            self.dummy_full_node_1.update_finalized_block_height(
                archive_node_height, self.logger, self.channel_set)

            test_monitor._last_height_checked = \
                self.dummy_finalized_block_height
            
            test_monitor._monitor_archive_state()

            self.assertEqual(self.counter_channel.critical_count,1)

    @patch(GET_STAKING_EVENTS_BY_HEIGHT_FUNCTION, return_value= \
            [{"escrow" : {"take" :  
            {"owner" : "entity_key_1", 
             "tokens": "2000000000"}}},
             {"escrow" : {"take" :  
            {"owner" : "entity_key_2", 
             "tokens": "2000000000"}}},
             {"escrow" : {"take" :  
            {"owner" : "entity_key_3", 
             "tokens": "2000000000"}}}])
    def test_monitor_archive_if_a_slashing_event_occurs_for_3_nodes(
            self, _1) -> None:
        with mock.patch(DATA_SOURCE_ARCHIVE_PATH, new_callable=PropertyMock) \
                as mock_data_source_indirect:
            mock_data_source_indirect.return_value = self.dummy_full_node_1

            self.data_sources = [
                self.dummy_validator_node_1,
                self.dummy_validator_node_2,
                self.dummy_validator_node_3
            ]

            test_monitor = NodeMonitor(
                self.monitor_name, self.channel_set, self.logger, 
                self.node_monitor_max_catch_up_blocks, 
                self.redis, self.validator, self.archive_alerts_disabled, 
                self.data_sources, TestInternalConf)
                
            # To make the monitor catch up 
            archive_node_height = self.dummy_finalized_block_height + 4

            self.dummy_full_node_1.update_finalized_block_height(
                archive_node_height, self.logger, self.channel_set)

            test_monitor._last_height_checked = \
                self.dummy_finalized_block_height
            
            test_monitor._monitor_archive_state()

            self.assertEqual(self.counter_channel.critical_count,3)
# @unittest.skip("Skipping Test Node Monitor With Redis")
class TestNodeMonitorWithRedis(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Same as in setUp(), to avoid running all tests if Redis is offline

        logger = logging.getLogger('dummy')
        db = TestInternalConf.redis_test_database
        host = TestUserConf.redis_host
        port = TestUserConf.redis_port
        password = TestUserConf.redis_password
        redis = RedisApi(logger, db, host, port, password)

        try:
            redis.ping_unsafe()
        except RedisConnectionError:
            raise Exception('Redis is not online.')

    def setUp(self) -> None:
        self.logger = logging.getLogger('dummy')
        self.logger_events = logging.getLogger('dummy_events')
        self.monitor_name = 'testnodemonitor'
        self.counter_channel = CounterChannel(self.logger)
        self.channel_set = ChannelSet([self.counter_channel], TestInternalConf)

        self.db = TestInternalConf.redis_test_database
        self.host = TestUserConf.redis_host
        self.port = TestUserConf.redis_port
        self.password = TestUserConf.redis_password
        self.redis = RedisApi(self.logger, self.db, self.host,
                              self.port, self.password)
        self.redis.delete_all_unsafe()

        try:
            self.redis.ping_unsafe()
        except RedisConnectionError:
            self.fail('Redis is not online.')

        self.node_monitor_max_catch_up_blocks = \
            TestInternalConf.node_monitor_max_catch_up_blocks
        self.node = None
        self.archive_alerts_disabled = False
        self.data_sources = []
        self.monitor = NodeMonitor(
            self.monitor_name, self.channel_set, self.logger,
            self.node_monitor_max_catch_up_blocks, 
            self.redis, self.node, self.archive_alerts_disabled, 
            self.data_sources, TestInternalConf)

        self.dummy_last_height_checked = 1000

        self.redis_alive_key_timeout = \
            TestInternalConf.redis_node_monitor_alive_key_timeout

    def test_load_state_changes_nothing_if_nothing_saved(self) -> None:
        self.monitor.load_state()

        self.assertEqual(NONE, self.monitor._last_height_checked)

    def test_load_state_sets_values_to_saved_values(self) -> None:
        # Set Redis values manually
        key_lh = Keys.get_node_monitor_last_height_checked(self.monitor_name)
        self.redis.set_unsafe(key_lh, self.dummy_last_height_checked)

        # Load the values from Redis
        self.monitor.load_state()

        # Assert
        self.assertEqual(self.dummy_last_height_checked,
                         self.monitor.last_height_checked)

    def test_save_state_sets_values_to_current_values_and_stores_alive_key_temp(
            self) -> None:
        # Set monitor values manually
        self.monitor._last_height_checked = self.dummy_last_height_checked

        # Save the values to Redis
        self.monitor.save_state()

        key_lh = Keys.get_node_monitor_last_height_checked(self.monitor_name)

        # Get last update, and its timeout in Redis
        last_update = self.redis.get(key_lh)
        timeout = self.redis.time_to_live(key_lh)

        # Assert
        self.assertEqual(self.dummy_last_height_checked,
                         self.redis.get_int(key_lh))
        self.assertIsNotNone(last_update)
        self.assertEqual(timeout, self.redis_alive_key_timeout)
