import logging
from typing import Optional

from src.alerts.alerts import *
from src.channels.channel import ChannelSet
from src.alerters.reactive.node import Node, NodeType
from src.utils.config_parsers.internal import InternalConfig
from src.utils.config_parsers.internal_parsed import InternalConf
from src.store.redis.redis_api import RedisApi
from src.store.store_keys import Keys
from src.utils.parsing import parse_int_from_string


class System:
    def __init__(self, name: str, redis: Optional[RedisApi],
                 node: Node,
                 internal_conf: InternalConfig = InternalConf) -> None:
        super().__init__()

        self.name = name
        self._node = node
        self._redis = redis
        self._redis_enabled = redis is not None
        self._redis_hash = Keys.get_hash_blockchain(node.chain)

        self._process_cpu_seconds_total = None

        # Process memory usage
        self._process_memory_usage = None

        # Virtual memory usage
        self._virtual_memory_usage = None

        # Open file descriptors
        self._open_file_descriptors = None

        # System CPU usage
        self._system_cpu_usage = None

        # System RAM usage
        self._system_ram_usage = None

        # System storage used
        self._system_storage_usage = None

        self._validator_process_memory_usage_danger_boundary = \
            internal_conf.validator_process_memory_usage_danger_boundary
        self._validator_process_memory_usage_safe_boundary = \
            internal_conf.validator_process_memory_usage_safe_boundary
        self._validator_open_file_descriptors_danger_boundary = \
            internal_conf.validator_open_file_descriptors_danger_boundary
        self._validator_open_file_descriptors_safe_boundary = \
            internal_conf.validator_open_file_descriptors_safe_boundary
        self._validator_system_cpu_usage_danger_boundary = \
            internal_conf.validator_system_cpu_usage_danger_boundary
        self._validator_system_cpu_usage_safe_boundary = \
            internal_conf.validator_system_cpu_usage_safe_boundary
        self._validator_system_ram_usage_danger_boundary = \
            internal_conf.validator_system_ram_usage_danger_boundary
        self._validator_system_ram_usage_safe_boundary = \
            internal_conf.validator_system_ram_usage_safe_boundary
        self._validator_system_storage_usage_danger_boundary = \
            internal_conf.validator_system_storage_usage_danger_boundary
        self._validator_system_storage_usage_safe_boundary = \
            internal_conf.validator_system_storage_usage_safe_boundary

        self._node_process_memory_usage_danger_boundary = \
            internal_conf.node_process_memory_usage_danger_boundary
        self._node_process_memory_usage_safe_boundary = \
            internal_conf.node_process_memory_usage_safe_boundary
        self._node_open_file_descriptors_danger_boundary = \
            internal_conf.node_open_file_descriptors_danger_boundary
        self._node_open_file_descriptors_safe_boundary = \
            internal_conf.node_open_file_descriptors_safe_boundary
        self._node_system_cpu_usage_danger_boundary = \
            internal_conf.node_system_cpu_usage_danger_boundary
        self._node_system_cpu_usage_safe_boundary = \
            internal_conf.node_system_cpu_usage_safe_boundary
        self._node_system_ram_usage_danger_boundary = \
            internal_conf.node_system_ram_usage_danger_boundary
        self._node_system_ram_usage_safe_boundary = \
            internal_conf.node_system_ram_usage_safe_boundary
        self._node_system_storage_usage_danger_boundary = \
            internal_conf.node_system_storage_usage_danger_boundary
        self._node_system_storage_usage_safe_boundary = \
            internal_conf.node_system_storage_usage_safe_boundary

    def __str__(self) -> str:
        return self.name

    @property
    def node(self) -> Node:
        return self._node

    @property
    def process_cpu_seconds_total(self) -> int:
        return self._process_cpu_seconds_total

    @property
    def process_memory_usage(self) -> int:
        return self._process_memory_usage

    @property
    def virtual_memory_usage(self) -> int:
        return self._virtual_memory_usage

    @property
    def open_file_descriptors(self) -> int:
        return self._open_file_descriptors

    @property
    def system_cpu_usage(self) -> int:
        return self._system_cpu_usage

    @property
    def system_ram_usage(self) -> int:
        return self._system_ram_usage

    @property
    def system_storage_usage(self) -> int:
        return self._system_storage_usage

    def status(self) -> str:
        return "process_cpu_seconds_total={}, " \
               "process_memory_usage={}, virtual_memory_usage={}, " \
               "open_file_descriptors={}, system_cpu_usage={}, " \
               "system_ram_usage={}, system_storage_usage={}, " \
               "".format(self._process_cpu_seconds_total,
                         self._process_memory_usage, self._virtual_memory_usage,
                         self._open_file_descriptors, self._system_cpu_usage,
                         self._system_ram_usage, self._system_storage_usage)

    def load_state(self, logger: logging.Logger) -> None:
        # If Redis is enabled, load any previously stored state
        if self._redis_enabled:
            self._process_cpu_seconds_total = self._redis.hget_int(
                self._redis_hash,
                Keys.get_system_get_process_cpu_seconds_total(self.name), None)
            self._process_memory_usage = self._redis.hget_int(
                self._redis_hash,
                Keys.get_system_get_process_memory_usage(self.name), None)
            self._virtual_memory_usage = self._redis.hget_int(
                self._redis_hash,
                Keys.get_system_get_virtual_memory_usage(self.name), None)
            self._open_file_descriptors = self._redis.hget_int(
                self._redis_hash,
                Keys.get_system_get_open_file_descriptors(self.name), None)
            self._system_cpu_usage = self._redis.hget_int(
                self._redis_hash,
                Keys.get_system_get_system_cpu_usage(self.name), None)
            self._system_ram_usage = self._redis.hget_int(
                self._redis_hash,
                Keys.get_system_get_system_ram_usage(self.name), None)
            self._system_storage_usage = self._redis.hget_int(
                self._redis_hash,
                Keys.get_system_get_system_storage_usage(self.name), None)

            logger.debug(
                'Restored %s state: _process_cpu_seconds_total=%s, '
                '_process_memory_usage=%s, _virtual_memory_usage=%s, '
                '_open_file_descriptors=%s, _system_cpu_usage=%s, '
                '_system_ram_usage=%s, _system_storage_usage=%s',
                self.name, self._process_cpu_seconds_total,
                self._process_memory_usage, self._virtual_memory_usage,
                self._open_file_descriptors, self._system_cpu_usage,
                self._system_ram_usage, self._system_storage_usage)

    def save_state(self, logger: logging.Logger) -> None:
        # If Redis is enabled, store the current state
        if self._redis_enabled:
            logger.debug(
                'Saving %s state: _process_cpu_seconds_total=%s, '
                '_process_memory_usage=%s, _virtual_memory_usage=%s, '
                '_open_file_descriptors=%s, _system_cpu_usage=%s, '
                '_system_ram_usage=%s, _system_storage_usage=%s',
                self.name, self._process_cpu_seconds_total,
                self._process_memory_usage, self._virtual_memory_usage,
                self._open_file_descriptors, self._system_cpu_usage,
                self._system_ram_usage, self._system_storage_usage)

            # Set values
            self._redis.hset_multiple(self._redis_hash, {
                Keys.get_system_get_process_cpu_seconds_total(self.name):
                    self._process_cpu_seconds_total,
                Keys.get_system_get_process_memory_usage(self.name):
                    self._process_memory_usage,
                Keys.get_system_get_virtual_memory_usage(self.name):
                    self._virtual_memory_usage,
                Keys.get_system_get_open_file_descriptors(self.name):
                    self._open_file_descriptors,
                Keys.get_system_get_system_cpu_usage(self.name):
                    self._system_cpu_usage,
                Keys.get_system_get_system_ram_usage(self.name):
                    self._system_ram_usage,
                Keys.get_system_get_system_storage_usage(self.name):
                    self._system_storage_usage
            })

    def set_process_cpu_seconds_total(self, new_process_cpu_seconds: int,
                                      channels: ChannelSet,
                                      logger: logging.Logger) \
            -> None:
        logger.debug('%s set_process_cpu_seconds: '
                     'set_process_cpu_seconds(currently)=%s, channels=%s', self,
                     self._process_cpu_seconds_total, channels)

        if self._process_cpu_seconds_total is None:
            self._process_cpu_seconds_total = new_process_cpu_seconds
            return

        if self._process_cpu_seconds_total != new_process_cpu_seconds:
            channels.alert_info(NewProcessCPUSecondsTotalAlert(self.name, \
                                                               new_process_cpu_seconds))

        self._process_cpu_seconds_total = new_process_cpu_seconds

    def set_process_memory_usage(self, new_process_memory_usage: int,
                                 channels: ChannelSet, logger: logging.Logger) \
            -> None:
        logger.debug('%s set_process_memory_usage: '
                     'set_process_memory_usage(currently)=%s, channels=%s',
                     self,
                     self._process_memory_usage, channels)

        if self._process_memory_usage is None:
            self._process_memory_usage = new_process_memory_usage
            return

        if self.node.is_validator:
            danger = self._validator_process_memory_usage_danger_boundary
            safe = self._validator_process_memory_usage_safe_boundary
        else:
            danger = self._node_process_memory_usage_danger_boundary
            safe = self._node_process_memory_usage_safe_boundary

        if self._process_memory_usage not in [None, new_process_memory_usage]:
            if safe <= new_process_memory_usage < danger:
                if new_process_memory_usage > self._process_memory_usage:
                    channels.alert_warning(
                        MemoryUsageIncreasedInsideWarningRangeAlert(
                            self.name, new_process_memory_usage, safe))
                elif new_process_memory_usage < self._process_memory_usage:
                    channels.alert_info(
                        MemoryUsageDecreasedAlert(
                            self.name, self._process_memory_usage,
                            new_process_memory_usage
                        ))
            elif new_process_memory_usage >= danger:
                if new_process_memory_usage > self._process_memory_usage:
                    channels.alert_critical(
                        MemoryUsageIncreasedInsideDangerRangeAlert(
                            self.name, new_process_memory_usage, danger))
                elif new_process_memory_usage < self._process_memory_usage:
                    channels.alert_critical(MemoryUsageDecreasedAlert(
                        self.name, self._process_memory_usage,
                        new_process_memory_usage))
            else:
                if new_process_memory_usage < self._process_memory_usage:
                    channels.alert_info(MemoryUsageDecreasedAlert(
                        self.name, self._process_memory_usage,
                        new_process_memory_usage))
                elif new_process_memory_usage > self._process_memory_usage:
                    channels.alert_info(MemoryUsageIncreasedAlert(
                        self.name, self._process_memory_usage,
                        new_process_memory_usage))

        self._process_memory_usage = new_process_memory_usage

    def set_virtual_memory_usage(self, new_virtual_memory_usage: int,
                                 channels: ChannelSet, logger: logging.Logger) \
            -> None:
        logger.debug('%s set_virtual_memory_usage: '
                     'set_virtual_memory_usage(currently)=%s, channels=%s',
                     self,
                     self._virtual_memory_usage, channels)

        if self._virtual_memory_usage is None:
            self._virtual_memory_usage = new_virtual_memory_usage
            return

        if self._virtual_memory_usage != new_virtual_memory_usage:
            channels.alert_info(NewVirtualMemoryUsageAlert(self.name, \
                                                           new_virtual_memory_usage))

        self._virtual_memory_usage = new_virtual_memory_usage

    def set_open_file_descriptors(self, new_open_file_descriptors: int,
                                  channels: ChannelSet, logger: logging.Logger) \
            -> None:
        logger.debug('%s set_open_file_descriptors: '
                     'set_open_file_descriptors(currently)=%s, channels=%s',
                     self,
                     self._open_file_descriptors, channels)

        if self._open_file_descriptors is None:
            self._open_file_descriptors = new_open_file_descriptors
            return

        if self.node.is_validator:
            danger = self._validator_open_file_descriptors_danger_boundary
            safe = self._validator_open_file_descriptors_safe_boundary
        else:
            danger = self._node_open_file_descriptors_danger_boundary
            safe = self._node_open_file_descriptors_safe_boundary

        if self._open_file_descriptors not in [None, new_open_file_descriptors]:
            if safe <= new_open_file_descriptors < danger:
                if new_open_file_descriptors > self._open_file_descriptors:
                    channels.alert_warning(
                        OpenFileDescriptorsIncreasedInsideWarningRangeAlert(
                            self.name, new_open_file_descriptors, safe))
                elif new_open_file_descriptors < self._open_file_descriptors:
                    channels.alert_info(
                        OpenFileDescriptorsDecreasedAlert(
                            self.name, self._open_file_descriptors,
                            new_open_file_descriptors
                        ))
            elif new_open_file_descriptors >= danger:
                if new_open_file_descriptors > self._open_file_descriptors:
                    channels.alert_critical(
                        OpenFileDescriptorsIncreasedInsideDangerRangeAlert(
                            self.name, new_open_file_descriptors, danger))
                elif new_open_file_descriptors < self._open_file_descriptors:
                    channels.alert_critical(OpenFileDescriptorsDecreasedAlert(
                        self.name, self._open_file_descriptors,
                        new_open_file_descriptors))
            else:
                if new_open_file_descriptors < self._open_file_descriptors:
                    channels.alert_info(OpenFileDescriptorsDecreasedAlert(
                        self.name, self._open_file_descriptors,
                        new_open_file_descriptors))
                elif new_open_file_descriptors > self._open_file_descriptors:
                    channels.alert_info(OpenFileDescriptorsIncreasedAlert(
                        self.name, self._open_file_descriptors,
                        new_open_file_descriptors))

        self._open_file_descriptors = new_open_file_descriptors

    def set_system_cpu_usage(self, new_system_cpu_usage: int,
                             channels: ChannelSet, logger: logging.Logger) \
            -> None:
        logger.debug('%s set_system_cpu_usage: '
                     'set_system_cpu_usage(currently)=%s, channels=%s', self,
                     self._system_cpu_usage, channels)

        if self._system_cpu_usage is None:
            self._system_cpu_usage = new_system_cpu_usage
            return

        if self.node.is_validator:
            danger = self._validator_system_cpu_usage_danger_boundary
            safe = self._validator_system_cpu_usage_safe_boundary
        else:
            danger = self._node_system_cpu_usage_danger_boundary
            safe = self._node_system_cpu_usage_safe_boundary

        if self._system_cpu_usage not in [None, new_system_cpu_usage]:
            if safe <= new_system_cpu_usage < danger:
                if new_system_cpu_usage > self._system_cpu_usage:
                    channels.alert_warning(
                        SystemCPUUsageIncreasedInsideWarningRangeAlert(
                            self.name, new_system_cpu_usage, safe))
                elif new_system_cpu_usage < self._system_cpu_usage:
                    channels.alert_info(
                        SystemCPUUsageDecreasedAlert(
                            self.name, self._system_cpu_usage,
                            new_system_cpu_usage
                        ))
            elif new_system_cpu_usage >= danger:
                if new_system_cpu_usage > self._system_cpu_usage:
                    channels.alert_critical(
                        SystemCPUUsageIncreasedInsideDangerRangeAlert(
                            self.name, new_system_cpu_usage, danger))
                elif new_system_cpu_usage < self._system_cpu_usage:
                    channels.alert_critical(SystemCPUUsageDecreasedAlert(
                        self.name, self._system_cpu_usage,
                        new_system_cpu_usage))
            else:
                if new_system_cpu_usage < self._system_cpu_usage:
                    channels.alert_info(SystemCPUUsageDecreasedAlert(
                        self.name, self._system_cpu_usage,
                        new_system_cpu_usage))
                elif new_system_cpu_usage > self._system_cpu_usage:
                    channels.alert_info(SystemCPUUsageIncreasedAlert(
                        self.name, self._system_cpu_usage,
                        new_system_cpu_usage))

        self._system_cpu_usage = new_system_cpu_usage

    def set_system_ram_usage(self, new_system_ram_usage: int,
                             channels: ChannelSet, logger: logging.Logger) \
            -> None:
        logger.debug('%s set_system_ram_usage: '
                     'set_system_ram_usage(currently)=%s, channels=%s', self,
                     self._system_ram_usage, channels)

        if self._system_ram_usage is None:
            self._system_ram_usage = new_system_ram_usage
            return

        if self.node.is_validator:
            danger = self._validator_system_ram_usage_danger_boundary
            safe = self._validator_system_ram_usage_safe_boundary
        else:
            danger = self._node_system_ram_usage_danger_boundary
            safe = self._node_system_ram_usage_safe_boundary

        if self._system_ram_usage not in [None, new_system_ram_usage]:
            if safe <= new_system_ram_usage < danger:
                if new_system_ram_usage > self._system_ram_usage:
                    channels.alert_warning(
                        SystemRAMUsageIncreasedInsideWarningRangeAlert(
                            self.name, new_system_ram_usage, safe))
                elif new_system_ram_usage < self._system_ram_usage:
                    channels.alert_info(
                        SystemRAMUsageDecreasedAlert(
                            self.name, self._system_ram_usage,
                            new_system_ram_usage
                        ))
            elif new_system_ram_usage >= danger:
                if new_system_ram_usage > self._system_ram_usage:
                    channels.alert_critical(
                        SystemRAMUsageIncreasedInsideDangerRangeAlert(
                            self.name, new_system_ram_usage, danger))
                elif new_system_ram_usage < self._system_ram_usage:
                    channels.alert_critical(SystemRAMUsageDecreasedAlert(
                        self.name, self._system_ram_usage,
                        new_system_ram_usage))
            else:
                if new_system_ram_usage < self._system_ram_usage:
                    channels.alert_info(SystemRAMUsageDecreasedAlert(
                        self.name, self._system_ram_usage,
                        new_system_ram_usage))
                elif new_system_ram_usage > self._system_ram_usage:
                    channels.alert_info(SystemRAMUsageIncreasedAlert(
                        self.name, self._system_ram_usage,
                        new_system_ram_usage))

        self._system_ram_usage = new_system_ram_usage

    def set_system_storage_usage(self, new_system_storage_usage: int,
                                 channels: ChannelSet, logger: logging.Logger) \
            -> None:
        logger.debug('%s set_system_storage_usage: '
                     'set_system_storage_usage(currently)=%s, channels=%s',
                     self,
                     self._system_storage_usage, channels)

        if self._system_storage_usage is None:
            self._system_storage_usage = new_system_storage_usage
            return

        if self.node.is_validator:
            danger = self._validator_system_storage_usage_danger_boundary
            safe = self._validator_system_storage_usage_safe_boundary
        else:
            danger = self._node_system_storage_usage_danger_boundary
            safe = self._node_system_storage_usage_safe_boundary

        if self._system_storage_usage not in [None, new_system_storage_usage]:
            if safe <= new_system_storage_usage < danger:
                if new_system_storage_usage > self._system_storage_usage:
                    channels.alert_warning(
                        SystemStorageUsageIncreasedInsideWarningRangeAlert(
                            self.name, new_system_storage_usage, safe))
                elif new_system_storage_usage < self._system_storage_usage:
                    channels.alert_info(
                        SystemStorageUsageDecreasedAlert(
                            self.name, self._system_storage_usage,
                            new_system_storage_usage
                        ))
            elif new_system_storage_usage >= danger:
                if new_system_storage_usage > self._system_storage_usage:
                    channels.alert_critical(
                        SystemStorageUsageIncreasedInsideDangerRangeAlert(
                            self.name, new_system_storage_usage, danger))
                elif new_system_storage_usage < self._system_storage_usage:
                    channels.alert_critical(SystemStorageUsageDecreasedAlert(
                        self.name, self._system_storage_usage,
                        new_system_storage_usage))
            else:
                if new_system_storage_usage < self._system_storage_usage:
                    channels.alert_info(SystemStorageUsageDecreasedAlert(
                        self.name, self._system_storage_usage,
                        new_system_storage_usage))
                elif new_system_storage_usage > self._system_storage_usage:
                    channels.alert_info(SystemStorageUsageIncreasedAlert(
                        self.name, self._system_storage_usage,
                        new_system_storage_usage))

        self._system_storage_usage = new_system_storage_usage
