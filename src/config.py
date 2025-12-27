"""Application configuration"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    debug: bool = False
    demo_mode: bool = True
    log_level: str = "INFO"

    # Square API
    square_access_token: str = ""
    square_location_id: str = ""
    square_environment: str = "sandbox"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_to_numbers: str = ""

    # Slack
    slack_webhook_url: str = ""

    # Monitoring
    check_interval_minutes: int = 15
    low_stock_threshold_percentage: int = 20
    critical_stock_threshold_percentage: int = 5

    # Database
    database_url: str = "sqlite:///./stockalert.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def twilio_to_numbers_list(self) -> List[str]:
        """Parse comma-separated phone numbers"""
        if not self.twilio_to_numbers:
            return []
        return [num.strip() for num in self.twilio_to_numbers.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
