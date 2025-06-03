import learning_observer.integrations.canvas
import learning_observer.integrations.google
import learning_observer.integrations.schoology

INTEGRATIONS = {}


def register_integrations(app):
    # TODO go through settings to determine which of these we want to enable on the system
    # these keys correspond to roster source values
    INTEGRATIONS['google'] = learning_observer.integrations.google.register_endpoints(app)
    INTEGRATIONS['schoology'] = learning_observer.integrations.schoology.register_endpoints(app)
    canvas_providers = ['ncsu-canvas']
    for provider in canvas_providers:
        provider_endpoint_registrar = learning_observer.integrations.canvas.setup_canvas_provider(provider)
        # TODO check that provider doesn't already exist and is trying to be overwritten
        INTEGRATIONS[provider] = provider_endpoint_registrar(app)
