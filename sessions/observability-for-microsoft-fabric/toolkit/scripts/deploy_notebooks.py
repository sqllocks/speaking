"""Deploy the toolkit notebooks into a Fabric workspace.

    python scripts/deploy_notebooks.py --workspace-id <guid>

Creates each notebook, or replaces its definition if one with the same name already
exists. It does not run anything and does not attach a lakehouse: open the notebook
in Fabric, attach a lakehouse, and fill in the settings cell.

Status: adapted from the REST calls used to build the demo workspace (2026-11-03). Run it
first against a workspace you can afford to clutter.
"""
import argparse
import os

import fabric_api as fx

NOTEBOOKS = {
    "Obs_BPA_Scan": "01_bpa_scan.ipynb",
    "Obs_Freshness_And_Grain": "02_freshness_and_grain.ipynb",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace-id", required=True)
    ap.add_argument("--only", choices=sorted(NOTEBOOKS), help="deploy just one notebook")
    args = ap.parse_args()

    token = fx.get_token()
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notebooks")
    for name, filename in NOTEBOOKS.items():
        if args.only and args.only != name:
            continue
        with open(os.path.join(root, filename), encoding="utf-8") as f:
            definition = fx.ipynb_definition(f.read())
        item_id = fx.create_or_update(token, args.workspace_id, name, "Notebook", definition)
        print(f"  {name}: {item_id}")


if __name__ == "__main__":
    main()
