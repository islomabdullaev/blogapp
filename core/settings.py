from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    password: str = ...
    user: str = ...
    db: str = ...
    host: str = ...
    port: str = ...
    model_config = SettingsConfigDict(env_prefix="postgres_")

    @property
    def adsn(self):
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def dsn(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    host: str = ...
    port: int = ...
    model_config = SettingsConfigDict(env_prefix="redis_")

    @property
    def dsn(self):
        return f"redis://{self.host}:{self.port}"


class JWTSettings(BaseSettings):
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    model_config = SettingsConfigDict(env_prefix="jwt_")


class Settings(BaseSettings):
    postgres: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()
    jwt: JWTSettings = JWTSettings()
