# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from benchmark_reliability import run_benchmark


def test_reliability_benchmark_has_no_unsafe_automation():
    report = run_benchmark()
    assert report["cases"] >= 30
    assert report["unsafe_auto_decisions"] == 0
    assert report["human_review_recall"] == 1.0
    assert report["accuracy"] >= 0.95
