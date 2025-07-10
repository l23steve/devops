import re
from pathlib import Path


def test_dockerfile_base_image():
    dockerfile_path = Path('Dockerfile')
    content = dockerfile_path.read_text()
    first_line = content.splitlines()[0]
    assert first_line == 'FROM ubuntu:22.04', f"Base image should be ubuntu:22.04, got: {first_line}"
