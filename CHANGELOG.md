# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-11-11

### Fixed

create-eval now matches a repo generated from inspect-evals-template v2.0:

- It starts from the skeleton the template generates, and covers the `multi-eval` and `single-eval` layouts.
- It reads the version with `load_eval_version(__file__)` from inspect-evals-utils. It named `load_eval_metadata` before.
- It describes `make check` as the generated Makefile runs it (ruff, basedpyright, inspect-evals-lint, the README check and pre-commit), including the pre-commit hooks that fix files in place. It named mypy, markdownlint and `tools/enforcement.config` before.
- Dependencies are added with `uv add`. It described optional extras and a `test` extra before.
- The agentic guidance uses `react()` from `inspect_ai.agent`, as the template's agentic example does. It named `basic_agent()` before.
- Multiple-choice evals have an entry in the solver and scorer guidance (`multiple_choice()` and `choice()`).
- The `huggingface` marker guidance follows pytest-inspect-evals 0.4.0, and the dataset structure test example shows a nested feature.
- Reference evals point to `src/examples/` and to inspect_evals by URL. BEST_PRACTICES.md and EVALUATION_CHECKLIST.md are linked in inspect_evals, with a list of the checklist items that do not apply to a generated repo.

## [1.0.0] - 2026-11-06

### Added

- First release: the create-eval, investigate-dataset, ensure-test-coverage, read-eval-logs, check-trajectories-workflow, eval-validity-review and eval-report-workflow skills, moved from inspect-evals-template, installable in Claude Code, Codex and other agents.
