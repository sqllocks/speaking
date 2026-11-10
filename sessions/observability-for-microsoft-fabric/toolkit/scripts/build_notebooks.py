"""Build the two Fabric notebooks from the tested modules in ../src.

Why a build step: the logic that decides NEW/FIXED and PASS/FAIL lives in src/ and
is unit tested. This script pastes that same source into the notebook cells, so
what you run in Fabric is what the tests ran.

Run from the repo root:   python scripts/build_notebooks.py
Fabric requires every cell `source` to be a list of strings, so we split lines.
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def read_src(name):
    with open(os.path.join(ROOT, "src", name), encoding="utf-8") as f:
        return f.read().rstrip() + "\n"


def lines(text):
    return text.splitlines(keepends=True)


_n = [0]


def _id():
    _n[0] += 1
    return "cell%04d" % _n[0]


def md(text):
    return {"cell_type": "markdown", "id": _id(), "metadata": {}, "source": lines(text.strip() + "\n")}


def code(text):
    return {"cell_type": "code", "id": _id(), "metadata": {}, "outputs": [], "execution_count": None,
            "source": lines(text.strip() + "\n")}


def write_nb(name, cells, kernel):
    nb = {
        "nbformat": 4, "nbformat_minor": 5, "cells": cells,
        "metadata": {
            "language_info": {"name": "python"},
            "kernel_info": {"name": kernel},
            "microsoft": {"language": "python",
                          "language_group": "jupyter_python" if kernel == "jupyter" else "synapse_pyspark"},
        },
    }
    path = os.path.join(ROOT, "notebooks", name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, indent=1)
        f.write("\n")
    print("wrote", path)


# ---------------------------------------------------------------- 01 BPA scan
bpa_cells = [
    md("""
# 01 - Best Practice Analyzer scan, with last-scan vs this-scan

Scans one semantic model with the Best Practice Analyzer from Semantic Link Labs,
saves the findings, and compares them with the previous scan so you see what is
**NEW** and what is **FIXED**. The scan is not the value. The comparison is.

**Before you run it**
1. Attach a lakehouse to this notebook (the scan files are written under `Files/bpa`).
2. Set `MODEL` and `MODEL_WORKSPACE` in the first code cell.
3. You need Read and Write permission on the model (`run_model_bpa` requires it).

**Known limits (seen with semantic-link-labs 0.18.1)**
- Semantic Link Labs rule *Direct Lake using a view* crashed on a Direct Lake model
  (`numpy vectorize on size 0 inputs`). The rule's code runs numpy `vectorize` on a query result
  with no check for an empty result, which is the likely trigger (not re-tested).
  `SKIP_DIRECT_LAKE_VIEW_RULE = True` switches that one rule off, so it is **not evaluated**.
  Set it to `False` to try again on a newer version of the library.
- The library's own save-to-table option failed in a Python (non-Spark) notebook
  (`schema_mode 'merge' is not supported in pyarrow engine`), so this notebook saves
  timestamped CSV files instead.
- The notebook reports only the rules that fired, not how many rules were checked. Do not
  quote a rule total from this output.
"""),
    code('''
# ---- settings: change these ----
MODEL = "Your_Semantic_Model"
MODEL_WORKSPACE = "Your Workspace Name"      # name or ID of the workspace that holds the model
SKIP_DIRECT_LAKE_VIEW_RULE = True            # see "Known limits" above
SCAN_DIR = "/lakehouse/default/Files/bpa"    # needs a default lakehouse attached
'''),
    code('''
# Unpinned on purpose for the first run. After you test it, pin the version you tested.
%pip install semantic-link-labs -q
'''),
    code("# ---- tested helper code (src/bpa_diff.py) ----\n" + read_src("bpa_diff.py")),
    code('''
import os, glob
from datetime import datetime, timezone
import sempy_labs as labs

if SKIP_DIRECT_LAKE_VIEW_RULE:
    from sempy_labs.tom._model import TOMWrapper
    TOMWrapper.is_direct_lake_using_view = lambda self: False   # skips that one rule

current = labs.run_model_bpa(dataset=MODEL, workspace=MODEL_WORKSPACE, return_dataframe=True, export=False)
print("findings this scan:", len(current))
'''),
    code('''
os.makedirs(SCAN_DIR, exist_ok=True)

# The previous scan is the newest stamped file that exists BEFORE we write this one.
previous_files = sorted(glob.glob(os.path.join(SCAN_DIR, "bpa_results_*.csv")))
previous = pd.read_csv(previous_files[-1]) if previous_files else None

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
current = current.copy()
current["ScanUtc"] = stamp
current.to_csv(os.path.join(SCAN_DIR, f"bpa_results_{stamp}.csv"), index=False)
current.to_csv(os.path.join(SCAN_DIR, "bpa_results.csv"), index=False)   # always the latest, easy to point a report at
print("saved", f"bpa_results_{stamp}.csv", "| previous scan:", os.path.basename(previous_files[-1]) if previous_files else "none (first scan)")
'''),
    code('''
print("FINDINGS BY CATEGORY AND SEVERITY")
display(summarize(current))

changes = diff_scans(previous, current)
print(f"NEW since last scan: {len(changes['new'])}   FIXED: {len(changes['fixed'])}   UNCHANGED: {len(changes['unchanged'])}")
if previous is None:
    print("First scan, so everything counts as NEW. Run it again after the next deployment.")
print("\\nNEW findings");   display(changes["new"])
print("FIXED findings");   display(changes["fixed"])
'''),
    md("""
