# jev-game

A minimal Python starter project, now home to a small experiment comparing
TypeSafe's Jev model against two plain chat models - a small one (SLM) and
a large one (LLM) - as judges.

## Jev vs SLM vs LLM: Mafia judge comparison

Each round is a full whodunit case, designed offline before the server ever
runs:

1. **Case design** (`case_generator.py`) — an OpenAI model (`GENERATOR_MODEL`)
   invents an original background, victim, `CHARACTERS_PER_ROUND` characters
   (currently 6; with a role, relationship to the victim, and motive each),
   one piece of independent **key evidence**, a ground-truth killer, and each
   character's true timeline. The killer's true timeline is written to
   directly conflict with the key evidence — a "fair play" whodunit clue
   (present, checkable, but not spelled out) rather than a stylistic tell.
   Setting seeds (`settings.py`) are generic mystery tropes, not text from
   any specific existing book/show/film.
2. **Statement writing** (`generator.py`) — the same model then writes what
   each character actually says: all statements equally specific and
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

## Results (v3 — more characters)

Same case-design logic as v1 (one `key_evidence`, the killer's statement
contradicts it, everyone else is consistent), but `CHARACTERS_PER_ROUND`
raised from 4 to 6 in `settings.py`. v1 was played before the third judge
(SLM) existed, so its row leaves that column blank; v3 is played with all
three judges live, using `JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17` and
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`. Runs against real APIs, 10 rounds
each, played through `round_runner.run_round` (not simulated):

| Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|
| v1 — 4 characters/round | 100% | 388 ms | — | — | 100% | 701 ms |
| **v3 — 6 characters/round** | **100%** | **389 ms** | **100%** | **718 ms** | **100%** | **858 ms** |

**Takeaways:**
- Accuracy stayed at 100% for all three judges even with 6 suspects instead
  of 4 (a 16.7% random-guess floor vs. 25% before) — the "fair play" clue
  design from v1 is robust to more characters, so raw character count alone
  still doesn't create a measurable accuracy gap between any of the three
  judges on `gpt-5.4-nano`/`gpt-5.4`.
- An earlier run of this same batch against `gpt-4.1-nano` as the SLM did
  show a gap (70% accuracy, missing 3/10), so the accuracy ceiling here is
  sensitive to which small model is used — `gpt-5.4-nano` closes the gap
  that `gpt-4.1-nano` opened on the identical 6-character case design.
- Jev's latency held steady versus v1; both chat judges got slower on
  `gpt-5.4-nano`/`gpt-5.4` than on `gpt-4.1-nano`/`gpt-4.1-mini`, widening
  the Jev-vs-chat-model latency gap to roughly 1.8–2.2×.
- **Offline case generation itself did get noticeably more expensive**: 10
  rounds of case+statement generation (2 OpenAI calls/round) took ~4m30s
  wall-clock (~27s/round) with 6 characters — expected, since the generator
  model now has to invent and hold consistent 6 motives/relationships/
  timelines instead of 4. This cost is paid once offline into
  `scenarios.json` and never touches judge-vs-judge timing, but it's a real
  cost if scenario count grows.
- Confirms the same open question from v1: making the case harder via raw
  character count doesn't widen the Jev-vs-LLM accuracy gap; a red herring or
  a two-fact clue is still the more promising lever to try next.

## Test

```bash
pytest
```
