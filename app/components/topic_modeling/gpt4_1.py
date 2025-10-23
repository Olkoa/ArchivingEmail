import json
from collections import defaultdict
from openai import OpenAI

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-"
,  # Replace with your actual API key
)

# Load sampled documents
def load_sampled_docs(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# Build the full summarization prompt
def build_prompt(docs):
    prompt_parts = [
        "You are given emails grouped by topic ID.",
        "Each topic has several sample emails.",
        "Summarize what each topic is mainly about, based on these emails in a single short sentence and in French.",
        "Return your answer as a JSON object like:",
        '{ "0": "Summary of topic 0...", "1": "Summary of topic 1...", ... }',
        "",
        "Topics and emails:"
    ]

    # Iterate through topics and add emails to the prompt
    for topic_id, emails in docs.items():
        prompt_parts.append(f"[Topic {topic_id}]")
        for email in emails[:10]:  # limit to 10 per topic
            prompt_parts.append(f"- {email[:1500]}")  # clip long emails
        prompt_parts.append("")  # spacing between topics

    return "\n".join(prompt_parts)

# Ask the model to summarize topics
def summarize_all_topics(sampled_json_path, output_path):
    docs = load_sampled_docs(sampled_json_path)
    
    # Build the prompt
    prompt = build_prompt(docs)
    
    print(f"Prompt length: {len(prompt.split())} words")

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-5-mini",
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

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"✅ Topic summaries saved to {output_path}")

summarize_all_topics("split_1.json","topic_summaries.json")
summarize_all_topics("split_2.json","topic_summaries2.json")