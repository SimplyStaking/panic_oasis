import logging
import unittest
from datetime import timedelta
from time import sleep

import dateutil
from redis import ConnectionError as RedisConnectionError

from src.alerters.reactive.node import Node, NodeType
from src.alerts.alerts import *
from src.channels.channel import ChannelSet
from src.store.redis.redis_api import RedisApi
from src.store.store_keys import Keys
from src.utils.scaling import scale_to_giga
from src.utils.types import NONE
from test import TestInternalConf, TestUserConf
from test.test_helpers import CounterChannel, DummyException

# @unittest.skip("Skipping Test Node Without Redis")
class TestNodeWithoutRedis(unittest.TestCase):
    ERROR_MARGIN = timedelta(seconds=1)

    def setUp(self) -> None:
        self.node_name = 'testnode'
        self.logger = logging.getLogger('dummy')

        self.downtime_alert_interval_seconds = \
            TestInternalConf.downtime_alert_interval_seconds

        self.downtime_alert_interval_seconds_with_error_margin = \
            self.downtime_alert_interval_seconds + self.ERROR_MARGIN

        self.bonded_balance_threshold = \
                scale_to_giga(TestInternalConf.change_in_bonded_balance_threshold)
        
        self.debonding_balance_threshold = \
                scale_to_giga(TestInternalConf.change_in_debonding_balance_threshold)

        self.shares_balance_threshold = \
                scale_to_giga(TestInternalConf.change_in_shares_balance_threshold)

        self.no_change_in_height_interval_seconds = \
            timedelta(seconds=int(
                TestInternalConf.no_change_in_height_interval_seconds))

        self.no_change_in_height_interval_seconds_with_error = \
            self.no_change_in_height_interval_seconds + self.ERROR_MARGIN

        self.no_change_in_height_first_warning_seconds = \
            timedelta(seconds=int(
                TestInternalConf.no_change_in_height_first_warning_seconds))

        self.no_change_in_height_first_warning_seconds_with_error = \
            self.no_change_in_height_first_warning_seconds + self.ERROR_MARGIN

        self.validator_peer_danger_boundary = \
            TestInternalConf.validator_peer_danger_boundary

        self.validator_peer_safe_boundary = \
            TestInternalConf.validator_peer_safe_boundary
            
        self.full_node_peer_danger_boundary = \
            TestInternalConf.full_node_peer_danger_boundary

        self.max_missed_blocks_time_interval = \
            TestInternalConf.max_missed_blocks_time_interval

        self.max_missed_blocks_time_interval_with_error_margin = \
            self.max_missed_blocks_time_interval + timedelta(seconds=0.5)

        self.max_missed_blocks_in_time_interval = \
            TestInternalConf.max_missed_blocks_in_time_interval

        self.validator_entity_owner = "askdasssd188ssassalkdnalsdasss"
        self.validator_entity_other = "ad99sdaknjsd010saodnaaosnd91"
        self.validator_entity_tokens = "200000000"

        self.full_node = Node(name=self.node_name, api_url=None,
                              node_type=NodeType.NON_VALIDATOR_FULL_NODE,
                              node_public_key='', chain='', redis=None,
                              is_archive_node=True,
                              consensus_public_key="USDKAJBD123hdas9dassodnaasd",
                              tendermint_address_key="skojabdba991231dsqkslndad",
                              entity_public_key=self.validator_entity_owner,
                              internal_conf=TestInternalConf)

        self.validator = Node(name=self.node_name, api_url=None,
                              node_type=NodeType.VALIDATOR_FULL_NODE,
                              node_public_key='', chain='', redis=None,
                              is_archive_node=True,
                              consensus_public_key="USDKAJBD123hdas9dasodnaasd",
                              tendermint_address_key="skojabdba991231dsqkslnda",
                              entity_public_key=self.validator_entity_owner,
                              internal_conf=TestInternalConf)

        self.counter_channel = CounterChannel(self.logger)
        self.channel_set = ChannelSet([self.counter_channel], TestInternalConf)

        self.dummy_exception = DummyException()
        self.dummy_event_height = 34567
        self.dummy_no_of_peers = 100
        self.dummy_active = True
        self.dummy_finalized_block_height = 34535
        self.dummy_bonded_balance = scale_to_giga(5)
        self.dummy_debonding_balance = scale_to_giga(5)
        self.dummy_shares_balance = scale_to_giga(5)
        self.dummy_missing_validators = -1
        self.dummy_voting_power = 1000
        self.dummy_block_height = -1
        self.dummy_block_time = datetime.min + timedelta(days=123)
        self.dummy_block_time_after_time_interval = \
            self.dummy_block_time + \
            self.max_missed_blocks_time_interval_with_error_margin
            
        self.full_node_no_of_peers_less_than_danger_boundary = \
            self.full_node_peer_danger_boundary - 2
        self.full_node_no_of_peers_greater_than_danger_boundary = \
            self.full_node_peer_danger_boundary + 2
        self.validator_no_of_peers_less_than_danger_boundary = \
            self.validator_peer_danger_boundary - 2
        self.validator_no_of_peers_greater_than_danger_boundary = \
            self.validator_peer_danger_boundary + 2
        self.validator_no_of_peers_less_than_safe_boundary = \
            self.validator_peer_safe_boundary - 2
        self.validator_no_of_peers_greater_than_safe_boundary = \
            self.validator_peer_safe_boundary + 2

        # Dummy Events for testing of process_event function
        self.dummy_take_event_owner = {"escrow" : {"take": 
            {"owner" : self.validator_entity_owner, 
             "tokens": self.validator_entity_tokens}}}
        
        self.dummy_take_event_not_owner = {"escrow" : {"take": 
            {"owner" : self.validator_entity_other, 
             "tokens": self.validator_entity_tokens}}}
        
        self.dummy_burn_event_owner = {"burn" : 
            {"owner" : self.validator_entity_owner,
             "tokens": self.validator_entity_tokens}}

        self.dummy_burn_event_not_owner = {"burn" : 
            {"owner" : self.validator_entity_other,
             "tokens": self.validator_entity_tokens}}

        self.dummy_transfer_event_from_owner = {"transfer" : 
            {"from": self.validator_entity_owner,
             "to": self.validator_entity_other,
             "tokens": self.validator_entity_tokens}}
        
        self.dummy_transfer_event_to_owner = {"transfer" : 
            {"from": self.validator_entity_other,
             "to": self.validator_entity_owner,
             "tokens": self.validator_entity_tokens}}
        
        self.dummy_transfer_event_not_owner = {"transfer" : 
            {"from": self.validator_entity_other,
             "to": self.validator_entity_other,
             "tokens": self.validator_entity_tokens}}

        self.dummy_reclaim_event_owner_is_not_escrow = {"escrow" : {"reclaim": 
            {"owner" : self.validator_entity_owner,
             "escrow" : self.validator_entity_other,
             "tokens" : self.validator_entity_tokens}}}
        
        self.dummy_reclaim_event_owner_is_escrow = {"escrow" : {"reclaim": 
            {"owner" : self.validator_entity_other,
             "escrow" : self.validator_entity_owner,
             "tokens" : self.validator_entity_tokens}}}

        self.dummy_reclaim_event_owner_is_neither = {"escrow" : {"reclaim": 
            {"owner" : self.validator_entity_other,
             "escrow" : self.validator_entity_other,
             "tokens" : self.validator_entity_tokens}}}

        self.dummy_add_event_owner_is_not_escrow = {"escrow" : {"add": 
            {"owner" : self.validator_entity_owner,
             "escrow" : self.validator_entity_other,
             "tokens": self.validator_entity_tokens}}}
        
        self.dummy_add_event_owner_is_escrow = {"escrow" : {"add": 
            {"owner" : self.validator_entity_other,
             "escrow" : self.validator_entity_owner,
             "tokens": self.validator_entity_tokens}}}

        self.dummy_add_event_owner_is_neither = {"escrow" : {"add": 
            {"owner" : self.validator_entity_other,
             "escrow" : self.validator_entity_other,
             "tokens": self.validator_entity_tokens}}}
        
        self.dummy_unknown_event = {"Uknown" : {"take": 
            {"owner" : self.validator_entity_owner, 
             "tokens" : self.validator_entity_tokens}}}


    def test_voting_power_is_none_by_default(self) -> None:
        self.assertIsNone(self.validator.voting_power)
    
    def test_is_missing_blocks_false_by_default(self) -> None:
        self.assertFalse(self.validator.is_missing_blocks)

    def test_str_returns_name_of_node(self) -> None:
        self.assertEqual(str(self.validator), self.node_name)

    def test_is_validator_true_if_is_validator(self) -> None:
        self.assertTrue(self.validator.is_validator)

    def test_is_validator_false_if_not_validator(self) -> None:
        self.assertFalse(self.full_node.is_validator)

    def test_is_down_false_by_default(self) -> None:
        self.assertFalse(self.validator.is_down)

    def test_is_down_true_when_went_down_not_none(self) -> None:
        self.validator._went_down_at = datetime.now().timestamp()
        self.assertTrue(self.validator.is_down)

    def test_is_active_none_by_default(self) -> None:
        self.assertIsNone(self.validator.is_active)

    def test_is_syncing_false_by_default(self) -> None:
        self.assertFalse(self.validator.is_syncing)
    
    def test_bonded_balance_none_by_default(self) -> None:
        self.assertIsNone(self.validator.bonded_balance)

    def test_debonding_balance_none_by_default(self) -> None:
        self.assertIsNone(self.validator.debonding_balance)

    def test_shares_balance_none_by_default(self) -> None:
        self.assertIsNone(self.validator.shares_balance)

    def test_number_of_peers_none_by_default(self) -> None:
        self.assertIsNone(self.validator.no_of_peers)

    def test_is_no_change_in_height_warning_sent_false_by_default(self) -> None:
        self.assertFalse(self.validator.is_no_change_in_height_warning_sent)

    def test_finalized_block_height_zero_by_default(self) -> None:
        self.assertEqual(self.validator.finalized_block_height, 0)

    def test_is_connected_to_api_server_true_by_default(self) -> None:
        self.assertTrue(self.validator.is_connected_to_api_server)
        self.assertTrue(self.full_node.is_connected_to_api_server)

    def test_status_returns_as_expected(self) -> None:
        self.validator._bonded_balance = self.dummy_bonded_balance
        self.validator._debonding_balance = self.dummy_debonding_balance
        self.validator._shares_balance = self.dummy_shares_balance
        self.validator._no_of_peers = self.dummy_no_of_peers
        self.validator._active = self.dummy_active
        self.validator._finalized_block_height = \
            self.dummy_finalized_block_height

        self.assertEqual(
            self.validator.status(), "bonded_balance={}, debonding_balance={},"\
                                     " shares_balance={}, "\
                                     "is_syncing=False, " \
                                     "no_of_peers={}, active={}, " \
                                     "finalized_block_height={}, " \
                                     "is_missing_blocks=False".format(
                self.dummy_bonded_balance,
                self.dummy_debonding_balance,
                self.dummy_shares_balance,
                self.dummy_no_of_peers, self.dummy_active,
                self.dummy_finalized_block_height))

    def test_first_set_as_down_sends_info_experiencing_delays_alert_and_sets_node_as_down(
            self) -> None:
        self.validator.set_as_down(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertFalse(self.validator._initial_downtime_alert_sent)
        self.assertTrue(self.validator.is_down)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ExperiencingDelaysAlert)

    def test_second_set_as_down_sends_critical_cannot_access_node_alert_if_validator(
            self) -> None:
        self.validator.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts
        self.validator.set_as_down(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertTrue(self.validator.is_down)
        self.assertTrue(self.validator._initial_downtime_alert_sent)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              CannotAccessNodeAlert)

    def test_second_set_as_down_sends_warning_cannot_access_node_alert_if_non_validator(
            self) -> None:
        self.full_node.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts
        self.full_node.set_as_down(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertTrue(self.full_node._initial_downtime_alert_sent)
        self.assertTrue(self.full_node.is_down)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              CannotAccessNodeAlert)

    def test_third_set_as_down_does_nothing_if_within_time_interval_for_validator(
            self) -> None:
        self.validator.set_as_down(self.channel_set, self.logger)
        self.validator.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts
        self.validator.set_as_down(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertTrue(self.validator.is_down)

    def test_third_set_as_down_does_nothing_if_within_time_interval_for_non_validator(
            self) -> None:
        self.full_node.set_as_down(self.channel_set, self.logger)
        self.full_node.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts
        self.full_node.set_as_down(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertTrue(self.full_node.is_down)

    def test_third_set_as_down_sends_critical_alert_if_after_time_interval_for_validator(
            self) -> None:
        self.validator.set_as_down(self.channel_set, self.logger)
        self.validator.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts
        sleep(self.downtime_alert_interval_seconds_with_error_margin.seconds)
        self.validator.set_as_down(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertTrue(self.validator.is_down)
        self.assertTrue(self.validator._initial_downtime_alert_sent)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              StillCannotAccessNodeAlert)

    def test_third_set_as_down_sends_warning_alert_if_after_time_interval_for_non_validator(
            self) -> None:
        self.full_node.set_as_down(self.channel_set, self.logger)
        self.full_node.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts
        sleep(self.downtime_alert_interval_seconds_with_error_margin.seconds)
        self.full_node.set_as_down(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertTrue(self.full_node.is_down)
        self.assertTrue(self.full_node._initial_downtime_alert_sent)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              StillCannotAccessNodeAlert)

    def test_set_as_up_does_nothing_if_not_down(self) -> None:
        self.validator.set_as_up(self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertFalse(self.validator.is_down)

    def test_set_as_up_sets_as_up_but_no_alerts_if_set_as_down_called_only_once(
            self) -> None:
        self.validator.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts

        self.validator.set_as_up(self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertFalse(self.validator.is_down)

    def test_set_as_up_sets_as_up_and_sends_info_alert_if_set_as_down_called_twice(
            self) -> None:
        self.validator.set_as_down(self.channel_set, self.logger)
        self.validator.set_as_down(self.channel_set, self.logger)
        self.counter_channel.reset()  # ignore previous alerts

        self.validator.set_as_up(self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertFalse(self.validator.is_down)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NowAccessibleAlert)

    def test_set_as_up_resets_alert_time_interval(self) -> None:
        self.validator.set_as_down(self.channel_set, self.logger)
        self.validator.set_as_down(self.channel_set, self.logger)
        self.validator.set_as_up(self.channel_set, self.logger)

        self.counter_channel.reset()  # ignore previous alerts

        self.validator.set_as_down(self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertTrue(self.validator.is_down)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ExperiencingDelaysAlert)

    def test_set_bonded_balance_raises_no_alerts_first_time_round(self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                            self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.bonded_balance,
                         self.dummy_bonded_balance)

    def test_set_bonded_balance_raises_no_alerts_if_bonded_balance_the_same(
            self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.bonded_balance,
                         self.dummy_bonded_balance)
    
    def test_set_balance_no_alerts_if_difference_is_negative_below_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)
        new_bonded_balance = self.dummy_bonded_balance - \
                             self.bonded_balance_threshold + 1
        self.validator.set_bonded_balance(new_bonded_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.bonded_balance,
                         new_bonded_balance)

    def test_set_balance_no_alerts_if_difference_is_positive_below_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)
        new_bonded_balance = self.dummy_bonded_balance + \
                             self.bonded_balance_threshold - 1
        self.validator.set_bonded_balance(new_bonded_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.bonded_balance,
                         new_bonded_balance)
    
    def test_set_balance_no_alerts_if_difference_is_negative_and_equal_to_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)
        new_bonded_balance = self.dummy_bonded_balance - \
                             self.bonded_balance_threshold
        self.validator.set_bonded_balance(new_bonded_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.bonded_balance,
                         new_bonded_balance)
    def test_set_balance_no_alerts_if_difference_is_positive_and_equal_to_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)
        new_bonded_balance = self.dummy_bonded_balance + \
                             self.bonded_balance_threshold
        self.validator.set_bonded_balance(new_bonded_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.bonded_balance,
                         new_bonded_balance)

    def test_set_balance_raises_info_alert_if_difference_is_positive_above_threshold_no_balance_is_0(
            self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)
        new_bonded_balance = self.dummy_bonded_balance + \
                             self.bonded_balance_threshold + 1
        self.validator.set_bonded_balance(new_bonded_balance, self.channel_set,
                                          self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              BondedBalanceIncreasedByAlert)
        self.assertEqual(self.validator.bonded_balance,
                         new_bonded_balance)

    def test_set_balance_raises_info_alert_if_difference_is_negative_above_threshold_no_balance_is_0(
            self) -> None:
        self.validator.set_bonded_balance(self.dummy_bonded_balance,
                                          self.channel_set, self.logger)
        new_bonded_balance = self.dummy_bonded_balance - \
                             self.bonded_balance_threshold - 1
        self.validator.set_bonded_balance(new_bonded_balance, self.channel_set,
                                          self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              BondedBalanceDecreasedByAlert)
        self.assertEqual(self.validator.bonded_balance, new_bonded_balance)

    def test_set_debonding_balance_raises_no_alerts_first_time_round(self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                            self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.debonding_balance,
                         self.dummy_debonding_balance)

    def test_set_debonding_balance_raises_no_alerts_if_debonding_balance_the_same(
            self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.debonding_balance,
                         self.dummy_debonding_balance)
    
    def test_set_debonding_balance_no_alerts_if_difference_is_negative_below_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        new_debonding_balance = self.dummy_debonding_balance - \
                             self.debonding_balance_threshold + 1
        self.validator.set_debonding_balance(new_debonding_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.debonding_balance,
                         new_debonding_balance)

    def test_set_debonding_balance_no_alerts_if_difference_is_positive_below_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        new_debonding_balance = self.dummy_debonding_balance + \
                             self.debonding_balance_threshold - 1
        self.validator.set_debonding_balance(new_debonding_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.debonding_balance,
                         new_debonding_balance)
    
    def test_set_debonding_balance_no_alerts_if_difference_is_negative_and_equal_to_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        new_debonding_balance = self.dummy_debonding_balance - \
                             self.debonding_balance_threshold
        self.validator.set_debonding_balance(new_debonding_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.debonding_balance,
                         new_debonding_balance)

    def test_set_debonding_balance_no_alerts_if_difference_is_positive_and_equal_to_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        new_debonding_balance = self.dummy_debonding_balance + \
                             self.debonding_balance_threshold
        self.validator.set_debonding_balance(new_debonding_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.debonding_balance,
                         new_debonding_balance)

    def test_set_debonding_balance_raises_info_alert_if_difference_is_positive_above_threshold_no_balance_is_0(
            self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        new_debonding_balance = self.dummy_debonding_balance + \
                             self.debonding_balance_threshold + 1
        self.validator.set_debonding_balance(new_debonding_balance, self.channel_set,
                                          self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              DebondingBalanceIncreasedByAlert)
        self.assertEqual(self.validator.debonding_balance,
                         new_debonding_balance)

    def test_set_debonding_balance_raises_info_alert_if_difference_is_negative_above_threshold_no_balance_is_0(
            self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        new_debonding_balance = self.dummy_debonding_balance - \
                             self.debonding_balance_threshold - 1
        self.validator.set_debonding_balance(new_debonding_balance, self.channel_set,
                                          self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              DebondingBalanceDecreasedByAlert)
        self.assertEqual(self.validator.debonding_balance, new_debonding_balance)

    def test_set_debonding_balance_raises_critical_alert_if_new_balance_0(self) -> None:
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)
        self.validator.set_debonding_balance(0, self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              DebondingBalanceDecreasedAlert)
        self.assertEqual(self.validator.debonding_balance, 0)

    def test_set_debonding_balance_info_alert_if_new_balance_non_0_from_0(self) -> None:
        self.validator.set_debonding_balance(0, self.channel_set, self.logger)
        self.validator.set_debonding_balance(self.dummy_debonding_balance,
                                          self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              DebondingBalanceIncreasedAlert)
        self.assertEqual(self.validator.debonding_balance,
                         self.dummy_debonding_balance)

    def test_set_shares_balance_raises_no_alerts_first_time_round(self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                            self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.shares_balance,
                         self.dummy_shares_balance)

    def test_set_shares_balance_raises_no_alerts_if_share_balance_the_same(
            self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.shares_balance,
                         self.dummy_shares_balance)
    
    def test_set_shares_balance_no_alerts_if_difference_is_negative_below_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        new_shares_balance = self.dummy_shares_balance - \
                             self.shares_balance_threshold + 1
        self.validator.set_shares_balance(new_shares_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.shares_balance,
                         new_shares_balance)

    def test_set_shares_balance_no_alerts_if_difference_is_positive_below_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        new_shares_balance = self.dummy_shares_balance + \
                             self.shares_balance_threshold - 1
        self.validator.set_shares_balance(new_shares_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.shares_balance,
                         new_shares_balance)
    
    def test_set_shares_balance_no_alerts_if_difference_is_negative_and_equal_to_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        new_shares_balance = self.dummy_shares_balance - \
                             self.shares_balance_threshold
        self.validator.set_shares_balance(new_shares_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.shares_balance,
                         new_shares_balance)

    def test_set_shares_balance_no_alerts_if_difference_is_positive_and_equal_to_threshold_and_no_balance_is_0(
            self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        new_shares_balance = self.dummy_shares_balance + \
                             self.shares_balance_threshold
        self.validator.set_shares_balance(new_shares_balance, self.channel_set,
                                          self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.shares_balance,
                         new_shares_balance)

    def test_set_shares_balance_raises_info_alert_if_difference_is_positive_above_threshold_no_balance_is_0(
            self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        new_shares_balance = self.dummy_shares_balance + \
                             self.shares_balance_threshold + 1
        self.validator.set_shares_balance(new_shares_balance, self.channel_set,
                                          self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              SharesBalanceIncreasedByAlert)
        self.assertEqual(self.validator.shares_balance,
                         new_shares_balance)

    def test_set_shares_balance_raises_info_alert_if_difference_is_negative_above_threshold_no_balance_is_0(
            self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        new_shares_balance = self.dummy_shares_balance - \
                             self.shares_balance_threshold - 1
        self.validator.set_shares_balance(new_shares_balance, self.channel_set,
                                          self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              SharesBalanceDecreasedByAlert)
        self.assertEqual(self.validator.shares_balance, new_shares_balance)

    def test_set_shares_balance_raises_alert_if_new_balance_0(self) -> None:
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)
        self.validator.set_shares_balance(0, self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              SharesBalanceDecreasedAlert)
        self.assertEqual(self.validator.shares_balance, 0)

    def test_set_shares_balance_info_alert_if_new_balance_non_0_from_0(self) -> None:
        self.validator.set_shares_balance(0, self.channel_set, self.logger)
        self.validator.set_shares_balance(self.dummy_shares_balance,
                                          self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              SharesBalanceIncreasedAlert)
        self.assertEqual(self.validator.shares_balance,
                         self.dummy_shares_balance)

    def test_is_syncing_raises_warning_is_syncing_alert_first_time_round_if_now_is_syncing(
            self) -> None:
        self.validator.set_is_syncing(True, self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert, IsSyncingAlert)
        self.assertEqual(self.validator.is_syncing, True)

    def test_is_syncing_raises_no_alerts_first_time_round_if_now_not_syncing(
            self) -> None:
        self.validator.set_is_syncing(False, self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.is_syncing, False)

    def test_is_syncing_raises_no_alerts_from_true_to_true(self) -> None:
        self.validator.set_is_syncing(True, self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.set_is_syncing(True, self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.is_syncing, True)

    # The case false to false was handled in test
    # `test_is_syncing_raises_no_alerts_first_time_round_if_now_not_syncing`

    def test_is_syncing_raises_info_is_no_longer_syncing_alert_from_true_to_false(
            self) -> None:
        self.validator.set_is_syncing(True, self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.set_is_syncing(False, self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              IsNoLongerSyncingAlert)
        self.assertEqual(self.validator.is_syncing, False)

    def test_set_no_of_peers_sets_and_raises_no_alerts_first_time_round_for_validator(
            self) -> None:
        self.validator.set_no_of_peers(self.dummy_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.no_of_peers, self.dummy_no_of_peers)

    def test_set_no_of_peers_sets_and_raises_no_alerts_first_time_round_for_full_node(
            self) -> None:
        self.full_node.set_no_of_peers(self.dummy_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node.no_of_peers, self.dummy_no_of_peers)

    def test_set_no_of_peers_raises_no_alerts_if_no_peer_change_for_validators(
            self) -> None:
        self.validator.set_no_of_peers(self.dummy_no_of_peers, self.channel_set,
                                       self.logger)
        self.validator.set_no_of_peers(self.dummy_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_peers_raises_no_alerts_if_no_peer_change_for_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(self.dummy_no_of_peers, self.channel_set,
                                       self.logger)
        self.full_node.set_no_of_peers(self.dummy_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_peers_sets_and_raises_no_alerts_if_decrease_outside_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_greater_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.full_node_no_of_peers_greater_than_danger_boundary - 1
        self.full_node.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_warning_alert_if_decrease_equal_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_greater_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.full_node_no_of_peers_greater_than_danger_boundary - 2
        self.full_node.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.full_node.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_warning_alert_if_decrease_from_outside_to_inside_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_greater_than_danger_boundary,
            self.channel_set, self.logger)

        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.full_node.no_of_peers,
                         self.full_node_no_of_peers_less_than_danger_boundary)

    def test_set_peers_sets_and_raises_warning_alert_if_decrease_inside_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.full_node_no_of_peers_less_than_danger_boundary - 1
        self.full_node.set_no_of_peers(new_no_of_peers,
                                       self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.full_node.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_less_than_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.full_node_no_of_peers_less_than_danger_boundary + 1
        self.full_node.set_no_of_peers(new_no_of_peers,
                                       self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedAlert)
        self.assertEqual(self.full_node.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_equal_to_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.full_node_no_of_peers_less_than_danger_boundary + 2
        self.full_node.set_no_of_peers(new_no_of_peers,
                                       self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedAlert)
        self.assertEqual(self.full_node.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_from_inside_to_outside_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.full_node_no_of_peers_greater_than_danger_boundary
        self.full_node.set_no_of_peers(new_no_of_peers,
                                       self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedOutsideDangerRangeAlert)
        self.assertEqual(self.full_node.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_no_alerts_if_increase_from_outside_to_outside_danger_full_nodes(
            self) -> None:
        self.full_node.set_no_of_peers(
            self.full_node_no_of_peers_greater_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.full_node_no_of_peers_greater_than_danger_boundary + 1
        self.full_node.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_no_alerts_if_increase_from_outside_to_outside_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_greater_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.validator_no_of_peers_greater_than_safe_boundary + 1
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_no_alerts_if_decrease_outside_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_greater_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.validator_no_of_peers_greater_than_safe_boundary - 1
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_warning_alert_if_decrease_equal_to_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_greater_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.validator_no_of_peers_greater_than_safe_boundary - 2
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_warning_alert_if_decrease_from_outisde_safe_to_safe_outside_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_greater_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.validator_no_of_peers_greater_than_safe_boundary - 3
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_warning_alert_if_decrease_inside_safe_outside_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.validator_no_of_peers_less_than_safe_boundary - 1
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_critical_alert_if_decrease_from_outside_safe_to_equal_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_greater_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_peer_danger_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_critical_alert_if_decrease_from_outside_safe_inside_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_greater_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_no_of_peers_less_than_danger_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_critical_alert_if_decrease_from_safe_to_equal_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_peer_danger_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_critical_alert_if_decrease_from_safe_to_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_peer_danger_boundary - 1
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_critical_alert_if_decrease_inside_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.validator_no_of_peers_less_than_danger_boundary - 1
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersDecreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_inside_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = \
            self.validator_no_of_peers_less_than_danger_boundary + 1
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_equal_danger_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_peer_danger_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_danger_to_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_no_of_peers_less_than_safe_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_danger_to_outside_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_danger_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_no_of_peers_greater_than_safe_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedOutsideSafeRangeAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_inside_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_no_of_peers_less_than_safe_boundary + 1
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_safe_to_equal_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_peer_safe_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_peers_sets_and_raises_info_alert_if_increase_safe_to_outside_safe_validator(
            self) -> None:
        self.validator.set_no_of_peers(
            self.validator_no_of_peers_less_than_safe_boundary,
            self.channel_set, self.logger)
        new_no_of_peers = self.validator_no_of_peers_greater_than_safe_boundary
        self.validator.set_no_of_peers(new_no_of_peers, self.channel_set,
                                       self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              PeersIncreasedOutsideSafeRangeAlert)
        self.assertEqual(self.validator.no_of_peers, new_no_of_peers)

    def test_set_active_no_alerts_first_time_round_and_sets_active_true_if_now_active(
            self) -> None:
        self.validator.set_active(True, self.channel_set, self.logger)

        self.assertTrue(self.validator.is_active)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_active_no_alerts_if_active_and_now_active_and_sets_active_true(
            self) -> None:
        self.validator.set_active(True, self.channel_set, self.logger)
        self.validator.set_active(True, self.channel_set, self.logger)

        self.assertTrue(self.validator.is_active)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_active_raises_info_alert_if_inactive_and_now_active_and_sets_active_true(
            self) \
            -> None:
        self.validator.set_active(False, self.channel_set, self.logger)
        self.validator.set_active(True, self.channel_set, self.logger)

        self.assertTrue(self.validator.is_active)
        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ValidatorIsNowActiveAlert)

    def test_set_active_no_alerts_first_time_round_if_now_inactive_and_sets_active_false(
            self) -> None:
        self.validator.set_active(False, self.channel_set, self.logger)

        self.assertFalse(self.validator.is_active)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_active_no_alerts_if_inactive_and_still_inactive_and_sets_active_false(
            self) -> None:
        self.validator.set_active(False, self.channel_set, self.logger)
        self.validator.set_active(False, self.channel_set, self.logger)

        self.assertFalse(self.validator.is_active)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_active_raises_critical_alert_if_active_and_now_not_active_and_sets_active_false(
            self) -> None:
        self.validator.set_active(True, self.channel_set, self.logger)
        self.validator.set_active(False, self.channel_set, self.logger)

        self.assertFalse(self.validator.is_active)
        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ValidatorIsNotActiveAlert)

    def test_update_height_no_alerts_if_increase_and_first_warning_not_sent(
            self) -> None:
        self.validator._finalized_block_height = \
            self.dummy_finalized_block_height
        new_height = self.dummy_finalized_block_height + 1

        self.validator.update_finalized_block_height(new_height, self.logger,
                                                     self.channel_set)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_update_height_no_alerts_if_decrease_and_first_warning_not_sent(
            self) -> None:
        self.validator._finalized_block_height = \
            self.dummy_finalized_block_height
        new_height = self.dummy_finalized_block_height - 1

        self.validator.update_finalized_block_height(new_height, self.logger,
                                                     self.channel_set)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_update_height_info_alert_if_increase_and_warning_sent(self) \
            -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.counter_channel.reset()

        new_height = self.dummy_finalized_block_height + 1

        self.validator.update_finalized_block_height(new_height, self.logger,
                                                     self.channel_set)
        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeFinalizedBlockHeightHasNowBeenUpdatedAlert)

    def test_update_height_info_alert_if_increase_and_both_warning_interval_alert_sent(
            self) -> None:
        # Initialize the limiters
        self.validator.finalized_height_alert_limiter.did_task()

        sleep(self.no_change_in_height_interval_seconds_with_error.seconds)

        # Sends first warning alert.
        self.validator.update_finalized_block_height(0, self.logger,
                                                     self.channel_set)
        self.counter_channel.reset()

        # Sends interval alert
        self.validator.update_finalized_block_height(0, self.logger,
                                                     self.channel_set)
        self.counter_channel.reset()

        new_height = self.dummy_finalized_block_height

        self.validator.update_finalized_block_height(new_height, self.logger,
                                                     self.channel_set)
        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeFinalizedBlockHeightHasNowBeenUpdatedAlert)

    def test_update_height_unsets_warning_sent_if_height_increase(self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.counter_channel.reset()

        new_height = self.dummy_finalized_block_height + 1

        self.validator.update_finalized_block_height(new_height, self.logger,
                                                     self.channel_set)
        self.assertFalse(self.validator._no_change_in_height_warning_sent)

    def test_update_height_unsets_warning_sent_if_height_decrease(self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.counter_channel.reset()

        new_height = self.dummy_finalized_block_height - 1

        self.validator.update_finalized_block_height(new_height, self.logger,
                                                     self.channel_set)
        self.assertFalse(self.validator._no_change_in_height_warning_sent)

    def test_update_height_modifies_state_if_new_height(self) -> None:
        old_finalized_block_height = self.validator.finalized_block_height
        old_time_of_last_height_change = \
            self.validator._time_of_last_height_change
        old_time_of_last_height_check_activity = \
            self.validator._time_of_last_height_check_activity
        old_last_time_did_task = self.validator.finalized_height_alert_limiter. \
            last_time_that_did_task

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertNotEqual(old_finalized_block_height,
                            self.validator.finalized_block_height)
        self.assertNotEqual(old_time_of_last_height_change,
                            self.validator._time_of_last_height_change)
        self.assertNotEqual(old_time_of_last_height_check_activity,
                            self.validator._time_of_last_height_check_activity)
        self.assertNotEqual(old_last_time_did_task,
                            self.validator.finalized_height_alert_limiter.
                            last_time_that_did_task)

    def test_update_height_warning_alert_if_height_not_updated_warning_time_passed(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeFinalizedBlockHeightDidNotChangeInAlert)

    def test_update_height_no_alerts_if_height_not_updated_warning_time_not_passed(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_update_height_sets_warning_sent_if_height_not_updated_warning_time_passed(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertTrue(self.validator.is_no_change_in_height_warning_sent)

    def test_update_height_does_not_set_warning_sent_if_height_not_updated_warning_time_not_passed(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertFalse(self.validator.is_no_change_in_height_warning_sent)

    def test_update_height_critical_alert_if_validator_interval_time_passed_and_warning_sent(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        sleep(self.no_change_in_height_interval_seconds_with_error.seconds)

        # To send the warning
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.counter_channel.reset()

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeFinalizedBlockHeightDidNotChangeInAlert)

    def test_update_height_warning_alert_if_full_node_interval_time_passed_and_warning_sent(
            self) -> None:
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        
        sleep(self.no_change_in_height_interval_seconds_with_error.seconds)

        # To send the warning
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.counter_channel.reset()

        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        
        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeFinalizedBlockHeightDidNotChangeInAlert)

    def test_update_height_updates_state_if_validator_interval_time_passed_and_warning_sent(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        sleep(self.no_change_in_height_interval_seconds_with_error.seconds)

        # To send the warning
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        old_finalized_block_height = self.validator.finalized_block_height
        old_time_of_last_height_change = \
            self.validator._time_of_last_height_change
        old_time_of_last_height_check_activity = \
            self.validator._time_of_last_height_check_activity
        old_last_time_did_task = self.validator.finalized_height_alert_limiter. \
            last_time_that_did_task

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertEqual(old_finalized_block_height,
                         self.validator.finalized_block_height)
        self.assertEqual(old_time_of_last_height_change,
                         self.validator._time_of_last_height_change)
        self.assertNotEqual(old_time_of_last_height_check_activity,
                            self.validator._time_of_last_height_check_activity)
        self.assertNotEqual(old_last_time_did_task,
                            self.validator.finalized_height_alert_limiter.
                            last_time_that_did_task)

    def test_update_height_updates_state_if_full_node_interval_time_passed_and_warning_sent(
            self) -> None:
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        sleep(self.no_change_in_height_interval_seconds_with_error.seconds)

        # To send the warning
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        old_finalized_block_height = self.full_node.finalized_block_height
        old_time_of_last_height_change = \
            self.full_node._time_of_last_height_change
        old_time_of_last_height_check_activity = \
            self.full_node._time_of_last_height_check_activity
        old_last_time_did_task = self.full_node. \
            finalized_height_alert_limiter.last_time_that_did_task

        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertEqual(old_finalized_block_height,
                         self.full_node.finalized_block_height)
        self.assertEqual(old_time_of_last_height_change,
                         self.full_node._time_of_last_height_change)
        self.assertNotEqual(old_time_of_last_height_check_activity,
                            self.full_node._time_of_last_height_check_activity)
        self.assertNotEqual(old_last_time_did_task,
                            self.full_node.finalized_height_alert_limiter.
                            last_time_that_did_task)

    def test_update_height_no_critical_alert_if_validator_interval_time_not_passed_and_warning_sent(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        # To send the warning because height has not changed
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.assertEqual(self.counter_channel.critical_count, 0)

    def test_update_height_no_alert_if_validator_interval_time_not_passed_and_warning_not_sent(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_update_height_no_warning_alert_if_full_node_interval_time_not_passed_and_warning_sent(
            self) -> None:
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        # To send the warning because height has not changed
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.counter_channel.reset()

        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.assertEqual(self.counter_channel.warning_count, 0)

    def test_update_height_no_alert_if_full_node_interval_time_not_passed_and_warning_not_sent(
            self) -> None:
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_update_height_no_state_update_if_validator_interval_time_not_passed_and_warning_sent(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        # To send the warning because height has not changed
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        old_finalized_block_height = self.validator.finalized_block_height
        old_time_of_last_height_change = \
            self.validator._time_of_last_height_change
        old_time_of_last_height_check_activity = \
            self.validator._time_of_last_height_check_activity
        old_last_time_did_task = self.validator.finalized_height_alert_limiter. \
            last_time_that_did_task

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertEqual(old_finalized_block_height,
                         self.validator.finalized_block_height)
        self.assertEqual(old_time_of_last_height_change,
                         self.validator._time_of_last_height_change)
        self.assertEqual(old_time_of_last_height_check_activity,
                         self.validator._time_of_last_height_check_activity)
        self.assertEqual(old_last_time_did_task,
                         self.validator.finalized_height_alert_limiter.
                         last_time_that_did_task)

    def test_update_height_no_state_update_if_validator_interval_time_not_passed_and_warning_not_sent(
            self) -> None:
        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        old_finalized_block_height = self.validator.finalized_block_height
        old_time_of_last_height_change = \
            self.validator._time_of_last_height_change
        old_time_of_last_height_check_activity = \
            self.validator._time_of_last_height_check_activity
        old_last_time_did_task = self.validator. \
            finalized_height_alert_limiter.last_time_that_did_task

        self.validator.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertEqual(old_finalized_block_height,
                         self.validator.finalized_block_height)
        self.assertEqual(old_time_of_last_height_change,
                         self.validator._time_of_last_height_change)
        self.assertEqual(old_time_of_last_height_check_activity,
                         self.validator._time_of_last_height_check_activity)
        self.assertEqual(old_last_time_did_task,
                         self.validator.finalized_height_alert_limiter.
                         last_time_that_did_task)

    def test_update_height_no_state_update_if_full_node_interval_time_not_passed_and_warning_sent(
            self) -> None:
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)
        sleep(self.no_change_in_height_first_warning_seconds_with_error.seconds)

        # To send the warning
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        old_finalized_block_height = self.full_node.finalized_block_height
        old_time_of_last_height_change = \
            self.full_node._time_of_last_height_change
        old_time_of_last_height_check_activity = \
            self.full_node._time_of_last_height_check_activity
        old_last_time_did_task = self.full_node. \
            finalized_height_alert_limiter.last_time_that_did_task

        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertEqual(old_finalized_block_height,
                         self.full_node.finalized_block_height)
        self.assertEqual(old_time_of_last_height_change,
                         self.full_node._time_of_last_height_change)
        self.assertEqual(old_time_of_last_height_check_activity,
                         self.full_node._time_of_last_height_check_activity)
        self.assertEqual(old_last_time_did_task,
                         self.full_node.finalized_height_alert_limiter.
                         last_time_that_did_task)

    def test_update_height_no_state_update_if_full_node_interval_time_not_passed_and_warning_not_sent(
            self) -> None:
        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        old_finalized_block_height = self.full_node.finalized_block_height
        old_time_of_last_height_change = \
            self.full_node._time_of_last_height_change
        old_time_of_last_height_check_activity = \
            self.full_node._time_of_last_height_check_activity
        old_last_time_did_task = self.full_node. \
            finalized_height_alert_limiter.last_time_that_did_task

        self.full_node.update_finalized_block_height(
            self.dummy_finalized_block_height, self.logger, self.channel_set)

        self.assertEqual(old_finalized_block_height,
                         self.full_node.finalized_block_height)
        self.assertEqual(old_time_of_last_height_change,
                         self.full_node._time_of_last_height_change)
        self.assertEqual(old_time_of_last_height_check_activity,
                         self.full_node._time_of_last_height_check_activity)
        self.assertEqual(old_last_time_did_task,
                         self.full_node.finalized_height_alert_limiter.
                         last_time_that_did_task)

    def test_consecutive_blocks_missed_is_0_by_default(self):
        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 0)

    def test_first_missed_block_increases_missed_blocks_count_but_no_alerts(
            self):
        if TestInternalConf.missed_blocks_danger_boundary != 5:
            self.fail('Expected missed blocks danger boundary to be 5.')

        self.validator.add_missed_block(self.dummy_block_height,
                                        self.dummy_block_time,
                                        self.dummy_missing_validators,
                                        self.channel_set, self.logger)

        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 1)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_four_missed_blocks_increases_missed_blocks_count_and_alerts(
            self):
        if TestInternalConf.missed_blocks_danger_boundary != 5:
            self.fail('Expected missed blocks danger boundary to be 5.')

        for i in range(4):
            self.validator.add_missed_block(self.dummy_block_height,
                                            self.dummy_block_time,
                                            self.dummy_missing_validators,
                                            self.channel_set, self.logger)

        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 4)
        self.assertEqual(self.counter_channel.info_count, 3)
    
    def test_four_missed_blocks_increases_missed_blocks_count_and_alerts(
            self):
        if TestInternalConf.missed_blocks_danger_boundary != 5:
            self.fail('Expected missed blocks danger boundary to be 5.')

        for i in range(4):
            self.validator.add_missed_block(self.dummy_block_height,
                                            self.dummy_block_time,
                                            self.dummy_missing_validators,
                                            self.channel_set, self.logger)

        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 4)
        self.assertEqual(self.counter_channel.info_count, 3)
        # 1 raises no alerts, 2,3,4 raise an info alert

    def test_five_missed_blocks_increases_missed_blocks_count_and_alerts(
            self):
        if TestInternalConf.missed_blocks_danger_boundary != 5:
            self.fail('Expected missed blocks danger boundary to be 5.')

        for i in range(5):
            self.validator.add_missed_block(self.dummy_block_height,
                                            self.dummy_block_time,
                                            self.dummy_missing_validators,
                                            self.channel_set, self.logger)

        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 5)
        self.assertEqual(self.counter_channel.info_count, 3)
        self.assertEqual(self.counter_channel.warning_count, 1)
        # 1 raises no alerts, 2,3,4 raise an info alert, 5 raises a minor alert

    def test_ten_missed_blocks_increases_missed_blocks_count_and_alerts(
            self):
        if TestInternalConf.missed_blocks_danger_boundary != 5:
            self.fail('Expected missed blocks danger boundary to be 5.')

        for i in range(10):
            self.validator.add_missed_block(self.dummy_block_height,
                                            self.dummy_block_time,
                                            self.dummy_missing_validators,
                                            self.channel_set, self.logger)

        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 10)
        self.assertEqual(self.counter_channel.info_count, 3)
        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertEqual(self.counter_channel.critical_count, 1)
        # 1 raises no alerts, 2,3,4 raise an info alert,
        # 5 raises a minor alert, 10 raises a major alert
    
    def test_ten_non_consecutive_missed_blocks_within_time_interval_triggers_major_alert(
            self):
        if TestInternalConf.missed_blocks_danger_boundary != 5:
            self.fail('Expected missed blocks danger boundary to be 5.')

        # Miss 9 non-consecutive blocks
        for i in range(9):
            self.validator.add_missed_block(self.dummy_block_height,
                                            self.dummy_block_time,
                                            self.dummy_missing_validators,
                                            self.channel_set, self.logger)
            self.validator.clear_missed_blocks(self.channel_set, self.logger)

        self.counter_channel.reset()  # ignore previous alerts

        # Miss 10th block within time interval
        self.validator.add_missed_block(
            self.dummy_block_height, self.dummy_block_time,
            self.dummy_missing_validators, self.channel_set, self.logger)

        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 1)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_ten_non_consecutive_missed_blocks_outside_time_interval_does_nothing(
            self):
        if TestInternalConf.missed_blocks_danger_boundary != 5:
            self.fail('Expected missed blocks danger boundary to be 5.')

        # Miss 9 non-consecutive blocks
        for i in range(9):
            self.validator.add_missed_block(self.dummy_block_height,
                                            self.dummy_block_time,
                                            self.dummy_missing_validators,
                                            self.channel_set, self.logger)
            self.validator.clear_missed_blocks(self.channel_set, self.logger)

        self.counter_channel.reset()  # ignore previous alerts

        # Miss 10th block outside of time interval
        self.validator.add_missed_block(
            self.dummy_block_height, self.dummy_block_time_after_time_interval,
            self.dummy_missing_validators, self.channel_set, self.logger)

        self.assertEqual(self.validator.consecutive_blocks_missed_so_far, 1)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_clear_missed_blocks_raises_no_alert_if_was_not_missing_blocks(
            self):
        self.validator.clear_missed_blocks(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())
    
    def test_clear_missed_blocks_raises_info_alert_if_no_longer_missing_blocks_for_one_missed_block(
            self):
        # Miss one block
        self.validator.add_missed_block(
            self.dummy_block_height, self.dummy_block_time,
            self.dummy_missing_validators, self.channel_set, self.logger)

        self.counter_channel.reset()  # ignore previous alerts
        self.validator.clear_missed_blocks(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_clear_missed_blocks_raises_info_alert_if_no_longer_missing_blocks_for_two_missed_blocks(
            self):
        # Miss two blocks
        self.validator.add_missed_block(
            self.dummy_block_height, self.dummy_block_time,
            self.dummy_missing_validators, self.channel_set, self.logger)
        self.validator.add_missed_block(
            self.dummy_block_height, self.dummy_block_time,
            self.dummy_missing_validators, self.channel_set, self.logger)

        self.counter_channel.reset()  # ignore previous alerts
        self.validator.clear_missed_blocks(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
    

    def test_set_voting_power_raises_no_alerts_first_time_round(self):
        self.validator.set_voting_power(0, self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_voting_power_raises_no_alerts_if_voting_power_the_same(self):
        self.validator.set_voting_power(self.dummy_voting_power,
                                        self.channel_set, self.logger)
        self.validator.set_voting_power(self.dummy_voting_power,
                                        self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_set_voting_power_raises_info_alert_if_voting_power_increases_from_non_0(
            self):
        increased_voting_power = self.dummy_voting_power + 1

        self.validator.set_voting_power(self.dummy_voting_power,
                                        self.channel_set, self.logger)
        self.validator.set_voting_power(increased_voting_power,
                                        self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)

    def test_set_voting_power_raises_info_alert_if_voting_power_increases_from_0(
            self):
        # This is just to cover the unique message when power increases from 0

        self.validator.set_voting_power(0, self.channel_set, self.logger)
        self.validator.set_voting_power(self.dummy_voting_power,
                                        self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)

    def test_set_voting_power_raises_info_alert_if_voting_power_decreases_to_non_0(
            self):
        decreased_voting_power = self.dummy_voting_power - 1

        self.validator.set_voting_power(self.dummy_voting_power,
                                        self.channel_set, self.logger)
        self.validator.set_voting_power(decreased_voting_power,
                                        self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)

    def test_set_voting_power_raises_major_alert_if_voting_power_decreases_to_0(
            self):
        self.validator.set_voting_power(self.dummy_voting_power,
                                        self.channel_set, self.logger)
        self.validator.set_voting_power(0, self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)

    
    def test_dummy_take_event_owner(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_take_event_owner, self.channel_set, self.logger)
        
        self.assertEqual(self.counter_channel.critical_count, 1)
    
    def test_dummy_take_event_not_owner(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_take_event_not_owner, self.channel_set, self.logger)
        
        self.assertEqual(self.counter_channel.critical_count, 0)

    def test_dummy_burn_event_owner(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_burn_event_owner, self.channel_set, self.logger)
        
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_dummy_burn_event_not_owner(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_burn_event_not_owner, self.channel_set, self.logger)
        
        self.assertEqual(self.counter_channel.critical_count, 0)
    
    def test_dummy_transfer_event_from_owner(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_transfer_event_from_owner, self.channel_set, self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_dummy_transfer_event_to_owner(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_transfer_event_to_owner, self.channel_set, self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_dummy_transfer_event_not_owner(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_transfer_event_not_owner, self.channel_set, self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 0)

    def test_dummy_reclaim_event_owner_is_not_escrow(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_reclaim_event_owner_is_not_escrow, self.channel_set,
            self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_dummy_reclaim_event_owner_is_escrow(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_reclaim_event_owner_is_escrow, self.channel_set,
            self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_dummy_reclaim_event_owner_is_neither(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_reclaim_event_owner_is_neither, self.channel_set,
            self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 0)
    
    def test_dummy_add_event_owner_is_not_escrow(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_add_event_owner_is_not_escrow, self.channel_set,
            self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_dummy_add_event_owner_is_escrow(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_add_event_owner_is_escrow, self.channel_set,
            self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_dummy_add_event_owner_is_neither(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_add_event_owner_is_neither, self.channel_set,
            self.logger)
        
        self.assertEqual(self.counter_channel.info_count, 0)
    
    def test_dummy_unknown_event(self):
        self.validator.process_event(self.dummy_event_height,
            self.dummy_unknown_event, self.channel_set,
            self.logger)
        
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_disconnect_from_api_raises_critical_alert_for_validators_if_connected_to_api(
            self) -> None:
        self.validator.disconnect_from_api(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.critical_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeWasNotConnectedToApiServerAlert)

    def test_disconnect_from_api_raises_warning_alert_for_full_nodes_if_connected_to_api(
            self) -> None:
        self.full_node.disconnect_from_api(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.warning_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeWasNotConnectedToApiServerAlert)

    def test_disconnect_from_api_raises_no_alerts_for_validators_if_not_connected_to_api(
            self) -> None:
        self.validator.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.disconnect_from_api(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_disconnect_from_api_raises_no_alerts_for_full_nodes_if_not_connected_to_api(
            self) -> None:
        self.full_node.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.full_node.disconnect_from_api(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_disconnect_from_api_sets_is_connected_false_for_validators_if_connected_to_api(
            self) -> None:
        self.validator.disconnect_from_api(self.channel_set, self.logger)

        self.assertFalse(self.validator.is_connected_to_api_server)

    def test_disconnect_from_api_sets_is_connected_false_for_full_nodes_if_connected_to_api(
            self) -> None:
        self.full_node.disconnect_from_api(self.channel_set, self.logger)

        self.assertFalse(self.full_node.is_connected_to_api_server)

    def test_disconnect_from_api_sets_is_connected_false_for_validators_if_not_connected_to_api(
            self) -> None:
        self.validator.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.disconnect_from_api(self.channel_set, self.logger)

        self.assertFalse(self.validator.is_connected_to_api_server)

    def test_disconnect_from_api_sets_is_connected_false_for_full_nodes_if_not_connected_to_api(
            self) -> None:
        self.full_node.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.full_node.disconnect_from_api(self.channel_set, self.logger)

        self.assertFalse(self.full_node.is_connected_to_api_server)

    def test_connect_with_api_raises_info_alert_for_validators_if_not_connected_to_api(
            self) -> None:
        self.validator.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.connect_with_api(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeConnectedToApiServerAgainAlert)

    def test_connect_with_api_raises_info_alert_for_full_nodes_if_not_connected_to_api(
            self) -> None:
        self.full_node.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.full_node.connect_with_api(self.channel_set, self.logger)

        self.assertEqual(self.counter_channel.info_count, 1)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              NodeConnectedToApiServerAgainAlert)

    def test_connect_with_api_raises_no_alerts_for_validators_if_connected_to_api(
            self) -> None:
        self.validator.connect_with_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.connect_with_api(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_connect_with_api_raises_no_alerts_for_full_nodes_if_connected_to_api(
            self) -> None:
        self.full_node.connect_with_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.full_node.connect_with_api(self.channel_set, self.logger)

        self.assertTrue(self.counter_channel.no_alerts())

    def test_connect_with_api_sets_is_connected_true_for_validators_if_connected_to_api(
            self) -> None:
        self.validator.connect_with_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.connect_with_api(self.channel_set, self.logger)

        self.assertTrue(self.validator.is_connected_to_api_server)

    def test_connect_with_api_sets_is_connected_true_for_full_nodes_if_connected_to_api(
            self) -> None:
        self.full_node.connect_with_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.full_node.connect_with_api(self.channel_set, self.logger)

        self.assertTrue(self.validator.is_connected_to_api_server)

    def test_connect_with_api_sets_is_connected_true_for_validators_if_not_connected_to_api(
            self) -> None:
        self.validator.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.validator.connect_with_api(self.channel_set, self.logger)

        self.assertTrue(self.validator.is_connected_to_api_server)

    def test_connect_with_api_sets_is_connected_true_for_full_nodes_if_not_connected_to_api(
            self) -> None:
        self.full_node.disconnect_from_api(self.channel_set, self.logger)
        self.counter_channel.reset()
        self.full_node.connect_with_api(self.channel_set, self.logger)

        self.assertTrue(self.validator.is_connected_to_api_server)

# @unittest.skip("Skipping Test Node With Redis")
class TestNodeWithRedis(unittest.TestCase):

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
        self.node_name = 'testnode'
        self.date = datetime.now().timestamp()
        self.chain = 'testchain'
        self.redis_prefix = self.node_name + "@" + self.chain
        self.date = datetime.min + timedelta(days=123)
        self.logger = logging.getLogger('dummy')

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

        self.non_validator = Node(name=self.node_name, api_url=None,
                              node_type=NodeType.NON_VALIDATOR_FULL_NODE,
                              node_public_key='',chain=self.chain, 
                              redis=self.redis,
                              is_archive_node=True,
                              consensus_public_key="USDKAJBD123hdas9dasodnaasd",
                              tendermint_address_key="skojabdba991231dsqkslndaknsd",
                              entity_public_key="askdasssd188ssassalkdnalsdasss",
                              internal_conf=TestInternalConf)

        self.validator = Node(name=self.node_name, api_url=None,
                              node_type=NodeType.VALIDATOR_FULL_NODE,
                              node_public_key='', chain=self.chain,
                              redis=self.redis,
                              is_archive_node=True,
                              consensus_public_key="USDKAJBD123hdas9dasodnaasd",
                              tendermint_address_key="skojabdba991231dsqkslndaknsd",
                              entity_public_key="askdasssd188ssassalkdnalsdasss",
                              internal_conf=TestInternalConf)


    def test_load_state_changes_nothing_if_nothing_saved(self):
        self.validator.load_state(self.logger)

        self.assertFalse(self.validator.is_down)
        self.assertFalse(self.validator.is_missing_blocks)
        self.assertIsNone(self.validator.bonded_balance)
        self.assertIsNone(self.validator.debonding_balance)
        self.assertIsNone(self.validator.shares_balance)
        self.assertFalse(self.validator.is_syncing)
        self.assertIsNone(self.validator.no_of_peers)
        self.assertIsNone(self.validator.is_active)
        self.assertEqual(self.validator._time_of_last_height_check_activity,
                         NONE)
        self.assertIsNotNone(self.validator._time_of_last_height_change)
        self.assertEqual(self.validator.finalized_block_height, 0)
        self.assertFalse(self.validator.is_no_change_in_height_warning_sent)

    def test_load_state_sets_values_to_saved_values(self):
        # Set Redis values manually
        hash_name = Keys.get_hash_blockchain(self.validator.chain)
        node = self.validator.name
        self.redis.hset_multiple_unsafe(hash_name, {
            Keys.get_node_went_down_at(node): str(self.date),
            Keys.get_node_is_syncing(node): str(True),
            Keys.get_consecutive_blocks_missed(node): 123,
            Keys.get_voting_power(node): 456,
            Keys.get_node_bonded_balance(node): 456,
            Keys.get_node_debonding_balance(node): 456,
            Keys.get_node_shares_balance(node): 456,
            Keys.get_node_no_of_peers(node): 789,
            Keys.get_node_active(node): str(True),
            Keys.get_node_time_of_last_height_check_activity(node): 456.6,
            Keys.get_node_time_of_last_height_change(node): 35.4,
            Keys.get_node_finalized_block_height(node): 43,
            Keys.get_node_no_change_in_height_warning_sent(node): str(True),
        })

        # Load the Redis values
        self.validator.load_state(self.logger)

        # Assert
        self.assertTrue(self.validator.is_down)
        self.assertTrue(self.validator.is_syncing)
        self.assertEqual(self.validator.bonded_balance, 456)
        self.assertEqual(self.validator.debonding_balance, 456)
        self.assertEqual(self.validator.shares_balance, 456)
        self.assertEqual(self.validator.no_of_peers, 789)
        self.assertTrue(self.validator.is_active)
        self.assertEqual(self.validator._time_of_last_height_check_activity,
                         456.6)
        self.assertEqual(self.validator._time_of_last_height_change, 35.4)
        self.assertEqual(self.validator.finalized_block_height, 43)
        self.assertTrue(self.validator.is_no_change_in_height_warning_sent)

    def test_load_state_sets_last_height_timer_to_last_activity_if_not_NONE(
            self) -> None:
        hash_name = Keys.get_hash_blockchain(self.chain)
        self.redis.hset_multiple_unsafe(hash_name, {
            Keys.get_node_time_of_last_height_check_activity(
                self.node_name): 123.4
        })
        last_time = datetime.fromtimestamp(123.4)

        self.validator.load_state(self.logger)
        self.assertEqual(self.validator.finalized_height_alert_limiter.
                         last_time_that_did_task, last_time)

    def test_load_state_sets_height_timer_to_not_NONE_if_last_activity_NONE(
            self) -> None:
        self.validator.load_state(self.logger)
        self.assertIsNotNone(self.validator.finalized_height_alert_limiter.
                             last_time_that_did_task)

    def test_load_state_sets_time_of_last_change_to_not_NONE_if_last_activity_NONE(
            self) -> None:
        self.validator.load_state(self.logger)
        self.assertIsNotNone(self.validator._time_of_last_height_change)

    def test_load_state_sets_went_down_at_to_none_if_incorrect_type(self):
        # Set Redis values manually
        self.redis.set_unsafe(self.redis_prefix + '_went_down_at', str(True))

        # Load the Redis values
        self.validator.load_state(self.logger)

        # Assert
        self.assertIsNone(self.validator._went_down_at)

    def test_save_state_sets_values_to_current_values(self):
        # Set node values manually
        self.validator._went_down_at = self.date
        self.validator._bonded_balance = 456
        self.validator._debonding_balance = 456
        self.validator._shares_balance = 456
        self.validator._voting_power = 456
        self.validator._consecutive_blocks_missed = 123
        self.validator._is_syncing = True
        self.validator._no_of_peers = 789
        self.validator._active = True
        self.validator._time_of_last_height_check_activity = 45.5
        self.validator._time_of_last_height_change = 45.5
        self.validator._finalized_block_height = 34
        self.validator._no_change_in_height_warning_sent = True

        # Save the values to Redis
        self.validator.save_state(self.logger)

        # Assert
        hash_name = Keys.get_hash_blockchain(self.validator.chain)

        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_consecutive_blocks_missed(self.validator.name)), 123)
       
        self.assertEqual(dateutil.parser.parse(self.redis.hget_unsafe(
            hash_name, Keys.get_node_went_down_at(self.validator.name))),
            self.date)
        
        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_voting_power(self.validator.name)), 456)

        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_node_bonded_balance(self.validator.name)), 456)
        
        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_node_debonding_balance(self.validator.name)), 456)

        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_node_shares_balance(self.validator.name)), 456)

        self.assertTrue(self.redis.hget_bool_unsafe(
            hash_name, Keys.get_node_is_syncing(self.validator.name)))
        
        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_node_no_of_peers(self.validator.name)), 789)
        
        self.assertTrue(self.redis.hget_bool_unsafe(
            hash_name, Keys.get_node_active(self.validator.name)))
        
        self.assertEqual(float(self.redis.hget(
            hash_name, Keys.get_node_time_of_last_height_check_activity(
                self.validator.name))), 45.5)
        
        self.assertEqual(float(self.redis.hget(
            hash_name,
            Keys.get_node_time_of_last_height_change(self.validator.name))),
            45.5)
        
        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name,
            Keys.get_node_finalized_block_height(self.validator.name)), 34)
        
        self.assertTrue(self.redis.hget_bool_unsafe(
            hash_name, Keys.get_node_no_change_in_height_warning_sent(
                self.validator.name)))
