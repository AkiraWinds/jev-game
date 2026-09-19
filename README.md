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

## Results (v3 — more characters)

Same case-design logic as v1 (one `key_evidence`, the killer's statement
contradicts it, everyone else is consistent), but `CHARACTERS_PER_ROUND`
raised from 4 to 6 in `settings.py`. A batch run of
`python -m jev_game.run_benchmark --repeats 3` against real APIs
(`jev-latest`, `JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`): 30 pre-generated 6-character
scenarios, each judge called 3 independent times per scenario (90
rounds/judge total), not simulated. Latency is reported as p50/p95 in
seconds rather than a mean in milliseconds, since tail latency is what
users actually feel and a single average hides it. **Stability** is the
fraction of scenarios where a judge gave the *same* answer on all 3
independent repeats — a judge that flips its answer on a fixed input is
unreliable even if its accuracy looks fine.

| Scenarios × repeats | Jev | SLM | LLM |
|---|---|---|---|
| 30 × 3 (90 rounds/judge) | acc 100% (90/90) / p50 0.335s / p95 0.437s / stability 100% | acc 93.3% (84/90) / p50 0.681s / p95 0.924s / stability 80% | acc 100% (90/90) / p50 0.892s / p95 1.128s / stability 100% |

**Takeaways:**
- Accuracy stayed at 100% for both Jev and the large LLM judge even with 6
  suspects instead of 4 (a 16.7% random-guess floor vs. 25% before) — the
  "fair play" clue design is robust to more characters for the stronger
  judges.
- The small-model judge (SLM) was both the least accurate (93.3%, missing
  6/90) and the least stable (80%): on 1 in 5 scenarios it gave a different
  answer across its 3 repeats, which the original single-run methodology
  couldn't have caught.
- Jev matched the large LLM judge's accuracy and stability (both 100%)
  while being roughly 2.5x faster at both p50 and p95 — the same pattern
  seen on the v1 baseline, now confirmed to hold with 6 characters/round
  too.
- Making the case harder via raw character count doesn't widen the
  Jev-vs-chat-model accuracy gap for the stronger judges; the SLM is the
  one that struggles, and a red herring or a two-fact clue is a more
  promising lever to try next for stressing Jev and the LLM specifically.

## Test

```bash
pytest
```
