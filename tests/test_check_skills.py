import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "tools" / "check_skills.py"
spec = importlib.util.spec_from_file_location("check_skills", SCRIPT)
assert spec is not None and spec.loader is not None
check_skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_skills)

FORBIDDEN = [
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


def skill_body(name: str, extra: str = "") -> str:
    return f"---\nname: {name}\ndescription: Does a thing.\n---\n\n# {name}\n{extra}"


def make_repo(
    tmp_path: Path,
    *,
    skills: dict[str, str],
    version: str = "1.0.0",
    codex_version: str | None = None,
    entry_name: str = "inspect-evals",
) -> Path:
    root = tmp_path / "repo"
    plugin = root / "plugins" / "inspect-evals"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".agents" / "plugins").mkdir(parents=True)
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".codex-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps({"name": "generality", "owner": {"name": "x"}, "plugins": [{"name": entry_name, "source": "./plugins/inspect-evals"}]})
    )
    (root / ".agents" / "plugins" / "marketplace.json").write_text(
        json.dumps({"name": "generality", "plugins": [{"name": entry_name, "source": {"source": "local", "path": "./plugins/inspect-evals"}}]})
    )
    (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "inspect-evals", "version": version}))
    (plugin / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": "inspect-evals", "version": codex_version or version, "skills": "./skills/"})
    )
    for name, body in skills.items():
        d = plugin / "skills" / name
        d.mkdir(parents=True)
        if body is not None:
            (d / "SKILL.md").write_text(body)
    return root


def test_clean_repo_has_no_problems(tmp_path: Path) -> None:
    root = make_repo(tmp_path, skills={"alpha": skill_body("alpha"), "beta": skill_body("beta")})
    assert check_skills.check_repo(root) == []


def test_missing_skill_md(tmp_path: Path) -> None:
    root = make_repo(tmp_path, skills={"alpha": None})
    problems = check_skills.check_repo(root)
    assert any("SKILL.md" in p and "alpha" in p for p in problems)


def test_name_must_match_directory(tmp_path: Path) -> None:
    root = make_repo(tmp_path, skills={"foo": skill_body("other")})
    problems = check_skills.check_repo(root)
    assert any("foo" in p and "other" in p for p in problems)


def test_only_name_and_description_in_frontmatter(tmp_path: Path) -> None:
    body = "---\nname: alpha\ndescription: Does a thing.\nuser-invocable: false\n---\n\n# alpha\n"
    root = make_repo(tmp_path, skills={"alpha": body})
    problems = check_skills.check_repo(root)
    assert any("user-invocable" in p for p in problems)


@pytest.mark.parametrize("token", FORBIDDEN)
def test_forbidden_tokens(tmp_path: Path, token: str) -> None:
    root = make_repo(tmp_path, skills={"alpha": skill_body("alpha", f"\nUse {token} here.\n")})
    problems = check_skills.check_repo(root)
    assert any(token in p and "alpha" in p for p in problems)


def test_relative_link_must_stay_inside_skill_dir(tmp_path: Path) -> None:
    root = make_repo(tmp_path, skills={"alpha": skill_body("alpha", "\nSee [guide](../../README.md).\n")})
    assert any("../../README.md" in p for p in check_skills.check_repo(root))

    root = make_repo(tmp_path / "b", skills={"alpha": skill_body("alpha", "\nSee [ref](references/notes.md).\n")})
    refs = root / "plugins" / "inspect-evals" / "skills" / "alpha" / "references"
    refs.mkdir()
    (refs / "notes.md").write_text("# notes\n")
    assert check_skills.check_repo(root) == []

    root = make_repo(tmp_path / "c", skills={"alpha": skill_body("alpha", "\nSee [ref](references/notes.md).\n")})
    assert any("references/notes.md" in p for p in check_skills.check_repo(root))


def test_absolute_links_are_fine(tmp_path: Path) -> None:
    body = skill_body("alpha", "\n[x](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/BEST_PRACTICES.md)\n")
    root = make_repo(tmp_path, skills={"alpha": body})
    assert check_skills.check_repo(root) == []


def test_versions_must_agree(tmp_path: Path) -> None:
    root = make_repo(tmp_path, skills={"alpha": skill_body("alpha")}, codex_version="1.0.1")
    problems = check_skills.check_repo(root)
    assert any("1.0.0" in p and "1.0.1" in p for p in problems)


def test_entry_name_must_match_plugin_json(tmp_path: Path) -> None:
    root = make_repo(tmp_path, skills={"alpha": skill_body("alpha")}, entry_name="inspect-eval")
    problems = check_skills.check_repo(root)
    assert any("inspect-eval" in p for p in problems)


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clean = make_repo(tmp_path / "clean", skills={"alpha": skill_body("alpha")})
    assert check_skills.main([str(clean)]) == 0
    assert capsys.readouterr().out == ""

    broken = make_repo(tmp_path / "broken", skills={"foo": skill_body("other")})
    assert check_skills.main([str(broken)]) == 1
    assert "foo" in capsys.readouterr().out
