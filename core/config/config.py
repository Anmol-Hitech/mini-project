from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    DATABASE_URL:str
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    EMAIL_ADDRESS:str
    EMAIL_PASSWORD:str
    SMTP_SERVER:str
    SMTP_PORT:int
    INVITE_KEY:str
    INVITE_TOKEN_EXPIRE_TIME:int
    model_config=SettingsConfigDict(env_file=".env")

    
settings=Settings()