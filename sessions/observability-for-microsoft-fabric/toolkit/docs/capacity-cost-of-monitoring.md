# Monitoring is not free: what it cost on a small capacity

Fabric's monitoring features run on your Fabric capacity. That means the thing you
add to watch the capacity also draws from it. This page is one measured case, so you
can plan for it before you turn everything on.

## What I saw

An F2 (the smallest paid size) that held a monitoring demo workspace:

- Over 14 days, peak utilization reached **329.08%**. Average was **14.22%**.
- The Capacity Metrics app showed **283,801 CU seconds** used by all items in that period.
- Items that exist only to do monitoring used **192,122 CU seconds, 67.7%** of that total:

| Monitoring item type | CU seconds | Share of total |
|---|---:|---:|
| Eventhouses (workspace monitoring database, capacity events database) | 156,001 | 55.0% |
| Eventstreams (capacity events, workspace monitoring) | 32,427 | 11.4% |
| Activator (the alert rule) | 3,694 | 1.3% |
| Everything else on the capacity | 91,679 | 32.3% |

One Eventhouse, the one that received the capacity events, was about 44% of the total
by itself. The Metrics app showed 86,040 seconds of running time for it, which is
about 24 hours, or one full day.

Numbers were read from the Capacity Metrics app (Compute page, Items, last 14 days) on
2026-11-04. That is one small capacity over one stretch of days. Do not read it as a
price list.

## What I tried

I turned off data collection on the three workspace monitoring items. Utilization did
not fall in the readings I took afterward, so workspace monitoring collection was not
the main load in this case.

I did **not** pause the capacity events stream. Microsoft's pause and resume page lists
both of its nodes (the capacity overview events source and the Eventhouse direct
ingestion destination) as not supporting pause.

## The likely cause, and what is not proven

The capacity events stream writes a row every 30 seconds. An Eventhouse is documented to
suspend when it is not in use. My guess is that the steady 30-second writes keep the
Eventhouse awake all day. A full day of running time fits that guess.

**This is a hypothesis.** I did not remove the source and measure again, so I have not
shown that the stream is what keeps the Eventhouse running. If you can run that
experiment on a capacity you can spare, it would settle it.

## What I would do differently

1. **Do not stream capacity events around the clock into an Eventhouse on a small
   capacity.** Capture a bounded window, or ingest in batches.
2. **Put the monitoring on a capacity with headroom**, or schedule it, instead of the
   capacity you are trying to protect.
3. **Check the pause and resume support table** before you pick sources and
   destinations for anything you may want to stop later.
4. **Measure before and after each change** with the Capacity Metrics app, per item.
5. **Turn it on anyway, with your eyes open.** Capacity events and workspace monitoring
   do not backfill. A day you wait is history you never get back. Start small, on one
   workspace, and read the bill in CU seconds.

## Where to read more

- Workspace monitoring overview: https://learn.microsoft.com/fabric/fundamentals/workspace-monitoring-overview
- Capacity overview events: https://learn.microsoft.com/fabric/real-time-hub/explore-fabric-capacity-overview-events
- Capacity Metrics app: https://learn.microsoft.com/fabric/enterprise/metrics-app
