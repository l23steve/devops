import docker

class DockerManager:
    def __init__(self, image: str = "ubuntu:latest"):
        self.client = docker.from_env()
        self.container = self.client.containers.run(image, tty=True, detach=True)

    def run_command(self, command: str, stream_callback=None) -> str:
        """Run a command inside the container and return its output.

        If ``stream_callback`` is provided, the decoded output is also passed to
        the callback. This allows callers to forward command output while
        retaining the return value for compatibility.
        """
        exec_result = self.container.exec_run(command, tty=True)
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
