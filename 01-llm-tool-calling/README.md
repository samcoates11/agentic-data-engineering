# 01 · LLM Tool Calling

First project in the [Agentic Data Engineering](../README.md) portfolio. It's a hands-on exploration of **LLM tool calling (function calling)** using **AWS Bedrock** as the model provider — the foundational pattern that every later agent in this portfolio (Snowflake agent, data quality agent, pipeline investigator, etc.) builds on.

The goal: give an LLM a set of Python functions ("tools") describing what they do and what arguments they take, let the model decide when to call them based on a user's request, execute the calls, and feed the results back so the model can produce a final answer. This is the core loop behind every "agent."

## What it does

A **data inspector agent**: ask natural-language questions about a local CSV/Parquet file, and the model calls tools to list available files, inspect a file's schema (columns, dtypes, null counts), preview sample rows, or summarize a column's values — then answers using what it found, rather than guessing.

```
$ uv run 01-llm-tool-calling "How many rows are in orders.csv, and are there any missing values?"
orders.csv has 10 rows. The "customer" and "quantity" columns each have 1 missing value.
```

This use case is deliberately dependency-free (no warehouse, no cloud resource beyond the Bedrock call itself) so the project stays focused on the tool-calling mechanics. The same four-tool shape — *list things, inspect schema, preview/sample data, summarize a field* — is what projects 02 (Snowflake) and 06 (AWS) are meant to adapt against a real warehouse and cloud services respectively.

## Status

Working end to end at the code level — tool dispatch, error handling, and the model loop are implemented and unit-tested with a mocked Bedrock client (`uv run pytest`). The one thing not yet verified **live** is an actual model response, because this AWS account currently doesn't have Bedrock model access enabled (`ValidationException: Error 002: Access to Bedrock models is not allowed for this account`) — an AWS Support case is the fix, not a code change. Once that clears, `uv run 01-llm-tool-calling "..."` should work immediately with no further changes.

## How it works (the tool-calling pattern)

Bedrock's `Converse` API supports **tool use**: alongside the conversation messages, you pass a `toolConfig` describing each available tool as a JSON schema (name, description, input parameters). The model can then respond either with a normal text answer, or with a request to invoke one or more tools. [agent.py](src/llm_tool_calling/de_agent/agent.py)'s `ask()` function implements the loop:

1. Send the user's question, plus the tool definitions, to the model.
2. Check `stopReason` on the response — if it isn't `"tool_use"`, return the model's text answer.
3. Otherwise, for each `toolUse` block in the response, call the matching Python function in `tools/data_tools.py` with the arguments the model supplied (tool errors — bad filename, unknown column — are caught and reported back to the model as a failed `toolResult`, not raised).
4. Append the tool result(s) to the conversation and go back to step 1.
5. Give up after `MAX_TURNS` (8) round trips, so a confused model can't loop forever.

### Files

- **[agent.py](src/llm_tool_calling/de_agent/agent.py)** — the loop above: builds the `toolConfig` from `TOOL_SPECS`, calls Bedrock, dispatches tool calls, and exposes `ask(question)` plus a CLI `main()` (single question as an argument, or an interactive prompt loop if none given).
- **[tools/data_tools.py](src/llm_tool_calling/de_agent/tools/data_tools.py)** — the four tool functions (`list_files`, `inspect_schema`, `preview_rows`, `summarize_column`) backed by `pandas`, each paired with its Bedrock tool spec in `TOOL_SPECS`. File access is scoped to `DATA_DIR` (defaults to `./data`, overridable via the `DATA_DIR` env var) and rejects paths that try to escape it.
- **[bedrock_test.py](src/llm_tool_calling/de_agent/bedrock_test.py)** — a minimal, standalone example of calling Bedrock's `converse` API with no tools; a reference for the request/response shape, independent of the rest of the package.
- **[aws_test.py](src/llm_tool_calling/de_agent/aws_test.py)** — confirms your local AWS credentials resolve correctly by calling STS `get_caller_identity`.
- **[data/orders.csv](data/orders.csv)** — a small sample dataset (10 rows, with a couple of deliberately missing values) to try the agent against out of the box.
- **[tests/](tests/)** — `test_data_tools.py` exercises the tools directly against the sample dataset; `test_agent.py` exercises the tool-dispatch loop (including error handling and the turn-limit guard) against a fake Bedrock client, so the loop logic is verified without needing live AWS access.

