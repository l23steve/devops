import json
from unittest.mock import MagicMock
from app.ai_agent import AIAgent, RUN_COMMAND_TOOL

class DummyContainer:
    def run_command(self, command):
        return 'hello'
    def exec_run(self, command, tty=True):
        class Result:
            output = b'hello'
        return Result()

    def stop(self):
        pass

    def remove(self):
        pass

class DummyOpenAI:
    class Chat:
        class Completions:
            def __init__(self, responses):
                self.responses = responses
                self.index = 0

            def create(self, **kwargs):
                resp = self.responses[self.index]
                self.index += 1
                return resp
    def __init__(self, responses):
        self.chat = type('chat', (), {'completions': self.Chat.Completions(responses)})

class DummyResponse:
    def __init__(self, message, tool_calls=None, finish_reason=None):
        self.choices = [type('choice', (), {
            'message': message,
            'finish_reason': finish_reason
        })]

class DummyMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

class DummyToolCall:
    def __init__(self, command):
        self.function = type('func', (), {'name': 'run_command', 'arguments': json.dumps({'command': command})})


def test_ai_agent_chat_runs_command(monkeypatch):
    dm = DummyContainer()
    tool_call = DummyToolCall('echo hello')
    response1 = DummyResponse(DummyMessage(tool_calls=[tool_call]))
    response2 = DummyResponse(DummyMessage(content='done'))
    dummy_client = DummyOpenAI([response1, response2])
    monkeypatch.setattr('openai.OpenAI', lambda api_key, base_url=None: dummy_client)
    agent = AIAgent(dm, api_key='test')
    result = agent.chat('hi')
    assert result == 'done'


def test_ai_agent_chat_handles_error(monkeypatch):
    dm = DummyContainer()

    class ErrorCompletions:
        def create(self, **kwargs):
            import openai
            raise openai.APIConnectionError(message='fail', request=None)

    class ErrorClient:
        def __init__(self):
            self.chat = type('chat', (), {'completions': ErrorCompletions()})

    monkeypatch.setattr('openai.OpenAI', lambda api_key, base_url=None: ErrorClient())
    agent = AIAgent(dm, api_key='test')
    result = agent.chat('hi')
    assert result.startswith('Error communicating with language model')
