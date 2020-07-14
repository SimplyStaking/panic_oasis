import sys
from datetime import timedelta

import configparser

from src.alerts.alerts import AlertCode, SeverityCode
from src.utils.config_parsers.config_parser import ConfigParser
from src.utils.config_parsers.user import to_bool


def to_bool(bool_str: str) -> bool:
    return bool_str.lower() in ['true', 'yes', 'y']


class InternalConfig(ConfigParser):

    # Use internal_parsed.py rather than creating a new instance of this class
    def __init__(self, main_config_file_path: str,
                 alerts_config_file_path: str) -> None:
        super().__init__([main_config_file_path,
                          alerts_config_file_path])

        cp = configparser.ConfigParser()
        cp.optionxform = str  # to preserve case of keys
        cp.read(main_config_file_path)
        cp.read(alerts_config_file_path)

        # ------------------------ Main Config

        # [logging]
        section = cp['logging']
        self.logging_level = section['logging_level']

        self.telegram_commands_general_log_file = section[
            'telegram_commands_general_log_file']
        self.github_monitor_general_log_file_template = section[
            'github_monitor_general_log_file_template']
        self.node_monitor_general_log_file_template = section[
            'node_monitor_general_log_file_template']
        self.system_monitor_general_log_file_template = section[
            'system_monitor_general_log_file_template']

        self.alerts_log_file = section['alerts_log_file']
        self.redis_log_file = section['redis_log_file']
        self.mongo_log_file = section['mongo_log_file']
        self.general_log_file = section['general_log_file']

        # [twilio]
        section = cp['twilio']
        self.twiml = section['twiml']
        self.twiml_is_url = to_bool(section['twiml_is_url'])

        # [mongo]
        section = cp['mongo']
        self.mongo_coll_alerts_prefix = section['coll_alerts_prefix']

        # [redis]
        section = cp['redis']
        self.redis_database = int(section['redis_database'])
        self.redis_test_database = int(section['redis_test_database'])

        self.redis_twilio_snooze_key_default_hours = timedelta(hours=float(
            section['redis_twilio_snooze_key_default_hours']))
        self.redis_periodic_alive_reminder_mute_key_default_hours = timedelta(
            hours=float(section['redis_periodic_alive_reminder_mute_key_'
                                'default_hours']))

        self.redis_node_monitor_alive_key_timeout = int(
            section['redis_node_monitor_alive_key_timeout'])
        self.redis_node_monitor_last_height_key_timeout = int(
            section['redis_node_monitor_last_height_key_timeout'])
        self.redis_system_monitor_alive_key_timeout = int(
            section['redis_system_monitor_alive_key_timeout'])

        # [monitoring_periods]
        section = cp['monitoring_periods']
        self.node_monitor_period_seconds = int(
            section['node_monitor_period_seconds'])

        self.system_monitor_period_seconds = int(
            section['system_monitor_period_seconds'])

        self.node_monitor_max_catch_up_blocks = int(
            section['node_monitor_max_catch_up_blocks'])

        self.github_monitor_period_seconds = int(
            section['github_monitor_period_seconds'])

        # [alert_intervals_and_limits]
        section = cp['alert_intervals_and_limits']
        self.downtime_alert_interval_seconds = timedelta(seconds=int(
            section['downtime_alert_interval_seconds']))

        self.validator_peer_danger_boundary = int(
            section['validator_peer_danger_boundary'])

        self.validator_peer_safe_boundary = int(
            section['validator_peer_safe_boundary'])

        self._check_if_peer_safe_and_danger_boundaries_are_valid()

        self.full_node_peer_danger_boundary = int(
            section['full_node_peer_danger_boundary'])

        self.github_error_interval_seconds = timedelta(seconds=int(
            section['github_error_interval_seconds']))

        self.no_change_in_height_interval_seconds = int(
            section['no_change_in_height_interval_seconds'])

        self.no_change_in_height_first_warning_seconds = int(
            section['no_change_in_height_first_warning_seconds'])

        self.change_in_bonded_balance_threshold = int(
            section['change_in_bonded_balance_threshold'])

        self.change_in_debonding_balance_threshold = int(
            section['change_in_debonding_balance_threshold'])

        self.change_in_shares_balance_threshold = int(
            section['change_in_shares_balance_threshold'])

        self.max_missed_blocks_time_interval = timedelta(seconds=int(
            section['max_missed_blocks_interval_seconds']))

        self.max_missed_blocks_in_time_interval = int(
            section['max_missed_blocks_in_time_interval'])

        self.missed_blocks_danger_boundary = int(
            section['missed_blocks_danger_boundary'])

        self._check_if_block_height_warning_and_interval_are_valid()

        section = cp['system_intervals_and_limits']
        self.validator_process_memory_usage_danger_boundary = int(
            section['validator_process_memory_usage_danger_boundary'])
        self.validator_process_memory_usage_safe_boundary = int(
            section['validator_process_memory_usage_safe_boundary'])
        self.validator_open_file_descriptors_danger_boundary = int(
            section['validator_open_file_descriptors_danger_boundary'])
        self.validator_open_file_descriptors_safe_boundary = int(
            section['validator_open_file_descriptors_safe_boundary'])
        self.validator_system_cpu_usage_danger_boundary = int(
            section['validator_system_cpu_usage_danger_boundary'])
        self.validator_system_cpu_usage_safe_boundary = int(
            section['validator_system_cpu_usage_safe_boundary'])
        self.validator_system_ram_usage_danger_boundary = int(
            section['validator_system_ram_usage_danger_boundary'])
        self.validator_system_ram_usage_safe_boundary = int(
            section['validator_system_ram_usage_safe_boundary'])
        self.validator_system_storage_usage_danger_boundary = int(
            section['validator_system_storage_usage_danger_boundary'])
        self.validator_system_storage_usage_safe_boundary = int(
            section['validator_system_storage_usage_safe_boundary'])

        self.node_process_memory_usage_danger_boundary = int(
            section['node_process_memory_usage_danger_boundary'])
        self.node_process_memory_usage_safe_boundary = int(
            section['node_process_memory_usage_safe_boundary'])
        self.node_open_file_descriptors_danger_boundary = int(
            section['node_open_file_descriptors_danger_boundary'])
        self.node_open_file_descriptors_safe_boundary = int(
            section['node_open_file_descriptors_safe_boundary'])
        self.node_system_cpu_usage_danger_boundary = int(
            section['node_system_cpu_usage_danger_boundary'])
        self.node_system_cpu_usage_safe_boundary = int(
            section['node_system_cpu_usage_safe_boundary'])
        self.node_system_ram_usage_danger_boundary = int(
            section['node_system_ram_usage_danger_boundary'])
        self.node_system_ram_usage_safe_boundary = int(
            section['node_system_ram_usage_safe_boundary'])
        self.node_system_storage_usage_danger_boundary = int(
            section['node_system_storage_usage_danger_boundary'])
        self.node_system_storage_usage_safe_boundary = int(
            section['node_system_storage_usage_safe_boundary'])

        # [links]
        section = cp['links']
        self.validators_oasis_link = section['validators_oasis_link']
        self.validators_oasisstake_link = section['validators_oasisstake_link']

        self.github_releases_template = section['github_releases_template']

        # ------------------------ Alerts Config

        # [severities_enabled_disabled]
        self.severities_enabled_map = {
            SeverityCode.INFO.name:
                to_bool(cp['severities_enabled_disabled']["Info"]),
            SeverityCode.WARNING.name:
                to_bool(cp['severities_enabled_disabled']["Warning"]),
            SeverityCode.CRITICAL.name:
                to_bool(cp['severities_enabled_disabled']["Critical"]),
            SeverityCode.ERROR.name:
                to_bool(cp['severities_enabled_disabled']["Error"]),
        }

        # Remaining sections (ending with _alerts_enabled_disabled)
        self.alerts_enabled_map = {}
        self.alerts_enabled_disabled_sections = \
            [s for s in cp.sections() if s.endswith("_alerts_enabled_disabled")]

        for s in self.alerts_enabled_disabled_sections:
            for alert in cp[s]:
                self.alerts_enabled_map[alert] = \
                    to_bool(cp[s][alert])

        # Check that map has all possible alerts
        for ac in AlertCode:
            if ac.name not in self.alerts_enabled_map:
                print('Missing alert {} from alerts config.'.format(ac.name))
                sys.exit(-1)

        # Check that map has no extra alerts
        all_alert_codes = [ac.name for ac in AlertCode]
        try:
            extra_alert = next(a for a in self.alerts_enabled_map.keys()
                               if a not in all_alert_codes)
            print('WARNING: Extra alert {} in alerts config. PANIC will '
                  'ignore this and continue normally.'.format(extra_alert))
        except StopIteration:
            pass  # If no extra alert found, this is a good thing

    # Safe boundary must be greater than danger boundary at all times for
    # correct execution
    def _peer_safe_and_danger_boundaries_are_valid(self) -> bool:
        return self.validator_peer_safe_boundary > \
               self.validator_peer_danger_boundary > 0

    def _check_if_peer_safe_and_danger_boundaries_are_valid(self):
        if not self._peer_safe_and_danger_boundaries_are_valid():
            print("validator_peer_safe_boundary must be STRICTLY GREATER than "
                  "validator_peer_danger_boundary for correct execution."
                  "\nPlease do the necessary modifications in the "
                  "config/internal_config_main.ini file and restart the "
                  "alerter.")
            sys.exit(-1)

    # The warning value must be less than the interval value at all times for
    # correct execution
    def _block_height_warning_and_interval_values_valid(self) -> bool:
        return self.no_change_in_height_interval_seconds > \
               self.no_change_in_height_first_warning_seconds > 0

    def _check_if_block_height_warning_and_interval_are_valid(self):
        if not self._block_height_warning_and_interval_values_valid():
            print(
                "no_change_in_height_interval_seconds must be STRICTLY GREATER "
                "than no_change_in_height_first_warning_seconds for correct "
                "execution.\nPlease do the necessary modifications in the "
                "config/internal_config_main.ini file and restart the alerter.")
            sys.exit(-1)