## Make it a habit

- Run this after each deployment or refresh (schedule the notebook).
- Alert on any **new** high-severity finding. Treat security findings (no row-level security,
  open permissions) as immediate.
- Watch the total as a trend, not a single number.
"""),
]
write_nb("01_bpa_scan.ipynb", bpa_cells, "jupyter")

# ------------------------------------------------- 02 freshness, grain, silent loss
fresh_cells = [
    md("""
# 02 - Did the data actually land? Freshness, volume, grain and silent loss

A green pipeline run does not prove the rows landed. This notebook checks, per Delta table:

1. **Freshness** - when was the last commit, and is that inside the window the owner expects?
2. **Volume** - is the table empty, or smaller than a floor you set?
3. **Grain** - is the key column unique (no duplicate grain)?
4. **Silent loss** - no null keys, and every child row points at a real parent row (no orphans).

Every check becomes one row (check, target, PASS/FAIL/SKIP, detail, time). The notebook
prints a GREEN or RED verdict and, if anything failed, **raises so the job shows as Failed**.
That is what lets a scheduled run alert you. Optionally it appends the rows to a Delta
table so you keep a platform-health history.

**Before you run it**: fill in the config cell. Table and column names below are examples.
The freshness SLA and the results table are additions made after the demo run and have **not**
been run in a live workspace. The grain, null-key and orphan checks are the same checks that
ran on 2026-11-03 (green, then red with a planted orphan, then green again).
"""),
    code('''
# ---- settings: change these ----
WORKSPACE_ID = "<your-workspace-id>"
LAKEHOUSE_ID = "<your-lakehouse-id>"

# table -> key column, freshness SLA in hours (None = just report the age), minimum rows (None = no floor)
TABLES = {
    "orders":      {"key": "order_id",      "sla_hours": 26, "min_rows": 1},
    "order_lines": {"key": "order_line_id", "sla_hours": 26, "min_rows": 1},
    "customers":   {"key": "customer_id",   "sla_hours": None, "min_rows": 1},
}
# (child table, child column, parent table, parent column): every child row must have a parent
REFERENCES = [
    ("order_lines", "order_id", "orders", "order_id"),
    ("orders", "customer_id", "customers", "customer_id"),
]

WRITE_RESULTS = False                          # True = append every check to a Delta table (needs a default lakehouse)
RESULTS_TABLE = "observability_check_results"
'''),
    code("# ---- tested helper code (src/check_logic.py) ----\n" + read_src("check_logic.py")),
    code('''
from datetime import timezone
from delta.tables import DeltaTable
from pyspark.sql import Row, functions as F

# Delta history timestamps come back as naive datetimes in the session time zone.
# Pin the session to UTC so we can safely treat them as UTC.
spark.conf.set("spark.sql.session.timeZone", "UTC")

BASE = f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_ID}/Tables"
def table_path(t):
    return f"{BASE}/{t}"

frames, results = {}, []
for t, cfg in TABLES.items():
    df = spark.read.format("delta").load(table_path(t))
    frames[t] = df

    last = DeltaTable.forPath(spark, table_path(t)).history(1).select("timestamp").collect()[0]["timestamp"]
    results.append(freshness_result(t, last.replace(tzinfo=timezone.utc), cfg["sla_hours"]))
    results.append(volume_result(t, df.count(), cfg["min_rows"]))

    key = cfg["key"]
    total, distinct = df.count(), df.select(key).distinct().count()
    results.append(count_result("grain", f"{t}.{key}", total - distinct, "duplicate keys"))
    results.append(count_result("null-key", f"{t}.{key}", df.filter(F.col(key).isNull()).count(), "null keys"))

for child, ccol, parent, pcol in REFERENCES:
    orphans = frames[child].join(frames[parent], frames[child][ccol] == frames[parent][pcol], "left_anti").count()
    results.append(count_result("orphan", f"{child}.{ccol} -> {parent}.{pcol}", orphans, "orphan rows"))
'''),
    code('''
print(f"{'check':10} {'target':38} {'status':6} detail")
for r in results:
    print(f"{r['check']:10} {r['target']:38} {r['status']:6} {r['detail']}")

if WRITE_RESULTS:
    spark.createDataFrame([Row(**r) for r in results]).write.format("delta").mode("append").saveAsTable(RESULTS_TABLE)
    print(f"\\nappended {len(results)} rows to {RESULTS_TABLE}")

state, failed = verdict(results)
print("\\n" + "=" * 48)
if state == "RED":
    print(f"DATA-TRUST VERDICT: RED ({len(failed)} failed)")
    for r in failed:
        print(f"  - {r['check']} {r['target']}: {r['detail']}")
    raise SystemExit(f"observability checks failed: {[(r['check'], r['target']) for r in failed]}")
print("DATA-TRUST VERDICT: GREEN - data landed at every grain")
'''),
    md("""
## Demo the RED path

Plant an orphan row (a child row whose parent does not exist), re-run, and the verdict flips
to RED and the job fails. Remove the orphan, re-run, and it goes green again. That is the whole
demo: *fresh is not the same as correct*.
"""),
]
write_nb("02_freshness_and_grain.ipynb", fresh_cells, "synapse_pyspark")
