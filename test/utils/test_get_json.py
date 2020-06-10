import logging
import unittest
from unittest.mock import patch

from src.utils.exceptions import *
from src.utils.get_json import get_oasis_json, get_json

GET_JSON_FUNCTION = 'src.utils.get_json.get_json'
GET_FUNCTION = 'src.utils.get_json.requests.get'
LOGGER = logging.getLogger('dummy')

ENDPOINT = 'the_endpoint'
API_CALL = 'the_api_call'
PARAMS = {'name': 'OASIS_NODE',
          'consensus_public_key': 'the_address'}
RESULT = 'the_result'

# @unittest.skip("Skipping Test Get JSON")
class TestGetJson(unittest.TestCase):
    class DummyGetReturn:
        CONTENT_BYTES = b'{"a":"b","c":1,"2":3}'
        CONTENT_DICT = {"a": "b", "c": 1, "2": 3}

        def __init__(self) -> None:
            self.content = self.CONTENT_BYTES

    @patch(GET_FUNCTION, return_value=DummyGetReturn())
    def test_get_json_accesses_content_and_parses_bytes_to_dict(self, _):
        self.assertEqual(TestGetJson.DummyGetReturn.CONTENT_DICT,
                         get_json(ENDPOINT, LOGGER, PARAMS))

    @patch(GET_FUNCTION, return_value=DummyGetReturn())
    def test_get_json_with_no_params_works_just_the_same(self, _):
        self.assertEqual(TestGetJson.DummyGetReturn.CONTENT_DICT,
                         get_json(ENDPOINT, LOGGER))

# @unittest.skip("Skipping Test Get Oasis JSON")
class TestGetOasisJson(unittest.TestCase):

    @patch(GET_JSON_FUNCTION, return_value={})
    def test_get_oasis_json_error_if_api_returns_blank(self, _):
        try:
            get_oasis_json(ENDPOINT, PARAMS, LOGGER, API_CALL)
            self.fail('Expected UnexpectedApiErrorWhenReadingDataException')
        except UnexpectedApiErrorWhenReadingDataException:
            pass

    @patch(GET_JSON_FUNCTION, return_value={
        'unexpected_key': 'unexpected_value'})
    def test_get_oasis_json_error_if_api_returns_unexpected_key(self, _):
        try:
            get_oasis_json(ENDPOINT, PARAMS, LOGGER, API_CALL)
            self.fail('Expected UnexpectedApiErrorWhenReadingDataException')
        except UnexpectedApiErrorWhenReadingDataException:
            pass

    @patch(GET_JSON_FUNCTION, return_value={'result': RESULT})
    def test_get_oasis_json_result_if_api_return_has_result(self, _):
        ret = get_oasis_json(ENDPOINT, PARAMS, LOGGER, API_CALL)
        self.assertEqual(RESULT, ret)

    @patch(GET_JSON_FUNCTION, return_value={
        'error': 'Error: API call the_api_call failed.'})
    def test_get_oasis_json_error_if_api_call_failed(self, _):
        try:
            get_oasis_json(ENDPOINT, PARAMS, LOGGER, API_CALL)
            self.fail('Expected ApiCallFailedException')
        except ApiCallFailedException:
            pass
