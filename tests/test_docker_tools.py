from unittest.mock import MagicMock
import os
from app.docker_tools import DockerManager

class DummyContainer:
    def exec_run(self, command, tty=True, stream=False):
        class Result:
            output = b'test\n'
        return Result()

    def stop(self):
        pass

    def remove(self):
        pass

class DummyClient:
    def __init__(self):
        self.built = {}

        class Images:
            def build(_, path=None, dockerfile=None, tag=None):
                self.built['path'] = path
                self.built['dockerfile'] = dockerfile
                self.built['tag'] = tag
                return None, None

        self.images = Images()
        self.containers = None


def test_init_passes_env_and_volume(monkeypatch, tmp_path):
    captured = {}

    class DummyContainers:
        def run(self, image, tty=True, detach=True, volumes=None, environment=None):
            captured['image'] = image
            captured['volumes'] = volumes
            captured['environment'] = environment
            return DummyContainer()

    dummy_client = DummyClient()
    dummy_client.containers = DummyContainers()
    monkeypatch.setattr('docker.from_env', lambda: dummy_client)

    dm = DockerManager(volume_host_path=tmp_path, dockerfile_path='Dockerfile')
    assert captured['image'] == 'ubuntu-aws-cli:latest'
    assert str(tmp_path.resolve()) in captured['volumes']
    assert captured['environment']['PATH'] == os.environ['PATH']
    assert dummy_client.built['tag'] == 'ubuntu-aws-cli:latest'
    assert dummy_client.built['dockerfile'] == 'Dockerfile'
    dm.stop()


def test_run_command(monkeypatch):
    dm = DockerManager.__new__(DockerManager)
    dm.client = MagicMock()
    dm.container = DummyContainer()
    output = dm.run_command('echo test')
    assert output == 'test\n'


def test_run_command_streams(monkeypatch):
    dm = DockerManager.__new__(DockerManager)
    dm.client = MagicMock()
    dm.container = DummyContainer()
    captured = []

    def cb(data):
        captured.append(data)

    output = dm.run_command('echo test', stream_callback=cb)
    assert output == 'test\n'
    assert captured == ['test\n']


def test_run_command_handles_shell_operators(monkeypatch):
    captured = {}

    class DummyContainerShell:
        def exec_run(self, command, tty=True, stream=False):
            captured['command'] = command

            class Result:
                output = b'test\n'

            return Result()

        def stop(self):
            pass

        def remove(self):
            pass

    dm = DockerManager.__new__(DockerManager)
    dm.client = MagicMock()
    dm.container = DummyContainerShell()

    output = dm.run_command('echo test && echo done')

    assert captured['command'][0].endswith('bash')
    assert captured['command'][1] in ('-c', '-lc')
    assert captured['command'][2] == 'echo test && echo done'
    assert output == 'test\n'
