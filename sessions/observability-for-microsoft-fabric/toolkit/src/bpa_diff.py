import pandas as pd

# A finding is "the same finding" when these columns match. Severity is left out
# on purpose: a rule changing severity is not a new finding.
BPA_KEYS = ["Category", "Rule Name", "Object Type", "Object Name"]


def diff_scans(previous, current, keys=BPA_KEYS):
    """Compare two BPA scans (pandas DataFrames).

    Returns a dict of three DataFrames:
      new       - in `current` but not in `previous`
      fixed     - in `previous` but not in `current`
      unchanged - in both

    `previous` may be None or empty (first scan): everything is then NEW.
    """
    cur = current.drop_duplicates(subset=keys).reset_index(drop=True)
    if previous is None or len(previous) == 0:
        return {"new": cur, "fixed": cur.iloc[0:0], "unchanged": cur.iloc[0:0]}

    prev = previous.drop_duplicates(subset=keys).reset_index(drop=True)
    merged = cur.merge(prev[keys], on=keys, how="outer", indicator=True)
    new = merged[merged["_merge"] == "left_only"].drop(columns="_merge").reset_index(drop=True)
    unchanged = merged[merged["_merge"] == "both"].drop(columns="_merge").reset_index(drop=True)
    fixed = (
        prev.merge(cur[keys], on=keys, how="left", indicator=True)
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
        .reset_index(drop=True)
    )
    return {"new": new, "fixed": fixed, "unchanged": unchanged}


def summarize(df):
    """Count findings by Category and Severity (the 'findings by category' view)."""
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Category", "Severity", "Findings"])
    return (
        df.groupby(["Category", "Severity"]).size().reset_index(name="Findings")
        .sort_values(["Category", "Severity"]).reset_index(drop=True)
    )