## Project structure

```
01-llm-tool-calling/
├── pyproject.toml              # Project metadata, dependencies, and build config (managed by uv)
├── uv.lock                     # Locked dependency versions
├── .python-version             # Pins Python 3.14 for this project
├── README.md
├── data/
│   └── orders.csv              # Sample dataset the agent can be asked about
├── tests/
│   ├── test_data_tools.py      # Unit tests for the tool functions
│   └── test_agent.py           # Tool-dispatch loop tests, using a fake Bedrock client
└── src/
    └── llm_tool_calling/        # Importable package (module-name set explicitly in pyproject.toml,
        ├── __init__.py          # since the distribution name "01-llm-tool-calling" isn't a valid Python identifier)
        └── de_agent/
            ├── __init__.py      # Re-exports `agent.main` as the console-script entry point
            ├── agent.py         # Tool-calling agent loop (ask(), main())
            ├── aws_test.py      # AWS credentials sanity check
            ├── bedrock_test.py  # Minimal Bedrock `converse` API example
            └── tools/
                ├── __init__.py
                └── data_tools.py # Tool functions + their Bedrock tool specs (TOOL_SPECS)
```

## Prerequisites

- **Python 3.14** (pinned via `.python-version`).
- **[uv](https://docs.astral.sh/uv/)** for dependency management and running scripts.
- **An AWS account with Bedrock model access enabled** for the region you intend to use. The scripts default to:
  - Region: `eu-west-2`
  - Model: `amazon.nova-micro-v1:0`

  AWS has retired the manual "Model access" console page — serverless foundation models now auto-enable on first invocation per account/region. If you still get `ValidationException: Error 002: Access to Bedrock models is not allowed for this account`, that's an account-level restriction (common on new/low-spend accounts); open an AWS Support case (Service: Bedrock) requesting on-demand access — this isn't something fixable from the console or code.
- **IAM permissions** for the identity you're using: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `bedrock:Converse`, and `bedrock:ConverseStream` on the model's ARN (plus `bedrock:ListFoundationModels` / `bedrock:GetFoundationModel` if you want to run discovery commands).
- **AWS credentials configured locally** — via `aws configure`, AWS SSO (`aws sso login`), environment variables, or an assumed role. `boto3` picks these up automatically through the standard AWS credential chain.

## Setup

From this directory (`01-llm-tool-calling/`):

```bash
# Install dependencies into a local virtual environment
uv sync
```

This creates a `.venv` and installs everything listed in `pyproject.toml` / `uv.lock` (`boto3`, `pandas`, `pyarrow`, plus `pytest` as a dev dependency).

## Usage

### 1. Confirm your AWS credentials are working

```bash
uv run python src/llm_tool_calling/de_agent/aws_test.py
```

You should see your AWS account identity (account ID, user/role ARN) printed. If this fails, fix your AWS credentials before continuing — nothing else in this project will work without them.

### 2. Confirm Bedrock access works

```bash
uv run python src/llm_tool_calling/de_agent/bedrock_test.py
```

This sends a single prompt ("Explain a data pipeline in one sentence.") to the configured Bedrock model and prints its response. If this fails, see the Bedrock access troubleshooting note under Prerequisites above.

### 3. Ask the data inspector agent a question

```bash
# One-off question
uv run 01-llm-tool-calling "What columns are in orders.csv and which have missing values?"

# Or drop into an interactive prompt
uv run 01-llm-tool-calling
> how many unique customers are there?
> exit
```

By default it looks in `./data` (the sample `orders.csv` lives there already). Point it at a different folder by setting `DATA_DIR`:

```bash
DATA_DIR=/path/to/your/csvs uv run 01-llm-tool-calling "describe this data"
```

### 4. Run tests

```bash
uv run pytest
```

Runs the tool-function tests against the sample dataset and the agent loop tests against a fake Bedrock client — no AWS credentials or live access required for `uv run pytest` to pass.

## Adapting this for a new data source

The pattern to copy for projects 02 (Snowflake) and 06 (AWS): keep `agent.py`'s loop as-is, and swap out `tools/data_tools.py` for a module with the same shape — one function per capability (list, inspect schema, sample/query, summarize), each paired with a `TOOL_SPECS` entry describing it to the model. Everything else (the Converse request/response handling, error-to-tool-result wiring, the turn-limit guard) carries over unchanged.
