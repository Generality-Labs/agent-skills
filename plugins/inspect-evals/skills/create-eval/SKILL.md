---
name: create-eval
description: Implement a new evaluation from an issue or paper. Guides through requirements gathering, architecture design, scaffolding, implementation, testing, and quality checks. Use when user asks to create/implement/build a new evaluation.
---
# Create Evaluation

Implement a new evaluation from an issue, paper, or benchmark specification. This is a phased workflow with human checkpoints between major phases. You should usually do human checkpoints. If the user requests that you do not do this, or you are in a fully autonomous workflow that says that there is no user to check with, you should ignore the human checkpoints. If you check in with the user several times and the user always replies with the same generic message like "Please continue the task", this indicates you are in an autonomous workflow.

## Where This Skill Applies

This skill is written for a repo generated from [inspect-evals-template](https://github.com/Generality-Labs/inspect-evals-template). Such a repo holds one evaluation and already contains a working skeleton: a package under `src/`, its `eval.yaml`, a README, tests, and the `inspect_ai` entry point in `pyproject.toml`. The work is to replace the skeleton's placeholder dataset, solver and scorer with the benchmark's. Do not create a second package beside the skeleton.

Read `AGENTS.md` at the repo root first. Then find these three things:

- **The package name.** It is the directory under `src/` other than `examples`. This skill writes it as `<eval_name>`. It was set when the repo was generated, so check with the user before renaming it.
- **The layout.** `preset` under `[tool.inspect-evals-lint]` in `pyproject.toml` is `multi-eval` or `single-eval`. The layout decides where the tests and the README are:

  | File   | `multi-eval`                | `single-eval`                                             |
  | ------ | --------------------------- | --------------------------------------------------------- |
  | Tests  | `tests/<eval_name>/`        | `tests/test_<eval_name>.py`, plus other `tests/test_*.py` |
  | README | `src/<eval_name>/README.md` | `README.md` at the repo root                              |

- **The examples.** `src/examples/` holds worked examples (`gpqa`, `agentic`, and sometimes `llm_judge`) when the repo was generated with them. They are not part of the eval.

Two guides this skill refers to are in the inspect_evals repo, and are not copied into the generated repo:

- [BEST_PRACTICES.md](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/BEST_PRACTICES.md)
- [EVALUATION_CHECKLIST.md](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/EVALUATION_CHECKLIST.md)

## Expected Arguments

When invoked, this skill expects:

- **issue** (optional): A GitHub issue number or URL (e.g., `#42`, `https://github.com/<owner>/<repo>/issues/42`)
- **paper_url** (optional): URL to the paper (arXiv, etc.)
- **reference_impl** (optional): URL to the reference implementation

If none of these is provided, ask the user which benchmark to implement. The `<eval_name>` comes from the repo, as described above.

## Phase 1: Requirements Gathering

Collect all information needed to make architectural decisions.

### 1.1 Gather Sources

- If an issue was provided, fetch it with `gh issue view <number> --json title,body,labels`
- If a paper URL was provided, fetch the page and read it
- If a reference implementation was provided, explore its structure
- If a HuggingFace dataset exists, fetch its metadata: `https://huggingface.co/api/datasets/<name>`

### 1.2 Classify the Evaluation

Determine the eval type by answering these questions:

| Question                     | Options                                                                     |
| ---------------------------- | --------------------------------------------------------------------------- |
| What does the model produce? | Text answer / Code / Multi-step actions / Structured output                 |
| How is it scored?            | Exact match / Partial credit / LLM judge / Code execution / Custom checker  |
| Does scoring need a sandbox? | No / Yes (Docker)                                                           |
| Does the solver need tools?  | No / Yes (bash, python, custom)                                             |
| Is it multi-turn?            | No / Yes                                                                    |
| What's the dataset source?   | HuggingFace / GitHub / URL / Local                                          |

Use this decision tree to pick the eval archetype:

```text
Model produces text answer?
  Scored by exact match? ──> Simple Q&A (pattern: gsm8k)
  Multiple choice? ──> Simple Q&A (pattern: gpqa)
  Scored by LLM judge? ──> LLM-as-judge (pattern: llm_judge example, xstest)
  Scored by code execution? ──> Code-in-sandbox (pattern: humaneval)

Model produces code?
  Single file, run + check? ──> Code generation (pattern: humaneval)
  Multi-step with tools? ──> Agentic coding (pattern: agentic example, swe_bench)

Model takes multi-step actions?
  With bash/python tools? ──> Agentic (pattern: agentic example, agent_bench)
  With custom tools? ──> Agentic + custom tools (pattern: gdm_intercode_ctf)
```

### 1.3 Identify Key Components

Document:

- **Dataset**: Source, format, columns, splits, sample count, license
- **Scoring**: Mechanism, metrics (binary vs continuous), partial credit rules
- **Sandbox needs**: What needs to run in Docker, what software must be installed
- **Dependencies**: Any Python packages needed beyond inspect_ai
- **Task variants**: Multiple tasks, parameterized variants, or single task

### 1.4 Write Requirements

Create `agent_artefacts/<eval_name>/create/REQUIREMENTS.md` with all findings. The generated repo's `.gitignore` excludes this directory, so the notes stay out of commits.

### 1.5 Human Checkpoint

Present a summary to the user and wait for approval before proceeding. Include:

- Eval archetype classification
- Proposed task structure (how many @task functions, what parameters)
- Scoring approach
- Sandbox needs (if any)
- Any open questions or ambiguities

## Phase 2: Architecture Design

### 2.1 Select Reference Eval(s)

Choose 1-2 existing evals as architectural models based on the archetype:

| Archetype          | Reference Eval                         | Key Pattern                                          |
| ------------------ | -------------------------------------- | ---------------------------------------------------- |
| Simple Q&A         | `src/examples/gpqa`, or `gpqa`         | CSV loader + `multiple_choice()` + `choice()`        |
| Math with few-shot | `gsm8k`                                | Few-shot prompting + `match(numeric=True)`           |
| Code generation    | `humaneval`                            | `generate()` solver + custom `@scorer` with sandbox  |
| Agentic            | `src/examples/agentic`, or `swe_bench` | `react()` agent + `bash()`/`python()` tools + Docker |
| LLM-as-judge       | `src/examples/llm_judge`, or `xstest`  | `model_graded_qa()` or custom judge scorer           |

A reference under `src/examples/` is in this repo when it was generated with the examples. Every other name is an eval in inspect_evals, at `https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals/<name>`.

Read the reference eval's source code to understand its patterns. The evals in inspect_evals import helpers from `inspect_evals.*` modules (for example `inspect_evals.utils` and `inspect_evals.metadata`), and that package is not installed in a generated repo. Take the structure from them and use the imports this skill names (2.3 and 4.5).

### 2.2 Design File Structure

The skeleton already has these files. The README is beside them in the `multi-eval` layout and at the repo root in the `single-eval` layout:

```text
src/<eval_name>/
  __init__.py           # Public exports
  <eval_name>.py        # @task function(s), solver, scorer (if simple)
  eval.yaml             # Metadata
  README.md             # Documentation (multi-eval layout)
```

**Add when needed:**

```text
  dataset.py            # When dataset loading is complex (multi-source, caching, transforms)
  scorers.py            # When scorer has significant custom logic
  prompts.py            # When there are multiple/complex prompt templates
  compose.yaml          # When Docker sandbox is needed
  Dockerfile            # When a custom Docker image is needed
```

**Tests**, which the skeleton also has:

```text
# multi-eval layout
tests/<eval_name>/
  __init__.py
  test_<eval_name>.py   # Unit tests + E2E (or split into test_dataset.py, test_scorer.py, test_e2e.py)

# single-eval layout
tests/
  test_<eval_name>.py   # Unit tests + E2E (or split into test_dataset.py, test_scorer.py, test_e2e.py)
```

### 2.3 Design Dataset Loading

Choose the dataset loading strategy:

```text
HuggingFace dataset?
  Simple columns? ──> hf_dataset() with FieldSpec or record_to_sample
  Complex transforms? ──> hf_dataset() with record_to_sample function

JSON or CSV file at a URL (GitHub raw file, etc.)?
  ──> load_json_dataset() / load_csv_dataset(), which download and cache the file

Other remote data (archives, many files)?
  ──> Download to INSPECT_EVALS_CACHE_PATH at task init, pinned to a revision

Local data?
  JSON? ──> json_dataset()
  CSV? ──> csv_dataset()
```

Where these come from:

- `hf_dataset`: `from inspect_evals_utils.huggingface import hf_dataset`. It takes the same arguments as `inspect_ai.dataset.hf_dataset` and retries with backoff on transient Hub errors.
- `load_json_dataset`, `load_csv_dataset`: `from inspect_evals_utils.datasets import ...`. Call as `load_json_dataset(url, "<eval_name>", sample_fields=record_to_sample)`.
- `INSPECT_EVALS_CACHE_PATH`: `from inspect_evals_utils import INSPECT_EVALS_CACHE_PATH`.
- `json_dataset`, `csv_dataset`: `inspect_ai.dataset`.

**Always pin dataset versions:**

- HuggingFace: Use `revision` parameter with commit SHA from `https://huggingface.co/api/datasets/<name>` (`sha` field)
- GitHub: Pin to a specific commit SHA

### 2.4 Design Scoring

Choose the scoring strategy:

```text
Binary outcome (correct/incorrect)?
  ──> Score.value = CORRECT/INCORRECT, metrics = [accuracy(), stderr()]

Continuous score (0.0-1.0 or 0-100)?
  ──> Score.value = float, metrics = [mean(), stderr()]
  ──> Normalize to 0.0-1.0 range for Score.value

Multiple sub-scores?
  ──> Score.value = dict, custom metrics or per-key mean()/stderr()
```

Key rules from [BEST_PRACTICES.md](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/BEST_PRACTICES.md):

- Store all aggregatable values in `Score.value`, NOT in `Score.metadata`
- Use `Score.metadata` only for identifiers and debugging info
- Use `Score.explanation` for human-readable scoring details

### 2.5 Design Solver

```text
Simple generation?
  ──> generate() or [prompt_template(...), generate()]

Multiple choice?
  ──> multiple_choice(), scored with choice()

Needs system message?
  ──> [system_message(...), generate()]

Needs tools (bash, python)?
  ──> react(prompt=SYSTEM_PROMPT, tools=[bash(), python()])   # from inspect_ai.agent

Needs few-shot examples?
  ──> [system_message(fewshot_text), prompt_template(...), generate()]
```

**Choice of agent**: If the eval should run with more than one agent (for example Inspect's ReAct agent and Claude Code), expose an `agent` task parameter typed as a `Literal` and build the agent from it. `src/examples/agentic/agentic.py` shows this with `react(...)` and `inspect_swe.claude_code(system_prompt=...)`. An eval that imports `inspect_swe` needs it as a runtime dependency (`uv add inspect-swe`).

**Paper methodology check**: If the original paper uses single-turn evaluation but an agentic approach is also valid, implement **both** solvers and expose a parameter (e.g., `agentic: bool = True`). Default to agentic (since this is an agentic framework) but allow paper-faithful reproduction with `agentic=False`. Include separate system prompt constants for each mode.

### 2.5b Identify Hardware/Environment Requirements

Check if any subset of problems requires special hardware (GPUs, large memory, specific software). If so:

- Add a filtering parameter (e.g., `include_gpu_problems: bool = False`) that defaults to **excluding** problems the user likely can't run
- Document which problems are excluded and why
- Tag problems in metadata so filtering is data-driven, not hardcoded to specific IDs

This applies broadly: GPU-dependent problems, problems needing internet access, problems requiring specific commercial software, etc.

### 2.6 Write Architecture

Create `agent_artefacts/<eval_name>/create/ARCHITECTURE.md` with:

- File structure with descriptions
- Dataset loading approach
- Scoring mechanism
- Solver design
- Docker setup (if applicable)
- Dependencies needed

### 2.7 Human Checkpoint

Present the architecture to the user and wait for approval.

## Phase 3: Scaffolding

The repo already has the skeleton, so this phase edits files more than it creates them. Three values set here depend on code written in Phase 4: `dataset_samples` in `eval.yaml`, the exports in `__init__.py`, and the place the dataset revision is used. Set what is known now and update them in Phase 4.

### 3.1 Check the Skeleton

Run `uv sync`, then `make check` and `make test`. Both should pass before any change. If they do not, report that to the user before going further.

A newly generated repo has no `uv.lock`, and the first `uv` command writes one. Commit it: CI runs `uv sync --locked`, which fails without a committed lockfile.

Confirm the files in 2.2 exist. If `src/<eval_name>/` is missing, the repo did not come from the template: create the files in 2.2 by hand and add the entry point from 4.6.

### 3.2 Update eval.yaml

Edit `src/<eval_name>/eval.yaml`. A new eval stays at version `1-A`.

```yaml
title: "Full Title: Subtitle"
description: |
  Description from the paper abstract.
arxiv: https://arxiv.org/abs/XXXX.XXXXX
group: <Group>  # One of: Assistants, Coding, Cybersecurity, Knowledge, Mathematics, Multimodal, Reasoning, Safeguards, Scheming, Writing
contributors:
  - github-username  # the people writing this port; ask the user
version: "1-A"
tasks:
  - name: <task_name>
    dataset_samples: <count>  # samples the task runs with its default parameters
tags: ["Agent"]  # Only if agentic. Omit if not applicable.
metadata:
  sandbox: ["solver", "scorer"]  # Only if sandbox used. Omit individual items or entire field if not needed.
```

If inspect_evals already lists the benchmark, use the `group` from its `eval.yaml` there.

### 3.3 Update `__init__.py`

Export all public symbols: task functions, dataset functions, scorer functions, constants. The skeleton exports its one task. Add the others as Phase 4 creates them.

### 3.4 Create Docker Files (if needed)

**compose.yaml** (at eval root, NOT in data/):

```yaml
services:
  default:
    build: .
    init: true
    command: tail -f /dev/null
```

**Dockerfile:**

- Start from a minimal base (e.g., `ubuntu:24.04`, `python:3.12-slim`)
- Install only what's needed for scoring/execution
- Keep it small — models don't need IDE tools

`src/examples/agentic/` has a `compose.yaml` and `Dockerfile` to compare with, when the examples are present.

### 3.5 Test Files

The skeleton's tests cover the placeholder task. Phase 5 replaces them. In the `multi-eval` layout, keep `tests/<eval_name>/__init__.py`.

### 3.6 Pin Dataset Version

- For HuggingFace: Fetch SHA from API and use as `revision` parameter
- For GitHub: Get commit SHA and pin downloads to it

Record the SHA in `ARCHITECTURE.md` now. The loader written in 4.1 uses it.

### 3.7 Add Dependencies (if needed)

```bash
uv add <package>          # a package that code under src/<eval_name>/ imports
uv add --dev <package>    # a package only the tests or tooling use
```

`uv add` writes `pyproject.toml` and `uv.lock`. Commit both.

**Critical rule**: Every package that code under `src/<eval_name>/` imports must be in `[project] dependencies`. A package in the `dev` group is installed locally by `uv sync`, so a missing runtime dependency does not fail on your machine. It fails for someone who installs the package.

### 3.8 Run Checks

```bash
make check
```

This runs `ruff check`, `ruff format --check`, `basedpyright`, `inspect-evals-lint --all`, `inspect-evals-readmes generate --check` and the pre-commit hooks, and stops at the first command that fails. The first five commands report problems and change no files. To fix what they report:

- Formatting: `uv run ruff format`
- Lint findings with an automatic fix: `uv run ruff check --fix`
- README sections that are out of date: `make readmes` (see 6.3)

Some pre-commit hooks fix files in place (file endings, Markdown formatting, `uv.lock`). A hook that changes a file fails that run and prints "files were modified by this hook". Run `make check` again and commit the changed files.

## Phase 4: Core Implementation

Implement in dependency order: dataset -> prompts -> scorer -> solver -> @task.

### 4.1 Dataset Loading

- Use `hf_dataset()` from `inspect_evals_utils.huggingface` for HuggingFace datasets (see 2.3)
- Keep the dataset path and its pinned revision as module-level constants (for example `DATASET_PATH` and `DATASET_REVISION`), so the tests can import them
- Write a `record_to_sample` function that maps raw records to `Sample` objects
- Include all useful fields in `sample.metadata` for debugging
- Use stable, canonical IDs for `sample.id`
- Leave the skeleton's `SAMPLE_RECORDS` placeholder in the module until Phase 5. The skeleton's tests import it, so removing it now makes `make check` in 4.7 fail on that import

### 4.2 Prompts

- Keep prompt text as module-level constants (ALL_CAPS)
- Use `.format()` or f-strings for variable injection
- Separate system prompt from user prompt

### 4.3 Scorer

- Prefer built-in scorers (`match()`, `includes()`, `choice()`, `model_graded_qa()`) when possible
- For custom scorers, use `@scorer(metrics=[...])` decorator
- For sandbox execution in scorer, use `await sandbox().exec(...)`
- Handle timeouts and errors gracefully
- Return `Score(value=..., answer=..., explanation=...)`

### 4.4 Solver

- Prefer built-in solvers and agents (`generate()`, `multiple_choice()`, `react()`)
- For agentic evals, use `react(prompt=SYSTEM_PROMPT, tools=[...])` from `inspect_ai.agent` and pass it as the task's `solver`
- Set sensible `message_limit` defaults

### 4.5 Task Function

The skeleton module already reads the version this way. Keep it:

```python
from inspect_evals_utils.metadata import load_eval_version

# The version comes from eval.yaml, the file beside this module.
EVAL_VERSION = load_eval_version(__file__)


@task
def <eval_name>(...) -> Task:
    return Task(
        dataset=...,
        solver=...,
        scorer=...,
        sandbox=...,  # ("docker", str(compose_file)) if needed
        version=EVAL_VERSION,
    )
```

Key rules:

- Do NOT pass a `name` parameter to `@task`
- Use `load_eval_version(__file__)` for the version, so `eval.yaml` is the one place it is written
- Use absolute imports throughout

### 4.6 Check the Task Registration

`pyproject.toml` in a generated repo already registers the package with the `inspect_ai` entry-point group, which is how the `inspect eval` CLI finds the tasks:

```toml
[project.entry-points.inspect_ai]
<eval_name> = "<eval_name>"
```

The key is the prefix the `inspect eval` CLI uses; the value is the Python package it imports to find the tasks. Check that the package's `__init__.py` imports every `@task` function. `inspect eval <eval_name>/<task_name>` finds only the tasks that importing the package registers.

### 4.7 Run Checks

```bash
make check
```

### 4.8 Human Checkpoint

Tell the user the core implementation is done. Suggest they smoke-test:

```bash
uv run inspect eval <eval_name>/<task_name> --model mockllm/model --limit 1
```

For Docker-based evals, this requires Docker to be running. If the user can't run Docker, note this and move on.

## Phase 5: Testing

### 5.1 Create Tests

Replace the skeleton's tests with tests of the benchmark, and delete `SAMPLE_RECORDS` from the module in the same step. Follow the test patterns from the `ensure-test-coverage` skill. Its commands are written for the inspect_evals repo (paths under `tests/<eval_name>/`, and `--cov` options that need `pytest-cov`, which a generated repo does not install), so run the tests with `make test` here. At minimum:

**record_to_sample test** (use real data from the dataset):

```python
def test_record_to_sample() -> None:
    record = { ... }  # Real example from dataset
    sample = record_to_sample(record)
    assert sample.id == "expected_id"
    assert "expected_text" in str(sample.input)
    assert sample.target == "expected_target"
```

**HuggingFace dataset structure validation** (if using HF datasets):

Use `assert_huggingface_dataset_structure` from `pytest_inspect_evals.huggingface` to document and validate the expected schema:

```python
from pytest_inspect_evals.huggingface import (
    DatasetInfosDict,
    assert_huggingface_dataset_structure,
    get_dataset_infos_dict,
)

from <eval_name>.<eval_name> import DATASET_PATH  # the constant the loader uses

@pytest.fixture(scope="module")
def dataset_infos() -> DatasetInfosDict:
    return get_dataset_infos_dict(DATASET_PATH)

@pytest.mark.huggingface
def test_dataset_structure(dataset_infos: DatasetInfosDict) -> None:
    assert_huggingface_dataset_structure(
        dataset_infos,
        {
            "configs": {
                "default": {
                    "splits": ["test"],
                    "features": {
                        "question": str,
                        # A nested feature is a dict with its own fields.
                        "choices": {"type": "dict", "fields": {"label": list[str], "text": list[str]}},
                    },
                }
            }
        },
    )
```

**E2E test with mockllm:**

```python
from inspect_ai import eval
from pytest_inspect_evals.assertions import assert_eval_success

@pytest.mark.dataset_download  # If downloads data
@pytest.mark.huggingface       # If the data comes from the HuggingFace Hub
@pytest.mark.docker            # If uses Docker
def test_<eval_name>_e2e() -> None:
    [log] = eval(
        tasks=<task_function>(),
        model="mockllm/model",
        limit=1,
        message_limit=1,  # For agentic evals
    )
    assert_eval_success(log, expected_sample_count=1)
```

**Version test**: keep the skeleton's `test_version_comes_from_eval_yaml`, and update its expected value when `version` in `eval.yaml` changes.

**Custom scorer/solver/tool tests** if any exist. At minimum a type-check (`isinstance(scorer, Scorer)`) is required by inspect-evals-lint for custom scorers (rule IETS006; IETS005 and IETS007 cover custom solvers and tools).

### 5.2 Add Pytest Markers

- `@pytest.mark.dataset_download` — if test downloads a dataset
- `@pytest.mark.huggingface` — if test calls the HuggingFace Hub. A test that downloads a dataset from the Hub carries both this marker and `dataset_download`
- `@pytest.mark.docker` — if test uses Docker sandbox
- `@pytest.mark.slow(<seconds>)` — if test takes >10 seconds (use observed duration)

Tests marked `huggingface` run when `HF_TOKEN` is unset, and the test summary then says how many ran without authentication. CI passes no token, so a test that needs a private or gated dataset fails there.

### 5.3 Run Tests

```bash
make test
```

`make test` runs `uv run pytest` over the whole repo and works in both layouts. Slow tests need `uv run pytest --runslow`. Fix any failures. For tests requiring Docker or datasets, note which tests need special setup.

## Phase 6: Quality and Submission

### 6.1 Run inspect-evals-lint

```bash
uv run inspect-evals-lint <eval_name>
```

`make check` and CI run the same linter with `--all`, and a failed rule fails both. A rule reported as `WARN` does not fail the check; tell the user about it and leave the decision to them. `uv run inspect-evals-lint --explain <RULE>` prints a rule's documentation, and the [rule pages](https://github.com/Generality-Labs/inspect-evals-lint/tree/main/docs/rules) have one page per rule code.

### 6.2 Run All Checks

```bash
make check
```

See 3.8 for what this runs and how to fix what it reports. Fix any errors before proceeding.

### 6.3 Update the README

The README already exists (see "Where This Skill Applies" for its location). It has two kinds of section.

**Generated sections** sit between `<!-- ...: Automatically Generated -->` comments (Contributors, Usage, Options, Parameters). They come from `eval.yaml` and the task signatures. Do not edit them by hand in the `multi-eval` layout. Regenerate them:

```bash
make readmes
```

In the `single-eval` layout the generator does not yet process the README at the repo root ([inspect-evals-utils issue #12](https://github.com/Generality-Labs/inspect-evals-utils/issues/12)). Until that is fixed, update the generated sections of the root README by hand when `eval.yaml` or a task signature changes.

**Hand-written sections** are yours to fill in: the title, the opening description, Dataset, Scoring, "Deviations from the original implementation" (a table of what changed, why, and the expected effect on scores), and Architecture. The evaluation report can be left for the `eval-report-workflow` skill.

### 6.4 Verify Against EVALUATION_CHECKLIST.md

Read [EVALUATION_CHECKLIST.md](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/EVALUATION_CHECKLIST.md) and verify every applicable item. The checklist is written for the inspect_evals repo, so some items name things a generated repo does not have:

- Its run command `uv run inspect eval inspect_evals/<eval_name>` is `uv run inspect eval <eval_name>/<task_name>` here.
- `uv run mypy` is `uv run basedpyright src tests` here, and `tools/generate_readmes.py` is `make readmes`. Both run as part of `make check`.
- Skip the items about the register, `changelog.d/` fragments, the Master Checklist in `AGENTS.md`, the other scripts under `tools/`, and uploading files under `agent_artefacts/` (a generated repo's `.gitignore` excludes that directory).
- A generated repo has no root `NOTICE` file. If the eval copies code from another project, tell the user so they can decide where to record it.

**Smoke Test**: This is the checklist's first item. Run the eval with `--limit 1` on a model the user has an API key for, in addition to the `mockllm/model` run in 4.8, and read the transcript.

If the evaluation takes longer than five minutes to run and you can identify what component is failing, Add tests to reproduce any failure modes first. Only once those pass should you run it again.

**Evaluation Report**: Use the `eval-report-workflow` skill. This is the place you will stop for human approval unless you are specifically told not to or it is clear you are in a fully autonomous workflow.

**Trajectory Analysis**: Use the `check-trajectories-workflow` skill. If there are significant problems in trajectory analysis, these should be fixed. If the problem is related to the code at all, such as a broken environment, you should fix them using Test Driven Development. Create a unit test or tests with data that reproduces the failure mode, verify the test fails, then fix the issue and verify the test succeeds.

## Gotchas (Lessons from Real Implementations)

- **Regex with language names**: If building regex patterns from language names like `c++`, use `re.escape()` — the `+` is a regex special character.
- **Filtering datasets by category**: `hf_dataset()` with `FieldSpec` loads all samples. If you need to filter (e.g., by category/track), load once, convert to samples, then filter. Use `MemoryDataset(samples=filtered_list, name=...)` to create a new dataset (NOT `Dataset()` which takes no constructor args).
- **Mixed config formats**: Dataset fields that look like YAML may contain JSON in some records. Always implement fallback parsing (YAML → JSON → raw string).
- **`react()` API**: Use `react(prompt=..., tools=[...])` from `inspect_ai.agent`, and pass the agent as the task's `solver`. The system prompt goes in `prompt=`; `react()` has no `init=` parameter. `src/examples/agentic/agentic.py` is a working example when the examples are present.
- **`sandbox().exec()` API**: The parameter for passing stdin is `input=`, NOT `stdin=`. Signature: `exec(cmd, input=None, cwd=None, env=None, user=None, timeout=None)`.
- **HF dataset structure validation**: Use `assert_huggingface_dataset_structure` from `pytest_inspect_evals.huggingface` (`from pytest_inspect_evals.huggingface import ...`) to document the expected schema. It compares the field names and types you list with the schema the Hub reports for the dataset's current revision, which can be newer than the revision the loader pins. A failure means the dataset has changed upstream.
- **README generator**: `make readmes` runs `uv run inspect-evals-readmes generate`, which rewrites the generated README sections. `make check` runs the same command with `--check`, which fails when a section is out of date and writes nothing.
- **Checks**: `make check` runs every check CI runs (ruff, basedpyright, inspect-evals-lint, the README check, pre-commit). It stops at the first failing command. It does not reformat Python code or regenerate READMEs: run `uv run ruff format` and `make readmes` for that, then `make check` again. Its pre-commit step does fix file endings, Markdown formatting and `uv.lock` in place, and fails on the run where it changes a file.
- **Scorer robustness for agentic evals**: When a model hits `message_limit` during a tool call, `state.output.completion` is empty. If your scorer extracts code from the completion, add a fallback that reads solution files from the sandbox (e.g., `find /tmp /home -name '*.cpp'`).
- **Version pinning in Dockerfiles**: Pin all downloaded dependencies (e.g., `testlib.h`) to specific commit SHAs, not branch names like `master` or `main`. Same applies to GitHub archive downloads in dataset code.
- **Paper vs agentic methodology**: If a paper uses single-turn evaluation, implement both single-turn and agentic solvers. Default to agentic, but expose a parameter so users can reproduce paper results. Compare against the reference implementation's system prompts.
- **Hardware-gated problems**: Some benchmarks include problems requiring GPUs, specific hardware, or commercial software. Add a filtering parameter (e.g., `include_gpu_problems=False`) so these are excluded by default but can be opted into.
- **Multiple execution modes in one benchmark**: Some benchmarks have problems with fundamentally different execution models (e.g., batch file I/O vs interactive bidirectional piping). Check the reference implementation's config schema for `type` fields and implement all modes, not just the most common one.
- **Sandbox config must reference compose.yaml**: Passing `sandbox="docker"` uses a bare container. To use a custom Dockerfile, pass `sandbox=("docker", str(compose_file))` where `compose_file = Path(__file__).parent / "compose.yaml"`.
- **HF image fields → base64 data URI**: When loading a HuggingFace dataset that contains images, `hf_dataset()` delivers them as `{"bytes": ..., "path": ...}` dicts. Encode inline: `image_uri = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"` and pass to `ContentImage(image=image_uri)`. No disk cache or PIL thumbnail needed — `hf_dataset()` already caches the dataset locally.
- **`Dataset.filter()` return value must be assigned**: `dataset.filter(pred)` returns a new dataset; it does not mutate in place. `dataset.filter(...)` on a line by itself silently does nothing. Always write `dataset = dataset.filter(...)`.
- **Use `create_stable_id` for sample IDs**: `from inspect_evals_utils import create_stable_id` and call `create_stable_id(*fields, prefix=..., length=8)` rather than computing raw `hashlib.md5(...).hexdigest()` yourself. It uses a null-byte delimiter between fields so combinations like `("ab", "c")` and `("a", "bc")` hash differently.
- **Include image content in sample IDs**: When a dataset contains image fields and the same question can be asked about multiple different images (common in VQA benchmarks), the sample ID must include a hash of the image bytes, not just the question text. Hashing question text alone produces duplicate IDs.
- **Check answer length distribution before committing to exact match**: Before implementing a scorer for open-ended answers, inspect the distribution of ground-truth answer lengths (`Counter(len(a.split()) for a in answers)`). Long multi-word answers are practically unreproducible verbatim — consider filtering out long answers with a `MAX_ANSWER_WORDS` constant and update `eval.yaml dataset_samples` to the post-filter count. Alternatively, switch to a model graded scorer.
- **Constrain binary-answer format explicitly**: For yes/no questions, the prompt must say "answer ONLY 'yes' or 'no'" (or equivalent). Without this constraint, models append qualifications ("Yes, there is cardiomegaly") which fail exact match even when the answer is correct.

## Things NOT to Do

- **Don't create a second package or a new `tests/` tree**: Edit the skeleton the template generated
- **Don't pass `name` to `@task`**: This is only for dynamically created tasks
- **Don't import a package under `src/<eval_name>/` that is only in the `dev` dependency group**: Add it with `uv add <package>` first
- **Don't use relative imports**: Use absolute imports (e.g. `from <your_package>.<module> import <symbol>`) so modules and tests run from any working directory
- **Don't use private Inspect AI APIs**: Avoid `inspect_ai.*._internal` modules
- **Don't store aggregatable values in Score.metadata**: Use Score.value (can be a dict)
- **Don't upload new dataset copies**: Use official sources
- **Don't implement manual HF token checks**: pytest-inspect-evals handles `@pytest.mark.huggingface`
- **Don't over-test thin wrappers**: A type check is sufficient for a function that only returns a built-in solver or agent
- **Don't add type annotations that are redundant**: Only annotate function signatures
- **Don't create documentation files unless asked**: The README already exists; fill it in (see 6.3)
- **Don't run `uv lock --upgrade`**: It moves every locked dependency. `uv add` and `uv lock` change only what is needed
- **Don't hardcode magic numbers**: Extract to named constants if used 3+ times or unclear
- **Don't write try/catch unless truly necessary**: Let errors crash early
