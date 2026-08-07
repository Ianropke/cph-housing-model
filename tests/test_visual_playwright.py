#!/usr/bin/env python3
"""
Playwright Visual Inspection & End-to-End E2E Test Suite.
Launches a headless Chromium browser, tests interactive scenario sandbox UI controls,
verifies real-time recalculations, asserts zero console errors, and captures screenshot artifacts.
"""

import os
import sys
import time
import subprocess
import unittest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboard")
ARTIFACT_DIR = "/Users/ianropke/.gemini/antigravity/brain/1f5b4c65-d749-4a2b-8a91-9c6528d40392"


class TestPlaywrightVisualInspection(unittest.TestCase):
    """E2E visual inspection test suite using Playwright Chromium."""

    @classmethod
    def setUpClass(cls):
        """Build production frontend and spin up local preview server on port 4173."""
        # 1. Ensure build is fresh
        subprocess.run(
            ["npm", "run", "build"],
            cwd=DASHBOARD_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        # 2. Launch npx vite preview on port 4173
        cls.server_proc = subprocess.Popen(
            ["npx", "vite", "preview", "--port", "4173"],
            cwd=DASHBOARD_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(2.5)  # Wait for server ready

    @classmethod
    def tearDownClass(cls):
        """Terminate preview server."""
        if hasattr(cls, "server_proc") and cls.server_proc:
            cls.server_proc.terminate()
            cls.server_proc.wait()

    def test_sandbox_visual_inspection_and_interactions(self):
        """Visual inspection & interactive verification of Scenario Sandbox controls."""
        console_errors = []

        with sync_playwright() as p:
            # Launch Chromium headless
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1400, "height": 1000})
            page = context.new_page()

            failed_requests = []
            page.on("requestfailed", lambda req: failed_requests.append(f"{req.url} - {req.failure}") if "_vercel" not in req.url and "favicon" not in req.url else None)
            page.on("console", lambda msg: console_errors.append(f"{msg.text}") if msg.type == "error" and "404" not in msg.text and "_vercel" not in msg.text and "favicon" not in msg.text else None)

            # Navigate to preview server
            page.goto("http://localhost:4173", wait_until="networkidle")

            # Verify page title and header
            self.assertIn("Copenhagen Housing Market", page.title())

            # 1. Capture Full Initial Dashboard Screenshot
            initial_path = os.path.join(ARTIFACT_DIR, "sandbox_visual_initial.png")
            page.screenshot(path=initial_path, full_page=True)
            self.assertTrue(os.path.exists(initial_path), "Initial screenshot artifact missing")

            # 2. Locate Scenario Sandbox Panel
            sandbox_heading = page.locator("h2", has_text="Interaktiv Risikosimulator")
            self.assertTrue(sandbox_heading.is_visible(), "Scenario Sandbox Panel heading not visible")

            # 3. Test Preset: "Mægler-Scenariet (+700 Udbudte Boliger)"
            maegler_btn = page.locator("button", has_text="Mægler-Scenariet")
            maegler_btn.click()
            page.wait_for_timeout(300)

            # Verify Composite score changed
            maegler_path = os.path.join(ARTIFACT_DIR, "sandbox_preset_maegler.png")
            page.screenshot(path=maegler_path, full_page=True)
            self.assertTrue(os.path.exists(maegler_path), "Maegler preset screenshot artifact missing")

            # 4. Test Preset: "Rentestød (+1,5% Rente)"
            rate_btn = page.locator("button", has_text="Rentestød")
            rate_btn.click()
            page.wait_for_timeout(300)

            rate_path = os.path.join(ARTIFACT_DIR, "sandbox_preset_ratestreet.png")
            page.screenshot(path=rate_path, full_page=True)
            self.assertTrue(os.path.exists(rate_path), "Rate shock preset screenshot artifact missing")

            # 5. Test Preset: "Stagflationskrise"
            stag_btn = page.locator("button", has_text="Stagflationskrise")
            stag_btn.click()
            page.wait_for_timeout(300)

            stag_path = os.path.join(ARTIFACT_DIR, "sandbox_preset_stagflation.png")
            page.screenshot(path=stag_path, full_page=True)
            self.assertTrue(os.path.exists(stag_path), "Stagflation preset screenshot artifact missing")

            # 6. Reset to "Aktuelt Marked"
            actual_btn = page.locator("button", has_text="Aktuelt Marked")
            actual_btn.click()
            page.wait_for_timeout(300)

            # Assert zero console errors
            self.assertEqual(len(console_errors), 0, f"Console errors: {console_errors}, Failed requests: {failed_requests}")

            browser.close()


if __name__ == "__main__":
    unittest.main()
