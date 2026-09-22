from pathlib import Path
import re


def get_field(text: str, name: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(name)}:\s*(.+?)\s*$",
        text,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def get_usage_field(text: str, name: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(name)}:\s*(.+?)\s*$",
        text,
        re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def convert_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    #print("text:", text)

    question = None
    elapsed = None
    input_tokens = None
    output_tokens = None
    cost = None

    # -------------------------
    # Format 1: --- Test ---
    # -------------------------
    if "--- Test ---" in text and "--- Response ---" in text:
        test_section, response = text.split(
            "--- Response ---", 1
        )

        model = get_field(test_section, "Model")
        question = get_field(test_section, "Question")
        elapsed = get_field(test_section, "Elapsed time")

        # Remove redundant model line from response.
        if model:
            response = re.sub(
                rf"^\s*model:\s*{re.escape(model)}\s*\n?",
                "",
                response,
                count=1,
                flags=re.IGNORECASE | re.MULTILINE,
            )

    # -------------------------
    # Format 2: --- Usage ---
    # -------------------------
    elif "--- Usage ---" in text:
        print("usage")
        usage_section, response = text.split(
            "--- Usage ---", 1
        )

        # Model may be in the usage line itself:
        # Estimated cost with model:claude-haiku...: $0.027050
        model_match = re.search(
            r"Estimated cost with model\\?:\s*([^:]+):",
            response,
            re.IGNORECASE,
        )

        model = model_match.group(1).strip() if model_match else ""

        input_tokens = get_usage_field(response, "Input tokens")
        output_tokens = get_usage_field(response, "Output tokens")

        cost_match = re.search(
            r"Estimated cost with model\\?:[^:]+:\s*\$([0-9.]+)",
            response,
            re.IGNORECASE,
        )
        cost = f"${cost_match.group(1)}" if cost_match else ""

        # Remove usage section from response.
        response = response.strip()

        # Remove usage metadata from the response.
        response = re.sub(
            r"^\s*Input tokens:.*$\n?",
            "",
            response,
            flags=re.MULTILINE,
        )
        response = re.sub(
            r"^\s*Output tokens:.*$\n?",
            "",
            response,
            flags=re.MULTILINE,
        )
        response = re.sub(
            r"^\s*Estimated cost with model\\?:.*$\n?",
            "",
            response,
            flags=re.MULTILINE,
        )

    else:
        print(f"Skipping unknown format: {path}")
        return

    response = response.strip()

    # -------------------------
    # Build Markdown
    # -------------------------

    lines = ["# Test", ""]

    if model:
        lines.append(f"- **Model:** {model}")

    if question:
        lines.append(f"- **Question:** {question}")

    if elapsed:
        lines.append(f"- **Elapsed time:** {elapsed}")

    if input_tokens:
        lines.append(f"- **Input tokens:** {input_tokens}")

    if output_tokens:
        lines.append(f"- **Output tokens:** {output_tokens}")

    if cost:
        lines.append(f"- **Estimated cost:** {cost}")

    lines.extend(
        [
            "",
            "## Response",
            "",
            response,
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Converted: {path}")


def main() -> None:
    root = Path("ai-model-tests")

    for path in root.rglob("*.md"):
        print("path:", path)
        convert_file(path)


if __name__ == "__main__":
    main()