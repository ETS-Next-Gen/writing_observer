import learning_observer.cache
import learning_observer.communication_protocol.integration
import learning_observer.prestartup
import learning_observer.settings
import learning_observer.util
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
        lt_started = learning_observer.util.check_service(host, port)
        if not lt_started:
            raise learning_observer.prestartup.StartupCheck(
                f'A service was not found running on port {port}.\n'
                'Please make sure to run the LanguageTool server before starting the server. '
                'Run `java -cp languagetool-server.jar org.languagetool.server.HTTPServer --port {port} --allow-origin "*"` '
                'from within the `AWE_LanguageTool/awe_languagetool` directory.\n'
                'If the LanguageTool is already running on a different port, make sure to adjust '
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
