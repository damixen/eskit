import ollama
import json

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

    print("model:", model)

    prompt = SYSTEM_PROMPT + json.dumps(
        command_description,
        indent=2,
        )

    #print("prompt:", prompt)

    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    return response["message"]["content"]