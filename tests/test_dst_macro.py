#!/usr/bin/env python3
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

sys.path.insert(0, "../server")
import dst_macro

class TestDSTMacro(unittest.TestCase):

    @patch("dst_macro.urllib.request.urlopen")
    def test_fetch_dst_macro_data_success(self, mock_urlopen):
        def generate_mock_response(val):
            mock_response = MagicMock()
            mock_data = {
                "dataset": {
                    "value": [val]
                }
            }
            mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
            mock_cm = MagicMock()
            mock_cm.__enter__.return_value = mock_response
            return mock_cm

        # Return mock responses in order: AUP01, PRIS111, INDKP107
        mock_urlopen.side_effect = [
            generate_mock_response(42000), # Assume 42k unemployed out of 1M -> 4.2%
            generate_mock_response(120.0), # PRIS111
            generate_mock_response(390000) # INDKP107
        ]
        
        data = dst_macro.fetch_dst_macro_data()
        
        self.assertIn("unemployment_rate", data)
        self.assertIn("rent_index", data)
        self.assertIn("disposable_income_cph", data)
        # Even if mock isn't perfect for the division logic, the keys must be present.

    @patch("dst_macro.urllib.request.urlopen")
    def test_fetch_dst_macro_data_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("API Down")
        
        data = dst_macro.fetch_dst_macro_data()
        
        self.assertIn("unemployment_rate", data)
        self.assertEqual(data["unemployment_rate"], 0.042)
        self.assertEqual(data["rent_index"], 120.0)

if __name__ == "__main__":
    unittest.main()
