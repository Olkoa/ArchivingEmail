from dotenv import load_dotenv
import os
import json

from openai import OpenAI


def openrouter_llm_api_call(
    system_prompt: str = "",
    user_prompt : str = "Result of 2+2 ?",
    assistant_prompt: str = "",
    model: str ="openai/gpt-4o",
    env_var_open_router_base_url: str = "OPENAI_BASE_URL", # "OPENROUTER_BASE_URL",
    env_var_open_router_api_key: str = "OPENAI_API_KEY" # "OPENROUTER_API_KEY"
    ):
    """

    Function to execute API calls with Openrouter using the OpenAI chat completions API.
    This function sets up an OpenAI client with OpenRouter credentials and makes a chat completion
    request using the specified model and prompts.

    Basically you need a .env file with the OPENROUTER_BASE_URL and OPENROUTER_API_KEY vars set.

    Args:
        system_prompt (str, optional): The system message to set context. Defaults to "".
        user_prompt (str, optional): The user message/query. Defaults to "Result of 2+2 ?".
        assistant_prompt (str, optional): The assistant's previous message for context. Defaults to "".
        model (str, optional): The model identifier to use. Defaults to "openai/gpt-4o".
        env_var_open_router_base_url (str, optional): Environment variable name for OpenRouter base URL.
            Defaults to "OPENROUTER_BASE_URL".
        env_var_open_router_api_key (str, optional): Environment variable name for OpenRouter API key.
            Defaults to "OPENROUTER_API_KEY".
    Returns:
        str: The content of the model's response message.
    Requires:
        - python-dotenv
        - openai
    Environment Variables:
        - OPENROUTER_BASE_URL: The base URL for OpenRouter API
        - OPENROUTER_API_KEY: The API key for OpenRouter authentication
    """

    # Load environment variables from .env
    load_dotenv()

    # Get base URL and API key
    base_url = os.getenv(env_var_open_router_base_url)
    api_key = os.getenv(env_var_open_router_api_key)

    # Optional user identifier
    username = os.getenv("USER")

    # Initialize OpenAI client
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    # Prepare common arguments
    request_args = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_prompt}
        ]
    }

    # Conditionally add user ID if it exists
    if username:
        print(username)
        request_args["extra_headers"] = {"HTTP-Referer": username, "X-Title": username}

    # Make the API call
    completion = client.chat.completions.create(**request_args)

    print(completion.choices[0].message.content)
    return completion.choices[0].message.content

def openrouter_llm_api_call_with_historic(
    user_key: str,
    project_name: str,
    system_prompt: str = "",
    user_prompt: str = "",
    model: str = "openai/gpt-4o",
    env_var_open_router_base_url: str = "OPENAI_BASE_URL",
    env_var_open_router_api_key: str = "OPENAI_API_KEY",
    history_file_path: str = "historic.json",
    max_history_messages: int = 20
) -> (str, None):
    """
    Make a chat completion call to OpenRouter, storing and retrieving conversation history
    per user/project in a JSON file.

    Args:
        user_key: Identifier for the user (e.g., username or user ID).
        project_name: Identifier for the project under that user.
        system_prompt: Optional system message.
        user_prompt: The user’s new message.
        model: The model identifier to use.
        env_var_open_router_base_url: Environment var for base URL.
        env_var_open_router_api_key: Environment var for API key.
        history_file_path: Path to the JSON file storing histories.
        max_history_messages: Maximum number of messages in the history to keep (oldest dropped).

    Returns:
        assistant_content: The assistant’s response text.
    """

    load_dotenv()
    base_url = os.getenv(env_var_open_router_base_url)
    api_key = os.getenv(env_var_open_router_api_key)
    if not base_url or not api_key:
        raise ValueError("OPENROUTER_BASE_URL or OPENROUTER_API_KEY environment variable not set")

    client = OpenAI(base_url=base_url, api_key=api_key)

    # Compute the key used in the JSON file
    hist_key = f"{user_key}:{project_name}"

    # Load existing histories JSON (if exists)
    
    if os.path.exists(history_file_path):
        with open(history_file_path, "r", encoding="utf-8") as f:
            all_histories = json.load(f)
    else:
        all_histories = {}

    # Get the history list for this user/project
    history = all_histories.get(hist_key, [])

    # Add system prompt if provided (and if starting fresh or if you want repeat each time)
    if system_prompt:
        # Optionally include system prompt only once or always; here we include each time
        history.append({"role": "system", "content": system_prompt})

    # Add user message
    history.append({"role": "user", "content": user_prompt})

    # Trim if too many messages
    if len(history) > max_history_messages:
        history = history[-max_history_messages:]

    request_args = {
        "model": model,
        "messages": history,
        "user": hist_key  # optional: pass user identifier to the API for abuse tracking etc.
    }

    # Optional extra headers (if you still want them)
    username = os.getenv("USER")
    if username:
        request_args["extra_headers"] = {"HTTP-Referer": username, "X-Title": username}

    completion = client.chat.completions.create(**request_args)
    assistant_content = completion.choices[0].message.content

    # Append assistant response to history
    history.append({"role": "assistant", "content": assistant_content})

    # Trim again, if needed
    if len(history) > max_history_messages:
        history = history[-max_history_messages:]

    # Store back the updated history
    all_histories[hist_key] = history
    # Ensure directory exists

    hist_dir = os.path.dirname(history_file_path)
    if hist_dir:                      # seulement si on a un dossier dans le chemin
        os.makedirs(hist_dir, exist_ok=True)

    with open(history_file_path, "w", encoding="utf-8") as f:
        json.dump(all_histories, f, indent=2, ensure_ascii=False)

    # Return the assistant answer
    print(assistant_content)
    return assistant_content


if __name__ == "__main__":
    # Example usage
    openrouter_llm_api_call(
        system_prompt="You are a helpful assistant.",
        user_prompt="What is the capital of Madagascar?"
    )
