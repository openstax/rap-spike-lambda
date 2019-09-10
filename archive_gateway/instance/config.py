import os
import uuid

# MAIN FLASK APPLICATION
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
FLASK_APP = 'wsgi.py'
DEBUG = os.environ.get('FLASK_DEBUG', False)
SECRET_KEY = os.environ.get('SESSION_SECRET', str(uuid.uuid4()))
