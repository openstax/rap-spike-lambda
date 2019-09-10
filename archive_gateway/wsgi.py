import os

from gateway import create_app

app = create_app()

if __name__ == '__main__':  # pragma: nocov
    port = int(os.environ.get('FLASK_PORT', 5000))
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    app.run(host=host, port=port)
