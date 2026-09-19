# jev-game

A minimal Python starter project.

## Jev vs. SLM vs. LLM judge comparison

The runnable comparison app (case generator, judges, FastAPI server) lives
on [`feature/jev-mafia-judge-comparison`](https://github.com/AkiraWinds/jev-game/tree/feature/jev-mafia-judge-comparison),
not on `master`. It pits TypeSafe's Jev model (`Choice` primitive) against
plain OpenAI chat models on the task of picking the killer in a generated
murder-mystery case from character statements and one piece of key
evidence. The comparison started as Jev vs. one large chat model (LLM),
then added a second, smaller chat model (SLM) as a third judge. Three
follow-up case-design variants were each built as their own branch off the
v1 baseline, to keep the experiments independent and avoid confounding
which change caused which effect. Full write-up, prompts, and setup/run/test
instructions are in each branch's own README.

Every row below is one live 10-round run against real APIs, played through
the actual judges (not simulated); "—" means that judge didn't exist yet
for that run.

| Branch | Commit | Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|---|---|
| [`experiment/red-herring`](https://github.com/AkiraWinds/jev-game/commit/aa1b32fd22975281ea2e8a214a5b185ffadc5e2f) | `aa1b32f` | v0 — killer's statement just "subtly evasive" (no explicit checkable clue) | 40–50% | 815 ms* | — | — | 40–50% | 841 ms* |
| [`experiment/two-step-evidence`](https://github.com/AkiraWinds/jev-game/commit/aa1b32fd22975281ea2e8a214a5b185ffadc5e2f) | `aa1b32f` | v1 baseline (2-judge) — killer's statement contains one fact that contradicts an explicit `key_evidence` | 100% | 388 ms | — | — | 100% | 701 ms |
| [`feature/jev-mafia-judge-comparison`](https://github.com/AkiraWinds/jev-game/commit/c5a3077eaf84ecc40eefa39647b90f555c129031) | `c5a3077` | **v1 baseline, 3-judge** (`JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`, `JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`) | **100%** (10/10) | **449 ms** | **90%** (9/10) | **872 ms** | **100%** (10/10) | **1060 ms** |
| [`experiment/red-herring`](https://github.com/AkiraWinds/jev-game/commit/d82f2a870883d7704a4b42bb2e27aa2864efc9c5) | `d82f2a8` | v2 — v1 + a non-killer character given a suspicious-looking but irrelevant detail (2-judge) | 100% | 385 ms | — | — | 100% | 712 ms |
| [`experiment/red-herring`](https://github.com/AkiraWinds/jev-game/commit/de9f89fc1203deeac0a4ececd59ae7d27501fc13) | `de9f89f` | **v2, 3-judge** (`JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`, `JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`) | **100%** | **403 ms** | **100%** | **700 ms** | **100%** | **857 ms** |
| [`experiment/more-characters`](https://github.com/AkiraWinds/jev-game/commit/a370609c8d12e06456199789a381f828156e9783) | `a370609` | **v3** — v1 with `CHARACTERS_PER_ROUND` raised from 4 to 6, 3-judge | **100%** | **389 ms** | **100%** | **718 ms** | **100%** | **858 ms** |
| [`experiment/two-step-evidence`](https://github.com/AkiraWinds/jev-game/commit/7bdff5c5d8806d9efbf4845cb8edf22110f9c54c) | `7bdff5c` | v4 — `key_evidence` is a neutral fact that only convicts the killer once combined with a separate "connecting fact" in `background` (2-judge) | **100%** (10/10) | 380 ms | — | — | **90%** (9/10) | 618 ms |
| [`experiment/two-step-evidence`](https://github.com/AkiraWinds/jev-game/commit/bb0193d6841a2efcbd6da79ee19de3d14962c89a) | `bb0193d` | **v4, 3-judge** (`JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`, `JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`) | **100%** (10/10) | **385 ms** | **90%** (9/10) | **705 ms** | **100%** (10/10) | **902 ms** |

\* v0's latency numbers predate a fix where both judge clients were being
re-created per round (fresh TCP/TLS handshake each time), which added fixed
overhead that shrank the visible gap between models. All later rows are
measured after switching to one long-lived client per process.

**Takeaways across all variants:**
- Across the **2-judge (Jev vs. LLM only)** runs, only **v4 (two-step
  evidence)** produced a real accuracy gap: Jev held 100% while the LLM
  judge dropped to 90% (missed 1/10). **v2 (red herring)** and **v3 (more
  characters)** left both judges at 100% — a single distractor character,
  or more suspects to choose from, wasn't enough on its own to make the
  puzzle harder in a way that mattered to either model.
- Adding a **third, small-model judge (SLM, `gpt-5.4-nano-2026-03-17`)**
  turned out to be the more reliable way to expose an accuracy gap: it
  missed 1/10 rounds on both the v1 baseline and v4 (90%), while matching
  the large model at 100% on v2 and v3.
- **v4 (two-step evidence)** is the only case design that produced an
  accuracy gap under both the 2-judge and 3-judge setups, making it the
  most consistently "harder" variant tried so far.
- Jev was the fastest judge in every single run, typically ~1.6–2.4x faster
  than the LLM judge and consistently faster than the SLM judge too — the
  latency advantage held regardless of case design, judge count, or which
  chat models were used as SLM/LLM.
- All numbers are single 10-round samples; the SLM's 90% on v1 baseline and
  v4 are each a single missed round, worth re-running with more
  rounds/seeds before treating any gap as reliable.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
python -m jev_game.main
```

## Test

```bash
pip install pytest
pytest
```
