from unittest.mock import MagicMock
from app.docker_tools import DockerManager

class DummyContainer:
    def exec_run(self, command, tty=True):
        class Result:
            output = b'test\n'
        return Result()

    def stop(self):
        pass

    def remove(self):
        pass

class DummyClient:
    def containers(self):
        pass


def test_run_command(monkeypatch):
    dm = DockerManager.__new__(DockerManager)
    dm.client = MagicMock()
    dm.container = DummyContainer()
    output = dm.run_command('echo test')
    assert output == 'test\n'
