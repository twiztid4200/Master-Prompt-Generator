# MASTER AWAKENING

The public site is a static prompt library: 500 prompts in 20 categories. Prompt text now lives in `data/prompts.json`. `index.html` loads that file and keeps the existing browse, favorites, random, copy, mobile drawer, and Grok deep-link behavior.

The local factory is a separate Phase 1 loop:

```
python3 -m factory awaken "Analyze the MASTER AWAKENING repository and determine the best architecture for evolving it into an AI Agent Factory."
```

It plans with one Scout and one Verifier, reads public GitHub metadata, writes a markdown discovery and a run log, then stops. It does not implement the Scout recommendation in the same run.

## Implemented

- Prompt library extracted and still counted at 500 / 20
- Agent, workflow, report, verdict, run, and tool schemas
- Agent contracts for architect, scout, and verifier
- Provider interface and mock provider
- Read-only GitHub tool
- CLI mission, markdown memory, run log
- Tests in `tests/test_factory.py`

## Not implemented

- No license file. The owner has not approved one.
- No hosted API and no browser-side model calls
- No real model provider. The mock reports token usage as unavailable.
- No MCP server, no REA install, no binary analysis
- No swarm and no recursive loop beyond one iteration

## Test

```
python3 -m unittest discover -s tests -v
```

Requires Python 3.10 or newer. No third-party packages.

## REA

See `docs/rea-evaluation.md`. REA is not a dependency of this repository.


## Phase 1.1

Search matches category title and description only. It is case-insensitive substring matching, not prompt-text search and not fuzzy search.

Hard limits default to 0.05 USD, 20,000 input tokens, 4,000 output tokens, 60 seconds, 6 provider calls, and 2 retries. A missing token count is null, not zero.

No live model key was present in this environment. The HTTP adapter is tested with an injected transport. A live-model mission was not run.

Local rollback tag `phase1-rollback-d8a0d7e` points at `d8a0d7ecd1652f635f3660f61e640e48ab238a52` and is not pushed.
