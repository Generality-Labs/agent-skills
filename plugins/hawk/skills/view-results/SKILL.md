---
name: view-results
description: View and analyze Hawk evaluation results. Use when the user wants to see eval-set results, check evaluation status, list samples, view transcripts, or analyze agent behavior from a completed evaluation run.
---

# View Hawk Eval Results

When the user wants to analyze evaluation results, use these hawk CLI commands:

## 1. List Eval Sets

You can list all eval sets if the user do not know the eval set ID:

```bash
hawk list eval-sets
```

Shows: eval set ID, creation date, creator.

You can increase the limit of results returned by `--limit N`.

```bash
hawk list eval-sets --limit 50
```

Or you can search for a specific eval set by using `--search QUERY`.

```bash
hawk list eval-sets --search pico
```

## 2. List Evaluations

With an eval set ID, you can list all evaluations in the eval-set:

```bash
hawk list evals [EVAL_SET_ID]
```

Shows: task name, model, status (success/error/cancelled), and sample counts.

## 3. List Samples

Or you can list individual samples and their scores:

```bash
hawk list samples [EVAL_SET_ID] [--eval FILE] [--limit N]
```

## 4. Download Transcript

To get the full conversation for a specific sample:

```bash
hawk transcript <UUID>
```

The transcript includes full conversation with tool calls, scores, and metadata.

To get even more details, you can get the raw data by using `--raw`:

```bash
hawk transcript <UUID> --raw
```

### Batch Transcript Download

You can also download all transcripts for an entire eval set:

```bash
# Fetch all samples in an eval set
hawk transcripts <EVAL_SET_ID>

# Write to individual files in a directory
hawk transcripts <EVAL_SET_ID> --output-dir ./transcripts

# Limit number of samples
hawk transcripts <EVAL_SET_ID> --limit 10

# Raw JSON output (one JSON per line to stdout, or .json files with --output-dir)
hawk transcripts <EVAL_SET_ID> --raw
```

## Workflow

1. Run `hawk list eval-sets` to see available eval sets
2a. Run `hawk list evals <EVAL_SET_ID>` to see available evaluations
2b. or run `hawk list samples <EVAL_SET_ID>` to find samples of interest
3a. Run `hawk transcript <uuid>` to get full details on a single sample
3b. or run `hawk transcripts <eval_set_id> --output-dir ./transcripts` to download all
4. Read and analyze the transcript(s) to understand the agent's behavior

## Generality Labs deployment

The CLI has no built-in API default. Install the CLI version that matches the server (4.0.0) and point it at GL's deployment in `~/.config/hawk-cli/env`:

```bash
uv tool install "hawk[cli]==4.0.0"
hawk --version

mkdir -p ~/.config/hawk-cli
cat > ~/.config/hawk-cli/env <<'ENV'
HAWK_API_URL=https://api.hawk.hawk.generalitylabs.ai
HAWK_MIDDLEMAN_URL=https://middleman.hawk.generalitylabs.ai
HAWK_LOG_VIEWER_URL=https://viewer.hawk.hawk.generalitylabs.ai
ENV

hawk login            # add --no-browser in a devcontainer, SSH session or other headless environment
hawk list eval-sets
```

The CLI API URL and the browser viewer URL are different. To show an eval set to a person, link the viewer: `https://viewer.hawk.hawk.generalitylabs.ai/eval-set/<EVAL_SET_ID>`. The jobs page is `https://viewer.hawk.hawk.generalitylabs.ai/jobs`.
