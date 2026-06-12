#!/usr/bin/env python3
"""
triage_scanner.py - Triage an inherited Fabric / Power BI tenant.

Governance as Code. A read-only scanner for the Power BI Admin REST API.

Produces actionable lists so you can clean up a tenant you just inherited:
  1. Zero-view reports     (no ViewReport activity in the lookback window)
  2. Orphaned datasets     (no reports on top, or no/abandoned owner)
  3. Dead refresh schedules (refresh configured + failing)
  4. Access exposure       (no-admin workspaces, external write access,
                            org-wide share links, publish-to-web embeds)
...plus a workspace-owner join so each row has an admin email to notify.

API CONTRACTS (verified against Microsoft Learn):
  - Admin endpoints: /admin/groups, /admin/reports, /admin/datasets,
    /admin/activityevents, /admin/groups/{id}/users, /admin/capacities/refreshables
  - activityevents: ONE day per request (start/end same UTC day); returns
    ~5-10k entries + a continuationToken, so you MUST loop until the token is gone.
    History limited to ~28 days. Direct REST API throttle: 200 requests/hour.
    Source: learn.microsoft.com/power-bi/enterprise/service-admin-auditing
  - GetGroupsAsAdmin: $top max 5000, page with $skip.
  - Requires Fabric/Power BI admin rights (or a service principal enabled for
    read-only admin APIs). Premium/Fabric capacity, not free.

Auth: by default uses the public Azure CLI client id via device-code flow, so
you do NOT need to register an app. You just need to be a Fabric/Power BI admin
(or sign in as one). Tenant isolation: run only against a tenant you administer.

Setup:
  pip install msal requests

Usage:
  python triage_scanner.py --tenant <YOUR_TENANT_ID> --days 7
  python triage_scanner.py --tenant <YOUR_TENANT_ID> --domain yourcompany.com --days 7
  python triage_scanner.py --tenant <YOUR_TENANT_ID> --days 7 --teams-webhook "https://..."
  python triage_scanner.py --tenant <YOUR_TENANT_ID> --days 7 --out ./reports
  python triage_scanner.py --demo-data --out ./sample   # offline sample run, no API calls, no tenant needed

Config can also come from environment variables:
  TENANT_ID, PBI_DOMAIN, PBI_CLIENT_ID, PBI_TOKEN, PBI_OUT_DIR
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

try:
    import msal
except ImportError:
    msal = None  # only needed for live mode

# ---- Config -----------------------------------------------------------------
# Public Azure CLI client id (device-code capable, Power BI scope consented by
# default in most tenants). Override with --client-id or PBI_CLIENT_ID if you
# prefer your own app registration. This is a well-known public Microsoft id,
# not a secret.
DEFAULT_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

BASE = "https://api.powerbi.com/v1.0/myorg/admin"
# Output directory for the CSVs. Overridden at runtime by --out / PBI_OUT_DIR.
# Defaults to ./output relative to wherever you run the script.
OUT_DIR = Path(os.environ.get("PBI_OUT_DIR", "output"))


# ---- Auth -------------------------------------------------------------------
def get_token(tenant_id: str, client_id: str) -> str:
    # Optional shortcut: PBI_TOKEN env var skips the device-code flow entirely.
    # Handy for CI or when you already have a token, e.g.:
    #   az account get-access-token --resource https://analysis.windows.net/powerbi/api
    env_token = os.environ.get("PBI_TOKEN")
    if env_token:
        print("using PBI_TOKEN from environment (skipping device-code flow)")
        return env_token
    if msal is None:
        sys.exit("msal not installed: pip install msal requests")
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id, authority=authority)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        sys.exit(f"device flow failed: {json.dumps(flow, indent=2)}")
    print("\n" + flow["message"] + "\n")   # go to microsoft.com/devicelogin
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        sys.exit(f"auth failed: {result.get('error_description')}")
    return result["access_token"]


def _get(url: str, headers: dict) -> dict:
    """GET with basic 429 backoff (admin API throttles at 200 req/hr)."""
    for attempt in range(5):
        r = requests.get(url, headers=headers, timeout=60)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 30))
            print(f"  throttled; waiting {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return {}


# ---- Inventory pulls --------------------------------------------------------
def get_workspaces(headers: dict) -> list[dict]:
    """GetGroupsAsAdmin - $top max 5000, page with $skip."""
    out, skip, top = [], 0, 5000
    while True:
        page = _get(f"{BASE}/groups?$top={top}&$skip={skip}", headers).get("value", [])
        out.extend(page)
        if len(page) < top:
            break
        skip += top
    print(f"  {len(out)} workspaces")
    return out


def get_reports(headers: dict) -> list[dict]:
    """GetReportsAsAdmin - page with $top/$skip."""
    out, skip, top = [], 0, 5000
    while True:
        page = _get(f"{BASE}/reports?$top={top}&$skip={skip}", headers).get("value", [])
        out.extend(page)
        if len(page) < top:
            break
        skip += top
    print(f"  {len(out)} reports")
    return out


def get_datasets(headers: dict) -> list[dict]:
    """GetDatasetsAsAdmin - page with $top/$skip."""
    out, skip, top = [], 0, 5000
    while True:
        page = _get(f"{BASE}/datasets?$top={top}&$skip={skip}", headers).get("value", [])
        out.extend(page)
        if len(page) < top:
            break
        skip += top
    print(f"  {len(out)} datasets")
    return out


def get_refreshables(headers: dict) -> list[dict]:
    """Get Refreshables (admin) - authoritative source for refresh health.
    /admin/capacities/refreshables?$top=&$expand=capacity,group
    Returns refreshable items with last refresh status across the tenant."""
    out, skip, top = [], 0, 1000
    while True:
        url = f"{BASE}/capacities/refreshables?$top={top}&$skip={skip}&$expand=capacity,group"
        try:
            page = _get(url, headers).get("value", [])
        except requests.HTTPError as e:
            print(f"  refreshables unavailable ({e}); skipping dead-refresh detection")
            return out
        out.extend(page)
        if len(page) < top:
            break
        skip += top
    print(f"  {len(out)} refreshables")
    return out


def get_activity_events(headers: dict, days: int) -> list[dict]:
    """activityevents - one UTC day per request, looping continuation tokens.
    History limited to ~28 days. Returns flattened event list."""
    events: list[dict] = []
    printed_sample = False
    for d in range(1, days + 1):
        day = (datetime.now(timezone.utc).date() - timedelta(days=d))
        start = f"{day}T00:00:00"
        end = f"{day}T23:59:59"
        url = (f"{BASE}/activityevents?startDateTime='{start}'&endDateTime='{end}'")
        token = None
        try:
            while True:
                page_url = url if token is None else f"{BASE}/activityevents?continuationToken='{token}'"
                data = _get(page_url, headers)
                batch = data.get("activityEventEntities", []) or []
                if batch and not printed_sample:
                    # Verify field names against REAL data, not docs.
                    print("  sample event:", json.dumps(batch[0], indent=2)[:600])
                    printed_sample = True
                events.extend(batch)
                token = data.get("continuationToken")
                if not token:
                    break
        except requests.HTTPError as e:
            # Retention boundary: requesting a day older than ~28 days returns 400.
            # Stop gracefully and keep what we have.
            if e.response is not None and e.response.status_code == 400:
                print(f"  day -{d} ({day}): outside activity retention window (400) - "
                      f"stopping with {len(events)} events")
                break
            raise
        print(f"  day -{d} ({day}): {len(events)} cumulative events")
    return events


# ---- Analysis ---------------------------------------------------------------
def analyze(workspaces, reports, datasets, refreshables, events):
    ws_by_id = {w["id"]: w for w in workspaces}

    # Viewed report IDs. Activity events use PascalCase field names.
    viewed = {e.get("ReportId") for e in events if e.get("Activity") == "ViewReport"}
    viewed.discard(None)

    # 1) Zero-view reports
    zero_view = []
    for r in reports:
        if r.get("id") not in viewed:
            ws = ws_by_id.get(r.get("workspaceId") or r.get("groupId"), {})
            zero_view.append({
                "report": r.get("name"),
                "workspace": ws.get("name"),
                "workspace_id": ws.get("id"),
                "dataset_id": r.get("datasetId"),
                "modified": r.get("modifiedDateTime"),
            })

    # 2) Orphaned datasets: no report on top OR no owner (configuredBy blank)
    ds_with_report = {r.get("datasetId") for r in reports}
    orphaned = []
    for d in datasets:
        no_report = d.get("id") not in ds_with_report
        no_owner = not d.get("configuredBy")
        if no_report or no_owner:
            ws = ws_by_id.get(d.get("workspaceId") or d.get("groupId"), {})
            orphaned.append({
                "dataset": d.get("name"),
                "workspace": ws.get("name"),
                "workspace_id": ws.get("id"),
                "configured_by": d.get("configuredBy") or "(none)",
                "reason": "no reports" if no_report else "no owner",
            })

    # 3) Dead refresh: refreshable configured + last status failed
    dead_refresh = []
    for rf in refreshables:
        last = (rf.get("lastRefresh") or {})
        if str(last.get("status", "")).lower() in ("failed", "disabled"):
            grp = rf.get("group") or {}
            dead_refresh.append({
                "item": rf.get("name"),
                "workspace": grp.get("name"),
                "workspace_id": grp.get("id"),
                "last_status": last.get("status"),
                "configured_by": rf.get("configuredBy") or "(none)",
            })

    return zero_view, orphaned, dead_refresh


def fetch_workspace_users(wid, headers, users_cache):
    """GetGroupUsersAsAdmin, cached per workspace. Returns None on lookup
    failure (expected on personal workspaces)."""
    if wid not in users_cache:
        try:
            users_cache[wid] = _get(f"{BASE}/groups/{wid}/users", headers).get("value", [])
        except requests.HTTPError:
            users_cache[wid] = None
    return users_cache[wid]


def attach_owners(rows, headers, users_cache):
    """Join workspace admin email onto each row (GetGroupUsersAsAdmin)."""
    for row in rows:
        wid = row.get("workspace_id")
        if not wid:
            row["admin_email"] = "(unknown)"
            continue
        users = fetch_workspace_users(wid, headers, users_cache)
        if users is None:
            row["admin_email"] = "(lookup failed)"
            continue
        admins = [u.get("emailAddress") or u.get("identifier")
                  for u in users if u.get("groupUserAccessRight") == "Admin"]
        row["admin_email"] = ", ".join(a for a in admins if a) or "(no admin)"
    return rows


# ---- List 4: access exposure --------------------------------------------------
def get_widely_shared(headers, which):
    """WidelySharedArtifacts admin APIs. which is one of
    'linksSharedToWholeOrganization' or 'publishedToWeb'."""
    out = []
    url = f"{BASE}/widelySharedArtifacts/{which}"
    printed = False
    while url:
        try:
            data = _get(url, headers)
        except requests.HTTPError as e:
            print(f"  {which}: unavailable ({e}); skipping")
            return out
        batch = (data.get("ArtifactAccessEntities")
                 or data.get("artifactAccessEntities") or [])
        if batch and not printed:
            # Print the first raw entity to verify field names.
            print(f"  sample {which} entity:", json.dumps(batch[0], indent=2)[:500])
            printed = True
        out.extend(batch)
        url = data.get("continuationUri")
    print(f"  {len(out)} {which}")
    return out


def analyze_access(workspaces, headers, users_cache, org_links, published_web, domain):
    """List 4: guests/external accounts with write access, no-admin workspaces,
    org-wide share links, publish-to-web embeds.
    domain is your home tenant domain (e.g. yourcompany.com); accounts outside
    it are flagged as external. Pass None to skip the external-account check."""
    rows = []
    for w in workspaces:
        if (w.get("type") or "") == "PersonalGroup":
            continue
        users = fetch_workspace_users(w.get("id"), headers, users_cache)
        if users is None:
            continue
        admins = [u for u in users if u.get("groupUserAccessRight") == "Admin"]
        if not admins:
            rows.append({"check": "no admin", "item": w.get("name"),
                         "detail": "(workspace has no Admin principal)",
                         "severity": "fix this week"})
        for u in users:
            email = (u.get("emailAddress") or "").lower()
            ident = u.get("identifier") or ""
            right = u.get("groupUserAccessRight") or ""
            external = "#EXT#" in ident.upper() or (
                bool(email) and bool(domain) and not email.endswith("@" + domain))
            if external and right in ("Admin", "Member", "Contributor"):
                rows.append({"check": "external with write access",
                             "item": w.get("name"),
                             "detail": f"{email or ident} ({right})",
                             "severity": "review"})
    for a in org_links:
        sharer = a.get("sharer") or {}
        rows.append({"check": "org-wide share link",
                     "item": a.get("displayName") or a.get("artifactName") or a.get("artifactId"),
                     "detail": sharer.get("emailAddress") or sharer.get("name") or "(unknown sharer)",
                     "severity": "review"})
    for a in published_web:
        sharer = a.get("sharer") or {}
        rows.append({"check": "PUBLISHED TO WEB",
                     "item": a.get("displayName") or a.get("artifactName") or a.get("artifactId"),
                     "detail": sharer.get("emailAddress") or sharer.get("name") or "(unknown sharer)",
                     "severity": "TODAY"})
    return rows


# ---- Output -----------------------------------------------------------------
def write_csv(rows, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = OUT_DIR / f"{name}_{stamp}.csv"
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return path


def notify_teams(webhook, zero_view, orphaned, dead_refresh):
    text = (f"**Inherited-tenant triage**\n\n"
            f"- Zero-view reports: **{len(zero_view)}**\n"
            f"- Orphaned datasets: **{len(orphaned)}**\n"
            f"- Dead refresh schedules: **{len(dead_refresh)}**\n")
    requests.post(webhook, json={"text": text}, timeout=30).raise_for_status()
    print("  Teams notified")


# ---- Demo-data (offline backup; no API calls) -------------------------------
def demo_data():
    zero_view = [
        {"report": "Q3 Sales Final FINAL v2", "workspace": "Finance Ops",
         "workspace_id": "ws1", "dataset_id": "ds1", "modified": "2025-08-14"},
        {"report": "Exec Dashboard (OLD)", "workspace": "Executive",
         "workspace_id": "ws2", "dataset_id": "ds2", "modified": "2025-06-02"},
    ]
    orphaned = [
        {"dataset": "Legacy Corp KPIs", "workspace": "Executive", "workspace_id": "ws2",
         "configured_by": "(none)", "reason": "no owner"},
    ]
    dead_refresh = [
        {"item": "Daily Sales Load", "workspace": "Finance Ops", "workspace_id": "ws1",
         "last_status": "Failed", "configured_by": "departed.user@example.com"},
    ]
    access = [
        {"check": "PUBLISHED TO WEB", "item": "Regional Sales (embed)",
         "detail": "departed.user@example.com", "severity": "TODAY"},
        {"check": "external with write access", "item": "Finance Ops",
         "detail": "partner@vendor.com (Member)", "severity": "review"},
        {"check": "no admin", "item": "Marketing Archive",
         "detail": "(workspace has no Admin principal)", "severity": "fix this week"},
    ]
    return zero_view, orphaned, dead_refresh, access


# ---- Main -------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Triage an inherited Fabric/Power BI tenant.")
    ap.add_argument("--tenant", default=os.environ.get("TENANT_ID"),
                    help="your Entra tenant id (or set TENANT_ID env var). "
                         "Required for live runs; not needed with --demo-data.")
    ap.add_argument("--domain", default=os.environ.get("PBI_DOMAIN"),
                    help="your home tenant domain, e.g. yourcompany.com. Accounts "
                         "outside it are flagged external. Optional.")
    ap.add_argument("--client-id", default=os.environ.get("PBI_CLIENT_ID", DEFAULT_CLIENT_ID),
                    help="app registration client id for auth (defaults to the "
                         "public Azure CLI client; override only if you have your own).")
    ap.add_argument("--days", type=int, default=28, help="activity lookback (max ~28)")
    ap.add_argument("--out", default=os.environ.get("PBI_OUT_DIR", "output"),
                    help="directory for the CSV outputs (or set PBI_OUT_DIR). "
                         "Defaults to ./output. Tip: use a separate dir for "
                         "--demo-data so it does not overwrite a real run.")
    ap.add_argument("--teams-webhook", help="optional Teams Incoming Webhook URL")
    ap.add_argument("--demo-data", action="store_true", help="offline sample run, no API calls")
    ap.add_argument("--access", action="store_true",
                    help="access-exposure sweep only (list 4; skips the activity pull)")
    args = ap.parse_args()

    global OUT_DIR
    OUT_DIR = Path(args.out)

    if args.days > 28:
        print("note: activity history is limited to ~28 days; capping.")
        args.days = 28

    if args.demo_data:
        print("DEMO MODE - offline sample data, no API calls")
        zero_view, orphaned, dead_refresh, access = demo_data()
    else:
        if not args.tenant:
            sys.exit("error: --tenant <YOUR_TENANT_ID> is required for live runs "
                     "(or set the TENANT_ID env var). Use --demo-data for an "
                     "offline sample run.")
        token = get_token(args.tenant, args.client_id)
        headers = {"Authorization": f"Bearer {token}"}
        users_cache: dict = {}
        if args.access:
            print("Access sweep only (list 4; no activity pull)...")
            workspaces = get_workspaces(headers)
            zero_view, orphaned, dead_refresh = [], [], []
        else:
            print("Pulling inventory...")
            workspaces = get_workspaces(headers)
            reports = get_reports(headers)
            datasets = get_datasets(headers)
            refreshables = get_refreshables(headers)
            print(f"Pulling {args.days} days of activity (continuation-token paged)...")
            events = get_activity_events(headers, args.days)
            zero_view, orphaned, dead_refresh = analyze(
                workspaces, reports, datasets, refreshables, events)
            attach_owners(zero_view, headers, users_cache)
            attach_owners(orphaned, headers, users_cache)
            attach_owners(dead_refresh, headers, users_cache)
        print("Access exposure (list 4)...")
        org_links = get_widely_shared(headers, "linksSharedToWholeOrganization")
        published_web = get_widely_shared(headers, "publishedToWeb")
        access = analyze_access(workspaces, headers, users_cache,
                                org_links, published_web, args.domain)

    print("\n=== TRIAGE SUMMARY ===")
    if not (args.access and not args.demo_data):
        p1 = write_csv(zero_view, "zero_view_reports")
        p2 = write_csv(orphaned, "orphaned_datasets")
        p3 = write_csv(dead_refresh, "dead_refresh")
        print(f"Zero-view reports:      {len(zero_view):>5}  -> {p1.name}")
        print(f"Orphaned datasets:      {len(orphaned):>5}  -> {p2.name}")
        print(f"Dead refresh schedules: {len(dead_refresh):>5}  -> {p3.name}")
    p4 = write_csv(access, "access_exposure")
    print(f"Access exposures:       {len(access):>5}  -> {p4.name}")

    if args.teams_webhook and not args.demo_data:
        notify_teams(args.teams_webhook, zero_view, orphaned, dead_refresh)


if __name__ == "__main__":
    main()
