import re
import logging
import sys

def create_logger(prefix):
    """Crée une fonction de log avec un préfixe fixe."""
    def log(message):
        for line in message.split('\n'):
            print(line)
    return log

_ACCESS_LOG_RE = re.compile(r'"((?:GET|POST|PUT|DELETE|PATCH) \S+) HTTP/\S+" (\d+)')

def setup_flask_logger(prefix):
    """Configure le logger Flask/werkzeug : access logs uniquement, format condensé."""
    class AccessLogHandler(logging.StreamHandler):
        def emit(self, record):
            msg = self.format(record)
            match = _ACCESS_LOG_RE.search(msg)
            if match:
                print(f"{match.group(1)} -> {match.group(2)}")

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = []
    werkzeug_logger.addHandler(AccessLogHandler(sys.stdout))
    werkzeug_logger.setLevel(logging.INFO)
