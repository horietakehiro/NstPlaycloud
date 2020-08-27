from ..common.base import BaseTestCase

from unittest.mock import patch, Mock

from transfer.engine.core import NstEngine

@patch("transfer.engine.core.tf")
class InitTestCase(BaseTestCase):

    def test_init_1(self, tf_mock):
        """
        test_init_1 : initiate with params in config
        """
        engine = NstEngine(100, 200, self.test_config)

        self.assertTrue(isinstance(engine, NstEngine))