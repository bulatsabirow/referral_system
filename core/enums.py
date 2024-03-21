import enum


class ErrorDetails(str, enum.Enum):
    USER_NOT_FOUND = "User with entered id not found."
    REFERRAL_CODE_NOT_FOUND = "Referral code with entered id doesn't exist."
    REFERRAL_CODE_DOESNT_EXIST = "Referral code does not exist."
    EXPIRED_REFERRAL_CODE = "Referral code was expired. Please use another one."
    REFERRAL_CODE_ALREADY_USED = "Referral code was already used."
    INVALID_REFRESH_TOKEN = "Invalid refresh token. Please try login again."
    ACTIVE_REFERRAL_CODE_ALREADY_EXISTS = "Active referral code already exists"
