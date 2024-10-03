import aiohttp
import os
import pmss

import learning_observer.communication_protocol.integration
from learning_observer.log_event import debug_log
import learning_observer.prestartup
import learning_observer.settings

template = """[Task]\n{question}\n\n[Essay]\n{text}"""
rubric_template = """{task}\n\n[Rubric]\n{rubric}"""
gpt_responder = None

pmss.register_field(
    name='model',
    type=pmss.TYPES.string,
    description='Which model we wish to use with the GPT responder.'
)
pmss.register_field(
    name='api_key',
    type=pmss.TYPES.string,
    description='API Key required for connection.'
)
pmss.register_field(
    name='host',
    type=pmss.TYPES.string, # TODO this ought to be a hostname, but sometimes we want `None`
    description='Where to connect for the GPT usage.'
)

class GPTAPI:
    def chat_completion(self, prompt, system_prompt):
        '''
        Respond to user prompt
        '''
        raise NotImplementedError


class GPTInitializationError(Exception):
    '''Raise when GPT fails to initialize.
    This usually happens when the users forgets to
    provide information in the `creds.yaml` file.
    '''


class GPTRequestErorr(Exception):
    '''Raise when the GPT chat completion raises
    an exception
    '''


class OpenAIGPT(GPTAPI):
    def __init__(self, **kwargs):
        '''
        kwargs:
        - `model`: the GPT model we should use, defaults to `gpt-3.5-turbo-16k`
        - `api_key`: OpenAI api key, defaults to the `OPENAI_API_KEY` environment variable.
        '''
        super().__init__()
        self.model = kwargs.get('model', 'gpt-3.5-turbo-16k')
        self.api_key = kwargs.get('api_key', os.getenv('OPENAI_API_KEY'))
        if self.api_key is None:
            exception_text = 'Error while starting openai:\n'\
                'Please ensure that the API Key is correctly configured in '\
                '`creds.yaml` under `modules.writing_observer.gpt_responders.openai.api_key`, '\
                'or alternatively, set it as the `OPENAI_API_KEY` environment '\
                'variable.'
            raise GPTInitializationError(exception_text)

    async def chat_completion(self, prompt, system_prompt):
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}'}
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        content = {'model': self.model, 'messages': messages}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=content) as resp:
                json_resp = await resp.json()
                if resp.status == 200:
                    return json_resp['choices'][0]['message']['content']
                error = 'Error occured while making OpenAI request'
                if 'error' in json_resp:
                    error += f"\n{json_resp['error']['message']}"
                raise GPTRequestErorr(error)


class OllamaGPT(GPTAPI):
    '''GPT responder for handling request to the Ollama API
    TODO this ought to just use requests instead of the specific ollama package
    the format *should* be the same as the OpenAI responder. This will be one
    less external module to rely on.
    '''
    def __init__(self, **kwargs):
        '''
        kwargs
        - `model`: the GPT model we should use, defaults to `llama2`
        - `host`: Ollama server to connect to - the Ollama client will
                  default to `localhost:11434`.
        '''
        super().__init__()
        self.model = kwargs.get('model', 'llama2')
        # the Ollama client checks for the `OLLAMA_HOST` env variable
        # or defaults to `localhost:11434`. We provide a warning when
        # a specific host is not found.
        self.ollama_host = kwargs.get('host', os.getenv('OLLAMA_HOST', None))
        if self.ollama_host is None:
            debug_log('WARNING:: Ollama host not specified. Defaulting to '\
                      '`localhost:11434`.\nTo set a specific host, set '\
                      '`modules.writing_observer.gpt_responders.ollama.host` '\
                      'in `creds.yaml` or set the `OLLAMA_HOST` environment '\
                      'variable.\n'\
                      'If you wish to install Ollama and download a model, '\
                      'run the following commands:\n'\
                      '```bash\ncurl https://ollama.ai/install.sh | sh\n'\
                      'ollama run <desired_model>\n```')
            self.ollama_host = 'http://localhost:11434'

    async def chat_completion(self, prompt, system_prompt):
        '''Ollama only returns a single item compared to GPT returning a list
        '''
        url = f'{self.ollama_host}/api/chat'
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        content = {'model': self.model, 'messages': messages, 'stream': False}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=content) as resp:
                json_resp = await resp.json(content_type=None)
                if resp.status == 200:
                    return json_resp['message']['content']
                error = 'Error occured while making Ollama request'
                if 'error' in json_resp:
                    error += f"\n{json_resp['error']['message']}"
                raise GPTRequestErorr(error)


GPT_RESPONDERS = {
    'openai': OpenAIGPT,
    'ollama': OllamaGPT
}


@learning_observer.prestartup.register_startup_check
def initialize_gpt_responder():
    '''Iterate over the gpt_responders listed in `creds.yaml`
    and attempt to initialize it. On successful initialization
    of a responder, exit the this startup check. Otherwise,
    try the next one.
    '''
    global gpt_responder
    responder_type = learning_observer.settings.pmss_settings.type(types=['writing_observer', 'gpt_responder'])
    if responder_type not in GPT_RESPONDERS:
        raise KeyError(
            f'GPT Responder `{key}` is not yet configured on this system.\n'\
            f'The available responders are [{", ".join(GPT_RESPONDERS.keys())}].'
        )
    responder_kwargs = {
        'model': learning_observer.settings.pmss_settings.model(types=['writing_observer', 'gpt_responder']),
        'host': learning_observer.settings.pmss_settings.host(types=['writing_observer', 'gpt_responder']),
        'api_key': learning_observer.settings.pmss_settings.api_key(types=['writing_observer', 'gpt_responder'])
    }
    gpt_responder = GPT_RESPONDERS[responder_type](**responder_kwargs)
    debug_log(f'INFO:: Using GPT responder `{responder_type}` with model `{responder_kwargs["model"]}`')


@learning_observer.communication_protocol.integration.publish_function('wo_bulk_essay_analysis.gpt_essay_prompt')
async def process_student_essay(text, prompt, system_prompt, tags):
    '''
    This method processes text with a prompt through GPT.

    We use a closure to allow the system to connect to the memoization KVS.
    '''

    copy_tags = tags.copy()

    @learning_observer.cache.async_memoization()
    async def gpt(gpt_prompt):
        completion = await gpt_responder.chat_completion(gpt_prompt, system_prompt)
        return completion

    if len(prompt) == 0:
        output = {
            'text': text,
            'feedback': 'No prompt provided yet.',
            'prompt': prompt
        }
    elif len(text) == 0:
        output = {
            'text': text,
            'feedback': 'No text available for this student.',
            'prompt': prompt
        }
    else:
        copy_tags['student_text'] = text
        formatted_prompt = prompt.format(**copy_tags)

        output = {
            'text': text,
            'feedback': await gpt(formatted_prompt),
            'prompt': prompt
        }
    return output


async def test_responder():
    responder = OllamaGPT(model='llama2', host=None)
    response = await responder.chat_completion('Why is the sky blue?', 'You are a helper agent, please help fulfill user requests.')
    print('Response:', response)


if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(test_responder())
    loop.run_forever()
    loop.close()
