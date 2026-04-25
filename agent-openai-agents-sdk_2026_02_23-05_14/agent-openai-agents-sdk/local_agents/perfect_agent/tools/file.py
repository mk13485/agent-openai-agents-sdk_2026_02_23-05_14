import os


def read_file(path: str) -> str:
    if not os.path.exists(path):
        return f"ERROR: File not found: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File written: {path}"
