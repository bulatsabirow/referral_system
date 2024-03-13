import secrets


def generate_referral_code() -> str:
    return secrets.token_urlsafe(12)
