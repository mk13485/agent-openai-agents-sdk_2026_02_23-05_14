from pathlib import Path

from tools.file import read_file


def load_system_prompt() -> str:
    prompt_path = Path(__file__).with_name("system_prompt.txt")
    return read_file(str(prompt_path))


def main() -> None:
    prompt = load_system_prompt()
    print("PERFECT-AGENT scaffold ready.")
    print("Loaded system prompt (first 200 chars):")
    print(prompt[:200])


if __name__ == "__main__":
    main()
