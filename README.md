# agent-skills

Coding-agent skills from Generality Labs for working on [Inspect AI](https://inspect.aisi.org.uk/) evaluations. The repo is a plugin marketplace named `generality` with two plugins:

- `inspect-evals` holds the skills that [inspect-evals-template](https://github.com/Generality-Labs/inspect-evals-template) used to copy into every eval repo.
- `hawk` holds the user-facing skills for running evaluations on Generality Labs' [Hawk](https://github.com/Generality-Labs/hawk) deployment: viewing results, monitoring jobs, debugging stuck evals and babysitting a running eval.

Skills use the [Agent Skills](https://agentskills.io/) format, so one set of files serves Claude Code, Codex and the other agents that read it.

## Install

### Claude Code

Repos created from inspect-evals-template enable the `inspect-evals` plugin for you. Their `.claude/settings.json` names this marketplace and the plugin; add `"hawk@generality": true` to `enabledPlugins` for the Hawk skills (it needs a `ref` that includes the plugin, or none to track `main`):

```json
{
  "extraKnownMarketplaces": {
    "generality": { "source": { "source": "github", "repo": "Generality-Labs/agent-skills", "ref": "v1.0.1" } }
  },
  "enabledPlugins": { "inspect-evals@generality": true }
}
```

Once you trust the folder, Claude Code clones the marketplace and loads the plugin; there is no install step. To install by hand instead:

```text
/plugin marketplace add Generality-Labs/agent-skills
/plugin install inspect-evals@generality
/plugin install hawk@generality
```

Skills are invoked as `/<plugin>:<skill>`, for example `/inspect-evals:create-eval` or `/hawk:view-results`.

### Codex

```bash
codex plugin marketplace add Generality-Labs/agent-skills
codex plugin add inspect-evals@generality
codex plugin add hawk@generality
```

Start a new session afterwards. To update: `codex plugin marketplace upgrade generality`.

### Other agents (Cursor, GitHub Copilot and others)

```bash
npx skills add Generality-Labs/agent-skills --agent <agent> -g -y
```

`-y` installs every skill without prompting; add `--skill <name>` for one. Run `npx skills add --help` for the list of supported agents, and `npx skills update` to update.

## Skills

### inspect-evals

| Skill                                                                                              | When it fires                                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`check-trajectories-workflow`](plugins/inspect-evals/skills/check-trajectories-workflow/SKILL.md) | Use Inspect Scout to analyze agent trajectories from evaluation log files. Runs default and custom scanners to detect external failures, formatting issues, reward hacking, and ethical refusals. Use when user asks to check/analyze agent trajectories. Trigger when the user asks you to run the "Check Agent Trajectories" workflow.                                                                                                 |
| [`create-eval`](plugins/inspect-evals/skills/create-eval/SKILL.md)                                 | Implement a new evaluation from an issue or paper. Guides through requirements gathering, architecture design, scaffolding, implementation, testing, and quality checks. Use when user asks to create/implement/build a new evaluation.                                                                                                                                                                                                  |
| [`ensure-test-coverage`](plugins/inspect-evals/skills/ensure-test-coverage/SKILL.md)               | Ensure test coverage for a single evaluation - both reviewing existing tests and creating missing ones. Analyzes testable components, checks tests against repository conventions, reports coverage gaps, and creates or improves tests. Use when user asks to check/review/create/add/ensure tests for an eval. Use whenever you are asked to review an evaluation that contains tests, or whenever you need to write a suite of tests. |
| [`eval-report-workflow`](plugins/inspect-evals/skills/eval-report-workflow/SKILL.md)               | Create an evaluation report for a README by selecting models, estimating costs, running evaluations, and formatting results tables. Use when user asks to make/create/generate an evaluation report. Trigger when the user asks you to run the "Make An Evaluation Report" workflow.                                                                                                                                                     |
| [`eval-validity-review`](plugins/inspect-evals/skills/eval-validity-review/SKILL.md)               | Review a single evaluation's validity — whether its claims hold up, whether its name is accurate, whether samples can be both succeeded and failed at, and whether scoring measures ground truth. Use when user asks to check validity of an eval. Do NOT use for code quality or test coverage (use ensure-test-coverage instead).                                                                                                      |
| [`investigate-dataset`](plugins/inspect-evals/skills/investigate-dataset/SKILL.md)                 | Investigate datasets from HuggingFace, CSV, or JSON files to understand their structure, fields, and data quality. Trigger whenever you need to explore or inspect a dataset yourself without using pre-written scripts.                                                                                                                                                                                                                 |
| [`read-eval-logs`](plugins/inspect-evals/skills/read-eval-logs/SKILL.md)                           | View and analyse Inspect evaluation log files using the Python API. Trigger whenever you need to look at a .eval file yourself without using pre-written scripts.                                                                                                                                                                                                                                                                        |

### hawk

The Hawk skills assume CLI version 4.0.0, to match the server, and the GL endpoints set in `~/.config/hawk-cli/env`; the `view-results` skill shows the setup. They are adapted from [METR's Hawk](https://github.com/METR/hawk) under the MIT License; see [NOTICE.md](plugins/hawk/NOTICE.md).

| Skill | When it fires |
| --- | --- |
| [`babysit-eval`](plugins/hawk/skills/babysit-eval/SKILL.md) | Babysit a running Hawk eval over the ACP control channel — watch samples live, approve/reject parked tool calls, steer or cancel samples. |
| [`debug-stuck-eval`](plugins/hawk/skills/debug-stuck-eval/SKILL.md) | Debug stuck Hawk/Inspect AI evaluations: samples not completing, retry loops, 500 errors, timeouts. |
| [`monitoring`](plugins/hawk/skills/monitoring/SKILL.md) | Monitor Hawk job status, view logs, and diagnose issues or generate a monitoring report for a run. |
| [`view-results`](plugins/hawk/skills/view-results/SKILL.md) | View and analyze Hawk evaluation results: eval sets, evals, samples and transcripts. |

## Writing skills

The skills must work in every agent, so the checker in `tools/check_skills.py` runs in CI and fails on:

- a skill directory without a `SKILL.md`, or whose frontmatter `name` differs from the directory;
- frontmatter keys other than `name` and `description`;
- agent-specific tool and variable names (`AskUserQuestion`, `TodoWrite`, `Task tool`, `Agent tool`, `Skill tool`, `${CLAUDE_SKILL_DIR}`, `.claude/`, `CLAUDE.md`);
- relative links that leave the skill's directory or point at a missing file (links to other repos are absolute URLs);
- plugin names or versions that disagree between the marketplace entries and the two `plugin.json` files.

Run it with `python3 tools/check_skills.py`; it needs nothing beyond the standard library. Its tests run with `uvx --from pytest pytest tests`.

## Releasing

1. Bump `version` in the changed plugin's `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` (for example `plugins/inspect-evals/`).
1. Add a section to `CHANGELOG.md`.
1. Merge, then tag the merge commit `vX.Y.Z` and create a GitHub release from the changelog section.

Consumers pin the marketplace by `ref`, so a new version reaches a repo when its pin moves.
