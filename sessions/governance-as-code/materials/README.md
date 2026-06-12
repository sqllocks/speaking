# Triage Scanner - Governance as Code

A read-only scanner for the **Power BI / Fabric Admin REST API**. Point it at a
tenant you just inherited and it produces actionable cleanup lists. No writes,
no changes, just answers.

> This is the sanitized, take-home version of the scanner demoed in
> *Governance as Code: Triage an Inherited Fabric Tenant*. It ships with no
> tenant data. You supply your own tenant ID at runtime.

## What it finds

| List | Meaning |
|------|---------|
| **Zero-view reports** | No `ViewReport` activity in the lookback window. Candidates to retire. |
| **Orphaned datasets** | No reports on top, or no/abandoned owner. |
| **Dead refresh schedules** | Refresh configured *and* failing. |
| **Access exposure** | No-admin workspaces, external write access, org-wide share links, publish-to-web embeds. |

Every row is joined to a **workspace-owner email** so each finding has someone to notify.

## Requirements

- Python 3.9+ and `pip install msal requests`
- **Fabric / Power BI admin rights** (or a service principal enabled for the
  read-only admin APIs). Premium / Fabric capacity. The admin APIs are not on free.

## Run it

```bash
# Device-code sign-in (interactive). Prints a code, you approve in the browser.
python triage_scanner.py --tenant <YOUR_TENANT_ID> --days 7

# Narrow the activity lookback (max ~28 days of history is available)
python triage_scanner.py --tenant <YOUR_TENANT_ID> --days 28 --out ./reports

# Close the loop: post the summary to a Teams channel
python triage_scanner.py --tenant <YOUR_TENANT_ID> --days 7 \
    --teams-webhook "https://outlook.office.com/webhook/..."

# Try it with no tenant. Generates representative demo data so you see the output shape.
python triage_scanner.py --demo-data
```

Outputs land as CSVs in the `--out` directory (default `./`), one per list.

## API contracts (verified against Microsoft Learn)

- **Admin endpoints:** `/admin/groups`, `/admin/reports`, `/admin/datasets`,
  `/admin/activityevents`, `/admin/groups/{id}/users`, `/admin/capacities/refreshables`.
- **`activityevents`** returns **one UTC day per request** (start/end same day),
  roughly 5,000 to 10,000 entries plus a `continuationToken`. You **must** loop
  until the token is gone. History is limited to ~28 days. Direct REST throttle:
  **200 req/hour**.
  Source: [learn.microsoft.com/power-bi/enterprise/service-admin-auditing](https://learn.microsoft.com/power-bi/enterprise/service-admin-auditing)
- **`GetGroupsAsAdmin`:** `$top` max 5000, page with `$skip`.

## A note on the client ID

The default `--client-id` is Microsoft's well-known public **Azure CLI** client
(`04b07795-8ddb-461a-bbee-02f9e1bf7b46`) so device-code sign-in works out of the
box in most tenants. It is a public client identifier, **not a secret**. Override
with `--client-id` (or the `PBI_CLIENT_ID` env var) to use your own app
registration.

---

Part of the [Governance as Code](../) session · [sqlbites.net](https://sqlbites.net)
