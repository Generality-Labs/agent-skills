#!/usr/bin/env python3
"""Check that the skills in this repo work in every agent that reads them.

Standard library only, so CI and contributors can run it with a bare python3:

    python3 tools/check_skills.py [REPO_ROOT]

Exit status 1 and one line per problem when something is wrong.
"""

import json
import re
import sys
from pathlib import Path

ALLOWED_FRONTMATTER_KEYS = {"name", "description"}

# Names and variables that only one agent understands. A skill that mentions
# them reads as broken in every other agent.
FORBIDDEN_TOKENS = [
    "AskUserQuestion",
    "TodoWrite",
    "Task tool",
    "Agent tool",
    "Skill tool",
    "${CLAUDE_SKILL_DIR}",
    "${CLAUDE_",
    ".claude/",
    "CLAUDE.md",
]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return the key/value block between the first two `---` lines, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return None


def check_skill(skill_dir: Path) -> list[str]:
    label = f"{skill_dir.parent.parent.name}/{skill_dir.name}"
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{label}: no SKILL.md"]
    problems: list[str] = []
    text = skill_md.read_text(encoding="utf-8")

    fields = parse_frontmatter(text)
    if fields is None:
        problems.append(f"{label}: SKILL.md has no frontmatter block")
    else:
        extra = sorted(set(fields) - ALLOWED_FRONTMATTER_KEYS)
        if extra:
            problems.append(f"{label}: frontmatter keys other than name and description: {', '.join(extra)}")
        if fields.get("name") != skill_dir.name:
            problems.append(f"{label}: frontmatter name {fields.get('name')!r} does not match the directory {skill_dir.name!r}")
        if not fields.get("description"):
            problems.append(f"{label}: frontmatter has no description")

    for token in FORBIDDEN_TOKENS:
        if token in text:
            problems.append(f"{label}: mentions the agent-specific token {token!r}")

    root = skill_dir.resolve()
    for target in LINK_RE.findall(text):
        if SCHEME_RE.match(target) or target.startswith("#"):
            continue
        path = target.split("#", 1)[0]
        resolved = (skill_dir / path).resolve()
        if root not in resolved.parents and resolved != root:
            problems.append(f"{label}: link {target!r} points outside the skill directory")
        elif not resolved.exists():
            problems.append(f"{label}: link {target!r} points to a file that does not exist")
    return problems


def _load_json(path: Path, problems: list[str]) -> dict | None:
    if not path.is_file():
        problems.append(f"missing {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        problems.append(f"{path}: invalid JSON ({e})")
        return None


def check_manifests(root: Path) -> list[str]:
    problems: list[str] = []
    claude = _load_json(root / ".claude-plugin" / "marketplace.json", problems)
    codex = _load_json(root / ".agents" / "plugins" / "marketplace.json", problems)
    plugins_dir = root / "plugins"
    plugin_dirs = sorted(p for p in plugins_dir.iterdir() if p.is_dir()) if plugins_dir.is_dir() else []
    if not plugin_dirs:
        problems.append("no plugin directories under plugins/")

    for plugin_dir in plugin_dirs:
        name = plugin_dir.name
        claude_manifest = _load_json(plugin_dir / ".claude-plugin" / "plugin.json", problems)
        codex_manifest = _load_json(plugin_dir / ".codex-plugin" / "plugin.json", problems)
        names = {
            "plugins/.claude-plugin/plugin.json": (claude_manifest or {}).get("name"),
            "plugins/.codex-plugin/plugin.json": (codex_manifest or {}).get("name"),
        }
        for marketplace, label in ((claude, ".claude-plugin/marketplace.json"), (codex, ".agents/plugins/marketplace.json")):
            if marketplace is None:
                continue
            entries = [e for e in marketplace.get("plugins", []) if _entry_points_at(e, name)]
            if not entries:
                problems.append(f"{label}: no entry whose source is ./plugins/{name}")
            else:
                names[label] = entries[0].get("name")
        wrong = {label: value for label, value in names.items() if value != name}
        for label, value in wrong.items():
            problems.append(f"{label}: plugin name {value!r} does not match the directory {name!r}")

        versions = {
            ".claude-plugin/plugin.json": (claude_manifest or {}).get("version"),
            ".codex-plugin/plugin.json": (codex_manifest or {}).get("version"),
        }
        if len(set(versions.values())) > 1:
            listed = ", ".join(f"{label} has {value!r}" for label, value in versions.items())
            problems.append(f"plugins/{name}: versions disagree: {listed}")
    return problems


def _entry_points_at(entry: dict, plugin_name: str) -> bool:
    source = entry.get("source")
    if isinstance(source, str):
        return Path(source).name == plugin_name
    if isinstance(source, dict):
        return Path(str(source.get("path", ""))).name == plugin_name
    return False


def check_repo(root: Path) -> list[str]:
    """Return every problem found under `root`; an empty list means clean."""
    problems = check_manifests(root)
    for skills_dir in sorted(root.glob("plugins/*/skills")):
        for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            problems.extend(check_skill(skill_dir))
    return problems


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path(".")
    problems = check_repo(root)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
