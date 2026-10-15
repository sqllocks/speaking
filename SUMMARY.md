# Calendar materials summary

Completed October 15, 2026 (Eastern Time), on `cursor/calendar-materials`.

- Added three session materials pages, abstracts, audiences, objectives, and delivery logs. Inferred content carries `<!-- OWNER: confirm -->`; no slide decks or placeholder PDFs were created. PDF links appear only after a successful PDF response.
- Connected all three talks to their canonical materials URLs and added delivery branding links. Added the existing calendar's NYC and Boston deliveries to their respective session logs with links from their pages.
- Added five verified official conference URLs; recorded sources and unresolved fields in `OWNER-QUESTIONS.md`. Preserved all calendar titles, dates, locations, and JSON field names.
- Added “Materials coming soon” for missing materials in both widget views and made the widget's current date use Eastern Time.
- Generated a 13-entry all-day iCalendar feed, added subscription and speaking-calendar links, and documented regeneration. No session times were assumed. RFC 5545 requires the generation timestamp in UTC; event dates remain Eastern calendar dates.
- Validation: five feed tests, 62 repository links, widget rendering checks, and PDF availability checks pass. CBUS PASS is the sole intentionally empty materials URL.

## Files changed

- `.gitattributes`: preserve RFC 5545 CRLF and intentional whitespace in the feed.
- `README.md`: calendar maintenance instructions.
- `events.json`: three materials URLs and five official conference URLs.
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
- `OWNER-QUESTIONS.md`: questions and official URL evidence.
- `SUMMARY.md`: this record.

## Commands and exit codes

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

## Open questions

See `OWNER-QUESTIONS.md` for full evidence and details:

1. CBUS PASS: actual title and whether materials exist.
2. Confirm all inferred abstract, audience, and learning-objective text for the three new talks.
3. Supply the three slides PDFs when ready.
4. Jacksonville: confirm May 1 delivery versus the official May 2 conference date; the repo date is unchanged.
5. Supply official URLs for Fabric NYC, Hampton Roads, CBUS PASS, and Power BI Days DC; fields remain empty.
6. Confirm the existing MITechCon URL, which returned HTTP 403.
