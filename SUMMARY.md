# Calendar materials summary

Completed October 15, 2026 (Eastern Time), on `cursor/calendar-materials`.

- All 13 calendar entries now link to materials, including CBUS PASS's confirmed Translytical session. Both Translytical deliveries share one session folder with per-event branding.
- Applied the Owner's Jacksonville date correction to May 2, 2026 in the calendar, delivery log, and session page. Added Owner-supplied NYC, Hampton Roads, and CBUS event URLs; the NYC URL is explicitly recorded as not fetched.
- Copied the full Translytical abstract verbatim from the CBUS Meetup page into its README and landing page. Rewrote its audience and four objectives with confirmation markers. Removed inferred abstracts, audiences, and objectives for Observability and AI Agent; both now say “Abstract coming soon.”
- Added the three Power BI Days DC times and rooms (EDT) to their session delivery logs. No JSON fields were added; Power BI Days DC conference URLs remain empty.
- Retained the widget's materials fallback and Eastern current date, the subscription and speaking-calendar links, and the standard-library all-day iCalendar feed. Owner-confirmed talk times are documented in delivery logs; the feed remains all-day under the existing JSON contract.
- Moved resolved owner questions to an Answered section dated October 15, 2026. Open questions are listed below.

## Files changed

- `.gitattributes`: preserve RFC 5545 CRLF and intentional whitespace in the feed.
- `README.md`: calendar maintenance instructions.
- `events.json`: materials and official event URLs, confirmed CBUS title, and Jacksonville date correction.
- `events-widget.js`: missing-materials display and Eastern date calculation.
- `index.html`: three catalog links, speaking calendar, subscription.
- `events.ics`: generated calendar feed.
- `scripts/build_ics.py`: standard-library generator, stable UIDs, text escaping, UTF-8 folding, inclusive date-range conversion.
- `scripts/test_build_ics.py`: independent feed parsing and round-trip validation.
- `scripts/check_links.py`: calendar URL and local session HTML link validation.
- `sessions/observability-for-microsoft-fabric/README.md`
- `sessions/observability-for-microsoft-fabric/deliveries.md`
- `sessions/observability-for-microsoft-fabric/index.html`
- `sessions/your-ai-agent-just-ran-delete-without-where/README.md`
- `sessions/your-ai-agent-just-ran-delete-without-where/deliveries.md`
- `sessions/your-ai-agent-just-ran-delete-without-where/index.html`
- `sessions/translytical-task-flows/README.md`
- `sessions/translytical-task-flows/deliveries.md`
- `sessions/translytical-task-flows/index.html`
- `sessions/your-warehouse-your-semantic-model/deliveries.md`
- `sessions/your-warehouse-your-semantic-model/index.html`
- `sessions/building-scalable-data-warehouses/deliveries.md`
- `sessions/building-scalable-data-warehouses/index.html`
- `sessions/stop-borrowing-contoso/deliveries.md`: Power BI Days DC time and room.
- `sessions/governance-as-code/deliveries.md`: Power BI Days DC time and room.
- `OWNER-QUESTIONS.md`: questions and official URL evidence.
- `SUMMARY.md`: this record.

## Initial implementation commands and exit codes

Multiline inspection/research commands are grouped below by purpose; HTTP outcomes are separate from the successful Python process exit code. No credentials were printed.

