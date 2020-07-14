import unittest

from src.utils.config_parsers.internal import InternalConfig

# @unittest.skip("Skipping Test Internal Config")
class TestInternalConfig(unittest.TestCase):

    def test_internal_config_values_loaded_successfully(self) -> None:
        InternalConfig(
            'test/test_internal_config_main.ini',
            'test/test_internal_config_alerts.ini')
