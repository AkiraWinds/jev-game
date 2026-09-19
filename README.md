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

| Case design | Jev accuracy | Jev avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|
| v0 — killer's statement just "subtly evasive" (no explicit checkable clue) | 40–50% | 815 ms* | 40–50% | 841 ms* |
| **v1 — killer's statement contains one fact that contradicts an explicit `key_evidence`** | **100%** | **388 ms** | **100%** | **701 ms** |

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

## Results (v5 — three-way judge: Jev vs SLM vs LLM)

Same v1 case design (`scenarios.json`, one `key_evidence` fact the killer's
statement contradicts) and the same 10 pre-generated rounds used for v1, but
`judge_llm.py` now serves two separate judges off one shared client instead
of one, and a third judge was added to `round_runner.py`/`Scoreboard`. One
live run against real APIs (`jev-latest`, `JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`), played through `round_runner.run_round`
(not simulated):

| Judge | Accuracy | Avg latency |
|---|---|---|
| **Jev** (`Choice` primitive) | **100%** (10/10) | **449 ms** |
| SLM (`gpt-5.4-nano-2026-03-17`) | 90% (9/10) | 872 ms |
| LLM (`gpt-5.4-2026-03-05`) | 100% (10/10) | 1060 ms |

**Takeaways:**
- This is the first run where three-way comparison itself (not a harder
  case design) separated the judges: the small chat model missed one round
  that both Jev and the large chat model got right, on identical input.
- Jev was faster than *both* chat models here - not just the small one -
  roughly 2× faster than the SLM and 2.4× faster than the LLM, while
  matching the LLM's accuracy exactly.
- The SLM's miss is a single round out of 10 - suggestive of a real
  capability gap between the small and large chat model on this task, but
  not conclusive on this sample size; worth re-running with more rounds.
- This result is orthogonal to the v2/v3/v4 case-design experiments on the
  other branches (which only ever compared Jev vs. one LLM judge) - adding
  a small model as a third judge is a separate lever from making the case
  itself harder, and the two can be combined in a future variant.

## Test

```bash
pytest
```
