"""Environment configuration for the mafia-judge comparison game."""

import os

from dotenv import load_dotenv

load_dotenv()

TYPESAFE_API_KEY = os.environ.get("TYPESAFE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

JEV_MODEL = os.environ.get("JEV_MODEL", "jev-latest")

# Generator and the two chat-model judges are deliberately different OpenAI
# models from each other: no judge should be evaluating text written by its
# own weights/style. JUDGE_SLM_MODEL is a small model, JUDGE_LLM_MODEL a
# large one - together with Jev, that's a 3-way judge comparison.
GENERATOR_MODEL = os.environ.get("GENERATOR_MODEL", "gpt-4.1")
JUDGE_SLM_MODEL = os.environ.get("JUDGE_SLM_MODEL", "gpt-4.1-nano")
JUDGE_LLM_MODEL = os.environ.get("JUDGE_LLM_MODEL", "gpt-4.1")

SCENARIOS_PATH = os.environ.get("SCENARIOS_PATH", "scenarios.json")
