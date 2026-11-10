"""Create a few jobs that succeed, fail and run slow, so the monitoring queries have something to find.

    python scripts/create_demo_jobs.py --workspace-id <guid>            # create the items only
    python scripts/create_demo_jobs.py --workspace-id <guid> --run      # also run them to generate history

Creates:
  Obs_Job_Ok    notebook, finishes instantly
  Obs_Job_Slow  notebook, sleeps 150 s (after fast runs it becomes your duration-drift example)
  Obs_Job_Fail  notebook, raises on purpose
  Obs_Pipe_Ok   pipeline, one 20 s Wait
  Obs_Pipe_Fail pipeline, Wait then a Fail activity (FailureType UserError)

COST: --run uses capacity. The slow notebook alone holds a Spark session for about 2.5 minutes.
Use a workspace on a capacity with headroom, not the one you are trying to protect. Workspace
monitoring must already be on for the runs to show up in ItemJobEventLogs (it does not backfill).

Duration drift needs a baseline of the SAME item: --run runs Obs_Job_Slow's fast version three
times, then swaps in the slow version and runs it once.

Status: adapted from the scripts used to build the demo workspace (2026-11-03).
"""
import argparse

import fabric_api as fx

OK_CODE = "print('ok')\n"
FAST_CODE = "print('fast')\n"
SLOW_CODE = "import time\ntime.sleep(150)\nprint('slow but ok')\n"
FAIL_CODE = "raise Exception('Deliberate demo failure: upstream feed missing')\n"

WAIT = {"name": "Wait_Step", "type": "Wait", "dependsOn": [], "typeProperties": {"waitTimeInSeconds": 20}}
FAIL = {"name": "Fail_Step", "type": "Fail",
        "dependsOn": [{"activity": "Wait_Step", "dependencyConditions": ["Succeeded"]}],
        "typeProperties": {"message": "Deliberate demo failure", "errorCode": "DEMO001"}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace-id", required=True)
    ap.add_argument("--run", action="store_true", help="also run the notebooks to generate job history (uses capacity)")
    args = ap.parse_args()

    token, ws = fx.get_token(), args.workspace_id
    ids = {}
    for name, code in (("Obs_Job_Ok", OK_CODE), ("Obs_Job_Slow", FAST_CODE), ("Obs_Job_Fail", FAIL_CODE)):
        ids[name] = fx.create_or_update(token, ws, name, "Notebook", fx.ipynb_definition(fx.one_cell_notebook(code)))
    ids["Obs_Pipe_Ok"] = fx.create_or_update(token, ws, "Obs_Pipe_Ok", "DataPipeline", fx.pipeline_definition([WAIT]))
    ids["Obs_Pipe_Fail"] = fx.create_or_update(token, ws, "Obs_Pipe_Fail", "DataPipeline", fx.pipeline_definition([WAIT, FAIL]))
    print(ids)

    if not args.run:
        print("Created only. Re-run with --run to generate job history.")
        return

    print("ok run:", fx.run_notebook(token, ws, ids["Obs_Job_Ok"]))
    print("fail run (this one is supposed to fail):", fx.run_notebook(token, ws, ids["Obs_Job_Fail"]))
    for i in range(3):                       # the baseline: three fast runs
        print(f"baseline run {i + 1}:", fx.run_notebook(token, ws, ids["Obs_Job_Slow"]))
    fx.create_or_update(token, ws, "Obs_Job_Slow", "Notebook", fx.ipynb_definition(fx.one_cell_notebook(SLOW_CODE)))
    print("slow run:", fx.run_notebook(token, ws, ids["Obs_Job_Slow"]))
    print("Pipelines were created but not started. Run them from the portal or the job scheduler API.")


if __name__ == "__main__":
    main()
