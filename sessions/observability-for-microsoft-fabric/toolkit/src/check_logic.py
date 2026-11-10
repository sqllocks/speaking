from datetime import datetime, timezone


def make_result(check, target, status, detail):
    """One row of the platform-health history: check name, time, status, detail.

    status is one of PASS, FAIL, SKIP.
    """
    if status not in ("PASS", "FAIL", "SKIP"):
        raise ValueError("status must be PASS, FAIL or SKIP, got %r" % (status,))
    return {
        "check": check,
        "target": target,
        "status": status,
        "detail": detail,
        "checked_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def freshness_result(table, last_commit_utc, sla_hours, now_utc=None):
    """Is this table inside the window its owner expects?

    last_commit_utc: timezone-aware datetime of the latest Delta commit.
    sla_hours: the maximum age you accept, or None to only report the age.
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    age_h = (now_utc - last_commit_utc).total_seconds() / 3600.0
    if sla_hours is None:
        return make_result("freshness", table, "SKIP", "age %.1f h, no SLA set" % age_h)
    if age_h <= sla_hours:
        return make_result("freshness", table, "PASS", "age %.1f h, SLA %s h" % (age_h, sla_hours))
    return make_result("freshness", table, "FAIL", "age %.1f h is over the %s h SLA" % (age_h, sla_hours))


def count_result(check, target, bad_count, what):
    """A check that passes when it finds zero bad rows (duplicates, orphans, null keys)."""
    if bad_count == 0:
        return make_result(check, target, "PASS", "no %s" % what)
    return make_result(check, target, "FAIL", "%d %s" % (bad_count, what))


def volume_result(table, rows, min_rows):
    """Is the table empty, or smaller than the floor you set?"""
    if min_rows is None:
        return make_result("volume", table, "SKIP", "%d rows, no floor set" % rows)
    if rows >= min_rows:
        return make_result("volume", table, "PASS", "%d rows, floor %d" % (rows, min_rows))
    return make_result("volume", table, "FAIL", "%d rows is under the floor of %d" % (rows, min_rows))


def verdict(results):
    """GREEN when nothing failed, otherwise RED. SKIP never turns a run red."""
    failed = [r for r in results if r["status"] == "FAIL"]
    return ("RED" if failed else "GREEN"), failed
