import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "noah.hansen1323@gmail.com")
    MAIL_FROM = os.environ.get("MAIL_FROM", "onboarding@resend.dev")

    # Cache static files for 1 year (browsers won't re-fetch)
    SEND_FILE_MAX_AGE_DEFAULT = 31536000


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
