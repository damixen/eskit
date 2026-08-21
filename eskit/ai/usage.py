def print_usage(response, model):

    cost_map = {
        "claude-sonnet-4-6":{
            "input":3.00,
            "output":15.00
        },
        "claude-sonnet-5":{
            "input":2.00,
            "output":10.00
        },
        "claude-haiku-4-5-20251001":{
            "input":1.00,
            "output":5.00
        }
    }

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    print()
    print("# Usage ---")
    print(f"- **Input tokens:**  {input_tokens}")
    print(f"- **Output tokens:** {output_tokens}")

    input_cost = (
        input_tokens / 1_000_000
    ) * cost_map[model]["input"]

    output_cost = (
        output_tokens / 1_000_000
    ) * cost_map[model]["output"]

    print(
        f"- **Estimated cost with model:**{model}: ${input_cost + output_cost:.6f}"
    )
    print()