import logging
from datetime import timedelta
from typing import Optional

from src.alerts.alerts import ApiIsDownAlert, ApiIsUpAgainAlert
from src.channels.channel import ChannelSet
from src.utils.get_json import get_oasis_json
from src.utils.timing import TimedTaskLimiter
from src.utils.types import OasisWrapperType


class OasisApiWrapper:

    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._api_down = False

        # If after 15 seconds connection between a validator monitor and API
        # server is not re-established, user is informed via a critical alert
        self._api_down_limiter = TimedTaskLimiter(timedelta(seconds=int(15)))
        self._critical_alert_sent = False

    @property
    def is_api_down(self) -> bool:
        return self._api_down

    def set_api_as_down(self, monitor: str, is_validator_monitor,
                        channels: ChannelSet) -> None:

        self._logger.debug('%s set_api_as_down: api_down(currently)=%s, '
                           'channels=%s', self, self._api_down, channels)

        # If API is suddenly down, inform via a warning alert
        if not self._api_down:
            channels.alert_warning(ApiIsDownAlert(monitor))
            self._api_down_limiter.did_task()

        # If 15 seconds pass since a validator monitor lost connection with the
        # API server, the user is informed via critical alert once
        if is_validator_monitor and self._api_down_limiter.can_do_task() \
                and not self._critical_alert_sent:
            channels.alert_critical(ApiIsDownAlert(monitor))
            self._critical_alert_sent = True

        self._api_down = True

    def set_api_as_up(self, monitor: str, channels: ChannelSet) -> None:

        self._logger.debug('%s set_api_as_down: api_down(currently)=%s, '
                           'channels=%s', self, self._api_down, channels)

        if self._api_down:
            channels.alert_info(ApiIsUpAgainAlert(monitor))
        
        self._critical_alert_sent = False
        self._api_down = False

    def get_web_sockets_connected_to_an_api(self, api_url: str) \
            -> OasisWrapperType:

        endpoint = api_url + '/api/getconnectionslist'
        params = {}
        return get_oasis_json(endpoint, params, self._logger)

    def ping_api(self, api_url: str) -> OasisWrapperType:

        endpoint = api_url + '/api/ping'
        params = {}
        return get_oasis_json(endpoint, params, self._logger)

    def ping_node(self, api_url: str, node_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/pingnode'
        params = {'name': node_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_node(self, api_url: str, node_name: str,
                 node_id: str) -> OasisWrapperType:

        endpoint = api_url + '/api/registry/node'
        params = {'name': node_name, 'nodeID': node_id}
        return get_oasis_json(endpoint, params, self._logger)

    def get_consensus_genesis(self, api_url: str,
                              node_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/consensus/genesis'
        params = {'name': node_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_is_syncing(self, api_url: str,
                       node_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/nodecontroller/synced'
        params = {'name': node_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_prometheus_gauge(self, api_url: str, node_name: str,
                             gauge_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/prometheus/gauge'
        params = {'name': node_name, 'gauge': gauge_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_prometheus_counter(self, api_url: str, node_name: str,
                               counter_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/prometheus/counter'
        params = {'name': node_name, 'counter': counter_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_node_exporter_gauge(self, api_url: str, node_name: str,
                                gauge_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/exporter/gauge'
        params = {'name': node_name, 'gauge': gauge_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_node_export_counter(self, api_url: str, node_name: str,
                                counter_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/exporter/counter'
        params = {'name': node_name, 'counter': counter_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_block_header(self, api_url: str,
                         node_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/consensus/blockheader'
        params = {'name': node_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_session_validators(self, api_url: str,
                               node_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/scheduler/validators'
        params = {'name': node_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_consensus_block(self, api_url: str,
                            node_name: str) -> OasisWrapperType:

        endpoint = api_url + '/api/consensus/block'
        params = {'name': node_name}
        return get_oasis_json(endpoint, params, self._logger)

    def get_block_header_height(self, api_url: str,
                            node_name: str, height: str) -> OasisWrapperType:

        endpoint = api_url + '/api/consensus/blockheader'
        params = {'name': node_name, 'height': height}
        return get_oasis_json(endpoint, params, self._logger)

    def get_signed_blocks(self, api_url: str,
                          node_name: str, height: str) -> OasisWrapperType:

        endpoint = api_url + '/api/consensus/blocklastcommit'
        params = {'name': node_name, 'height': height}
        return get_oasis_json(endpoint, params, self._logger)

    def get_tendermint_address(self, api_url: str,
                               consensus_public_key: str) -> OasisWrapperType:

        endpoint = api_url + '/api/consensus/pubkeyaddress'
        params = {'consensus_public_key': consensus_public_key}
        return get_oasis_json(endpoint, params, self._logger)

    def get_registry_node(self, api_url: str, node_name: str,
                          node_id: str) -> OasisWrapperType:

        endpoint = api_url + '/api/registry/node'
        params = {'name': node_name, 'nodeID': node_id}
        return get_oasis_json(endpoint, params, self._logger)

    def get_staking_account(self, api_url: str, node_name: str,
                                address: str) -> OasisWrapperType:

        endpoint = api_url + '/api/staking/account'
        params = {'name': node_name, 'address': address}
        return get_oasis_json(endpoint, params, self._logger)

    def get_staking_address(self, api_url: str, public_key: \
        str) -> OasisWrapperType:

        endpoint = api_url + '/api/staking/publickeytoaddress'
        params = {'pubKey': public_key}
        return get_oasis_json(endpoint, params, self._logger)

    def get_staking_delegations(self, api_url: str, node_name: str,
                                address: str) -> OasisWrapperType:

        endpoint = api_url + '/api/staking/delegations'
        params = {'name': node_name, 'address': address}
        return get_oasis_json(endpoint, params, self._logger)

    def get_events_by_height(self, api_url: str, node_name: str,
                             height: str) -> OasisWrapperType:

        endpoint = api_url + '/api/staking/events'
        params = {'name': node_name, 'height': height}
        return get_oasis_json(endpoint, params, self._logger)
