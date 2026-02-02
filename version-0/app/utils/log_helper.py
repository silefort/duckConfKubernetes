def create_logger(prefix):
    """Crée une fonction de log avec un préfixe fixe."""
    def log(message):
        for line in message.split('\n'):
            print(f"[{prefix}] {line}")
    return log
