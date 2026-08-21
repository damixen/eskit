import json
import os
from dotenv import load_dotenv 
from anthropic import Anthropic
from eskit.ai.usage import print_usage


SYSTEM_PROMPT = """
You are an AI assistant for ESKit.

You help users understand how to use the ESKit command-line interface.

The ESKit command description below is the authoritative source for
available commands, arguments, options, and their meanings.

When answering a question about how to perform an operation:
- Explain the relevant command briefly.
- Provide the complete ESKit command when possible.
- Do not execute commands.
- Do not invent commands or options that are not present in the command description.
- Respect safety metadata and explain destructive operations when relevant.

ESKit command description:

"""


def ask(question, command_description, model):

    if not question:
        return "no question asked."

    load_dotenv()

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = SYSTEM_PROMPT + json.dumps(
        command_description,
        indent=2,
    )

    response = client.messages.create(
        model=model,
        max_tokens=10000,
        system=prompt,
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ],
    )

    print_usage(response, model)

    for block in response.content:
        if block.type == "text":
            return block.text

    return response.content[0].text