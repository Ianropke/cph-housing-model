#!/usr/bin/env python3
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

sys.path.insert(0, "../server")
import dst_macro

class TestDSTMacro(unittest.TestCase):

    def setUp(self):
        # Clear the global cache before each test case
        dst_macro._macro_data_cache = None

    @patch("dst_macro.urllib.request.urlopen")
    def test_fetch_dst_macro_data_success(self, mock_urlopen):
        def generate_mock_response(val):
            mock_response = MagicMock()
            mock_data = {
                "dataset": {
                    "value": [val],
                    "dimension": {
                        "Tid": {
                            "category": {
                                "index": {
                                    "2026M01": 0,
                                    "2026Q1": 0,
                                    "2026K1": 0
                                }
                            }
                        },
                        "OMRÅDE": {
                            "category": {
                                "index": {
                                    "101": 0,
                                    "147": 0
                                }
                            }
                        }
                    },
                    "updated": "2026-07-15T00:00:00Z"
                }
            }
            mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
            mock_cm = MagicMock()
            mock_cm.__enter__.return_value = mock_response
            return mock_cm

        # Return mock responses in order: AUS07, DNRENTM, HUS1, INDKP107 (twice for CPH and FRB)
        mock_urlopen.side_effect = [
            generate_mock_response(4.2),   # AUS07: 4.2% unemployment
            generate_mock_response(3.9),   # DNRENTM: 3.9% interest rate
            generate_mock_response(120.0), # HUS1: 120.0 rent index
            generate_mock_response(390000.0), # INDKP107 Cph: 390k DKK
            generate_mock_response(440000.0)  # INDKP107 Frb: 440k DKK
        ]
        
        data = dst_macro.fetch_dst_macro_data()
        
        self.assertIn("unemployment_rate", data)
        self.assertIn("rent_index", data)
        self.assertIn("rent_series", data)
        self.assertIn("disposable_income_cph", data)
        self.assertIn("disposable_income_frb", data)
        self.assertEqual(data["unemployment_rate"], 0.042)
        self.assertEqual(data["rent_index"], 120.0)

    @patch("dst_macro.urllib.request.urlopen")
    def test_fetch_dst_macro_data_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("API Down")
        
        data = dst_macro.fetch_dst_macro_data()
        
        self.assertIn("unemployment_rate", data)
        self.assertEqual(data["unemployment_rate"], 0.042)
        self.assertEqual(data["rent_index"], 120.0)

if __name__ == "__main__":
    unittest.main()
