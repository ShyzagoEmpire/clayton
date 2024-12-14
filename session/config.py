from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    MINIAPP_USERNAME: str
    REFERRAL: str
    END_POINT: str
    TASKS: list[str]
    AUTO_TASKS: bool
    AUTO_GAMES_STACK: bool

settings = Settings()