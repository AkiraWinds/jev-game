# jev-game

A minimal Python starter project, now home to a small experiment comparing
TypeSafe's Jev model against two plain chat models - a small one (SLM) and
a large one (LLM) - as judges.

## Jev vs SLM vs LLM: Mafia judge comparison

Each round is a full whodunit case, designed offline before the server ever
runs:

1. **Case design** (`case_generator.py`) — an OpenAI model (`GENERATOR_MODEL`)
   invents an original background, victim, 4 characters (with a role,
   relationship to the victim, and motive each), one piece of independent
   **key evidence**, a ground-truth killer, and each character's true
   timeline. The killer's true timeline is written to directly conflict with
   the key evidence — a "fair play" whodunit clue (present, checkable, but
   not spelled out) rather than a stylistic tell. Setting seeds
   (`settings.py`) are generic mystery tropes, not text from any specific
   existing book/show/film.
2. **Statement writing** (`generator.py`) — the same model then writes what
   each character actually says: all four statements equally specific and
   confident in tone, but the killer's contains one concrete factual claim
   that contradicts the key evidence.
3. Both steps are cached to `scenarios.json`.

At play time, three independent judges each see the case background,
victim, key evidence, character bios, and statements (never the
ground-truth killer or true timeline) and try to pick the killer:

- **Jev** (`Choice` primitive) — a calibrated probability per suspect
- **A small OpenAI chat model** (`JUDGE_SLM_MODEL`) — prompted for the same
  pick + a self-reported confidence
- **A large OpenAI chat model** (`JUDGE_LLM_MODEL`) — same prompt, bigger
  model

`GENERATOR_MODEL`, `JUDGE_SLM_MODEL`, and `JUDGE_LLM_MODEL` are deliberately
three different models so no judge is ever evaluating text written by its
own weights/style.

All three are timed independently per round; a web page shows a running
accuracy and average-latency comparison across all three.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in TYPESAFE_API_KEY, OPENAI_API_KEY
```

### Generate scenarios (offline, once)

```bash
python -m jev_game.generate_scenarios --rounds 5
```

### Run the comparison

```bash
uvicorn jev_game.server:app --reload
```

Open http://127.0.0.1:8000 and click "Run next round" to step through the
pre-generated scenarios.

## Results (v2 — red herring)

Branch `experiment/red-herring`: same v1 pipeline, but `case_generator.py`
now also designs a `red_herring` — a non-killer character is given a
suspicious-looking but irrelevant detail (a public argument with the
victim, a secret grudge, a strong motive) that has no bearing on the
`key_evidence` contradiction, and `generator.py` makes that character raise
or defend the detail in their own statement. A batch run of
`python -m jev_game.run_benchmark --repeats 3` against real APIs
(`jev-latest`, `GENERATOR_MODEL=gpt-4.1`,
`JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`, `JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`):
30 scenarios (10 original + 20 freshly generated through the same
red-herring case-design path), each judge called 3 independent times per
scenario (90 rounds/judge total), not simulated. Latency is reported as
p50/p95 in seconds rather than a mean in milliseconds, since tail latency is
what users actually feel and a single average hides it. **Stability** is
the fraction of scenarios where a judge gave the *same* answer on all 3
independent repeats — a judge that flips its answer on a fixed input is
unreliable even if its accuracy looks fine.

| Scenarios × repeats | Jev | SLM | LLM |
|---|---|---|---|
| 30 × 3 (90 rounds/judge) | acc 100% (90/90) / p50 0.346s / p95 0.477s / stability 100% | acc 90% (81/90) / p50 0.683s / p95 0.889s / stability 80% | acc 100% (90/90) / p50 0.878s / p95 1.142s / stability 100% |

**Takeaways:**
- Adding a red herring did not create an accuracy gap for Jev or the LLM
  judge: both correctly cross-checked every statement against
  `key_evidence` and ignored the suspicious-but-irrelevant character across
  all 90 rounds (100% accuracy, 100% stability).
- The SLM judge was the one to slip: 90% accuracy (81/90) and only 80%
  stability — on a meaningful share of scenarios it either picked the
  distractor character outright or flipped its answer across repeats on
  the same fixed input, something the original single-run methodology
  couldn't have caught.
- The latency ordering held regardless of accuracy: Jev fastest (p50
  0.346s), then SLM (p50 0.683s), then LLM slowest (p50 0.878s) — Jev's
  ~2.5x speed advantage over the LLM judge held up on this harder case
  design, while also being the more reliable judge than the SLM.
- Still an open question: whether a harder distractor (e.g. a red herring
  that itself weakly conflicts with a *secondary* piece of evidence, or
  multiple red herrings, or requiring two facts to be combined to solve the
  case) would widen the SLM's accuracy/stability gap further.

## Test

```bash
pytest
```
