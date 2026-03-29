from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'development'
    log_level: str = 'INFO'

    discord_bot_token: str
    discord_guild_id: int
    discord_admin_role_ids: str = ''
    discord_uploader_role_ids: str = ''
    discord_viewer_role_ids: str = ''
    allowed_channel_ids: str = ''

    google_service_account_file: str
    google_drive_root_folder_id: str
    google_drive_shared_drive_id: str = ''
    google_drive_use_shared_drive: bool = True

    database_url: str = 'sqlite:///./bot.db'

    max_upload_mb: int = 25
    allowed_extensions: str = 'pdf,docx,xlsx,pptx,txt,png,jpg,jpeg'
    date_format: str = '%Y%m%d'

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def admin_roles(self) -> set[int]:
        return parse_csv_ints(self.discord_admin_role_ids)

    @property
    def uploader_roles(self) -> set[int]:
        return parse_csv_ints(self.discord_uploader_role_ids)

    @property
    def viewer_roles(self) -> set[int]:
        return parse_csv_ints(self.discord_viewer_role_ids)

    @property
    def channel_allowlist(self) -> set[int]:
        return parse_csv_ints(self.allowed_channel_ids)

    @property
    def extensions(self) -> set[str]:
        return {token.strip().lower() for token in self.allowed_extensions.split(',') if token.strip()}


def parse_csv_ints(raw: str) -> set[int]:
    if not raw:
        return set()
    return {int(token.strip()) for token in raw.split(',') if token.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
