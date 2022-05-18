import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from src.alerters.reactive.system import System
from src.channels.channel import ChannelSet
from src.monitors.monitor import Monitor
from src.store.redis.redis_api import RedisApi
from src.store.store_keys import Keys
from src.utils.config_parsers.internal import InternalConfig
from src.utils.config_parsers.internal_parsed import InternalConf
from src.utils.get_prometheus import get_oasis_prometheus


class SystemMonitor(Monitor):

    def __init__(self, monitor_name: str, system: System,
                 channels: ChannelSet, logger: logging.Logger,
                 redis: Optional[RedisApi], prometheus_endpoint: str,
                 internal_conf: InternalConfig = InternalConf):
        super().__init__(monitor_name, channels, logger, redis, internal_conf)

        self._system = system
        self._prometheus_endpoint = prometheus_endpoint
        self._redis_alive_key_timeout = \
            self._internal_conf.redis_system_monitor_alive_key_timeout

    @property
    def system(self) -> System:
        return self._system

    @property
    def prometheus_endpoint(self) -> str:
        return self._prometheus_endpoint

    def save_state(self) -> None:
        # If Redis is enabled save the current time, indicating that the monitor
        # was alive at this time.
        if self.redis_enabled:
            self.logger.debug('Saving %s state', self._monitor_name)

            # Set alive key (to be able to query latest update from Telegram)
            key = Keys.get_system_monitor_alive(self.monitor_name)
            until = timedelta(seconds=self._redis_alive_key_timeout)
            self.redis.set_for(key, str(datetime.now().timestamp()), until)

    def status(self) -> str:
        return self.system.status()

    def monitor(self) -> None:
        metrics_to_monitor = ['process_cpu_seconds_total',
                              'go_memstats_alloc_bytes',
                              'go_memstats_alloc_bytes_total',
                              'process_virtual_memory_bytes',
                              'process_max_fds',
                              'process_open_fds',
                              'node_cpu_seconds_total',
                              'node_filesystem_avail_bytes',
                              'node_filesystem_size_bytes',
                              'node_memory_MemTotal_bytes',
                              'node_memory_MemAvailable_bytes']

        prometheus_data = get_oasis_prometheus(self.prometheus_endpoint,
                                               metrics_to_monitor, self.logger)

        try:
            process_cpu_seconds_total = ( \
                prometheus_data['process_cpu_seconds_total'])

            self._logger.debug('%s process_cpu_seconds_total: %s', self.system,
                               process_cpu_seconds_total)

            self.system.set_process_cpu_seconds_total(process_cpu_seconds_total,
                                                      self.channels,
                                                      self.logger)
        except:
            pass

        try:
            process_memory_usage = (prometheus_data['go_memstats_alloc_bytes'] \
                                    / prometheus_data[
                                        'go_memstats_alloc_bytes_total']) * 100

            process_memory_usage = float("{:.2f}".format(process_memory_usage))

            self._logger.debug('%s process_memory_usage: %s', self.system,
                               process_memory_usage)

            self.system.set_process_memory_usage(process_memory_usage, \
                                                 self.channels, self.logger)
        except:
            pass

        try:
            virtual_memory_usage = \
                prometheus_data['process_virtual_memory_bytes']

            self._logger.debug('%s virtual_memory_usage: %s', self.system,
                               virtual_memory_usage)

            self.system.set_virtual_memory_usage(virtual_memory_usage, \
                                                 self.channels, self.logger)
        except:
            pass

        try:
            open_file_descriptors = (prometheus_data['process_open_fds'] /
                                     prometheus_data['process_max_fds']) * 100

            open_file_descriptors = float("{:.2f}".format( \
                open_file_descriptors))

            self._logger.debug('%s open_file_descriptors: %s', self.system,
                               open_file_descriptors)

            self.system.set_open_file_descriptors(open_file_descriptors, \
                                                  self.channels, self.logger)
        except:
            pass

        try:
            node_cpu_seconds_idle = 0
            node_cpu_seconds_total = 0
            for i, j in enumerate(prometheus_data['node_cpu_seconds_total']):
                if json.loads(j)['mode'] == 'idle':
                    node_cpu_seconds_idle += \
                        prometheus_data['node_cpu_seconds_total'][j]
                node_cpu_seconds_total += \
                    prometheus_data['node_cpu_seconds_total'][j]

            system_cpu_usage = (100 - ((node_cpu_seconds_idle \
                                        / node_cpu_seconds_total) * 100))

            system_cpu_usage = float("{:.2f}".format(system_cpu_usage))

            self._logger.debug('%s system_cpu_usage: %s', self.system,
                               system_cpu_usage)

            self.system.set_system_cpu_usage(system_cpu_usage, \
                                             self.channels, self.logger)
        except:
            pass

        try:
            system_ram_usage = ((prometheus_data['node_memory_MemTotal_bytes'] \
                                 - prometheus_data[
                                     'node_memory_MemAvailable_bytes']) /
                                prometheus_data[
                                    'node_memory_MemTotal_bytes']) * 100

            system_ram_usage = float("{:.2f}".format(system_ram_usage))

            self._logger.debug('%s system_ram_usage: %s', self.system,
                               system_ram_usage)

            self.system.set_system_ram_usage(system_ram_usage, \
                                             self.channels, self.logger)
        except:
            pass

        node_filesystem_avail_bytes = 0
        node_filesystem_size_bytes = 0
        try:
            for i, j in enumerate( \
                    prometheus_data['node_filesystem_avail_bytes']):
                node_filesystem_avail_bytes += \
                    prometheus_data['node_filesystem_avail_bytes'][j]

            for i, j in enumerate( \
                    prometheus_data['node_filesystem_size_bytes']):
                node_filesystem_size_bytes += \
                    prometheus_data['node_filesystem_size_bytes'][j]

            system_storage_usage = 100 - \
                                   ((
                                                node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100)

            system_storage_usage = float("{:.2f}".format(system_storage_usage))

            self._logger.debug('%s system_storage_usage: %s', self.system,
                               system_storage_usage)

            self.system.set_system_storage_usage(system_storage_usage, \
                                                 self.channels, self.logger)

            # Output status
            self._logger.info('%s status: %s', self._monitor_name, \
                self.status())
        except:
            pass
