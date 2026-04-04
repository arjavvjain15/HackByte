import os


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def get_optional_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default
