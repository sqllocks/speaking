# Governance as Code

A speaking session by **Jonathan Stewart** · [sqlbites.net](https://sqlbites.net)

*Triage an inherited Fabric tenant.*

You just got handed 800 workspaces and no documentation. This session builds a
read-only scanner over the Power BI / Fabric Admin REST API that turns a tenant
you've never seen into four actionable lists (zero-view reports, orphaned
datasets, dead refresh schedules, and access exposure), each joined to a
workspace owner you can actually notify. Governance you can run, version, and
re-run, not a 40-page PDF nobody reads.

## Slides
- [View slides (canonical, conference-neutral)](slides.pdf)
- For a specific delivery, see [deliveries.md](deliveries.md)

## Take-home materials
- [Triage Scanner (`triage_scanner.py`)](materials/triage_scanner.py): the read-only Admin API scanner from the demo
- [Scanner README](materials/README.md): setup, flags, and verified API contracts

The scanner ships with **no tenant data**. You supply your own tenant ID at
runtime, or pass `--demo-data` to see the output shape with synthetic rows.

## Deliveries
See [deliveries.md](deliveries.md) for the history of where this session has been taught.

---

Source: [github.com/sqllocks/speaking](https://github.com/sqllocks/speaking)
