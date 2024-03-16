from core.utils import generate_random_string


def generate_referral_code() -> str:
    return generate_random_string(16)
