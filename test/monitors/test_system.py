import logging
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock

from redis import ConnectionError as RedisConnectionError

from src.alerters.reactive.system import System
from src.alerters.reactive.node import Node, NodeType
from src.channels.channel import ChannelSet
from src.monitors.system import SystemMonitor
from src.store.redis.redis_api import RedisApi
from src.store.store_keys import Keys
from src.utils.exceptions import NoLiveNodeConnectedWithAnApiServerException
from test import TestInternalConf, TestUserConf
from test.test_helpers import CounterChannel

GET_OASIS_PROMETHEUS = \
    'src.monitors.system.get_oasis_prometheus'

SYSTEM_PATH = \
    'src.monitors.system.SystemMonitor.system'

PROMETHEUS_RETURN = {
    'process_cpu_seconds_total': 8599.65,
    'go_memstats_alloc_bytes' : 2.223928e+06,
    'go_memstats_alloc_bytes_total': 1.14706855112e+11,
    'process_virtual_memory_bytes': 1.18775808e+08,
    'process_max_fds':1024,
    'process_open_fds': 8,
    'node_cpu_seconds_total':{
        "{\"cpu\": \"0\", \"mode\": \"idle\"}":752737.96,
        "{\"cpu\": \"0\", \"mode\": \"iowait\"}":27543.33,
        "{\"cpu\": \"0\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"0\", \"mode\": \"nice\"}":28.83,
        "{\"cpu\": \"0\", \"mode\": \"softirq\"}":4295.32,
        "{\"cpu\": \"0\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"0\", \"mode\": \"system\"}":19363.9,
        "{\"cpu\": \"0\", \"mode\": \"user\"}":61338.69,
        "{\"cpu\": \"1\", \"mode\": \"idle\"}":752765.99,
        "{\"cpu\": \"1\", \"mode\": \"iowait\"}":26523.94,
        "{\"cpu\": \"1\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"1\", \"mode\": \"nice\"}":26.01,
        "{\"cpu\": \"1\", \"mode\": \"softirq\"}":3393.48,
        "{\"cpu\": \"1\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"1\", \"mode\": \"system\"}":20271.08,
        "{\"cpu\": \"1\", \"mode\": \"user\"}":61747.17,
        "{\"cpu\": \"2\", \"mode\": \"idle\"}":752386.53,
        "{\"cpu\": \"2\", \"mode\": \"iowait\"}":26560.33,
        "{\"cpu\": \"2\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"2\", \"mode\": \"nice\"}":29.57,
        "{\"cpu\": \"2\", \"mode\": \"softirq\"}":3264.85,
        "{\"cpu\": \"2\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"2\", \"mode\": \"system\"}":20337.47,
        "{\"cpu\": \"2\", \"mode\": \"user\"}":61632.38,
        "{\"cpu\": \"3\", \"mode\": \"idle\"}":750801.25,
        "{\"cpu\": \"3\", \"mode\": \"iowait\"}":28653.92,
        "{\"cpu\": \"3\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"3\", \"mode\": \"nice\"}":23.78,
        "{\"cpu\": \"3\", \"mode\": \"softirq\"}":3085.45,
        "{\"cpu\": \"3\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"3\", \"mode\": \"system\"}":19650.69,
        "{\"cpu\": \"3\", \"mode\": \"user\"}":61513.88
    },
    'node_filesystem_avail_bytes':{
        "{\"device\": \"/dev/mapper/ubuntu--vg-ubuntu--lv\", \"fstype\": \"ext4\", \"mountpoint\": \"/\"}":40624627712.0,
        "{\"device\": \"/dev/sda2\", \"fstype\": \"ext4\", \"mountpoint\": \"/boot\"}":872026112.0,
        "{\"device\": \"lxcfs\", \"fstype\": \"fuse.lxcfs\", \"mountpoint\": \"/var/lib/lxcfs\"}":0.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run\"}":412160000.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run/lock\"}":5242880.0
    },
    'node_filesystem_size_bytes' : {
        "{\"device\": \"/dev/mapper/ubuntu--vg-ubuntu--lv\", \"fstype\": \"ext4\", \"mountpoint\": \"/\"}":104560844800.0,
        "{\"device\": \"/dev/sda2\", \"fstype\": \"ext4\", \"mountpoint\": \"/boot\"}":1023303680.0,
        "{\"device\": \"lxcfs\", \"fstype\": \"fuse.lxcfs\", \"mountpoint\": \"/var/lib/lxcfs\"}":0.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run\"}":413630464.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run/lock\"}":5242880.0
    },
    'node_memory_MemTotal_bytes' : 4.136280064e+09,
    'node_memory_MemAvailable_bytes' : 1.18239232e+08
}

