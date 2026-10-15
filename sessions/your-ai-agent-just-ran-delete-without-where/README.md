# Your AI Agent Just Ran DELETE Without WHERE. Now What?

A speaking session by **Jonathan Stewart** · [sqlbites.net](https://sqlbites.net)

## Abstract

Your AI agent deleted 1,943,200 rows. Not because it was malicious — because in a documented March 2026 incident, a developer gave an agent a routine AWS cleanup task, it substituted terraform destroy for the instructed CLI commands without asking, and a production database vanished. No confirmation prompt fired. No override path existed. The model’s guardrails didn’t catch it.

This session is for SQL Server DBAs, Fabric administrators, and data engineers who are already deploying — or being asked to deploy — AI agents against production data systems.

The fix is not better prompting. It is infrastructure enforcement. The destructive command gate is a Claude Code hook that intercepts tool calls before execution and hard-blocks dangerous operations regardless of what the model decided: DELETE without WHERE, DROP TABLE, terraform destroy, git push --force to main, rm -rf, and .env edits. Six operation categories. No override path. No reasoning around it. For Fabric and SQL Server environments, this means agent-initiated SQL executions, schema modifications, and Lakehouse destructive actions are intercepted — not just shell commands. The gate adds under 100 milliseconds to any tool call — imperceptible against the model’s own response time — and zero false positives across a tested corpus of common operations including softDelete patterns, TRUNCATE in datetime functions, and git rebase. The agent hits a wall only when it should.

Live demo: watch the gate fire mid-session on a real DELETE attempt. The session continues from control, not recovery.

You’ll leave with:

- A working hook pattern deployable on your Fabric and SQL Server estate today
- A threat model for AI agents with live data access — what breaks and how
- The implementation distinction between soft guardrails (model training) and hard blocks (infrastructure enforcement)
- The architectural principle: intercept between model decision and tool execution — the hook point differs by framework, the principle does not

## Session

MITechCon 2026 · Thursday, 2026-10-29 · 10:00 AM Eastern · 60 minutes · Room C

## Slides

Slides will be posted after the session.

## Deliveries

See [deliveries.md](deliveries.md).
