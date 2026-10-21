# nuzantara-showroom

Bali Zero's **public** showroom repository. Capabilities from our internal platform are moved here one at a time, as an act of transparency: anyone can see how we build, without exposing production systems.

## Publication Rules

Only what is safe to be public goes into this repo. Every PR must pass this checklist:

1. **No secrets.** No credentials, API keys, tokens, internal URLs, or `.env` contents. Use `.env.example` with empty values.
2. **No real data.** No client data, real names, or production documents. Synthetic sample material only.
3. **No production map.** No line numbers, internal commit hashes, production collection or database names, or Dockerfile details. Refer to modules by name only. Carve-out: code carried verbatim keeps its upstream identifiers (it is checksum-pinned in each unit's `verbatim.sha256`); the rule applies in full to everything written for this repo — docs, comments, scripts, tests.
4. **No internal people or tickets.** Write "pending review", not a colleague's name or an internal PR/ticket number.
5. **When in doubt, leave it out.** If you are unsure whether a detail may be public, remove it and ask in the PR.

## Structure

- `docs/capabilities/<unit>/`: the contract (`CONTRACT.md`), dependencies (`DEPENDENCIES.md`), and code provenance (`PROVENANCE.md`) for each capability.
- `backend/`: code carried from the internal platform for the capabilities below (verbatim where possible; rewritten files are listed in each unit's `PROVENANCE.md`).
- `showroom/`: thin adapters written for this repo.
- `corpus/`: synthetic sample documents only (3 **fictional** village regulations).
- `scripts/`, `tests/`: setup, acceptance tests, calibration and receipts.

## Unit Status

| Unit | Latest gate |
|---|---|
| pengetahuan-jawaban-bersumber (sourced answers) | G3 (carry + adapter) and G4 preparation — merged 20 Oct 2026 · G4 clean-clone check passed in `mock-only` and `lexical` modes (16 Oct 2026) · `openai` mode and threshold calibration — pending (needs a showroom-only API key) |

## Capability 1 — pengetahuan → jawaban bersumber (sourced answers)

Contract, dependencies and provenance: `docs/capabilities/pengetahuan-jawaban-bersumber/`.

### Prerequisites

- Python ≥ 3.10 (measured: 3.14.6 on macOS 12.7.6, Intel), `git`, `curl`.
- No Docker needed: the official Qdrant binary is run locally by `scripts/qdrant_local.sh`
  (bound to 127.0.0.1 only, data under `.showroom-data/`).
- Network on first setup: PyPI, the Qdrant release on GitHub, and the tiktoken encoding download.
- `OPENAI_API_KEY` only for `openai` mode (calibration and closing A1/A2). Put it in `.env`, never commit it.

### Setup from a clean clone

The block between the markers below is what the G4 check runs as-is, so this README is the source of the setup.

<!-- setup:start -->
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -q -r requirements-dev.txt
[ -e .env ] || cp .env.example .env
export TIKTOKEN_CACHE_DIR="$PWD/.showroom-data/tiktoken"
.venv/bin/python scripts/smoke_import.py
scripts/qdrant_local.sh start
```
<!-- setup:end -->

### Running

| Goal | Command | Evidence produced |
|---|---|---|
| Mock tests (no services) | `.venv/bin/python scripts/receipt.py` | receipt `mock-only` |
| Real Qdrant, lexical embeddings | `SHOWROOM_INTEGRATION=1 .venv/bin/python scripts/receipt.py` | receipt `lexical` |
| Full run, real OpenAI embeddings | `set -a; . ./.env; set +a; SHOWROOM_INTEGRATION=1 SHOWROOM_EMBEDDINGS=openai .venv/bin/python scripts/receipt.py` | receipt `openai` (closes A1/A2) |
| Threshold calibration | `SHOWROOM_EMBEDDINGS=openai .venv/bin/python scripts/calibrate.py` | `.showroom-data/calibration-*.json` |
| Stop Qdrant | `scripts/qdrant_local.sh stop` | — |

A receipt (`.showroom-data/receipts/<commit>-<mode>.json`) is only valid when the tree is clean and every test passes.
Mock ≠ integration ≠ direct observation: read `limitations` in every receipt.