PROMETHEUS_RETURN_MISSING = {
    'go_memstats_alloc_bytes' : 2.223928e+06,
    'go_memstats_alloc_bytes_total': 1.14706855112e+11,
    'process_virtual_memory_bytes': 1.18775808e+08,
    'process_max_fds':1024,
    'process_open_fds': 8,
    'node_cpu_seconds_total':{
        "{\"cpu\": \"0\", \"mode\": \"idle\"}":752737.96,
        "{\"cpu\": \"0\", \"mode\": \"iowait\"}":27543.33,
        "{\"cpu\": \"0\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"0\", \"mode\": \"nice\"}":28.83,
        "{\"cpu\": \"0\", \"mode\": \"softirq\"}":4295.32,
        "{\"cpu\": \"0\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"0\", \"mode\": \"system\"}":19363.9,
        "{\"cpu\": \"0\", \"mode\": \"user\"}":61338.69,
        "{\"cpu\": \"1\", \"mode\": \"idle\"}":752765.99,
        "{\"cpu\": \"1\", \"mode\": \"iowait\"}":26523.94,
        "{\"cpu\": \"1\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"1\", \"mode\": \"nice\"}":26.01,
        "{\"cpu\": \"1\", \"mode\": \"softirq\"}":3393.48,
        "{\"cpu\": \"1\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"1\", \"mode\": \"system\"}":20271.08,
        "{\"cpu\": \"1\", \"mode\": \"user\"}":61747.17,
        "{\"cpu\": \"2\", \"mode\": \"idle\"}":752386.53,
        "{\"cpu\": \"2\", \"mode\": \"iowait\"}":26560.33,
        "{\"cpu\": \"2\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"2\", \"mode\": \"nice\"}":29.57,
        "{\"cpu\": \"2\", \"mode\": \"softirq\"}":3264.85,
        "{\"cpu\": \"2\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"2\", \"mode\": \"system\"}":20337.47,
        "{\"cpu\": \"2\", \"mode\": \"user\"}":61632.38,
        "{\"cpu\": \"3\", \"mode\": \"idle\"}":750801.25,
        "{\"cpu\": \"3\", \"mode\": \"iowait\"}":28653.92,
        "{\"cpu\": \"3\", \"mode\": \"irq\"}":0.0,
        "{\"cpu\": \"3\", \"mode\": \"nice\"}":23.78,
        "{\"cpu\": \"3\", \"mode\": \"softirq\"}":3085.45,
        "{\"cpu\": \"3\", \"mode\": \"steal\"}":0.0,
        "{\"cpu\": \"3\", \"mode\": \"system\"}":19650.69,
        "{\"cpu\": \"3\", \"mode\": \"user\"}":61513.88
    },
    'node_filesystem_avail_bytes':{
        "{\"device\": \"/dev/mapper/ubuntu--vg-ubuntu--lv\", \"fstype\": \"ext4\", \"mountpoint\": \"/\"}":40624627712.0,
        "{\"device\": \"/dev/sda2\", \"fstype\": \"ext4\", \"mountpoint\": \"/boot\"}":872026112.0,
        "{\"device\": \"lxcfs\", \"fstype\": \"fuse.lxcfs\", \"mountpoint\": \"/var/lib/lxcfs\"}":0.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run\"}":412160000.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run/lock\"}":5242880.0
    },
    'node_filesystem_size_bytes' : {
        "{\"device\": \"/dev/mapper/ubuntu--vg-ubuntu--lv\", \"fstype\": \"ext4\", \"mountpoint\": \"/\"}":104560844800.0,
        "{\"device\": \"/dev/sda2\", \"fstype\": \"ext4\", \"mountpoint\": \"/boot\"}":1023303680.0,
        "{\"device\": \"lxcfs\", \"fstype\": \"fuse.lxcfs\", \"mountpoint\": \"/var/lib/lxcfs\"}":0.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run\"}":413630464.0,
        "{\"device\": \"tmpfs\", \"fstype\": \"tmpfs\", \"mountpoint\": \"/run/lock\"}":5242880.0
    },
    'node_memory_MemTotal_bytes' : 4.136280064e+09,
    'node_memory_MemAvailable_bytes' : 1.18239232e+08
}

