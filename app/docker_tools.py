import docker

class DockerManager:
    def __init__(self, image: str = "ubuntu:latest"):
        self.client = docker.from_env()
        self.container = self.client.containers.run(image, tty=True, detach=True)

    def run_command(self, command: str) -> str:
        """Run a command inside the container and return its output."""
        exec_result = self.container.exec_run(command, tty=True)
        output = exec_result.output
        if isinstance(output, bytes):
            return output.decode()
        return output

    def stop(self):
        if self.container:
            self.container.stop()
            self.container.remove()
