# Backend — Phase 0 report (Foundation, Contracts, Fakes)

## Sandbox decision (plan §6 P0 item 5) — `python scripts/sandbox_check.py`
| Machine | native | docker | Result |
|---|---|---|---|
| Backend dev laptop (Windows 11, Python 3.12) | NO — no `resource` module, cannot apply rlimits | **OK** — Docker 29.5.3; `--network none --memory 256m --cpus 1 --pids-limit 64 --read-only` hello-world ran | **Decision: Docker for everyone** (plan risk #9: any Windows machine ⇒ Docker/WSL for all) |

Compose check: `docker compose build && up` works (backend image fixed: build context is repo root; compose runs `MOCK=1` until real routers land); `scripts/smoke.sh` returned SMOKE_OK against the container.
Each teammate should run the script on their own machine and add a row here.

## Open items needing a human
- Ask organisers whether reading the learner's own LeetCode page is acceptable (plan §1.6, risk #2). Not done.
- GitHub repo branch protection (PR required, 0 approvals) must be set in GitHub settings.
- Replace `@TODO-*` handles in `.github/CODEOWNERS`.
- Contract freeze announcement at T+0:40 and acks from AI / Agents / Frontend.

## Contract-freeze announcement (draft, post at T+0:40)
> Backend: contracts frozen. `backend/app/contracts/` (models, protocols, enums) and `openapi.yaml` are final; additive optional fields only from now, each acked by producer + consumer. `make mock` serves examples. Sandbox mode: Docker for everyone (`python scripts/sandbox_check.py`). Please ack: AI ✅/❌, Agents ✅/❌, Frontend ✅/❌.
