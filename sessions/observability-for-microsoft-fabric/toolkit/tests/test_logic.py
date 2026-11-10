import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from bpa_diff import BPA_KEYS, diff_scans, summarize  # noqa: E402
from check_logic import (  # noqa: E402
    count_result, freshness_result, make_result, verdict, volume_result,
)


def scan(*rows):
    return pd.DataFrame(rows, columns=["Category", "Rule Name", "Severity", "Object Type", "Object Name"])


A = ("Performance", "Model should have a date table", "Warning", "Model", "M")
B = ("Maintenance", "Visible objects with no description", "Info", "Column", "Sales[Amount]")
C = ("Formatting", "Provide format string", "Warning", "Measure", "[Total]")


def test_first_scan_everything_is_new():
    d = diff_scans(None, scan(A, B))
    assert len(d["new"]) == 2 and len(d["fixed"]) == 0 and len(d["unchanged"]) == 0


def test_empty_previous_counts_as_first_scan():
    d = diff_scans(scan(), scan(A))
    assert len(d["new"]) == 1


def test_new_fixed_unchanged():
    d = diff_scans(scan(A, B), scan(B, C))
    assert list(d["new"]["Rule Name"]) == ["Provide format string"]
    assert list(d["fixed"]["Rule Name"]) == ["Model should have a date table"]
    assert list(d["unchanged"]["Rule Name"]) == ["Visible objects with no description"]


def test_severity_change_is_not_a_new_finding():
    b_error = ("Maintenance", "Visible objects with no description", "Error", "Column", "Sales[Amount]")
    d = diff_scans(scan(B), scan(b_error))
    assert len(d["new"]) == 0 and len(d["fixed"]) == 0 and len(d["unchanged"]) == 1


def test_identical_scans_have_no_changes():
    d = diff_scans(scan(A, B, C), scan(A, B, C))
    assert len(d["new"]) == 0 and len(d["fixed"]) == 0 and len(d["unchanged"]) == 3


def test_duplicate_rows_do_not_double_count():
    d = diff_scans(scan(A), scan(A, A, B))
    assert len(d["new"]) == 1 and len(d["unchanged"]) == 1


def test_summarize_counts_by_category_and_severity():
    s = summarize(scan(A, B, B[:4] + ("Other",), C))
    row = s[(s.Category == "Maintenance") & (s.Severity == "Info")]
    assert int(row.Findings.iloc[0]) == 2


def test_summarize_empty():
    assert len(summarize(scan())) == 0


NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


def test_freshness_inside_sla_passes():
    r = freshness_result("line_g", NOW - timedelta(hours=3), 26, NOW)
    assert r["status"] == "PASS"


def test_freshness_over_sla_fails():
    r = freshness_result("line_g", NOW - timedelta(hours=30), 26, NOW)
    assert r["status"] == "FAIL" and "30.0" in r["detail"]


def test_freshness_boundary_is_inclusive():
    assert freshness_result("t", NOW - timedelta(hours=26), 26, NOW)["status"] == "PASS"


def test_freshness_without_sla_is_skip_not_fail():
    assert freshness_result("t", NOW - timedelta(days=90), None, NOW)["status"] == "SKIP"


def test_count_result():
    assert count_result("grain", "line_g.id", 0, "duplicate ids")["status"] == "PASS"
    r = count_result("grain", "line_g.id", 3, "duplicate ids")
    assert r["status"] == "FAIL" and "3 duplicate ids" in r["detail"]


def test_volume_result():
    assert volume_result("t", 0, 1)["status"] == "FAIL"
    assert volume_result("t", 5, 1)["status"] == "PASS"
    assert volume_result("t", 0, None)["status"] == "SKIP"


def test_verdict_green_red_and_skip():
    ok = make_result("a", "t", "PASS", "")
    bad = make_result("b", "t", "FAIL", "x")
    skip = make_result("c", "t", "SKIP", "")
    assert verdict([ok, skip])[0] == "GREEN"
    v, failed = verdict([ok, bad, skip])
    assert v == "RED" and failed == [bad]
    assert verdict([])[0] == "GREEN"


def test_bad_status_rejected():
    with pytest.raises(ValueError):
        make_result("a", "t", "MAYBE", "")


def test_keys_exclude_severity():
    assert "Severity" not in BPA_KEYS
