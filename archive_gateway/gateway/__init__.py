from . import factory


def create_app(settings_override=None):
    return factory.create_app(__name__,
                              __path__,
                              settings_override)
