"""Tool-calling agent loop: answers natural-language questions about the
local data files in DATA_DIR by letting the model call the functions in
tools/data_tools.py and feeding the results back until it has a final answer.
"""

import sys

import boto3

from .tools.data_tools import TOOL_SPECS

REGION = "eu-west-2"
MODEL_ID = "amazon.nova-micro-v1:0"

SYSTEM_PROMPT = (
    "You are a data inspector assistant. Answer questions about the local "
    "data files using the list_files, inspect_schema, preview_rows, and "
    "summarize_column tools. Always call a tool to look at a file before "
    "answering a question about its contents - never guess. Keep answers concise."
)

# Hard cap on model<->tool round trips so a confused model can't loop forever.
MAX_TURNS = 8


def _build_tool_config() -> dict:
    return {
        "tools": [
            {
                "toolSpec": {
                    "name": spec["name"],
                    "description": spec["description"],
                    "inputSchema": {"json": spec["schema"]},
                }
            }
            for spec in TOOL_SPECS
        ]
    }


def _run_tool(name: str, tool_input: dict) -> dict:
    for spec in TOOL_SPECS:
        if spec["name"] == name:
            try:
                return {"result": spec["function"](**tool_input)}
            # Tool errors (bad filename, bad column, ...) get reported back to
            # the model as a failed tool result so it can retry or explain,
            # rather than crashing the whole conversation.
            except Exception as exc:
                return {"error": str(exc)}
    return {"error": f"Unknown tool: {name}"}


def ask(question: str) -> str:
    """Send `question` to the model, letting it call data-inspection tools as needed."""
    client = boto3.client("bedrock-runtime", region_name=REGION)
    tool_config = _build_tool_config()
    messages = [{"role": "user", "content": [{"text": question}]}]

    for _ in range(MAX_TURNS):
        response = client.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig=tool_config,
        )

        output_message = response["output"]["message"]
        messages.append(output_message)

        if response["stopReason"] != "tool_use":
            return "".join(
                block["text"] for block in output_message["content"] if "text" in block
            )

        tool_results = []
        for block in output_message["content"]:
            if "toolUse" not in block:
                continue
            tool_use = block["toolUse"]
            output = _run_tool(tool_use["name"], tool_use["input"])
            tool_results.append(
                {
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content": [{"json": output}],
                        "status": "error" if "error" in output else "success",
                    }
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return "Gave up after too many tool-calling turns without a final answer."


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if question:
        print(ask(question))
        return

    print("Ask a question about the data in ./data (Ctrl-D or 'exit' to quit).")
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question or question.lower() in {"exit", "quit"}:
            break
        print(ask(question))


if __name__ == "__main__":
    main()
