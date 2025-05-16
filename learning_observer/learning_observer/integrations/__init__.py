import learning_observer.integrations.google
import learning_observer.integrations.canvas

# Perhaps instead we should have a google and a canvas variable here
# perhaps the canvas endpoint knows how which canvas instance to fetch
INTEGRATIONS = {}


def register_integrations(app):
    # TODO check if we want this or not
    INTEGRATIONS['google'] = learning_observer.integrations.google.register_endpoints(app)
    # TODO pull from settings
    canvas_providers = ['ncsu-canvas']
    for provider in canvas_providers:
        provider_endpoint_registrar = learning_observer.integrations.canvas.setup_canvas_provider(provider)
        # TODO check that provider doesn't already exist and is trying to be overwritten
        INTEGRATIONS[provider] = provider_endpoint_registrar(app)