class TestSystemMonitorWithoutRedis(unittest.TestCase):

    def setUp(self) -> None:
        self.logger = logging.getLogger('dummy')
        self.monitor_name = 'testblockchainmonitor'
        self.counter_channel = CounterChannel(self.logger)
        self.channel_set = ChannelSet([self.counter_channel], TestInternalConf)
        self.redis = None

        self.prometheus_endpoint = 'prometheus_endpoint'

        self.dummy_chain_name = 'testchain'
        self.full_node_name = 'testfullnode'
        self.full_node_api_url = '123.123.123.11:9944'
        self.full_node_consensus_key = "ANDSAdisadjasdaANDAsa"
        self.full_node_tendermint_key = "ASFLNAFIISDANNSDAKKS2313AA"
        self.full_node_entity_public_key="a98dabsfkjabfkjabsf9j",

        self.full_node = Node(self.full_node_name, self.full_node_api_url, None,
                            NodeType.NON_VALIDATOR_FULL_NODE, '', 
                            self.dummy_chain_name,
                            None, True, self.full_node_consensus_key,
                            self.full_node_tendermint_key, 
                            self.full_node_entity_public_key,
                            TestInternalConf)

        self.validator = Node(self.full_node_name, self.full_node_api_url, None,
                        NodeType.VALIDATOR_FULL_NODE, '', 
                        self.dummy_chain_name,
                        None, True, self.full_node_consensus_key,
                        self.full_node_tendermint_key, 
                        self.full_node_entity_public_key,
                        TestInternalConf)

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

        self.dummy_system_node = System(self.dummy_chain_name, None,  
            self.full_node, TestInternalConf)

        self.dummy_system_validator = System(self.dummy_chain_name, None,
            self.validator, TestInternalConf)

        self.monitor_node = SystemMonitor(self.monitor_name, 
            self.dummy_system_node,
            self.channel_set, self.logger, None,
            self.prometheus_endpoint, TestInternalConf)

        self.monitor_validator = SystemMonitor(self.monitor_name, 
            self.dummy_system_validator,
            self.channel_set, self.logger, None,
            self.prometheus_endpoint, TestInternalConf)

        self.safe_node_process_cpu_seconds_total = 20
        self.safe_node_process_memory_usage = 20
        self.safe_node_virtual_memory_usage = 20
        self.safe_node_open_file_descriptors = 20
        self.safe_node_system_cpu_usage = 20
        self.safe_node_system_ram_usage = 20
        self.safe_node_system_storage_usage = 20

    def test_status_returns_as_expected(self) -> None:
        self.dummy_system_node._process_cpu_seconds_total = \
            self.safe_node_process_cpu_seconds_total
        self.dummy_system_node._process_memory_usage = \
            self.safe_node_process_memory_usage
        self.dummy_system_node._virtual_memory_usage = \
            self.safe_node_virtual_memory_usage
        self.dummy_system_node._open_file_descriptors = \
            self.safe_node_open_file_descriptors
        self.dummy_system_node._system_cpu_usage = \
            self.safe_node_system_cpu_usage
        self.dummy_system_node._system_ram_usage = \
            self.safe_node_system_ram_usage
        self.dummy_system_node._system_storage_usage = \
            self.safe_node_system_storage_usage
        
        self.assertEqual(self.monitor_node.status(), \
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

    @patch(GET_OASIS_PROMETHEUS, return_value=PROMETHEUS_RETURN)
    def test_return_and_save_prometheus_metrics(self, mock_prometheus) -> None:
        with mock.patch(SYSTEM_PATH, new_callable=PropertyMock) \
                as mock_data_source:
            mock_data_source.return_value = self.dummy_system_node
            mock_prometheus.return_value = PROMETHEUS_RETURN

            self.monitor_node.monitor()
            self.assertEqual(self.dummy_system_node.process_cpu_seconds_total,
                8599.65)
            self.assertEqual(self.dummy_system_node.process_memory_usage,
                0.0)
            self.assertEqual(self.dummy_system_node.virtual_memory_usage,
                1.18775808e+08)
            self.assertEqual(self.dummy_system_node.open_file_descriptors,
                0.78)
            self.assertEqual(self.dummy_system_node.system_cpu_usage,
                12.99)
            self.assertEqual(self.dummy_system_node.system_ram_usage,
                97.14)
            self.assertEqual(self.dummy_system_node.system_storage_usage,
                60.46)

    @patch(GET_OASIS_PROMETHEUS, return_value=PROMETHEUS_RETURN_MISSING)
    def test_return_prometheus_with_missing_values(self, mock_prometheus) \
        -> None:
        with mock.patch(SYSTEM_PATH, new_callable=PropertyMock) \
                as mock_data_source:
            mock_data_source.return_value = self.dummy_system_node
            mock_prometheus.return_value = PROMETHEUS_RETURN_MISSING

            self.monitor_node.monitor()
            self.assertEqual(self.dummy_system_node.process_cpu_seconds_total,
                None)
            self.assertEqual(self.dummy_system_node.process_memory_usage,
                0.0)
            self.assertEqual(self.dummy_system_node.virtual_memory_usage,
                1.18775808e+08)
            self.assertEqual(self.dummy_system_node.open_file_descriptors,
                0.78)
            self.assertEqual(self.dummy_system_node.system_cpu_usage,
                12.99)
            self.assertEqual(self.dummy_system_node.system_ram_usage,
                97.14)
            self.assertEqual(self.dummy_system_node.system_storage_usage,
                60.46)

    @patch(GET_OASIS_PROMETHEUS, return_value=PROMETHEUS_RETURN_MISSING)
    def test_return_prometheus_process_cpu_seconds_do_not_change(self, mock_prometheus) \
        -> None:
        with mock.patch(SYSTEM_PATH, new_callable=PropertyMock) \
                as mock_data_source:
            mock_data_source.return_value = self.dummy_system_node
            mock_prometheus.return_value = PROMETHEUS_RETURN_MISSING
            
            self.dummy_system_node.set_process_cpu_seconds_total(80,  
                self.counter_channel, self.logger)
            self.monitor_node.monitor()
            self.assertEqual(self.dummy_system_node.process_cpu_seconds_total,
                80)
            self.assertEqual(self.dummy_system_node.process_memory_usage,
                0.0)
            self.assertEqual(self.dummy_system_node.virtual_memory_usage,
                1.18775808e+08)
            self.assertEqual(self.dummy_system_node.open_file_descriptors,
                0.78)
            self.assertEqual(self.dummy_system_node.system_cpu_usage,
                12.99)
            self.assertEqual(self.dummy_system_node.system_ram_usage,
                97.14)
            self.assertEqual(self.dummy_system_node.system_storage_usage,
                60.46)

