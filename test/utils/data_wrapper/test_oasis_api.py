import logging
import unittest
from typing import Dict
from unittest.mock import patch
from time import sleep

from src.channels.channel import ChannelSet
from src.utils.data_wrapper.oasis_api import OasisApiWrapper
from src.alerts.alerts import ApiIsDownAlert, ApiIsUpAgainAlert
from test.test_helpers import CounterChannel
from test import TestInternalConf

GET_OASIS_JSON_FUNCTION = \
    'src.utils.data_wrapper.oasis_api.get_oasis_json'


def api_mock_generator(expected_endpoint: str, expected_params: Dict,
                       expected_api_call: str):

    def api_mock(endpoint: str, params: Dict, _, api_call: str = ''):
        print(endpoint)
        print(params)
        print(api_call)
        print(expected_endpoint)
        print(expected_params)
        print(expected_api_call)
        return (endpoint == expected_endpoint and
                params == expected_params and
                api_call == expected_api_call)

    return api_mock
# @unittest.skip("Skipping Test Oasis API")
class TestOasisApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ws_url = 'the_ws'
        cls.api_endpoint = 'http://localhost:8688'
        cls.acc_addr = 'the_account_address'
        cls.validator_id = "the_validator_id"
        cls.block_no = 1

    def setUp(self) -> None:
        self.logger = logging.getLogger('dummy')
        self.node_name = 'dummy_node'
        self.wrapper = OasisApiWrapper(self.logger)

        self.max_time = 15
        self.max_time_less = self.max_time - 10
        self.max_time_more = self.max_time + 2

        self.counter_channel = CounterChannel(self.logger)
        self.channel_set = ChannelSet([self.counter_channel], TestInternalConf)

        self.params = {'name': self.node_name}


    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_block_header(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/consensus/blockheader'
        api_call = ''
        self.params = {'name': self.node_name}
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)
        
        self.assertTrue(self.wrapper.get_block_header(self.api_endpoint, 
            self.node_name))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_is_syncing(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/nodecontroller/synced'
        api_call = ''
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_is_syncing(self.api_endpoint, 
            self.node_name))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_node(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/registry/node'
        api_call = ''
        self.params['nodeID'] = self.validator_id
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_node(self.api_endpoint, 
            self.node_name, self.validator_id))
    
    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_prometheus_gauge(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/prometheus/gauge'
        api_call = ''
        self.params['gauge'] = "peers"
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_prometheus_gauge(self.api_endpoint, 
            self.node_name, "peers")) 

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_consensus_genesis(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/consensus/genesis'
        api_call = ''
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_consensus_genesis(self.api_endpoint, 
            self.node_name))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_consensus_block(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/consensus/block'
        api_call = ''
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_consensus_block(self.api_endpoint, 
            self.node_name))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_block_header_at_height(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/consensus/blockheader'
        api_call = ''
        self.params['height'] = self.block_no
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_block_header_height(self.api_endpoint, 
            self.node_name, self.block_no))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_session_validators(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/scheduler/validators'
        api_call = ''
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_session_validators(self.api_endpoint, 
                self.node_name))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_web_sockets_connected_to_an_api(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/getconnectionslist'
        api_call = ''
        mock.api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_web_sockets_connected_to_an_api( \
            self.api_endpoint))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_ping_api(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/ping'
        self.params = {}
        api_call = ''
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.ping_api(self.api_endpoint))

    @patch (GET_OASIS_JSON_FUNCTION)
    def test_get_tendermint_address(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/consensus/pubkeyaddress'
        self.params = {'consensus_public_key': self.acc_addr}
        api_call = ''
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_tendermint_address(self.api_endpoint, \
           self.acc_addr))

    @patch (GET_OASIS_JSON_FUNCTION)
    def test_get_registry_node(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/registry/node'
        self.params = {'name' : self.node_name, 'nodeID' : self.acc_addr}
        api_call = ''
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)

        self.assertTrue(self.wrapper.get_registry_node(self.api_endpoint, \
             self.node_name, self.acc_addr))

    @patch(GET_OASIS_JSON_FUNCTION)
    def test_ping_node(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/pingnode'
        api_call = ''
        self.params = {'name': self.node_name}
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)
        self.assertTrue(self.wrapper.ping_node(self.api_endpoint, \
            self.node_name))
    
    @patch(GET_OASIS_JSON_FUNCTION)
    def test_get_staking_account_info(self, mock):
        # Set up mock
        endpoint = self.api_endpoint + '/api/staking/accountinfo'
        api_call = ''
        self.params = {'name': self.node_name, 'ownerKey': self.acc_addr}
        mock.side_effect = api_mock_generator(endpoint, self.params, api_call)
        self.assertTrue(self.wrapper.get_staking_account_info(self.api_endpoint,
            self.node_name, self.acc_addr))

    def test_set_api_as_down_produces_error_alert_if_api_not_down_for_val_monitors(
            self) -> None:
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.assertEqual(1, self.counter_channel.error_count)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ApiIsDownAlert)

    def test_set_api_as_down_produces_no_error_alert_if_api_down_for_val_monitors(
            self) -> None:
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.assertEqual(0, self.counter_channel.error_count)

    def test_set_api_as_down_produces_error_alert_if_api_not_down_for_non_val_monitors(
            self) -> None:
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.assertEqual(1, self.counter_channel.error_count)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ApiIsDownAlert)

    def test_set_api_as_down_produces_no_error_alert_if_api_down_for_non_val_monitors(
            self) -> None:
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.assertEqual(0, self.counter_channel.error_count)

    def test_set_api_as_down_sets_api_down_if_api_not_down_for_val_monitors(
            self) -> None:
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.assertTrue(self.wrapper.is_api_down)

    def test_api_not_down_by_default(self) -> None:
        self.assertFalse(self.wrapper.is_api_down)

    def test_set_api_as_down_sets_api_down_if_api_down_for_non_val_monitors(
            self) -> None:
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.assertTrue(self.wrapper.is_api_down)


    def test_set_api_as_down_sets_api_down_if_api_down_for_val_monitors(
            self) -> None:
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.assertTrue(self.wrapper.is_api_down)

    def test_set_api_as_down_sets_api_down_if_api_not_down_for_non_val_monitors(
            self) -> None:
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.assertTrue(self.wrapper.is_api_down)

    def test_set_api_as_down_raises_critical_alert_for_val_monitors_if_enough_time_passed_for_first_time(
            self) -> None:
        # To perform did task
        self.wrapper.set_api_as_up("", self.channel_set)
        self.counter_channel.reset()
        sleep(self.max_time_more)
        self.wrapper.set_api_as_down("", True, self.channel_set)

        self.assertEqual(1, self.counter_channel.critical_count)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ApiIsDownAlert)

    def test_set_api_as_down_raises_no_critical_alert_for_val_monitors_if_enough_time_passed_for_second_time(
            self) -> None:
        # To perform did task
        self.wrapper.set_api_as_up("", self.channel_set)
        sleep(self.max_time_more)
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", True, self.channel_set)

        self.assertEqual(0, self.counter_channel.critical_count)

    def test_set_api_as_down_raises_no_critical_alert_for_val_monitors_if_not_enough_time_passed_for_second_time(
            self) -> None:
        # To perform did task
        self.wrapper.set_api_as_up("", self.channel_set)
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.counter_channel.reset()
        self.wrapper.set_api_as_down("", True, self.channel_set)

        self.assertEqual(0, self.counter_channel.critical_count)

    def test_set_api_as_down_raises_no_critical_alert_for_non_val_monitors_if_enough_time_passed_for_first_time(
            self) -> None:
        # To perform did task
        self.wrapper.set_api_as_up("", self.channel_set)
        sleep(self.max_time_more)
        self.wrapper.set_api_as_down("", False, self.channel_set)

        self.assertEqual(0, self.counter_channel.critical_count)

    def test_set_api_as_down_raises_no_critical_alert_for_non_val_monitors_if_enough_time_passed_for_second_time(
            self) -> None:
        # To perform did task
        self.wrapper.set_api_as_up("", self.channel_set)
        sleep(self.max_time_more)
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.wrapper.set_api_as_down("", False, self.channel_set)

        self.assertEqual(0, self.counter_channel.critical_count)

    def test_set_api_as_down_raises_no_critical_alert_for_non_val_monitors_if_not_enough_time_passed_for_second_time(
            self) -> None:
        # To perform did task
        self.wrapper.set_api_as_up("", self.channel_set)
        self.wrapper.set_api_as_down("", False, self.channel_set)
        self.wrapper.set_api_as_down("", False, self.channel_set)

        self.assertEqual(0, self.counter_channel.critical_count)

    def test_set_api_as_up_produces_info_alert_if_api_is_down(self):
        self.wrapper.set_api_as_down("", True, self.channel_set)
        self.counter_channel.reset()
        self.wrapper.set_api_as_up("", self.channel_set)
        self.assertEqual(1, self.counter_channel.info_count)
        self.assertIsInstance(self.counter_channel.latest_alert,
                              ApiIsUpAgainAlert)

    def test_set_api_as_up_produces_no_alert_if_api_is_up(self):
        self.wrapper.set_api_as_up("", self.channel_set)
        self.assertTrue(self.counter_channel.no_alerts())
