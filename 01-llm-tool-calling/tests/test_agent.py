"""Tests for the tool-dispatch loop in agent.py, using a fake Bedrock client.

Live Bedrock access isn't available in CI/dev (account model access pending),
so these verify the request/response plumbing - tool dispatch, message
formatting, and the turn-limit guard - without calling AWS.
"""

from llm_tool_calling.de_agent import agent


class FakeBedrockClient:
    """Returns each response in `responses` in order, one per `converse` call."""

    def __init__(self, responses):
        self._responses = iter(responses)
        self.calls = []

    def converse(self, **kwargs):
        # Snapshot messages: agent.ask() keeps appending to the same list
        # object after this call returns, so a bare reference would reflect
        # later turns too.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return next(self._responses)


def _tool_use_response(tool_use_id, name, tool_input):
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"toolUse": {"toolUseId": tool_use_id, "name": name, "input": tool_input}}],
            }
        },
        "stopReason": "tool_use",
    }


def _final_text_response(text):
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
    }


def test_ask_dispatches_tool_call_and_returns_final_text(monkeypatch):
    fake_client = FakeBedrockClient(
        [
            _tool_use_response("t1", "list_files", {}),
            _final_text_response("There is one file: orders.csv"),
        ]
    )
    monkeypatch.setattr(agent.boto3, "client", lambda *a, **k: fake_client)

    answer = agent.ask("what files are there?")

    assert answer == "There is one file: orders.csv"
    assert len(fake_client.calls) == 2

    # Second call must carry the tool's actual result back to the model.
    second_call_messages = fake_client.calls[1]["messages"]
    tool_result_message = second_call_messages[-1]
    tool_result = tool_result_message["content"][0]["toolResult"]
    assert tool_result["toolUseId"] == "t1"
    assert tool_result["status"] == "success"
    assert tool_result["content"][0]["json"]["result"] == ["orders.csv"]


def test_ask_reports_tool_errors_back_to_the_model(monkeypatch):
    fake_client = FakeBedrockClient(
        [
            _tool_use_response("t1", "inspect_schema", {"filename": "nope.csv"}),
            _final_text_response("That file doesn't exist."),
        ]
    )
    monkeypatch.setattr(agent.boto3, "client", lambda *a, **k: fake_client)

    answer = agent.ask("describe nope.csv")

    assert answer == "That file doesn't exist."
    tool_result = fake_client.calls[1]["messages"][-1]["content"][0]["toolResult"]
    assert tool_result["status"] == "error"
    assert "No such file" in tool_result["content"][0]["json"]["error"]


def test_ask_gives_up_after_max_turns(monkeypatch):
    # A model that only ever asks for tools, never answers, must not loop forever.
    responses = [_tool_use_response("t", "list_files", {}) for _ in range(agent.MAX_TURNS)]
    fake_client = FakeBedrockClient(responses)
    monkeypatch.setattr(agent.boto3, "client", lambda *a, **k: fake_client)

    answer = agent.ask("loop forever")

    assert "Gave up" in answer
    assert len(fake_client.calls) == agent.MAX_TURNS
