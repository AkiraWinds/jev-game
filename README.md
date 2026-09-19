# jev-game

A minimal Python starter project.

## Jev vs. SLM vs. LLM judge comparison

The runnable comparison app (case generator, judges, FastAPI server) lives
right here on `master`, merged in from
[`feature/jev-mafia-judge-comparison`](https://github.com/AkiraWinds/jev-game/tree/feature/jev-mafia-judge-comparison),
the branch where it was originally built. It pits TypeSafe's Jev model (`Choice` primitive) against
plain OpenAI chat models on the task of picking the killer in a generated
murder-mystery case from character statements and one piece of key
evidence. The comparison started as Jev vs. one large chat model (LLM),
then added a second, smaller chat model (SLM) as a third judge. Three
follow-up case-design variants were each built as their own branch off the
v1 baseline, to keep the experiments independent and avoid confounding
which change caused which effect. Full write-up, prompts, and setup/run/test
instructions are in each branch's own README.

Every row below is one live 10-round, 3-judge run against real APIs
(`jev-latest`, `JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`), played through the actual judges (not
simulated).

| Branch | Commit | Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|---|---|
| [`feature/jev-mafia-judge-comparison`](https://github.com/AkiraWinds/jev-game/commit/b33aae4) | `b33aae4` | **v1 baseline** — killer's statement contains one fact that contradicts an explicit `key_evidence` | **100%** (10/10) | **449 ms** | **90%** (9/10) | **872 ms** | **100%** (10/10) | **1060 ms** |
| [`experiment/red-herring`](https://github.com/AkiraWinds/jev-game/commit/3bb9fcb) | `3bb9fcb` | **v2** — v1 + a non-killer character given a suspicious-looking but irrelevant detail | **100%** | **403 ms** | **100%** | **700 ms** | **100%** | **857 ms** |
| [`experiment/more-characters`](https://github.com/AkiraWinds/jev-game/commit/4667ff9) | `4667ff9` | **v3** — v1 with `CHARACTERS_PER_ROUND` raised from 4 to 6 | **100%** | **389 ms** | **100%** | **718 ms** | **100%** | **858 ms** |
| [`experiment/two-step-evidence`](https://github.com/AkiraWinds/jev-game/commit/f12f800) | `f12f800` | **v4** — `key_evidence` is a neutral fact that only convicts the killer once combined with a separate "connecting fact" in `background` | **100%** (10/10) | **385 ms** | **90%** (9/10) | **705 ms** | **100%** (10/10) | **902 ms** |

**Takeaways across all variants:**
- The small-model judge (SLM) is the only one that ever missed a round: 90%
  (9/10) on both **v1 baseline** and **v4 (two-step evidence)**, while
  matching the large LLM judge's 100% on **v2 (red herring)** and **v3
  (more characters)**. Jev held 100% across every variant.
- A single distractor character (v2) or more suspects to choose from (v3)
  wasn't enough on its own to trip up any judge. The two case designs that
  did produce a gap — v1's straightforward contradiction and v4's two-step
  inference — both did so only for the SLM, not the large LLM.
- Jev was the fastest judge in every single run, typically ~1.6–2.4x faster
  than the LLM judge and consistently faster than the SLM judge too — the
  latency advantage held regardless of case design or which chat models
  were used as SLM/LLM.
- All numbers are single 10-round samples; the SLM's two 90% results (v1,
  v4) are each a single missed round, worth re-running with more
  rounds/seeds before treating any gap as reliable.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in TYPESAFE_API_KEY, OPENAI_API_KEY
```

## Generate scenarios (offline, once)

```bash
python -m jev_game.generate_scenarios --rounds 5
```

## Run the comparison

```bash
uvicorn jev_game.server:app --reload
```

Open http://127.0.0.1:8000 and click "Run next round" to step through the
pre-generated scenarios.

## Test

```bash
pytest
```
