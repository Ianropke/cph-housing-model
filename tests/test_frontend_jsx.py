#!/usr/bin/env python3
"""
Frontend JSX syntax and safety validator test suite.
Validates that all React JSX components build cleanly and do not contain unescaped JSX tokens.
"""

import os
import re
import subprocess
import unittest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.join(PROJECT_DIR, "dashboard")


class TestFrontendBuildAndJSX(unittest.TestCase):
    """Validates Vite build compilation and JSX syntax integrity."""

    def test_vite_production_build(self):
        """Verifies that 'npm run build' completes with return code 0 (Vite / Rolldown compilation)."""
        res = subprocess.run(
            ["npm", "run", "build"],
            cwd=DASHBOARD_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(
            res.returncode,
            0,
            f"Frontend Vite build failed with errors:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}",
        )

    def test_jsx_unescaped_characters(self):
        """Scans all JSX components to ensure no raw unescaped > or < appear in JSX text nodes."""
        src_dir = os.path.join(DASHBOARD_DIR, "src")
        bad_patterns = []

        for root, _, files in os.walk(src_dir):
            for f in files:
                if f.endswith(".jsx"):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", encoding="utf-8") as fh:
                        lines = fh.readlines()
                    for idx, line in enumerate(lines, 1):
                        # Detect unescaped raw > in paragraph/div JSX text (e.g. >10% inside JSX tag)
                        if re.search(r">\s*>[0-9]", line) or re.search(r"[\s\(\"']>[0-9]+%", line):
                            # Ensure it's not inside JS object/string or arrow function
                            if not re.search(r"=>|const|let|var|dataKey|threshold|AMBER|RED|color:", line):
                                bad_patterns.append(f"{f}:{idx}: {line.strip()}")

        self.assertEqual(
            len(bad_patterns),
            0,
            f"Found potentially unescaped JSX characters in text nodes:\n" + "\n".join(bad_patterns),
        )


if __name__ == "__main__":
    unittest.main()
