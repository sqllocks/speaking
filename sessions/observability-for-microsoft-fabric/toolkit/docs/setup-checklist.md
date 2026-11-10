# Setup checklist: turn the data on first

Both data sources below **do not backfill**. You only get history from the day you
switch them on, so do this before anything else. Read `capacity-cost-of-monitoring.md`
first: both of them use your capacity.

Facts here come from Microsoft Learn pages checked on 2026-11-02. Workspace monitoring
was still in **Preview** then; check the current status before you rely on it.

## 1. Workspace monitoring (job history, pipelines, semantic model operations)

1. Open the workspace settings, go to the Monitoring tab, and turn on log collection.
   Fabric creates a monitoring item with an Eventhouse and a KQL database.
2. Open that KQL database. The tables the queries in `kql/` use are
   `ItemJobEventLogs` and `FabricDataPipelinesActivityRunsLogs`.
3. Know the limits:
   - Collection is off until you turn it on. It does not backfill.
   - Data is kept 30 days by default (you can change retention).
   - Contributors and above can query the monitoring database.
   - One monitoring item per workspace. Several workspaces can send to one central
     Eventhouse if they are in the same Azure region. Each sending workspace gets its
     own KQL database there, so you query one database per workspace, not one table
     with a workspace column.
4. **Treat that Eventhouse like production data.** Logs can contain sensitive values if
   pipeline configurations include them. Restrict who can read it, and use Secure Input
   and Secure Output on pipeline activities.

## 2. Capacity overview events (utilization and state)

1. In the Real-Time hub, open Fabric events, then Capacity overview events.
2. Create an Eventstream and route it to an Eventhouse (direct ingestion). The table in
   `kql/05` and `kql/06` is named `CapacityEvents`; rename the queries if yours differs.
3. A Summary event arrives every 30 seconds, and a State event when the capacity
   becomes overloaded or is paused or resumed.
4. Delivery is best-effort, so duplicates are possible. The queries remove them.
5. Capacity operation events (one per operation that uses CU) work the same way and are
   what `kql/07` needs. They have not been run in this toolkit yet.

## 3. Alerts

- **Capacity usage alert:** Real-Time hub, Capacity overview events, Set alert. Pick
  "usage % over a threshold" (the default is 80), choose the capacity, add an email
  action, save. It builds an Activator rule for you. Set one alert per capacity.
  The template's usage percent tracks the interactive delay threshold percentage, so
  know what your alert is really watching.
- **Pipeline failure alert:** save `kql/02-pipeline-failure-alert.kql` as a queryset and
  add an alert on it.
- **Email notifications to capacity admins** also exist. They are checked every 15
  minutes, and after one is sent there is no new one for 3 hours.

## 4. Order of work

1. Turn on workspace monitoring and start the capacity events stream (above).
2. Add the pipeline failure alert (`kql/02`).
3. Add the capacity usage alert.
4. Then: duration drift (`kql/04`), a BPA baseline (`notebooks/01`), and the freshness
   and grain notebook (`notebooks/02`).

## Sources

- https://learn.microsoft.com/fabric/fundamentals/workspace-monitoring-overview
- https://learn.microsoft.com/fabric/fundamentals/item-job-event-logs
- https://learn.microsoft.com/fabric/real-time-hub/explore-fabric-capacity-overview-events
- https://learn.microsoft.com/fabric/real-time-hub/explore-fabric-capacity-operation-events
- https://learn.microsoft.com/fabric/enterprise/throttling
- https://learn.microsoft.com/fabric/enterprise/metrics-app
- Samples from Microsoft: https://github.com/microsoft/fabric-samples (workspace-monitoring folder)
