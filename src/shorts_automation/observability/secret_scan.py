"""Repository credential-signature scanner used by local verification and CI."""

import re
import subprocess
from pathlib import Path

SECRET_PATTERNS = {
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
    "OpenAI key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "PEM private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

SENSITIVE_ASSIGNMENT = re.compile(
    r"(?im)^[ \t]*(?:export[ \t]+)?(?:"
    r"OPENAI_API_KEY|RUNWAYML_API_SECRET|USDA_API_KEY|"
    r"YOUTUBE_CLIENT_ID|YOUTUBE_CLIENT_SECRET|YOUTUBE_REFRESH_TOKEN|"
    r"AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN"
    r")[ \t]*[:=][ \t]*['\"]?(?P<value>[^\s#'\"]+)"
)

SAFE_SUFFIXES = {".pyc", ".mp4", ".png", ".jpg", ".jpeg"}


def tracked_files() -> list[Path]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            text=False,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return [
            path for path in Path.cwd().rglob("*") if path.is_file() and ".venv" not in path.parts
        ]
    return [Path(raw.decode()) for raw in output.split(b"\0") if raw]


def scan_paths(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if path.suffix.lower() in SAFE_SUFFIXES or not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                findings.append(f"{path}: potential {label}")
        if SENSITIVE_ASSIGNMENT.search(content):
            findings.append(f"{path}: nonblank project credential assignment")
    return findings


def main() -> int:
    findings = scan_paths(tracked_files())
    if findings:
        print("\n".join(findings))
        return 1
    print("No credential signatures found in tracked project files.")
    return 0
