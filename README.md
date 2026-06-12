# sqllocks/speaking

Public, durable home for the slides and handouts from sessions taught by **Jonathan Stewart** ([sqlbites.net](https://sqlbites.net)).

Hosted at: **https://sqllocks.github.io/speaking/**

## Structure

```
sessions/                     ← one canonical version per session (source of truth)
  fabric-fast-track/
    index.html                ← the deck
    handouts/                 ← workbook, quick-ref card, calculators
    README.md                 ← abstract, audience, learning objectives
    deliveries.md             ← log of where/when this session has been taught
```

## Why this structure

A session may be taught at many conferences. Conferences are **deliveries** of a session, not owners of the slides. The session folder is the single source of truth; conference branding is layered on at view time via `?event=<slug>` so the canonical URL stays stable forever.

## Per-delivery URLs

Each deck reads an `event` query-string parameter and looks up the conference name from an inline config inside the HTML.

| Canonical (no event)                            | Per-delivery                                                       |
|-------------------------------------------------|--------------------------------------------------------------------|
| `…/sessions/fabric-fast-track/`                 | `…/sessions/fabric-fast-track/?event=raleigh-dod-2026`             |

Adding a new conference = one line in the `events` map at the top of each deck. No fork, no copy.

## Footer convention

Every deck shows: **Jonathan Stewart · sqlbites.net**.

When `?event=<slug>` is present, the conference name and date are appended.

## Adding a new session

1. `cp -R sessions/_template sessions/<new-slug>` *(template TBD)*
2. Fill in `README.md`, drop slides at `index.html`, add handouts.
3. Link the session from the top-level `index.html` catalog.

## Adding a new delivery to an existing session

1. Add a row to that session's `deliveries.md`.
2. Add a line to the `events` map inside the session's `index.html`.
3. Share `…/<session>/?event=<slug>`.
