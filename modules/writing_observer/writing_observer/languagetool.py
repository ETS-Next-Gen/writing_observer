import requests

import learning_observer.cache
import learning_observer.communication_protocol.integration
import learning_observer.prestartup
import learning_observer.settings
from awe_languagetool import languagetoolClient

client = None
DEFAULT_PORT = 8081


@learning_observer.prestartup.register_startup_check
def check_languagetool_running():
    '''
    We want to make sure that the Language Tool service is running on the server
    before starting the rest of the Learning Observer platform.

    TODO create a stub function for language tool to return dummy data when testing.
    See aggregator.py:214 for stubbing in the function
    '''
    if learning_observer.settings.module_setting('writing_observer', 'use_languagetool', False):
        host = learning_observer.settings.module_setting('writing_observer', 'languagetool_host', 'localhost')
        port = learning_observer.settings.module_setting('writing_observer', 'languagetool_port', DEFAULT_PORT)

        # HACK the following code is a hack to check if the LanguageTool Server is up and running or not
        # We ought to set the LT Client object on startup (here); however,
        # the LT Client has no way of telling us whether the Server is running or not.
        # i.e. the LT Client runs normally even without the server running.
        # Thus, we manually make a request to the server to and check the response.
        lt_started = False
        try:
            resp = requests.get(f'http://{host}:{port}/v2/check', params={'text': 'test', 'language': 'en-US'})
            lt_started = resp.status_code == 200
        except requests.ConnectionError:
            pass

        if not lt_started:
            raise learning_observer.prestartup.StartupCheck(
                f'LanguageTool Server was not found running on port {port}.\n'
                'Please make sure to run the LanguageTool Server before starting Learning Observer.\n'
                'From within your Python environment, run\n'
                '```python\nfrom awe_languagetool import languagetoolServer\nlanguagetoolServer.runServer()\n```.\n'
                'If the LanguageTool is already running on a diffrent port, make sure to adjust '
                'the `writing_observer.languagetool_port` setting in the `creds.yaml`.'
            )


def initialize_client():
    '''
    Language Tool requires a client to connect with the server.
    This method checks to see if we've created a client yet and
    initializes one if we haven't.
    '''
    global client
    if client is None:
        port = learning_observer.settings.module_setting('writing_observer', 'languagetool_port', DEFAULT_PORT)
        client = languagetoolClient.languagetoolClient(port=port)


@learning_observer.communication_protocol.integration.publish_function('writing_observer.languagetool')
async def process_texts(texts):
    '''
    This method processes the text through Language Tool and returns
    the output.

    We use a closure to allow the system to initialize the memoization KVS.
    '''

    initialize_client()

    @learning_observer.cache.async_memoization()
    async def process_text(text):
        return await client.summarizeText(text)

    output = []
    for t in texts:
        text = t.get('text', '')
        text_data = await process_text(text)
        text_data['text'] = text
        text_data['provenance'] = t['provenance']
        output.append(text_data)
    return output
