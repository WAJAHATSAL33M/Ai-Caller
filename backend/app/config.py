from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    company_name: str = "Your Call Center"
    company_website: str = ""
    sales_email: str = ""
    public_base_url: str = ""
    sales_voice: str = "marin"
    sip_provider_url: str
    sip_username: str
    sip_password: str
    sip_caller_number: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
