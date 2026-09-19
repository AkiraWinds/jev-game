"""Environment configuration for the mafia-judge comparison game."""

import os

from dotenv import load_dotenv

load_dotenv()

TYPESAFE_API_KEY = os.environ.get("TYPESAFE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

JEV_MODEL = os.environ.get("JEV_MODEL", "jev-latest")

# Generator and Judge B are deliberately different OpenAI models: the judge
# should not be evaluating text written by its own weights/style.
GENERATOR_MODEL = os.environ.get("GENERATOR_MODEL", "gpt-4.1")
JUDGE_LLM_MODEL = os.environ.get("JUDGE_LLM_MODEL", "gpt-4.1-mini")

SCENARIOS_PATH = os.environ.get("SCENARIOS_PATH", "scenarios.json")
