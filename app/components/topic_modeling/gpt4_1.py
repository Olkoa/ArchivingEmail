import json
from pathlib import Path
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODULE_DIR = Path(__file__).resolve().parent


def _initialize_client() -> OpenAI:
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(base_url=base_url, api_key=api_key)


def _load_sampled_docs(filepath: Path | str):
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_prompt(docs):
    prompt_parts = [
        "You are given emails grouped by topic ID.",
        "Each topic has several sample emails.",
        "Summarize what each topic is mainly about, based on these emails in a single short sentence and in French.",
        "Return your answer as a JSON object like:",
        '{ "0": "Summary of topic 0...", "1": "Summary of topic 1...", ... }',
        "",
        "Topics and emails:"
    ]

    for topic_id, emails in docs.items():
        prompt_parts.append(f"[Topic {topic_id}]")
        for email in emails[:10]:
            prompt_parts.append(f"- {email[:1500]}")
        prompt_parts.append("")

    return "\n".join(prompt_parts)


def summarize_all_topics(sampled_json_path: Path, output_path: Path, client: OpenAI | None = None):
    docs = _load_sampled_docs(sampled_json_path)
    prompt = _build_prompt(docs)

    print(f"Prompt length: {len(prompt.split())} words")

    client = client or _initialize_client()

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
    except Exception as e:
        print("❌ API call failed:", e)
        return

    if not completion or not completion.choices:
        print("⚠️ No response returned from model.")
        return

    response = completion.choices[0].message.content

    try:
        summaries = json.loads(response)
    except json.JSONDecodeError:
        print("⚠️ Model did not return valid JSON. Saving raw output.")
        summaries = {"raw_response": response}

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"✅ Topic summaries saved to {output_path}")


def summarize_topics():
    split_1 = MODULE_DIR / "split_1.json"
    split_2 = MODULE_DIR / "split_2.json"
    summaries_1 = MODULE_DIR / "topic_summaries.json"
    summaries_2 = MODULE_DIR / "topic_summaries2.json"

    client = _initialize_client()
    summarize_all_topics(split_1, summaries_1, client)
    summarize_all_topics(split_2, summaries_2, client)
