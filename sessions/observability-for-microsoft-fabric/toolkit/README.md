# Fabric observability toolkit

Queries, notebooks and scripts for **Observability for Microsoft Fabric**. Everything is built on
features that any Fabric customer has: workspace monitoring, capacity events, Eventhouse
and KQL, Fabric notebooks, and the Fabric REST API. Nothing here is proprietary.

It answers three questions:

1. Which items used the most capacity last week?
2. If a pipeline failed at 2 AM, would you know before your users told you?
3. When was this table last refreshed, and was that on time?

## Read this first: what has and has not been run

I would rather you know than find out. Each file says its own status in its header.

| What | Status |
|---|---|
| `kql/02`, `kql/03`, `kql/04` | **Ran live on 2026-11-03 and again on 2026-11-10** against a demo workspace with jobs generated on purpose. On 11-10 the drift query flagged a notebook at 2.68 minutes against a 0.24 minute baseline |
| `kql/01`, `kql/06` | **Ran live on 2026-11-03** |
| `kql/05` | **Ran live on 2026-11-03**; returned 15.72% utilization on an F2 |
| `kql/07`, `kql/09` | **Not run.** Written from documented schemas. Test them on your data |
| `kql/08` | **An idea, not run.** Join keys not confirmed in a real tenant |
| `notebooks/01_bpa_scan` | **Ran live in Fabric on 2026-11-10, start to finish, twice.** The first run found 62 findings and counted all 62 as new. The second run saved a new file, picked the first as the previous scan, and reported 0 new, 0 fixed, 62 unchanged. The comparison logic also has 17 unit tests |
| `notebooks/02_freshness_and_grain` | The grain, null-key and orphan checks are generalized from a notebook that ran green, red and green again on 2026-11-03. The config cells, freshness SLA, volume floor and results table are new. **Not run in Fabric in this form** (the check logic is unit tested; the Spark cells are not) |
| `scripts/fabric_api.py` | **Ran live on 2026-11-10**: created a workspace's notebooks, pipelines and lakehouse, replaced a notebook's definition, started notebook and pipeline runs, and polled them to the end |
| `scripts/deploy_notebooks.py`, `scripts/create_demo_jobs.py` | Not run as command-line tools. The helper calls they are built on ran live (above), and `create_demo_jobs.py`'s notebook and pipeline definitions were used as written |

Workspace monitoring was **Preview** when this was written. Check the current status.

## Monday morning: start here

1. Turn on workspace monitoring and start streaming capacity events. They **do not
   backfill**. Read [docs/capacity-cost-of-monitoring.md](docs/capacity-cost-of-monitoring.md)
   first, because both use your capacity. Steps are in [docs/setup-checklist.md](docs/setup-checklist.md).
2. Save [kql/02-pipeline-failure-alert.kql](kql/02-pipeline-failure-alert.kql) and put an alert on it.
3. Add the capacity usage alert from the Real-Time hub (80% is the template default).
4. Then add duration drift, a BPA baseline and the freshness-and-grain notebook.

## What is in here

```
kql/        Queries for the Eventhouse (workspace monitoring and capacity events)
notebooks/  Two Fabric notebooks: BPA scan with last-vs-this comparison; freshness and grain checks
scripts/    Deploy the notebooks and create demo jobs through the Fabric REST API
src/        The small, tested logic that the notebooks embed
tests/      Unit tests for src/ (pytest)
docs/       Setup checklist, and what monitoring costs in capacity
```

### Queries

| File | Question it answers |
|---|---|
| `kql/01-pipeline-runs-by-status` | Are pipelines failing at all? |
| `kql/02-pipeline-failure-alert` | Which pipeline failed in the last 9 minutes? (alert on this) |
| `kql/03-failed-activities` | Which step failed, and with what failure type? |
| `kql/04-duration-drift` | Which job finished green but took far longer than normal? |
| `kql/05-capacity-utilization` | How busy has the capacity been? |
| `kql/06-capacity-by-workload` | Which workload is using the capacity? |
| `kql/07-capacity-by-item` | Which item is using the capacity? (not run) |
| `kql/08-slow-job-vs-capacity` | Did a slow job line up with capacity pressure? (idea) |
| `kql/09-completion-sla` | Did the job finish by its deadline? (not run) |

### Notebooks

Deploy both with `python scripts/deploy_notebooks.py --workspace-id <guid>`, or import the
`.ipynb` files in the Fabric portal. Then attach a lakehouse and fill in the settings cell.

The notebooks are generated from `src/` by `python scripts/build_notebooks.py`. Edit
`src/`, run the tests, rebuild. Do not hand-edit the notebooks.

## Try it without touching real data

`scripts/create_demo_jobs.py` creates notebooks and pipelines that succeed, fail and run
slow, so the queries have something to find. It uses capacity when you pass `--run`.
Use a workspace on a capacity with room to spare.

## Run the tests

```
pip install pandas pytest
python -m pytest tests
```

## Sensitive data

Workspace monitoring logs can contain sensitive values if your pipeline configurations
include them. Restrict who can read the monitoring Eventhouse. The scripts read a token
from `FABRIC_TOKEN` or the Azure CLI and never write one to disk. Do not commit tokens,
workspace IDs from a client, or exported logs.

## Contact

Jonathan Stewart, jonathanstewart.me

## License

MIT. See [LICENSE](LICENSE).
