from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    crustdata_api_key: str = ""
    unsiloed_api_key: str = ""
    producthunt_api_key: str = ""
    producthunt_api_secret: str = ""
    backend_url: str = "http://localhost:8000"
    use_mock: bool = True

    # Comma-separated origins for browser → API (only needed if frontend calls API
    # directly). Example: https://my-app.ondigitalocean.app
    cors_origins: str = ""

    # OpenRouter base URL (OpenAI-compatible)
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Default models — all Llama 3.3 70B via OpenRouter
    fast_model: str = "meta-llama/llama-3.3-70b-instruct"
    memo_model: str = "meta-llama/llama-3.3-70b-instruct"


settings = Settings()
