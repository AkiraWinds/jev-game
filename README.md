# jev-game

A minimal Python starter project.

## Jev vs. SLM vs. LLM judge comparison

The runnable comparison app (case generator, judges, FastAPI server) lives
right here on `master`. It pits TypeSafe's Jev model (`Choice` primitive) against
plain OpenAI chat models on the task of picking the killer in a generated
murder-mystery case from character statements and one piece of key
evidence. The comparison started as Jev vs. one LLM vs. a SLM as three judges. Three
follow-up case-design variants were each built as their own branch off the
v1 baseline, to keep the experiments independent and avoid confounding
which change caused which effect. Full write-up, prompts, and setup/run/test
instructions are in each branch's own README.

The **v1 baseline** row below is a batch run of
`python -m jev_game.run_benchmark --repeats 3` against real APIs
(`jev-latest`, `JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`): 30 pre-generated scenarios, each
judge called 3 independent times per scenario (90 rounds/judge total), not
simulated. Latency is reported as p50/p95 in seconds rather than a mean in
milliseconds, since tail latency is what users actually feel and a single
average hides it. **Stability** is the fraction of scenarios where a judge
gave the *same* answer on all 3 independent repeats — a judge that flips
its answer on a fixed input is unreliable even if its accuracy looks fine.
The **v2/v3/v4** rows have all been refreshed onto this same
30-scenario/3-repeat benchmark.

| Branch | Commit | Case design | Scenarios × repeats | Judge | Accuracy | Avg latency | p50 latency | p95 latency | Stability |
|---|---|---|---|---|---|---|---|---|---|
| [`feature/jev-mafia-judge-comparison`](https://github.com/AkiraWinds/jev-game/commit/b33aae4) | `b33aae4` | **v1 baseline** — killer's statement contains one fact that contradicts an explicit `key_evidence` | 30 × 3 (90 rounds/judge) | Jev | **100%** (90/90) | **0.342s** | **0.323s** | **0.421s** | 100% |
| | | | | SLM | 93.3% (84/90) | 0.686s | 0.648s | 0.894s | 80% |
| | | | | LLM | 97.8% (88/90) | 0.872s | 0.856s | 1.037s | 96.7% |
| [`experiment/red-herring`](https://github.com/AkiraWinds/jev-game/commit/d1d44e4) | `d1d44e4` | **v2** — v1 + a non-killer character given a suspicious-looking but irrelevant detail | 30 × 3 (90 rounds/judge) | Jev | **100%** (90/90) | **0.364s** | **0.346s** | **0.477s** | 100% |
| | | | | SLM | 90% (81/90) | 0.702s | 0.683s | 0.889s | 80% |
| | | | | LLM | **100%** (90/90) | 0.912s | 0.878s | 1.142s | 100% |
| [`experiment/more-characters`](https://github.com/AkiraWinds/jev-game/commit/4667ff9) | `4667ff9` | **v3** — v1 with `CHARACTERS_PER_ROUND` raised from 4 to 6 | 30 × 3 (90 rounds/judge) | Jev | **100%** (90/90) | **0.352s** | **0.335s** | **0.437s** | 100% |
| | | | | SLM | 93.3% (84/90) | 0.711s | 0.681s | 0.924s | 80% |
| | | | | LLM | **100%** (90/90) | 0.906s | 0.892s | 1.128s | 100% |
| [`experiment/two-step-evidence`](https://github.com/AkiraWinds/jev-game/commit/ed34948) | `ed34948` | **v4** — `key_evidence` is a neutral fact that only convicts the killer once combined with a separate "connecting fact" in `background` | 30 × 3 (90 rounds/judge) | Jev | **97.8%** (88/90) | **0.345s** | **0.326s** | **0.450s** | 96.7% |
| | | | | SLM | 96.7% (87/90) | 0.736s | 0.710s | 0.949s | 93.3% |
| | | | | LLM | 96.7% (87/90) | 0.882s | 0.857s | 1.034s | 100% |

**Takeaways (all branches, 30 scenarios × 3 repeats):**
- **v1 baseline** — Jev matched the large LLM judge's accuracy (100% vs.
  97.8%) while being roughly 2.5x faster at both p50 and p95, and was the
  only judge with perfect repeated-run stability (100%) — it never flipped
  its answer on a fixed input across 3 independent calls. The small-model
  judge (SLM) was both the least accurate (93.3%) and the least stable
  (80%): on 1 in 5 scenarios it gave a different answer across its 3
  repeats, which the original single-run methodology couldn't have caught.
  The large LLM judge sat between the two: 97.8% accuracy and 96.7%
  stability, at roughly double Jev's latency.
- **v2 — red herring** — the case design with the widest judge spread:
  Jev and the LLM judge both held 100% accuracy and 100% stability, but
  the SLM judge dropped to 90% accuracy (81/90) and 80% stability — a red
  herring distracting a non-killer character was the one variant that
  measurably pulled the SLM judge off the real, checkable contradiction,
  something the original single-run methodology couldn't have caught.
- **v3 — more characters** — with 6 characters/round instead of 4, Jev
  and the LLM judge both held 100% accuracy and 100% stability, while the
  SLM judge saw the same 93.3% accuracy / 80% stability weak spot as on
  the v1 baseline — more characters didn't change which judge struggles.
- **v4 — two-step evidence** — the first case design where Jev's accuracy
  (97.8%) edges out both chat-model judges (96.7% each) instead of tying
  or trailing the LLM judge — splitting `key_evidence` from the
  "connecting fact" in `background` forces a real two-step inference, and
  that extra hop cost the large LLM judge more than it cost Jev. The SLM
  judge was the least stable (93.3%), consistent with its weak spot on
  the other case designs.
- Across all four variants, Jev was the fastest judge on every latency
  metric (avg/p50/p95) and matched or beat both chat-model judges on
  accuracy — the case-design changes moved the SLM and LLM judges' numbers
  around more than they moved Jev's.

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

## Run the batch benchmark

```bash
python -m jev_game.run_benchmark --repeats 3
```

Runs every scenario in `scenarios.json` through all three judges,
`--repeats` times each, and prints accuracy, p50/p95 latency in seconds,
and the repeated-run stability rate per judge. Pass `--json` for machine-
readable output.

## Test

```bash
pytest
```
