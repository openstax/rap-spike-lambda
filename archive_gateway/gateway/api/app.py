import logging

from flask import current_app, Blueprint

from ..extensions import api
from .endpoints.ping import ns as ping_namespace

LOG = logging.getLogger(__name__)


bp = Blueprint('api', __name__)

api.init_app(bp)

# Add namespaces
api.add_namespace(ping_namespace)

# register error handlers
@api.errorhandler
def default_error_handler(e):  # pragma: no cover
    message = 'An unhandled exception occurred.'
    LOG.exception(message)

    if not current_app.config['FLASK_DEBUG']:
        return {'message': message}, 500
