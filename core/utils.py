import secrets


def generate_random_string(length: int):
    length = int(0.75 * length)
    return secrets.token_urlsafe(length)
