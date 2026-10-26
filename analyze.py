#!/usr/bin/env python3
"""
Post call pass. Turns a transcript note into the five gates, objections, buying
signals and a draft follow up. Uses OpenRouter (DeepSeek v4 pro by default).

  python analyze.py "/path/to/transcript.md"
"""
import argparse, os, sys, requests
from dotenv import load_dotenv

load_dotenv()

PROMPT = """You are analysing a discovery call transcript.
The call is in Taglish (English and Tagalog mixed). Do not translate quotes, keep them verbatim.

Return Markdown with exactly these sections:

## Qualifying gates
For each of the five gates, mark ANSWERED or MISSED and quote the evidence:
1. Decision maker, 2. Volume of inquiries, 3. Budget, 4. Timeline, 5. Current system.

## Objections raised
Every objection, quoted verbatim, with your one line read on what is really behind it.

## Buying signals
Quoted, strongest first.

## What you promised
Anything committed to on the call. This is what the follow up must deliver.

## Next actions
Short imperative bullets.

## Draft follow up message
Written in the prospect's own register and vocabulary, Taglish if they spoke Taglish.
Never use dashes of any kind. Keep it under 200 words.

TRANSCRIPT:
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("note")
    ap.add_argument("--model", default=os.getenv("ANALYSIS_MODEL", "deepseek/deepseek-v4-pro"))
    a = ap.parse_args()

    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        sys.exit("Set OPENROUTER_API_KEY in .env first.")
    text = open(a.note, encoding="utf-8").read()

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": a.model,
              "messages": [{"role": "user", "content": PROMPT + text}]},
        timeout=180,
    )
    r.raise_for_status()
    out = r.json()["choices"][0]["message"]["content"]

    with open(a.note, "a", encoding="utf-8") as f:
        f.write("\n\n---\n\n# Call Analysis\n\n" + out + "\n")
    print(out)
    print(f"\nAppended to {a.note}")


if __name__ == "__main__":
    main()
