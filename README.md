# jev-game

A minimal Python starter project.

## Jev vs. LLM judge comparison

The runnable comparison app (case generator, judges, FastAPI server) lives
on [`feature/jev-mafia-judge-comparison`](https://github.com/AkiraWinds/jev-game/tree/feature/jev-mafia-judge-comparison),
not on `master`. It pits TypeSafe's Jev model (`Choice` primitive) against a
plain OpenAI chat model on the task of picking the killer in a generated
murder-mystery case from character statements and one piece of key
evidence. Three follow-up case-design variants were each built as their own
branch off that baseline, to keep the experiments independent and avoid
confounding which change caused which effect. Full write-up, prompts, and
setup/run/test instructions are in each branch's own README.

| Branch | Commit | Case design | Jev accuracy | Jev avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|
| [`feature/jev-mafia-judge-comparison`](https://github.com/AkiraWinds/jev-game/commit/aa1b32fd22975281ea2e8a214a5b185ffadc5e2f) | `aa1b32f` | v1 baseline — killer's statement contains one fact that contradicts an explicit `key_evidence` | 100% | 388 ms | 100% | 701 ms |
| [`experiment/red-herring`](https://github.com/AkiraWinds/jev-game/commit/d82f2a870883d7704a4b42bb2e27aa2864efc9c5) | `d82f2a8` | v2 — v1 + a non-killer character given a suspicious-looking but irrelevant detail | 100% | 385 ms | 100% | 712 ms |
| [`experiment/more-characters`](https://github.com/AkiraWinds/jev-game/commit/796900823d7b97f001697e186fc766dddd0c4c96) | `7969008` | v3 — v1 with `CHARACTERS_PER_ROUND` raised from 4 to 6 | 100% | 422 ms | 100% | 727 ms |
| [`experiment/two-step-evidence`](https://github.com/AkiraWinds/jev-game/commit/7bdff5c5d8806d9efbf4845cb8edf22110f9c54c) | `7bdff5c` | v4 — `key_evidence` is a neutral fact that only convicts the killer once combined with a separate "connecting fact" in `background` | **100%** (10/10) | 380 ms | **90%** (9/10) | 618 ms |

All four rows are one live 10-round run each against real APIs (`jev-latest`,
`GENERATOR_MODEL=gpt-4.1`, `JUDGE_LLM_MODEL=gpt-4.1-mini`), not simulated.

**Takeaways across all variants:**
- Only **v4 (two-step evidence)** produced a real accuracy gap: Jev held
  100% while the plain chat LLM judge dropped to 90% (missed 1/10 rounds).
  Making the killer's contradiction require combining two separate facts,
  rather than a one-line lookup, was the one lever (of the three tried) that
  actually separated the two judges.
- **v2 (red herring)** and **v3 (more characters)** each left both judges at
  100% — a single distractor character, or more suspects to choose from,
  wasn't enough on its own to make the puzzle harder in a way that mattered
  to either model.
- Jev was consistently ~1.6-2x faster than the LLM judge across every
  variant, regardless of case difficulty.
- v4's 90% vs. 100% is a single 10-round sample (one missed round) — worth
  re-running with more rounds/seeds before treating the gap as reliable,
  and a natural next step if this comparison continues.

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
