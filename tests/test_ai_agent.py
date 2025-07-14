import json
from unittest.mock import MagicMock
from app.ai_agent import AIAgent, RUN_COMMAND_TOOL


class DummyContainer:
    def run_command(self, command, stream_callback=None):
        return "hello"

    def exec_run(self, command, tty=True):
        class Result:
            output = b"hello"

        return Result()

    def stop(self):
        pass

    def remove(self):
        pass


class DummyOpenAI:
    class Responses:
        def __init__(self, outputs):
            self.outputs = outputs
            self.index = 0

        def create(self, **kwargs):
            resp = self.outputs[self.index]
            self.index += 1
            return resp

    def __init__(self, outputs):
        self.responses = self.Responses(outputs)


class DummyResponse:
    def __init__(self, output):
        self.output = output


class DummyOutputText:
    def __init__(self, text):
        self.type = "output_text"
        self.text = text


class DummyMessage:
    def __init__(self, content):
        self.type = "message"
        self.role = "assistant"
        self.content = [DummyOutputText(content)]


class DummyToolCall:
    def __init__(self, command):
        self.id = "call-id"
        self.type = "function_call"
        self.name = "run_command"
        self.arguments = json.dumps({"command": command})


def test_ai_agent_chat_runs_command(monkeypatch):
    dm = DummyContainer()
    tool_call = DummyToolCall("echo hello")
    response1 = DummyResponse([tool_call])
    response2 = DummyResponse([DummyMessage("done")])
    dummy_client = DummyOpenAI([response1, response2])
    monkeypatch.setattr("openai.OpenAI", lambda api_key, base_url=None: dummy_client)
    agent = AIAgent(dm, None, api_key="test")
    captured = []

    def cb(data):
        captured.append(data)

    result = agent.chat("hi", stream_callback=cb)
    assert result == "done"
    tool_messages = [m for m in agent.messages if m.get("role") == "tool"]
    assert tool_messages[0]["tool_call_id"] == "call-id"
    assert captured == ["ai@container:~$ echo hello\nhello"]


def test_ai_agent_chat_handles_error(monkeypatch):
    dm = DummyContainer()

    class ErrorCompletions:
        def create(self, **kwargs):
            import openai

            raise openai.APIConnectionError(message="fail", request=None)

    class ErrorClient:
        def __init__(self):
            self.responses = type(
                "responses",
                (),
                {"create": lambda **kwargs: ErrorCompletions().create(**kwargs)},
            )

    monkeypatch.setattr("openai.OpenAI", lambda api_key, base_url=None: ErrorClient())
    agent = AIAgent(dm, None, api_key="test")
    result = agent.chat("hi")
    assert result.startswith("Error communicating with language model")
