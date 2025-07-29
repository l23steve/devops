# Cloud Manager AI

This project aims to provide an AI access to a docker container where it can build out its own environment, write its own scripts, and run its own code and third party software, all with internet access.

It will be given an assignment by the user and will work iteratively in an effort to complete the assignments before reporting back to the user.

All terminal output will be streamed via a websocket to the user. Websockets are also how the user will communicate with the AI, but using a different message type than the terminal output.

## Environment Variables

The application expects certain variables to be present in the environment. A
`.env` file can be used during development and will be loaded automatically.

- `OPENAI_KEY` – API key used for interacting with the language model. Without
  this key the AI cannot access the OpenAI/OpenRouter API and will be unable to
  respond to requests that require it.
- Optional AWS credential variables such as `AWS_ACCESS_KEY_ID` and
  `AWS_SECRET_ACCESS_KEY` may also be provided if the AI needs to interact with
  AWS services through the container's preinstalled AWS CLI.
