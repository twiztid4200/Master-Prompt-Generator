# MASTER AWAKENING Command Center — Dashboard MVP

Local-first observability layer. Not an agent. Does not execute commands, call providers, or write to the repository.

## Architecture

- Single static page at `dashboard/index.html`
- Navigation sections: Overview, Roadmap, Agent Operations, Income & Resources, Knowledge & Research, Karma ArKade
- Mobile-first CSS (tested conceptually at 390×844 and 1280×800)
- Dark technical theme with accent colors for status

## Data

- Baseline records in `data/baseline.json` (labeled from main@4c30b03 history)
- Read-only fetch of known factory run logs (`../factory/runs/*.json`)
- User edits (tasks, notes) persist in browser `localStorage` under key `master-awakening-dashboard-v1`
- No backend, no database, no authentication

## Security

- No API keys or secrets in browser
- Factory log ingestion is read-only fetch of static JSON
- No shell execution, no repository writes, no external paid services from the UI
- Verification requires explicit evidence reference; marking a task complete does not auto-set verified
- Mock vs live distinguished by `live` flag and provider field in run logs

## Run locally

From the repository root:

```
python3 -m http.server 8000
```

Then open http://localhost:8000/dashboard/

## Acceptance notes

Existing factory tests remain unchanged. Dashboard is additive and does not modify the prompt-generator site.

Baseline items marked UNKNOWN or NEEDS VERIFICATION lack independent confirmation in the current tree.
