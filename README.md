# nuzantara-showroom

Bali Zero's **public** showroom repository. Capabilities from our internal platform are moved here one at a time, as an act of transparency: anyone can see how we build, without exposing production systems.

## Publication Rules

Only what is safe to be public goes into this repo. Every PR must pass this checklist:

1. **No secrets.** No credentials, API keys, tokens, internal URLs, or `.env` contents. Use `.env.example` with empty values.
2. **No real data.** No client data, real names, or production documents. Synthetic sample material only.
3. **No production map.** No line numbers, internal commit hashes, production collection or database names, or Dockerfile details. Refer to modules by name only.
4. **No internal people or tickets.** Write "pending review", not a colleague's name or an internal PR/ticket number.
5. **When in doubt, leave it out.** If you are unsure whether a detail may be public, remove it and ask in the PR.

## Structure

- `docs/capabilities/<unit>/`: the contract (`CONTRACT.md`), dependencies (`DEPENDENCIES.md`), and code provenance (`PROVENANCE.md`) for each capability.

## Unit Status

| Unit | Latest gate |
|---|---|
| pengetahuan-jawaban-bersumber (sourced answers) | G2 (dependencies) — approved 14 Oct 2026 |
