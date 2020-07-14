import logging
import unittest
from datetime import timedelta
from time import sleep

import dateutil
from redis import ConnectionError as RedisConnectionError

from src.alerters.reactive.system import System
from src.alerts.alerts import *
from src.channels.channel import ChannelSet
from src.store.redis.redis_api import RedisApi
from src.store.store_keys import Keys
from src.utils.types import NONE
from test import TestInternalConf, TestUserConf
from src.alerters.reactive.node import Node, NodeType
from test.test_helpers import CounterChannel, DummyException

class TestSystemWithoutRedis(unittest.TestCase):
    
    def setUp(self) -> None:
        self.system_name = 'testsystem'
        self.logger = logging.getLogger('dummy')
        self.counter_channel = CounterChannel(self.logger)
        self.channel_set = ChannelSet([self.counter_channel], TestInternalConf)

        self._validator_process_memory_usage_danger_boundary = \
            TestInternalConf.validator_process_memory_usage_danger_boundary
        self._validator_process_memory_usage_safe_boundary = \
            TestInternalConf.validator_process_memory_usage_safe_boundary
        self._validator_open_file_descriptors_danger_boundary = \
            TestInternalConf.validator_open_file_descriptors_danger_boundary
        self._validator_open_file_descriptors_safe_boundary = \
            TestInternalConf.validator_open_file_descriptors_safe_boundary
        self._validator_system_cpu_usage_danger_boundary = \
            TestInternalConf.validator_system_cpu_usage_danger_boundary
        self._validator_system_cpu_usage_safe_boundary = \
            TestInternalConf.validator_system_cpu_usage_safe_boundary
        self._validator_system_ram_usage_danger_boundary = \
            TestInternalConf.validator_system_ram_usage_danger_boundary
        self._validator_system_ram_usage_safe_boundary = \
            TestInternalConf.validator_system_ram_usage_safe_boundary
        self._validator_system_storage_usage_danger_boundary = \
            TestInternalConf.validator_system_storage_usage_danger_boundary
        self._validator_system_storage_usage_safe_boundary = \
            TestInternalConf.validator_system_storage_usage_safe_boundary

        self._node_process_memory_usage_danger_boundary = \
            TestInternalConf.node_process_memory_usage_danger_boundary
        self._node_process_memory_usage_safe_boundary = \
            TestInternalConf.node_process_memory_usage_safe_boundary
        self._node_open_file_descriptors_danger_boundary = \
            TestInternalConf.node_open_file_descriptors_danger_boundary
        self._node_open_file_descriptors_safe_boundary = \
            TestInternalConf.node_open_file_descriptors_safe_boundary
        self._node_system_cpu_usage_danger_boundary = \
            TestInternalConf.node_system_cpu_usage_danger_boundary
        self._node_system_cpu_usage_safe_boundary = \
            TestInternalConf.node_system_cpu_usage_safe_boundary
        self._node_system_ram_usage_danger_boundary = \
            TestInternalConf.node_system_ram_usage_danger_boundary
        self._node_system_ram_usage_safe_boundary = \
            TestInternalConf.node_system_ram_usage_safe_boundary
        self._node_system_storage_usage_danger_boundary = \
            TestInternalConf.node_system_storage_usage_danger_boundary
        self._node_system_storage_usage_safe_boundary = \
            TestInternalConf.node_system_storage_usage_safe_boundary

        # safe values (0-safe)
        self.safe_node_process_cpu_seconds_total = 20
        self.safe_node_process_memory_usage = 20
        self.safe_node_virtual_memory_usage = 20
        self.safe_node_open_file_descriptors = 20
        self.safe_node_system_cpu_usage = 20
        self.safe_node_system_ram_usage = 20
        self.safe_node_system_storage_usage = 20

        # Above safe below danger values (safe-danger)
        self.not_safe_node_process_cpu_seconds_total = 72
        self.not_safe_node_process_memory_usage = 72
        self.not_safe_node_virtual_memory_usage = 72
        self.not_safe_node_open_file_descriptors = 72
        self.not_safe_node_system_cpu_usage = 72
        self.not_safe_node_system_ram_usage = 72
        self.not_safe_node_system_storage_usage = 72

        # Above danger values (danger-100)
        self.danger_node_process_cpu_seconds_total = 92
        self.danger_node_process_memory_usage = 92
        self.danger_node_virtual_memory_usage = 92
        self.danger_node_open_file_descriptors = 92
        self.danger_node_system_cpu_usage = 92
        self.danger_node_system_ram_usage = 92
        self.danger_node_system_storage_usage = 92

        # safe values (0-safe)
        self.safe_validator_process_cpu_seconds_total = 20
        self.safe_validator_process_memory_usage = 20
        self.safe_validator_virtual_memory_usage = 20
        self.safe_validator_open_file_descriptors = 20
        self.safe_validator_system_cpu_usage = 20
        self.safe_validator_system_ram_usage = 20
        self.safe_validator_system_storage_usage = 20

        # Above safe below danger values (safe-danger)
        self.not_safe_validator_process_cpu_seconds_total = 50
        self.not_safe_validator_process_memory_usage = 50
        self.not_safe_validator_virtual_memory_usage = 50
        self.not_safe_validator_open_file_descriptors = 50
        self.not_safe_validator_system_cpu_usage = 50
        self.not_safe_validator_system_ram_usage = 50
        self.not_safe_validator_system_storage_usage = 50

        # Above danger values (danger-100)
        self.danger_validator_process_cpu_seconds_total = 90
        self.danger_validator_process_memory_usage = 90
        self.danger_validator_virtual_memory_usage = 90
        self.danger_validator_open_file_descriptors = 90
        self.danger_validator_system_cpu_usage = 90
        self.danger_validator_system_ram_usage = 90
        self.danger_validator_system_storage_usage = 90

        self.chain = 'testchain'
        self.full_node_name = 'testfullnode'
        self.full_node_api_url = '123.123.123.11:9944'
        self.full_node_consensus_key = "ANDSAdisadjasdaANDAsa"
        self.full_node_tendermint_key = "ASFLNAFIISDANNSDAKKS2313AA"
        self.full_node_entity_public_key = "a98dabsfkjabfkjabsf9j"
        self.node_monitor_max_catch_up_blocks = \
            TestInternalConf.node_monitor_max_catch_up_blocks

        self.full_node = Node(self.full_node_name, self.full_node_api_url, None,
                            NodeType.NON_VALIDATOR_FULL_NODE, '', self.chain,
                            None, True, self.full_node_consensus_key,
                            self.full_node_tendermint_key, 
                            self.full_node_entity_public_key,
                            TestInternalConf)

        self.validator_node = Node(self.full_node_name, self.full_node_api_url,
                    None, NodeType.VALIDATOR_FULL_NODE, '', self.chain,
                    None, True, self.full_node_consensus_key,
                    self.full_node_tendermint_key, 
                    self.full_node_entity_public_key,
                    TestInternalConf)

        self.full_node_system = System(name=self.system_name, redis=None, \
            node=self.full_node, internal_conf=TestInternalConf)

        self.validator_system = System(name=self.system_name, redis=None, \
            node=self.validator_node, internal_conf=TestInternalConf)

    def test_process_cpu_seconds_total_is_none_by_default(self) -> None:
        self.assertIsNone(self.full_node_system.process_cpu_seconds_total)
        self.assertIsNone(self.validator_system.process_cpu_seconds_total)

    def test_process_memory_usage_is_none_by_default(self) -> None:
        self.assertIsNone(self.full_node_system.process_memory_usage)
        self.assertIsNone(self.validator_system.process_memory_usage)

    def test_virtual_memory_usage_is_none_by_default(self) -> None:
        self.assertIsNone(self.full_node_system.virtual_memory_usage)
        self.assertIsNone(self.validator_system.virtual_memory_usage)

    def test_open_file_descriptors_is_none_by_default(self) -> None:
        self.assertIsNone(self.full_node_system.open_file_descriptors)
        self.assertIsNone(self.validator_system.open_file_descriptors)

    def test_system_cpu_usage_is_none_by_default(self) -> None:
        self.assertIsNone(self.full_node_system.system_cpu_usage)
        self.assertIsNone(self.validator_system.system_cpu_usage)

    def test_system_ram_usage_is_none_by_default(self) -> None:
        self.assertIsNone(self.full_node_system.system_ram_usage)
        self.assertIsNone(self.validator_system.system_ram_usage)

    def test_system_storage_usage_is_none_by_default(self) -> None:
        self.assertIsNone(self.full_node_system.system_storage_usage)
        self.assertIsNone(self.validator_system.system_storage_usage)

    def test_status_returns_as_expected(self) -> None:
        self.full_node_system._process_cpu_seconds_total = \
            self.safe_node_process_cpu_seconds_total
        self.full_node_system._process_memory_usage = self.safe_node_process_memory_usage
        self.full_node_system._virtual_memory_usage = self.safe_node_virtual_memory_usage
        self.full_node_system._open_file_descriptors = self.safe_node_open_file_descriptors
        self.full_node_system._system_cpu_usage = self.safe_node_system_cpu_usage
        self.full_node_system._system_ram_usage = self.safe_node_system_ram_usage
        self.full_node_system._system_storage_usage = self.safe_node_system_storage_usage
        
        self.assertEqual(self.full_node_system.status(), ""\
            "process_cpu_seconds_total={}, " \
            "process_memory_usage={}, virtual_memory_usage={}, " \
            "open_file_descriptors={}, system_cpu_usage={}, " \
            "system_ram_usage={}, system_storage_usage={}, " \
            "".format(self.safe_node_process_cpu_seconds_total,
                self.safe_node_process_memory_usage,
                self.safe_node_virtual_memory_usage,
                self.safe_node_open_file_descriptors,
                self.safe_node_system_cpu_usage,
                self.safe_node_system_ram_usage,
                self.safe_node_system_storage_usage)
        )

    def test_set_process_cpu_seconds_total_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.full_node_system.set_process_cpu_seconds_total( \
            self.safe_node_process_cpu_seconds_total,
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node_system._process_cpu_seconds_total, \
            self.safe_node_process_cpu_seconds_total)

    def test_set_process_cpu_seconds_total_and_raise_info_alerts_on_increase(
        self) -> None:
        self.full_node_system.set_process_cpu_seconds_total( \
            self.safe_node_process_cpu_seconds_total, \
            self.channel_set, self.logger)
        self.full_node_system.set_process_cpu_seconds_total( \
        self.not_safe_node_process_cpu_seconds_total, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_set_process_cpu_seconds_total_and_raise_info_alerts_on_decrease(
        self) -> None:
        self.full_node_system.set_process_cpu_seconds_total( \
            self.not_safe_node_process_cpu_seconds_total,
            self.channel_set, self.logger)
        self.full_node_system.set_process_cpu_seconds_total( \
            self.safe_node_process_cpu_seconds_total, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_set_process_cpu_seconds_total_and_raise_no_alerts_on_no_change(
        self) -> None:
        self.full_node_system.set_process_cpu_seconds_total(
            self.safe_node_process_cpu_seconds_total, \
            self.channel_set, self.logger)
        self.full_node_system.set_process_cpu_seconds_total(
            self.safe_node_process_cpu_seconds_total, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 0)

    def test_set_virtual_memory_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.full_node_system.set_virtual_memory_usage( \
            self.safe_node_virtual_memory_usage,
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node_system._virtual_memory_usage, \
            self.safe_node_virtual_memory_usage)

    def test_set_virtual_memory_usage_and_raise_info_alerts_on_increase(
        self) -> None:
        self.full_node_system.set_virtual_memory_usage( \
            self.safe_node_virtual_memory_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_virtual_memory_usage( \
        self.not_safe_node_virtual_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_set_virtual_memory_usage_and_raise_info_alerts_on_decrease(
        self) -> None:
        self.full_node_system.set_virtual_memory_usage( \
            self.not_safe_node_virtual_memory_usage,
            self.channel_set, self.logger)
        self.full_node_system.set_virtual_memory_usage( \
            self.safe_node_virtual_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_set_virtual_memory_usage_and_raise_no_alerts_on_no_change(
        self) -> None:
        self.full_node_system.set_virtual_memory_usage(
            self.safe_node_virtual_memory_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_virtual_memory_usage(
            self.safe_node_virtual_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 0)

###############################################################################

    def test_node_set_process_memory_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.full_node_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node_system.process_memory_usage, \
            self.safe_validator_process_memory_usage)

    def test_node_set_process_memory_usage_and_raise_no_alerts_same_process_memory(
        self) -> None:
        self.full_node_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_node_set_process_memory_usage_and_raise_info_alerts_if_decrease_out_of_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage(self.danger_node_process_memory_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_process_memory_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_process_memory_usage_and_raise_info_alerts_if_increase_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.safe_validator_process_memory_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_process_memory_usage_and_raise_info_alerts_if_decrease_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.safe_validator_process_memory_usage + 5 , self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.safe_validator_process_memory_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_process_memory_usage_and_raise_warning_alerts_if_increase_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.not_safe_node_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.not_safe_node_process_memory_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_process_memory_usage_and_raise_info_alerts_if_decrease_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.not_safe_node_process_memory_usage + 5, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.not_safe_node_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_process_memory_usage_and_raise_warning_alerts_if_increase_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.not_safe_node_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.not_safe_node_process_memory_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_process_memory_usage_and_raise_info_alerts_if_decrease_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.not_safe_node_process_memory_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.not_safe_node_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_node_set_process_memory_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.not_safe_node_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.safe_node_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_process_memory_usage_and_raise_critical_alerts_if_increase_into_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.not_safe_node_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.danger_node_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_process_memory_usage_and_raise_critical_alerts_if_increase_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.danger_node_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.danger_node_process_memory_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_process_memory_usage_and_raise_critical_alerts_if_decrease_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.danger_node_process_memory_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.danger_node_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)
    
    def test_node_set_process_memory_usage_and_raise_info_alert_if_decrease_outside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_process_memory_usage( \
            self.danger_node_process_memory_usage, self.channel_set, self.logger)
        self.full_node_system.set_process_memory_usage(self.not_safe_node_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    ############################################################################

    def test_validator_set_process_memory_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator_system.process_memory_usage, \
            self.safe_validator_process_memory_usage)

    def test_validator_set_process_memory_usage_and_raise_no_alerts_same_process_memory(
        self) -> None:
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_validator_set_process_memory_usage_and_raise_info_alerts_if_decrease_out_of_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage(self.danger_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_process_memory_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_process_memory_usage_and_raise_info_alerts_if_increase_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_process_memory_usage_and_raise_info_alerts_if_decrease_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.safe_validator_process_memory_usage + 5 , self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_process_memory_usage_and_raise_warning_alerts_if_increase_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.not_safe_validator_process_memory_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_process_memory_usage_and_raise_info_alerts_if_decrease_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage + 5, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.not_safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_process_memory_usage_and_raise_warning_alerts_if_increase_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.not_safe_validator_process_memory_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_process_memory_usage_and_raise_info_alerts_if_decrease_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage+5, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.not_safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_validator_set_process_memory_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_process_memory_usage_and_raise_critical_alerts_if_increase_into_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.not_safe_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.danger_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_process_memory_usage_and_raise_critical_alerts_if_increase_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.danger_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.danger_validator_process_memory_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_process_memory_usage_and_raise_critical_alerts_if_decrease_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.danger_validator_process_memory_usage+5, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.danger_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)
    
    def test_validator_set_process_memory_usage_and_raise_info_alert_if_decrease_outside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_process_memory_usage( \
            self.danger_validator_process_memory_usage, self.channel_set, self.logger)
        self.validator_system.set_process_memory_usage(self.not_safe_validator_process_memory_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

################################################################################

    def test_node_set_open_file_descriptors_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node_system.open_file_descriptors, \
            self.safe_node_open_file_descriptors)

    def test_node_set_open_file_descriptors_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_node_set_open_file_descriptors_and_raise_info_alerts_if_decrease_out_of_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors(self.danger_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_open_file_descriptors_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.not_safe_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_open_file_descriptors_and_raise_info_alerts_if_increase_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.safe_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_open_file_descriptors_and_raise_info_alerts_if_decrease_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.safe_node_open_file_descriptors + 5 , self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_open_file_descriptors_and_raise_warning_alerts_if_increase_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.not_safe_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.not_safe_node_open_file_descriptors + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_open_file_descriptors_and_raise_info_alerts_if_decrease_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.not_safe_node_open_file_descriptors + 5, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.not_safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_open_file_descriptors_and_raise_warning_alerts_if_increase_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.not_safe_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.not_safe_node_open_file_descriptors + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_open_file_descriptors_and_raise_info_alerts_if_decrease_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.not_safe_node_open_file_descriptors+5, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.not_safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_node_set_open_file_descriptors_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.not_safe_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_open_file_descriptors_and_raise_critical_alerts_if_increase_into_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.not_safe_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.danger_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_open_file_descriptors_and_raise_critical_alerts_if_increase_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.danger_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.danger_node_open_file_descriptors + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_open_file_descriptors_and_raise_critical_alerts_if_decrease_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.danger_node_open_file_descriptors+5, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.danger_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_open_file_descriptors_and_raise_info_alert_if_decrease_outside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_open_file_descriptors( \
            self.danger_node_open_file_descriptors, self.channel_set, self.logger)
        self.full_node_system.set_open_file_descriptors(self.not_safe_node_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

###############################################################################

    def test_validator_set_open_file_descriptors_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator_system.open_file_descriptors, \
            self.safe_validator_open_file_descriptors)

    def test_validator_set_open_file_descriptors_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_validator_set_open_file_descriptors_and_raise_info_alerts_if_decrease_out_of_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors(self.danger_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.not_safe_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_info_alerts_if_increase_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.safe_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_info_alerts_if_decrease_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.safe_validator_open_file_descriptors + 5 , self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_warning_alerts_if_increase_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.not_safe_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.not_safe_validator_open_file_descriptors + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_info_alerts_if_decrease_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.not_safe_validator_open_file_descriptors + 5, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.not_safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_warning_alerts_if_increase_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.not_safe_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.not_safe_validator_open_file_descriptors + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_info_alerts_if_decrease_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.not_safe_validator_open_file_descriptors+5, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.not_safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_validator_set_open_file_descriptors_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.not_safe_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_critical_alerts_if_increase_into_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.not_safe_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.danger_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_critical_alerts_if_increase_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.danger_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.danger_validator_open_file_descriptors + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_critical_alerts_if_decrease_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.danger_validator_open_file_descriptors+5, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.danger_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_open_file_descriptors_and_raise_info_alert_if_decrease_outside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_open_file_descriptors( \
            self.danger_validator_open_file_descriptors, self.channel_set, self.logger)
        self.validator_system.set_open_file_descriptors(self.not_safe_validator_open_file_descriptors, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

###############################################################################

    def test_node_set_system_cpu_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node_system.system_cpu_usage, \
            self.safe_node_system_cpu_usage)

    def test_node_set_system_cpu_usage_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_node_set_system_cpu_usage_and_raise_info_alerts_if_decrease_out_of_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage(self.danger_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_cpu_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.not_safe_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_cpu_usage_and_raise_info_alerts_if_increase_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.safe_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_cpu_usage_and_raise_info_alerts_if_decrease_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.safe_node_system_cpu_usage + 5 , self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_cpu_usage_and_raise_warning_alerts_if_increase_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.not_safe_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.not_safe_node_system_cpu_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_system_cpu_usage_and_raise_info_alerts_if_decrease_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.not_safe_node_system_cpu_usage + 5, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.not_safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_cpu_usage_and_raise_warning_alerts_if_increase_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.not_safe_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.not_safe_node_system_cpu_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_system_cpu_usage_and_raise_info_alerts_if_decrease_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.not_safe_node_system_cpu_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.not_safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_node_set_system_cpu_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.not_safe_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_cpu_usage_and_raise_critical_alerts_if_increase_into_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.not_safe_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.danger_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_cpu_usage_and_raise_critical_alerts_if_increase_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.danger_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.danger_node_system_cpu_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_cpu_usage_and_raise_critical_alerts_if_decrease_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.danger_node_system_cpu_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.danger_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_cpu_usage_and_raise_info_alert_if_decrease_outside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_cpu_usage( \
            self.danger_node_system_cpu_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_cpu_usage(self.not_safe_node_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

################################################################################

    def test_node_set_system_cpu_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator_system.system_cpu_usage, \
            self.safe_validator_system_cpu_usage)

    def test_validator_set_system_cpu_usage_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_validator_set_system_cpu_usage_and_raise_info_alerts_if_decrease_out_of_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage(self.danger_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.not_safe_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_info_alerts_if_increase_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.safe_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_info_alerts_if_decrease_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.safe_validator_system_cpu_usage + 5 , self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_warning_alerts_if_increase_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.not_safe_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.not_safe_validator_system_cpu_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_info_alerts_if_decrease_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.not_safe_validator_system_cpu_usage + 5, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.not_safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_warning_alerts_if_increase_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.not_safe_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.not_safe_validator_system_cpu_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_info_alerts_if_decrease_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.not_safe_validator_system_cpu_usage+5, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.not_safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_validator_set_system_cpu_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.not_safe_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_critical_alerts_if_increase_into_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.not_safe_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.danger_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_critical_alerts_if_increase_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.danger_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.danger_validator_system_cpu_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_critical_alerts_if_decrease_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.danger_validator_system_cpu_usage+5, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.danger_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_cpu_usage_and_raise_info_alert_if_decrease_outside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_cpu_usage( \
            self.danger_validator_system_cpu_usage, self.channel_set, self.logger)
        self.validator_system.set_system_cpu_usage(self.not_safe_validator_system_cpu_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

################################################################################

    def test_node_set_system_ram_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node_system.system_ram_usage, \
            self.safe_node_system_ram_usage)

    def test_node_set_system_ram_usage_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_node_set_system_ram_usage_and_raise_info_alerts_if_decrease_out_of_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage(self.danger_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_ram_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.not_safe_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_ram_usage_and_raise_info_alerts_if_increase_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.safe_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_ram_usage_and_raise_info_alerts_if_decrease_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.safe_node_system_ram_usage + 5 , self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_ram_usage_and_raise_warning_alerts_if_increase_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.not_safe_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.not_safe_node_system_ram_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_system_ram_usage_and_raise_info_alerts_if_decrease_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.not_safe_node_system_ram_usage + 5, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.not_safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_ram_usage_and_raise_warning_alerts_if_increase_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.not_safe_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.not_safe_node_system_ram_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_system_ram_usage_and_raise_info_alerts_if_decrease_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.not_safe_node_system_ram_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.not_safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_node_set_system_ram_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.not_safe_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_ram_usage_and_raise_critical_alerts_if_increase_into_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.not_safe_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.danger_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_ram_usage_and_raise_critical_alerts_if_increase_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.danger_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.danger_node_system_ram_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_ram_usage_and_raise_critical_alerts_if_decrease_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.danger_node_system_ram_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.danger_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_ram_usage_and_raise_info_alert_if_decrease_outside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_ram_usage( \
            self.danger_node_system_ram_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_ram_usage(self.not_safe_node_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

################################################################################

    def test_validator_set_system_ram_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator_system.system_ram_usage, \
            self.safe_validator_system_ram_usage)

    def test_validator_set_system_ram_usage_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_validator_set_system_ram_usage_and_raise_info_alerts_if_decrease_out_of_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage(self.danger_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_ram_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.not_safe_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_ram_usage_and_raise_info_alerts_if_increase_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.safe_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_ram_usage_and_raise_info_alerts_if_decrease_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.safe_validator_system_ram_usage + 5 , self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_ram_usage_and_raise_warning_alerts_if_increase_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.not_safe_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.not_safe_validator_system_ram_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_system_ram_usage_and_raise_info_alerts_if_decrease_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.not_safe_validator_system_ram_usage + 5, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.not_safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_ram_usage_and_raise_warning_alerts_if_increase_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.not_safe_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.not_safe_validator_system_ram_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_system_ram_usage_and_raise_info_alerts_if_decrease_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.not_safe_validator_system_ram_usage+5, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.not_safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_validator_set_system_ram_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.not_safe_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_ram_usage_and_raise_critical_alerts_if_increase_into_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.not_safe_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.danger_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_ram_usage_and_raise_critical_alerts_if_increase_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.danger_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.danger_validator_system_ram_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_ram_usage_and_raise_critical_alerts_if_decrease_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.danger_validator_system_ram_usage+5, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.danger_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_ram_usage_and_raise_info_alert_if_decrease_outside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_ram_usage( \
            self.danger_validator_system_ram_usage, self.channel_set, self.logger)
        self.validator_system.set_system_ram_usage(self.not_safe_validator_system_ram_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

################################################################################

    def test_node_set_system_storage_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.full_node_system.system_storage_usage, \
            self.safe_node_system_storage_usage)

    def test_node_set_system_storage_usage_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_node_set_system_storage_usage_and_raise_info_alerts_if_decrease_out_of_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage(self.danger_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_storage_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.not_safe_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_storage_usage_and_raise_info_alerts_if_increase_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.safe_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_storage_usage_and_raise_info_alerts_if_decrease_inside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.safe_node_system_storage_usage + 5 , self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_storage_usage_and_raise_warning_alerts_if_increase_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.not_safe_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.not_safe_node_system_storage_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_system_storage_usage_and_raise_info_alerts_if_decrease_outside_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.not_safe_node_system_storage_usage + 5, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.not_safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_storage_usage_and_raise_warning_alerts_if_increase_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.not_safe_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.not_safe_node_system_storage_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_node_set_system_storage_usage_and_raise_info_alerts_if_decrease_between_safe_node_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.not_safe_node_system_storage_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.not_safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_node_set_system_storage_usage_and_raise_info_alerts_if_decrease_into_safe_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.not_safe_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_node_set_system_storage_usage_and_raise_critical_alerts_if_increase_into_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.not_safe_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.danger_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_storage_usage_and_raise_critical_alerts_if_increase_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.danger_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.danger_node_system_storage_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_storage_usage_and_raise_critical_alerts_if_decrease_inside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.danger_node_system_storage_usage+5, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.danger_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_node_set_system_storage_usage_and_raise_info_alert_if_decrease_outside_danger_node_boundary(
        self) -> None:
        self.full_node_system.set_system_storage_usage( \
            self.danger_node_system_storage_usage, self.channel_set, self.logger)
        self.full_node_system.set_system_storage_usage(self.not_safe_node_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

################################################################################

    def test_validator_set_system_storage_usage_and_raise_no_alerts_first_time_round(
        self) -> None:
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())
        self.assertEqual(self.validator_system.system_storage_usage, \
            self.safe_validator_system_storage_usage)

    def test_validator_set_system_storage_usage_and_raise_no_alerts_same_virtual_memory(
        self) -> None:
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertTrue(self.counter_channel.no_alerts())

    def test_validator_set_system_storage_usage_and_raise_info_alerts_if_decrease_out_of_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage(self.danger_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_storage_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.not_safe_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_storage_usage_and_raise_info_alerts_if_increase_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.safe_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_storage_usage_and_raise_info_alerts_if_decrease_inside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.safe_validator_system_storage_usage + 5 , self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage , \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_storage_usage_and_raise_warning_alerts_if_increase_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.not_safe_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.not_safe_validator_system_storage_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_system_storage_usage_and_raise_info_alerts_if_decrease_outside_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.not_safe_validator_system_storage_usage + 5, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.not_safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_storage_usage_and_raise_warning_alerts_if_increase_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.not_safe_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.not_safe_validator_system_storage_usage + 1, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.warning_count, 1)

    def test_validator_set_system_storage_usage_and_raise_info_alerts_if_decrease_between_safe_validator_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.not_safe_validator_system_storage_usage+5, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.not_safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)
    
    def test_validator_set_system_storage_usage_and_raise_info_alerts_if_decrease_into_safe_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.not_safe_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)

    def test_validator_set_system_storage_usage_and_raise_critical_alerts_if_increase_into_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.not_safe_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.danger_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_storage_usage_and_raise_critical_alerts_if_increase_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.danger_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.danger_validator_system_storage_usage + 5, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_storage_usage_and_raise_critical_alerts_if_decrease_inside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.danger_validator_system_storage_usage+5, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.danger_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.critical_count, 1)

    def test_validator_set_system_storage_usage_and_raise_info_alert_if_decrease_outside_danger_validator_boundary(
        self) -> None:
        self.validator_system.set_system_storage_usage( \
            self.danger_validator_system_storage_usage, self.channel_set, self.logger)
        self.validator_system.set_system_storage_usage(self.not_safe_validator_system_storage_usage, \
            self.channel_set, self.logger)
        self.assertEqual(self.counter_channel.info_count, 1)


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
        self.system_name = 'testsystem'
        self.chain = 'testchain'
        self.logger = logging.getLogger('dummy')
        self.counter_channel = CounterChannel(self.logger)
        self.channel_set = ChannelSet([self.counter_channel], TestInternalConf)

        self.redis_prefix = self.system_name + "@" + self.chain
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

        self._validator_process_memory_usage_danger_boundary = \
            TestInternalConf.validator_process_memory_usage_danger_boundary
        self._validator_process_memory_usage_safe_boundary = \
            TestInternalConf.validator_process_memory_usage_safe_boundary
        self._validator_open_file_descriptors_danger_boundary = \
            TestInternalConf.validator_open_file_descriptors_danger_boundary
        self._validator_open_file_descriptors_safe_boundary = \
            TestInternalConf.validator_open_file_descriptors_safe_boundary
        self._validator_system_cpu_usage_danger_boundary = \
            TestInternalConf.validator_system_cpu_usage_danger_boundary
        self._validator_system_cpu_usage_safe_boundary = \
            TestInternalConf.validator_system_cpu_usage_safe_boundary
        self._validator_system_ram_usage_danger_boundary = \
            TestInternalConf.validator_system_ram_usage_danger_boundary
        self._validator_system_ram_usage_safe_boundary = \
            TestInternalConf.validator_system_ram_usage_safe_boundary
        self._validator_system_storage_usage_danger_boundary = \
            TestInternalConf.validator_system_storage_usage_danger_boundary
        self._validator_system_storage_usage_safe_boundary = \
            TestInternalConf.validator_system_storage_usage_safe_boundary

        self._node_process_memory_usage_danger_boundary = \
            TestInternalConf.node_process_memory_usage_danger_boundary
        self._node_process_memory_usage_safe_boundary = \
            TestInternalConf.node_process_memory_usage_safe_boundary
        self._node_open_file_descriptors_danger_boundary = \
            TestInternalConf.node_open_file_descriptors_danger_boundary
        self._node_open_file_descriptors_safe_boundary = \
            TestInternalConf.node_open_file_descriptors_safe_boundary
        self._node_system_cpu_usage_danger_boundary = \
            TestInternalConf.node_system_cpu_usage_danger_boundary
        self._node_system_cpu_usage_safe_boundary = \
            TestInternalConf.node_system_cpu_usage_safe_boundary
        self._node_system_ram_usage_danger_boundary = \
            TestInternalConf.node_system_ram_usage_danger_boundary
        self._node_system_ram_usage_safe_boundary = \
            TestInternalConf.node_system_ram_usage_safe_boundary
        self._node_system_storage_usage_danger_boundary = \
            TestInternalConf.node_system_storage_usage_danger_boundary
        self._node_system_storage_usage_safe_boundary = \
            TestInternalConf.node_system_storage_usage_safe_boundary

        # safe values (0-safe)
        self.safe_node_process_cpu_seconds_total = 20
        self.safe_node_process_memory_usage = 20
        self.safe_node_virtual_memory_usage = 20
        self.safe_node_open_file_descriptors = 20
        self.safe_node_system_cpu_usage = 20
        self.safe_node_system_ram_usage = 20
        self.safe_node_system_storage_usage = 20

        # Above safe below danger values (safe-danger)
        self.not_safe_node_process_cpu_seconds_total = 72
        self.not_safe_node_process_memory_usage = 72
        self.not_safe_node_virtual_memory_usage = 72
        self.not_safe_node_open_file_descriptors = 72
        self.not_safe_node_system_cpu_usage = 72
        self.not_safe_node_system_ram_usage = 72
        self.not_safe_node_system_storage_usage = 72

        # Above danger values (danger-100)
        self.danger_node_process_cpu_seconds_total = 92
        self.danger_node_process_memory_usage = 92
        self.danger_node_virtual_memory_usage = 92
        self.danger_node_open_file_descriptors = 92
        self.danger_node_system_cpu_usage = 92
        self.danger_node_system_ram_usage = 92
        self.danger_node_system_storage_usage = 92

        # safe values (0-safe)
        self.safe_validator_process_cpu_seconds_total = 20
        self.safe_validator_process_memory_usage = 20
        self.safe_validator_virtual_memory_usage = 20
        self.safe_validator_open_file_descriptors = 20
        self.safe_validator_system_cpu_usage = 20
        self.safe_validator_system_ram_usage = 20
        self.safe_validator_system_storage_usage = 20

        # Above safe below danger values (safe-danger)
        self.not_safe_validator_process_cpu_seconds_total = 50
        self.not_safe_validator_process_memory_usage = 50
        self.not_safe_validator_virtual_memory_usage = 50
        self.not_safe_validator_open_file_descriptors = 50
        self.not_safe_validator_system_cpu_usage = 50
        self.not_safe_validator_system_ram_usage = 50
        self.not_safe_validator_system_storage_usage = 50

        # Above danger values (danger-100)
        self.danger_validator_process_cpu_seconds_total = 90
        self.danger_validator_process_memory_usage = 90
        self.danger_validator_virtual_memory_usage = 90
        self.danger_validator_open_file_descriptors = 90
        self.danger_validator_system_cpu_usage = 90
        self.danger_validator_system_ram_usage = 90
        self.danger_validator_system_storage_usage = 90

        self.chain = 'testchain'
        self.full_node_name = 'testfullnode'
        self.full_node_api_url = '123.123.123.11:9944'
        self.full_node_consensus_key = "ANDSAdisadjasdaANDAsa"
        self.full_node_tendermint_key = "ASFLNAFIISDANNSDAKKS2313AA"
        self.full_node_entity_public_key = "a98dabsfkjabfkjabsf9j"
        self.node_monitor_max_catch_up_blocks = \
            TestInternalConf.node_monitor_max_catch_up_blocks

        self.full_node = Node(self.full_node_name, self.full_node_api_url, None,
                            NodeType.NON_VALIDATOR_FULL_NODE, '', self.chain,
                            None, True, self.full_node_consensus_key,
                            self.full_node_tendermint_key, 
                            self.full_node_entity_public_key,
                            TestInternalConf)

        self.validator_node = Node(self.full_node_name, self.full_node_api_url,
                    None, NodeType.VALIDATOR_FULL_NODE, '', self.chain,
                    None, True, self.full_node_consensus_key,
                    self.full_node_tendermint_key, 
                    self.full_node_entity_public_key,
                    TestInternalConf)

        self.full_node_system = System(name=self.system_name, \
            redis=self.redis, node=self.full_node, \
                internal_conf=TestInternalConf)

        self.validator_system = System(name=self.system_name, \
            redis=self.redis, node=self.validator_node, \
                internal_conf=TestInternalConf)

    def test_load_state_changes_nothing_if_nothing_saved(self):
        self.full_node_system.load_state(self.logger)
        
        self.assertIsNone(self.full_node_system.process_cpu_seconds_total)
        self.assertIsNone(self.full_node_system.process_memory_usage)
        self.assertIsNone(self.full_node_system.virtual_memory_usage)
        self.assertIsNone(self.full_node_system.open_file_descriptors)
        self.assertIsNone(self.full_node_system.system_cpu_usage)
        self.assertIsNone(self.full_node_system.system_ram_usage)
        self.assertIsNone(self.full_node_system.system_storage_usage)

    def test_save_state_sets_values_to_current_values(self):
        # Set node values manually
        self.full_node_system.process_cpu_seconds_total = 20
        self.full_node_system.process_memory_usage = 20
        self.full_node_system.virtual_memory_usage = 20
        self.full_node_system.open_file_descriptors = 20
        self.full_node_system.system_cpu_usage = 20
        self.full_node_system.system_ram_usage = 20
        self.full_node_system.system_storage_usage = 20

        # Save the values to Redis
        self.full_node_system.save_state(self.logger)

        # Assert
        hash_name = Keys.get_hash_blockchain(self.full_node_system.node.chain)

        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_system_get_process_cpu_seconds_total(self.full_node_system.name)), 20)
        
        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_system_get_process_memory_usage(self.full_node_system.name)), 20)

        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_system_get_virtual_memory_usage(self.full_node_system.name)), 20)
        
        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_system_get_open_file_descriptors(self.full_node_system.name)), 20)

        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_system_get_system_cpu_usage(self.full_node_system.name)), 20)
        
        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_system_get_system_ram_usage(self.full_node_system.name)), 20)

        self.assertEqual(self.redis.hget_int_unsafe(
            hash_name, Keys.get_system_get_system_storage_usage(self.full_node_system.name)), 20)