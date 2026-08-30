from datetime import datetime
from pathlib import Path
import argparse
import re
import subprocess
import time


MODELS = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
    "claude-sonnet-5",
    "qwen3:8b",
    "qwen3:4b",
    "gemma3:4b",
    "mistral:7b",
    "qwen3:4b",
    "qwen3:14b",
]

QUESTIONS = [
    "What is ESKit?",
    "How do I create an index?",
    "How do I create a snapshot?",
    "Which operations are destructive?",
    "Can I delete a snapshot without confirmation?",
    "How do I reindex foo to bar?",
    "How do I transfer an archive to another host?",
    "Create a daily snapshot workflow.",
    "How do I accomplish X when there isn't a dedicated command?",
    "Compose a multi-step backup workflow.",
    "How do I create an repository?",
    "How can I see snapshot cache in eskit?",
    "How can I see repository cache in eskit?",
    "How can I see index cache in eskit?",
]


def question_filename(number, question, max_length=60):
    name = question.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    name = name[:max_length].rstrip("-")
    return f"{number:02d}-{name}.md"


def model_directory_name(model):
    return model.replace(":", "-")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        nargs="+",
        choices=MODELS,
        help="Run tests for one or more models.",
    )
    parser.add_argument(
        "--out-dir",
        help="output dir"
    )
    args = parser.parse_args()

    models = args.model if args.model else MODELS

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if args.out_dir:
        output_dir = Path(args.out_dir) / timestamp
    else:
        output_dir = Path("test-results") / timestamp
    output_dir.mkdir(parents=True)

    # The command description is the same for all models,
    # so dump it once for the entire test run.
    subprocess.run(
        [
            "eskit",
            "ai",
            "--model",
            models[0],
            "--output-command-json",
            str(output_dir / "command.json"),
            "",
        ],
        check=True,
    )

    for model in models:
        model_dir = output_dir / model_directory_name(model)
        model_dir.mkdir()

        for number, question in enumerate(QUESTIONS, start=1):
            output_file = model_dir / question_filename(number, question)

            print(f"[{model}] {number:02d}: {question}")

            start_time = time.perf_counter()

            result = subprocess.run(
                [
                    "eskit",
                    "ai",
                    "--model",
                    model,
                    question,
                ],
                capture_output=True,
                text=True,
            )

            elapsed_time = time.perf_counter() - start_time

            output_file.write_text(
                f"# Test\n"
                f"- **Model:** {model}\n"
                f"- **Question:** {question}\n"
                f"- **Elapsed time:** {elapsed_time:.3f} seconds\n"
                f"\n"
                f"# Response\n"
                f"{result.stdout}"
                f"{result.stderr}",
                encoding="utf-8",
            )

            print(f"    completed in {elapsed_time:.3f}s")

    print()
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()