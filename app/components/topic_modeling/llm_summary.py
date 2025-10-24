import json
from collections import defaultdict
from openai import OpenAI
import os

from dotenv import load_dotenv
load_dotenv()

ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

# Initialize OpenRouter client
client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY,
)

# Load sampled documents
def load_sampled_docs(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# Build the full summarization prompt
def build_prompt(docs):
    prompt_parts = [
    "You are given groups of emails, each associated with a unique topic ID.",
    "Each topic contains multiple sample emails.",
    "Your task is to summarize the **main idea** or **distinct concern** of each topic in **one concise sentence** in **French**.",
    "Ensure that each summary is **unique** and clearly **distinguishes** the topic from the others, avoiding generic or repetitive phrases.",
    "Focus on the **most important or recurring themes** in the emails for each topic.",
    "Return your answer as a JSON object, like this:",
    '{ "0": "Résumé du sujet 0...", "1": "Résumé du sujet 1...", ... }',
    "",
    "Here are the topics and their associated emails:"
]


    # Iterate through topics and add emails to the prompt
    for topic_id, emails in docs.items():
        prompt_parts.append(f"[Topic {topic_id}]")
        for email in emails[:100]:  # limit to 10 per topic
            prompt_parts.append(f"- {email}")  # clip long emails
        prompt_parts.append("")  # spacing between topics

    return "\n".join(prompt_parts)

# Ask the model to summarize topics
def summarize_all_topics(sampled_json_path, output_path="topic_summariesllm.json"):
    docs = load_sampled_docs(sampled_json_path)
    #print(docs)
    
    # Build the prompt
    prompt = build_prompt(docs)
    
    print(f"Prompt length: {len(prompt.split())} words")

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
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
        print('exepttt')
        print(summaries)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"✅ Topic summaries saved to {output_path}")


