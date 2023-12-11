import asyncio
import functools
import openai
import os
from concurrent.futures import ThreadPoolExecutor

import learning_observer.communication_protocol.integration
import learning_observer.prestartup
import learning_observer.settings

template = """[Task]\n{question}\n\n[Essay]\n{text}"""
rubric_template = """{task}\n\n[Rubric]\n{rubric}"""
gpt_responder = None


class GPTAPI:
    def chat_completion(self, prompt, system_prompt):
        '''
        Respond to user prompt
        '''
        raise NotImplementedError


class OpenAIGPT(GPTAPI):
    def __init__(self, model):
        super().__init__()
        self.model = model
        openai.api_key = learning_observer.settings.module_setting('writing_observer', 'openai_api_key', os.getenv('OPENAI_API_KEY'))

    def chat_completion(self, prompt, system_prompt):
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        return openai.ChatCompletion.create(model=self.model, messages=messages)


@learning_observer.prestartup.register_startup_check
def initialize_gpt_responder():
    global gpt_responder
    gpt_responder = OpenAIGPT('gpt-3.5-turbo-16k')
    if openai.api_key is None:
        exception_text = 'OpenAI API Key Missing:\n'\
            'Please ensure that the API Key is correctly configured in '\
            '`creds.yaml` under `modules.writing_observer.openai_api_key`, '\
            'or alternatively, set it as the `OPENAI_API_KEY` environment '\
            'variable.\n'\
            'You may also disable the `wo_bulk_essay_analysis` by '\
            'uninstalling it from your local environment.'
        raise learning_observer.prestartup.StartupCheck(exception_text)


@learning_observer.communication_protocol.integration.publish_function('wo_bulk_essay_analysis.gpt_essay_prompt')
async def process_student_essay(text, prompt, system_prompt, tags):
    '''
    This method processes text with a prompt through GPT.

    We use a closure to allow the system to connect to the memoization KVS.
    '''

    executor = ThreadPoolExecutor()
    copy_tags = tags.copy()

    @learning_observer.cache.async_memoization()
    async def gpt(gpt_prompt):
        loop = asyncio.get_event_loop()
        partial = functools.partial(gpt_responder.chat_completion, prompt=gpt_prompt, system_prompt=system_prompt)
        completion = await loop.run_in_executor(executor, partial)
        return completion["choices"][0]["message"]["content"]

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
