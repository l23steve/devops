import docker
import os

class DockerManager:
    def __init__(self, image: str | None = None, volume_host_path: str = "docker_data", dockerfile_path: str = "Dockerfile"):
        self.client = docker.from_env()
        self.volume_host_path = os.path.abspath(volume_host_path)
        os.makedirs(self.volume_host_path, exist_ok=True)

        if image is None:
            image = "ubuntu-aws-cli:latest"
            build_path = os.path.dirname(os.path.abspath(dockerfile_path)) or "."
            dockerfile = os.path.basename(dockerfile_path)
            self.client.images.build(path=build_path, dockerfile=dockerfile, tag=image)

        self.container = self.client.containers.run(
            image,
            tty=True,
            detach=True,
            volumes={self.volume_host_path: {"bind": "/data", "mode": "rw"}},
            environment=dict(os.environ),
        )

    def run_command(self, command: str, stream_callback=None) -> str:
        """Run a command inside the container and return its output.

        If ``stream_callback`` is provided, the decoded output is also passed to
        the callback. This allows callers to forward command output while
        retaining the return value for compatibility.
        """
        # Use a shell to correctly handle compound commands and operators
        exec_result = self.container.exec_run(["bash", "-lc", command], tty=True)
        output = exec_result.output
        if isinstance(output, bytes):
            output = output.decode()
        if stream_callback:
            stream_callback(output)
        return output

    def stop(self):
        if self.container:
            self.container.stop()
            self.container.remove()
