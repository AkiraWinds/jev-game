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

## Results (v1 / baseline)

Two live runs against real APIs (`jev-latest`, `GENERATOR_MODEL=gpt-4.1` (later
`gpt-5.6-terra`), `JUDGE_LLM_MODEL=gpt-4.1-mini`), 10 rounds each, played
through the actual server + judges (not simulated):

| Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|
| v0 — killer's statement just "subtly evasive" (no explicit checkable clue) | 40–50% | 815 ms* | — | — | 40–50% | 841 ms* |
| **v1 — killer's statement contains one fact that contradicts an explicit `key_evidence`** | **100%** | **388 ms** | — | — | **100%** | **701 ms** |

\* v0's latency numbers also predate a fix: both judge clients were being
re-created per round (fresh TCP/TLS handshake each time), which added fixed
overhead that shrank the visible gap between the two models. v1's numbers
are measured after switching to one long-lived client per process.

**Takeaways:**
- v0's "vague vs. confident tone" tell was too soft — both models were only
  marginally better than the 25% random-guess floor (4 suspects/round).
- Making the clue a concrete, checkable contradiction (a real "fair play"
  whodunit clue, not a stylistic hint) took both judges to 100% accuracy on
  this batch — the puzzle became reliably solvable, which is good for
  validating the design, but it's now too easy to show an *accuracy*
  difference between Jev and the LLM judge on this size of case.
- The **latency** gap held up once measurement overhead was removed: Jev
  runs roughly 2× faster than the LLM judge per round.
- Open question for future variants: can a harder case (more characters, a
  red herring, or a clue that needs two facts combined) create a real
  accuracy gap between a calibrated `Choice` judge and a chat LLM judge,
  without regressing to unsolvable-by-either?

## Results (v4 — two-step evidence)

v1's `key_evidence` directly named an impossible time/place for the killer,
which both judges solved at 100% accuracy - too easy to show a real gap. This
variant changes `case_generator.py`'s prompt so `key_evidence` is a standalone,
neutral fact (a sensor log, a door counter) that never names or implicates
anyone, and `background` separately states a load-bearing "connecting fact"
(e.g. the crime scene has exactly one entrance). The killer's statement only
contradicts the evidence once both facts are combined - a real two-step
inference, not a one-line lookup.

Two live runs against real APIs, 10 rounds each, played through the actual
judges (not simulated), scenarios saved to `scenarios_two_step.json`: a first
run with just Jev vs. one LLM judge (`GENERATOR_MODEL=gpt-4.1`,
`JUDGE_LLM_MODEL=gpt-4.1-mini`), then a second run through the full 3-judge
`round_runner.run_round` (`jev-latest`, `JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`) on the same 10 pre-generated scenarios:

| Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|
| v1 — one-step: key_evidence directly contradicts the killer's claim | 100% | 388 ms | — | — | 100% | 701 ms |
| v4 — two-step, Jev vs. LLM only | 100% (10/10) | 380 ms | — | — | 90% (9/10) | 618 ms |
| **v4 — two-step, three-way (Jev vs. SLM vs. LLM)** | **100%** (10/10) | **385 ms** | **90%** (9/10) | **705 ms** | **100%** (10/10) | **902 ms** |

Example case (round 2, "The Last Signal"): the signal room "could be opened
only with a brass key held by Rowan Vale" (the connecting fact, stated in
`background`); `key_evidence` says "The brass key was recorded turning in
the signal room lock at 10:14 p.m." - a neutral lock log that names no one.
The killer, Rowan Vale, claims "At 10:14 p.m., the brass key was hanging on
the sauna's hook beside me" - only provably false once you combine the lock
log (the key was in the door, not the sauna, at that exact time) with the
connecting fact (only Rowan held that key). Jev and the large chat model
both caught this; the SLM judge picked the wrong suspect (Tomas Reed) on
this round.

**Takeaways:**
- The two-step design produced the first real accuracy gap between Jev and
  a plain chat LLM judge on this project (Jev vs. LLM only run): Jev stayed
  at 100% while the LLM dropped to 90% (missed 1/10), on the same case
  difficulty.
- Re-running with the actual production judge models (`gpt-5.4-2026-03-05`
  as LLM, `gpt-5.4-nano-2026-03-17` as SLM) shifted where the gap shows up:
  the large model recovered to 100%, matching Jev exactly, while the small
  model was the one that missed a round (90%, 1/10) - so on this batch the
  accuracy gap tracks model size (small vs. large chat model) rather than
  being a fixed property of the two-step case design itself.
- This is a single 10-round sample per run, so these gaps are suggestive,
  not conclusive - worth re-running with more rounds or more seeds before
  treating them as reliable, and results can shift meaningfully between
  model versions (see the two different judge-model pairs used above).
- Latency ordering held across all three: Jev was fastest in both runs, and
  in the three-way run the SLM was faster than the LLM but still ~1.8x
  slower than Jev.
- Inspecting individual cases (e.g. round 2 above) confirms the generator is
  actually producing two-step clues as designed, not accidentally leaking a
  one-step tell - `key_evidence` alone never names a character or states an
  impossibility.
## Test

```bash
pytest
```
