# Writing Observer

The Writing Observer platform provides and interface to various Natural Language Processing (NLP) tools.

## Config (`creds.yaml`)

```yaml
modules:
    writing_observer:
        use_nlp: false
        use_google_documents: false
        use_languagetool: false
        languagetool_host: http://localhost
        languagetool_port: 8081
        verbose: false
        gpt_responders:
          ollama:
            model: llama2
            host: http://localhost:11434
          openai:
            model: gpt-3.5-turbo-16k
            api_key: your-secret-key
```

- `use_nlp` (bool, default false): determines whether or not we should use the AWE libraries or not to compute NLP indicators.
- `use_google_documents` (bool, default false): determines if we should attempt to update the reconstruct reducer with the ground truth (Google docs API).
- `use_languagetool` (bool, default false): enable LanguageTool information to be processed.
  - `languagetool_host` (str, default `localhost`): host that is running LanguageTool
  - `languagetool_port` (int, default 8081): which port LanguageTool is running on
- `verbose` (bool, default false): print state whenever reducers update
- `gpt_responders` (obj, {}): how you wish to connect to GPTs. See dedicated section below for more details.

## Available tools

There are 3 primary tools we have available to us.

1. NLP indicators to suppoprt automated writing evaulation. These indicators provide information about the text (parts of speech, main ideas, % of academic langauge, etc.).
2. LanguageTool to detect specific errors being made in text. These errors include spelling and incorrect word usage.
3. Ability to interface with LLMs.

## GPT Responders

We allow users to define different ways of interacting with GPTs. The system will iterate over each listed responder and return the first successfully configured one. The current supported responders are:

### Ollama

- `model` (str, default `llama2`): the model you wish to use.
- `host` (str, default `http://localhost:11434`): the host running Ollama. You may also set the `OLLAMA_HOST` environment variable.

### OpenAI

- `model` (str, default `gpt-3.5-turbo-16k`): the model you wish to use.
- `api_key` (str): your secret openai API key. You may also set this with the `OPENAI_API_KEY` environment variable.
