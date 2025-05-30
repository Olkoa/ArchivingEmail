from dotenv import load_dotenv
import os
# test normal API calls
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


if __name__ == "__main__":
    # Example usage
    openrouter_llm_api_call(
        system_prompt="You are a helpful assistant.",
        user_prompt="What is the capital of Madagascar?"
    )
