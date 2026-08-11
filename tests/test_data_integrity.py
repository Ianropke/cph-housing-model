#!/usr/bin/env python3
"""
Test suite to verify that all relevant data used by the CphHousingModel
is updated, correct, and structured properly.
"""

import sys
import unittest
import datetime

# Add server to path
sys.path.insert(0, "../server")

from cph_housing_server import (
    fetch_dst_housing_data,
    fetch_rkr_data,
    DST_EJ56_DATA
)

class TestDataIntegrity(unittest.TestCase):
    
    def test_dst_housing_data_updated(self):
        """Verifies that the housing price index data is updated to a recent date."""
        data = fetch_dst_housing_data("EJ56")
        
        # Check that we received the correct table
        self.assertEqual(data.get("table"), "EJ56")
        
        # Verify that the last updated date is 2026-05-29 or newer
        # (DST publishes quarterly — 2025Q4 released 2026-05-29)
        last_updated_str = data.get("last_updated", "2000-01-01")
        last_updated = datetime.datetime.strptime(last_updated_str, "%Y-%m-%d").date()
        target_date = datetime.date(2026, 5, 1)
        self.assertGreaterEqual(last_updated, target_date, 
                                f"Data is stale! Last updated: {last_updated_str}")
        
        # Verify that all segments have data up to at least 2025Q4
        segments = data.get("segments", {})
        self.assertIn("copenhagen_apartments", segments)
        self.assertIn("copenhagen_houses", segments)
        self.assertIn("frederiksberg_apartments", segments)
        
        for seg_id, seg_data in segments.items():
            latest_period = seg_data.get("latest_period")
            self.assertIsNotNone(latest_period)
            # Check that the latest period is at least 2025Q4
            self.assertGreaterEqual(latest_period, "2025Q4", 
                                    f"Segment {seg_id} data is stale. Latest: {latest_period}")
            
            # Verify basic structure
            self.assertGreater(seg_data.get("latest_value", 0), 0)
            self.assertIsNotNone(seg_data.get("yoy_change_pct"))

    def test_rkr_mortgage_data_validity(self):
        """Verifies that the mortgage data from Finance Denmark is properly formatted and valid."""
        tables = ["UDB010", "UDB030", "UL30"]
        for table in tables:
            data = fetch_rkr_data(table)
            self.assertEqual(data.get("table"), table)
            self.assertIn("query_timestamp", data)
            
            payload = data.get("data", {})
            self.assertIn("description", payload)
            self.assertEqual(payload.get("source"), "Finans Danmark Statistikbank")
            
            self.assertEqual(payload.get("status"), "live")
            if table == "UDB010":
                self.assertGreater(payload.get("active_listings", 0), 0)
            elif table == "UDB030":
                self.assertGreater(payload.get("median_days_on_market", 0), 0)
            elif table == "UL30":
                self.assertGreater(payload.get("interest_only_share_pct", 0), 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
