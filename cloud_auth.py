"""Production-only shared credentials; never read dotenv or expose the value in config."""
import os


def shared_api_key():
    if os.environ.get('VERCEL_ENV') != 'production':
        return ''
    return os.environ.get('TYPESAFE_API_KEY', '').strip()