| Command / operation | Exit code | Result |
|---------------------|-----------|--------|
| `pwd`, `rg --files` for instructions, `ls -a /workspace` | 0 (combined inspection) | Repo absent; located workspace. |
| `cat /etc/codex/network-policy.json`; optional `ls /AGENTS.md /workspace/AGENTS.md` | 0 / 2 | Read network policy; no parent instructions present. |
| `git clone https://github.com/sqllocks/speaking.git /workspace/speaking` | 0 | Created local checkout. |
| `git fetch origin && git checkout -B cursor/calendar-materials origin/main` | 0 | Required starting branch operation. |
| `rg --files`, `cat`, `find`, `rg -n`, `sed -n` repository inspections | 0 | Read root docs/data/widget/catalog, both requested session folders, scanner, and delivery/link conventions. |
| `command -v pdftotext`; `pdftotext` for both requested session PDFs | 0 | Inspected existing published materials. |
| Python standard-library public URL research and HTML text/link extraction | 0 | Verified official URLs; sqlbites.net and MITechCon returned 403, attempted Power BI Days site returned 503; public searches did not verify remaining groups. Evidence recorded in owner questions. |
| `python /tmp/add_calendar_pages.py` | 0 | Created pages/logs; updated calendar/widget/catalog and delivery links. |
| Shell here-documents for scripts, questions, root README, and summary; `mkdir -p scripts` | 0 | Wrote requested files. |
| `python scripts/build_ics.py` | 0 | Generated 13 events. |
| `python scripts/test_build_ics.py` | 0 | Five tests passed, including committed feed, escaping/folding, UIDs, and date boundaries. |
| `python scripts/check_links.py` | 0 | 62 links checked, one pending materials entry, zero errors. |
| `node --check events-widget.js` | 0 | Syntax valid. |
| `node /tmp/verify_calendar.js` | 0 | VM rendering checks: both widget views, materials fallback, Eastern date boundary, and absent/published PDFs for all three new pages. |
| Python inline negative link-checker checks | 0 | Rejected missing files, repository escapes, external session URLs; accepted queries/fragments. |
| `TZ=America/New_York date '+%Y-%m-%d %H:%M:%S %Z'` | 0 | Confirmed Eastern reporting date. |
| Python cleanup of generated `scripts/__pycache__` | 0 | Removed generated bytecode. |
| `git diff --stat`, `git diff`, `git status --short` | 0 | Reviewed changes. |
| Initial `git diff --cached --check` | 2 | Flagged required CRLF in `events.ics`; added a feed-specific `.gitattributes` rule to preserve calendar bytes. |
| Final `git diff --check`; `git diff --cached --check` | 0 | No whitespace errors with the calendar format declared. |
| `git add` (only listed task files) | 0 | Staged calendar changes. |
| `git commit -m "calendar: connect talks to materials and add subscription feed"` | 0 | Committed task changes. |
| `git push -u origin cursor/calendar-materials` | 0 | Published only the requested branch; no force push, tags, or PR. |

## Owner-answer follow-up — 2026-10-15 (Eastern Time)

Changed in this follow-up: `events.json`, `events.ics`, `OWNER-QUESTIONS.md`, `SUMMARY.md`; README and index for Translytical, Observability, and AI Agent; Translytical delivery log; warehouse delivery log and index; and the Stop Borrowing Contoso, Governance as Code, and Your Warehouse delivery logs.

| Command / operation | Exit code | Result |
|---------------------|-----------|--------|
| `git status --short`; `git branch --show-current`; `cat` / `rg -n` inspections | 0 | Clean requested branch; read current calendar materials and owner records. |
| `cat /etc/codex/network-policy.json`; `git fetch origin`; `git rev-list --left-right --count HEAD...origin/cursor/calendar-materials` | 0 | Read network policy; fetched without changing branches; local and remote branch aligned. |
| Python urllib CBUS Meetup fetch and HTML / embedded JSON extraction | 0 | HTTP 200; extracted the full description, not its truncated structured-data preview. NYC was not fetched. |
| `python /tmp/apply_owner_answers.py` | 0 | Applied owner answers; asserted the README abstract equals the fetched source verbatim. |
| `python /tmp/update_owner_records.py` | 0 | Updated answered questions, URL provenance, and summary. |
| `python scripts/build_ics.py` | 0 | Rebuilt all 13 entries with corrected dates, titles, and URLs. |
| `python -B scripts/test_build_ics.py` | 0 | All five feed tests passed. |
| `python -B scripts/check_links.py` | 0 | 64 repository links checked; zero missing materials URLs and zero errors. |
| Python inline content / JSON contract assertions | 0 | All entries have materials URLs, JSON keys unchanged, unpublished abstracts replaced by placeholders. |
| `git diff --stat`; `git diff`; `git diff --check`; `git diff --cached --check` | 0 | Reviewed changes and whitespace. |
| `git add` (the 16 follow-up files listed above) | 0 | Staged only the owner-answer changes. |
| `git commit -m "calendar: apply owner answers and confirm session details"` | 0 | Committed on `cursor/calendar-materials`. |
| `git push -u origin cursor/calendar-materials` | 0 | Updated only the requested branch; no force push, tags, or PR. |

## Open questions

1. Send the submitted abstracts for Observability and AI Agent.
2. Confirm the Translytical audience and objectives.
3. Should the NYC calendar title match the possibly different event-page title? The current title is preserved.
4. Provide the official Power BI Days DC event URL.
5. Supply slides for the three new session folders.
6. Confirm the existing MITechCon URL, previously blocked by HTTP 403.
