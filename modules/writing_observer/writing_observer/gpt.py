import openai

import learning_observer.communication_protocol.integration


model = 'gpt-3.5-turbo-16k'
template = """{question}\n\n{text}"""


@learning_observer.communication_protocol.integration.publish_function('writing_observer.gpt_essay_prompt')
async def process_student_essay(text, prompt):
    '''
    This method processes text with a prompt through GPT.

    We use a closure to allow the system to connect to the memoization KVS.
    '''

    @learning_observer.cache.async_memoization()
    async def gpt(gpt_prompt):
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": gpt_prompt}]
        )
        return completion["choices"][0]["message"]["content"]

    if len(prompt) == 0:
        output = {
            'text': text,
            'feedback': ''
        }
    else:
        output = {
            'text': text,
            'feedback': await gpt(template.format(question=prompt, text=text))
        }
    return output
