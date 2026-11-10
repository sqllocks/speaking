"""Small helpers for the Fabric REST API (no third-party packages).

Auth: set FABRIC_TOKEN to a bearer token, or sign in with the Azure CLI (`az login`)
and this module asks the CLI for a token for https://api.fabric.microsoft.com.
Never put a token in a file or commit one.
"""
import base64
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request

BASE = "https://api.fabric.microsoft.com/v1"


def get_token():
    token = os.environ.get("FABRIC_TOKEN")
    if token:
        return token
    az = shutil.which("az")
    if not az:
        raise SystemExit("No FABRIC_TOKEN set and the Azure CLI (az) was not found. Run `az login` or set FABRIC_TOKEN.")
    out = subprocess.run(
        [az, "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, timeout=60,
    )
    if out.returncode != 0 or not out.stdout.strip():
        raise SystemExit("az could not give a token: " + out.stderr.strip())
    return out.stdout.strip()


def call(token, url, method="GET", body=None):
    """Returns (status, headers, bytes). Does not raise on HTTP errors."""
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    elif method == "POST":
        data = b""
    req = urllib.request.Request(
        url, method=method, data=data,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def wait_for(token, headers, timeout_s=600, poll_s=5):
    """Wait for a long-running operation (HTTP 202 + Location header). Returns the final status string."""
    loc = headers.get("Location") or headers.get("location")
    if not loc:
        return "no-location"
    end = time.time() + timeout_s
    while time.time() < end:
        time.sleep(poll_s)
        status = json.loads(call(token, loc)[2]).get("status")
        if status not in ("Running", "NotStarted", "InProgress"):
            return status
    return "timeout"


def b64(text):
    return base64.b64encode(text.encode()).decode()


def ipynb_definition(notebook_json_text):
    """Item definition for creating or updating a notebook from .ipynb text."""
    return {"format": "ipynb",
            "parts": [{"path": "notebook-content.ipynb", "payload": b64(notebook_json_text), "payloadType": "InlineBase64"}]}


def one_cell_notebook(code):
    """A minimal notebook with one code cell. `source` must be a list of strings (Fabric rejects a plain string)."""
    return json.dumps({
        "nbformat": 4, "nbformat_minor": 5,
        "cells": [{"cell_type": "code", "id": "cell0001", "source": code.splitlines(True),
                   "metadata": {}, "outputs": [], "execution_count": None}],
        "metadata": {"language_info": {"name": "python"}, "kernel_info": {"name": "jupyter"},
                     "microsoft": {"language": "python", "language_group": "jupyter_python"}},
    })


def pipeline_definition(activities):
    payload = json.dumps({"properties": {"activities": activities}})
    return {"parts": [{"path": "pipeline-content.json", "payload": b64(payload), "payloadType": "InlineBase64"}]}


def find_item(token, workspace_id, name, item_type):
    status, _, body = call(token, f"{BASE}/workspaces/{workspace_id}/items")
    if status != 200:
        raise SystemExit(f"Listing items failed ({status}): {body[:300]!r}")
    for item in json.loads(body)["value"]:
        if item["displayName"] == name and item["type"] == item_type:
            return item["id"]
    return None


def create_or_update(token, workspace_id, name, item_type, definition):
    """Create the item if it does not exist, otherwise replace its definition. Returns the item id."""
    item_id = find_item(token, workspace_id, name, item_type)
    if item_id is None:
        status, headers, body = call(token, f"{BASE}/workspaces/{workspace_id}/items", "POST",
                                     {"displayName": name, "type": item_type, "definition": definition})
        if status == 202:
            wait_for(token, headers)
            item_id = find_item(token, workspace_id, name, item_type)
        elif status in (200, 201):
            item_id = json.loads(body).get("id")
        else:
            raise SystemExit(f"Create {name} failed ({status}): {body[:300]!r}")
        print(f"created {item_type} {name}")
    else:
        status, headers, body = call(token, f"{BASE}/workspaces/{workspace_id}/items/{item_id}/updateDefinition",
                                     "POST", {"definition": definition})
        if status == 202:
            wait_for(token, headers)
        elif status != 200:
            raise SystemExit(f"Update {name} failed ({status}): {body[:300]!r}")
        print(f"updated {item_type} {name}")
    return item_id


def run_notebook(token, workspace_id, item_id, timeout_s=900):
    """Start a notebook run and wait for it. Returns the final status."""
    status, headers, body = call(token, f"{BASE}/workspaces/{workspace_id}/items/{item_id}/jobs/instances?jobType=RunNotebook", "POST")
    if status != 202:
        raise SystemExit(f"Could not start the run ({status}): {body[:300]!r}")
    return wait_for(token, headers, timeout_s=timeout_s, poll_s=10)
