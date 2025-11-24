import subprocess
from pathlib import Path


def find_git_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError("Not in a git repository")


def get_repo_name() -> str:
    return find_git_root().name


def get_current_branch() -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def get_gitignore_patterns() -> list[str]:
    git_root = find_git_root()
    gitignore_path = git_root / ".gitignore"

    if not gitignore_path.exists():
        return []

    patterns = []
    with open(gitignore_path, "r") as f:
        for line in f:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith("#"):
                patterns.append(line_stripped)

    return patterns

