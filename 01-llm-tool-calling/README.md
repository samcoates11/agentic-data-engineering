# 01 · LLM Tool Calling

First project in the [Agentic Data Engineering](../README.md) portfolio. It's a hands-on exploration of **LLM tool calling (function calling)** using **AWS Bedrock** as the model provider — the foundational pattern that every later agent in this portfolio (Snowflake agent, data quality agent, pipeline investigator, etc.) builds on.

The goal: give an LLM a set of Python functions ("tools") describing what they do and what arguments they take, let the model decide when to call them based on a user's request, execute the calls, and feed the results back so the model can produce a final answer. This is the core loop behind every "agent."

## Status

This project is a working scaffold, not a finished agent. What exists today:

- A confirmed, working connection to AWS and to a Bedrock model via the `boto3` Bedrock Runtime `converse` API ([bedrock_test.py](src/llm_tool_calling/de_agent/bedrock_test.py)).
- A sanity check that AWS credentials are configured correctly ([aws_test.py](src/llm_tool_calling/de_agent/aws_test.py)).
- Placeholder modules for the agent loop and its tools ([agent.py](src/llm_tool_calling/de_agent/agent.py), [tools/data_tools.py](src/llm_tool_calling/de_agent/tools/data_tools.py)), not yet implemented.

In other words: the AWS/Bedrock plumbing is proven to work; the actual tool-calling agent loop is the next thing to build on top of it.

## How it works (the tool-calling pattern)

Bedrock's `Converse` API supports **tool use**: alongside the conversation messages, you pass a `toolConfig` describing each available tool as a JSON schema (name, description, input parameters). The model can then respond either with a normal text answer, or with a request to invoke one or more tools. The calling code is responsible for:

1. Sending the user's message plus the tool definitions to the model.
2. Checking whether the model's response is a tool-use request.
3. Running the corresponding local Python function with the arguments the model supplied.
4. Sending the tool's result back to the model as a new message.
5. Repeating until the model returns a final text answer.

For this project, the intended shape is:

- **[agent.py](src/llm_tool_calling/de_agent/agent.py)** — the agent loop described above: builds the tool config from the functions in `tools/`, calls Bedrock, dispatches tool calls, and loops until done.
- **[tools/data_tools.py](src/llm_tool_calling/de_agent/tools/data_tools.py)** — the actual Python functions exposed to the model as tools. Given the portfolio's data engineering focus, these are intended to be things like inspecting a dataset, running a query, validating a schema, etc. (not yet implemented).
- **[bedrock_test.py](src/llm_tool_calling/de_agent/bedrock_test.py)** — a minimal, standalone example of calling Bedrock's `converse` API (no tools), useful as a reference for the request/response shape.
- **[aws_test.py](src/llm_tool_calling/de_agent/aws_test.py)** — confirms your local AWS credentials resolve correctly by calling STS `get_caller_identity`.

## Project structure

```
01-llm-tool-calling/
├── pyproject.toml              # Project metadata, dependencies, and build config (managed by uv)
├── uv.lock                     # Locked dependency versions
├── .python-version             # Pins Python 3.14 for this project
├── README.md
└── src/
    └── llm_tool_calling/        # Importable package (module-name set explicitly in pyproject.toml,
        ├── __init__.py          # since the distribution name "01-llm-tool-calling" isn't a valid Python identifier)
        └── de_agent/
            ├── __init__.py      # `main()` — the console-script entry point
            ├── agent.py         # Tool-calling agent loop (placeholder)
            ├── aws_test.py      # AWS credentials sanity check
            ├── bedrock_test.py  # Minimal Bedrock `converse` API example
            └── tools/
                ├── __init__.py
                └── data_tools.py # Tool functions exposed to the model (placeholder)
```

## Prerequisites

- **Python 3.14** (pinned via `.python-version`).
- **[uv](https://docs.astral.sh/uv/)** for dependency management and running scripts.
- **An AWS account with Bedrock model access enabled** for the region you intend to use. The example scripts default to:
  - Region: `eu-west-2`
  - Model: `amazon.nova-micro-v1:0`

  Request access to this model in the [Bedrock console](https://console.aws.amazon.com/bedrock/) under "Model access" if you haven't already, or change `REGION` / `MODEL_ID` in [bedrock_test.py](src/llm_tool_calling/de_agent/bedrock_test.py) to a model/region you do have access to.
- **AWS credentials configured locally** — via `aws configure`, AWS SSO (`aws sso login`), environment variables, or an assumed role. `boto3` will pick these up automatically through the standard AWS credential chain.

## Setup

From this directory (`01-llm-tool-calling/`):

```bash
# Install dependencies into a local virtual environment
uv sync
```

This creates a `.venv` and installs everything listed in `pyproject.toml` / `uv.lock` (currently `boto3`, plus `pytest` as a dev dependency).

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

This sends a single prompt ("Explain a data pipeline in one sentence.") to the configured Bedrock model and prints its response. If this fails with an access-denied error, double-check model access is enabled for your account in the Bedrock console for the target region.

### 3. Run the package entry point

```bash
uv run 01-llm-tool-calling
```

This currently just prints a hello-world message from [`__init__.py`](src/llm_tool_calling/de_agent/__init__.py) — it will become the entry point for running the full tool-calling agent once `agent.py` and `tools/data_tools.py` are implemented.

### 4. Run tests

```bash
uv run pytest
```

(No tests exist yet — `pytest` is set up as a dev dependency for when they're added.)

## Next steps for this project

To turn this into a working tool-calling agent:

1. Implement one or more functions in `tools/data_tools.py` (e.g. a function to list files in a directory, read a CSV's schema, or query a sample dataset), each with a clear docstring/description.
2. Build a `toolConfig` in `agent.py` from those functions' names, descriptions, and parameters.
3. Implement the loop in `agent.py`: call `converse` with the tool config → check for a `toolUse` block in the response → execute the matching Python function → send the result back as a `toolResult` message → repeat until the model replies with plain text.
4. Wire `agent.py` into `__init__.py`'s `main()` so `uv run 01-llm-tool-calling` runs the full agent instead of the hello-world placeholder.
