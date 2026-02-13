import logging
import sys

def create_logger(prefix):
    """Crée une fonction de log avec un préfixe fixe."""
    def log(message):
        for line in message.split('\n'):
            print(f"[{prefix}] {line}")
    return log

def setup_flask_logger(prefix):
    """Configure le logger Flask/werkzeug pour utiliser le même format."""
    class PrefixedHandler(logging.StreamHandler):
        def emit(self, record):
            print(f"[{prefix}] {self.format(record)}")

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = []
    werkzeug_logger.addHandler(PrefixedHandler(sys.stdout))
    werkzeug_logger.setLevel(logging.INFO)
