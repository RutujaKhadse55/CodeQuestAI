# Backend — Phase 0 report (Foundation, Contracts, Fakes)

## Sandbox decision (plan §6 P0 item 5) — `python scripts/sandbox_check.py`
| Machine | native | docker | Result |
|---|---|---|---|
| Backend dev laptop (Windows 11, Python 3.12) | NO — no `resource` module, cannot apply rlimits | NOT VERIFIED — Docker 29.5.3 installed, Docker Desktop daemon not running | **Decision: Docker for everyone** (plan risk #9: any Windows machine ⇒ Docker/WSL for all) |

Action: start Docker Desktop and re-run `scripts/sandbox_check.py` (pulls `python:3.11-slim`) to confirm.
Each teammate should run the script on their own machine and add a row here.

## Open items needing a human
- Ask organisers whether reading the learner's own LeetCode page is acceptable (plan §1.6, risk #2). Not done.
- GitHub repo branch protection (PR required, 0 approvals) must be set in GitHub settings.
- Replace `@TODO-*` handles in `.github/CODEOWNERS`.
- Contract freeze announcement at T+0:40 and acks from AI / Agents / Frontend.
