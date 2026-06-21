from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    cors_origins: str = "*"

    # data: yfinance | indian_api | alpaca
    data_provider: str = "yfinance"
    indian_api_base_url: str = ""        # base URL of a deployed Indian-Stock-Market-API instance
    alpaca_key_id: str = ""              # NEVER hardcode - env only (US/crypto, optional)
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    twelvedata_api_key: str = ""   # free key at twelvedata.com - works from Render

    db_url: str = "sqlite:///./trading.db"

    # paper account + risk model (INR defaults)
    starting_cash: float = 1_000_000.0   # 10 lakh paper
    risk_per_trade_pct: float = 0.5
    max_open_positions: int = 5
    max_daily_loss_pct: float = 3.0

    benchmark: str = "^NSEI"             # NIFTY 50
    default_watchlist: str = (
        "RELIANCE.NS,TCS.NS,HDFCBANK.NS,INFY.NS,ICICIBANK.NS,SBIN.NS"
    )

    @property
    def cors_list(self):
        return [o.strip() for o in self.cors_origins.split(",")] if self.cors_origins else ["*"]

    @property
    def watchlist(self):
        return [t.strip() for t in self.default_watchlist.split(",") if t.strip()]


settings = Settings()
