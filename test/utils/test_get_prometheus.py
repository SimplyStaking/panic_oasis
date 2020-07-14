import logging
import unittest
from unittest.mock import patch

from src.utils.exceptions import *
from src.utils.get_prometheus import get_oasis_prometheus, get_prometheus

GET_PROMETHEUS_FUNCTION = 'src.utils.get_prometheus.get_prometheus'
GET_FUNCTION = 'src.utils.get_prometheus.requests.get'
LOGGER = logging.getLogger('dummy')

ENDPOINT = 'the_endpoint'
PARAMS = ['go_memstats_alloc_bytes']
PARAMS_WITH_MISSING = ['go_memstats_alloc_bytes', 'missing_undefined']
RESULT = "go_memstats_alloc_bytes 3.042024e+06"
PROCESSED_RESULT = {'go_memstats_alloc_bytes': 3042024.0}

class TestGetPrometheus(unittest.TestCase):
    class DummyGetReturn:
        CONTENT_BYTES = b'go_memstats_alloc_bytes 3.042024e+06'
        RETURNED_STRING = "go_memstats_alloc_bytes 3.042024e+06"
        CONTENT_DICT = {"go_memstats_alloc_bytes": "3.042024e+06"}

        def __init__(self) -> None:
            self.content = self.CONTENT_BYTES

    @patch(GET_FUNCTION, return_value=DummyGetReturn())
    def test_get_prometheus_accesses_content_and_parses_bytes_to_dict(self, _):
        self.assertEqual(TestGetPrometheus.DummyGetReturn.RETURNED_STRING,
                        get_prometheus(ENDPOINT, LOGGER))

    @patch(GET_PROMETHEUS_FUNCTION, return_value=DummyGetReturn())
    def test_get_prometheus_error_if_endpoint_is_down(self, _):
        try:
            get_prometheus(ENDPOINT, LOGGER)
            self.fail('Expected RequestCallFailedException')
        except RequestCallFailedException:
            pass


class TestGetOasisPrometheus(unittest.TestCase):

    @patch(GET_PROMETHEUS_FUNCTION, return_value={})
    def test_get_oasis_prometheus_error_if_no_params_where_given(self, _):
        try:
            get_oasis_prometheus(ENDPOINT, {}, LOGGER)
            self.fail('Expected NoParametersGivenException')
        except NoParametersGivenException:
            pass

    @patch(GET_PROMETHEUS_FUNCTION, return_value=RESULT)
    def test_get_oasis_prometheus_result_if_endpoint_has_all_results(self, _):
        ret = get_oasis_prometheus(ENDPOINT, PARAMS, LOGGER)
        self.assertEqual(PROCESSED_RESULT, ret)

    @patch(GET_PROMETHEUS_FUNCTION, return_value=RESULT)
    def test_get_oasis_prometheus_error_if_metric_not_found(self, _):
        try:
            get_oasis_prometheus(ENDPOINT, PARAMS_WITH_MISSING, LOGGER)
            self.fail('Expected MetricNotFoundException')
        except MetricNotFoundException:
            pass
