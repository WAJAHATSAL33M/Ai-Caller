from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "sqlite:///./sales.db"
    company_name: str = "Your Call Center"
    company_website: str = ""
    sales_email: str = ""
    public_base_url: str = ""
    sales_voice: str = "marin"
    sales_model: str = "gpt-realtime-2.1"
    # Legacy SIP starter settings; no longer needed for the Twilio pathway.
    sip_provider_url: str = ""
    sip_username: str = ""
    sip_password: str = ""
    sip_caller_number: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    sales_admin_key: str = ""
    enable_outbound_calls: bool = False
    approved_sales_facts: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
