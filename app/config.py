from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Google Drive
    google_credentials_file: str = "/data/token.json"
    # OAuth client (user sign-in mode, no service account). Used by `python -m app.authorize`.
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    # Folder where OCR results are written. Empty = same folder as the source CV.
    output_folder_id: str = ""
    # Recursive folder jobs move each finished subfolder here. Empty = leave them in place.
    processed_folder_id: str = ""

    # OCR
    ocr_lang: str = "en"
    pdf_dpi: int = 200
    max_pages: int = 10
    max_file_mb: int = 25
    # oneDNN CPU acceleration. Set false if Paddle crashes with oneDNN errors (slower, but safe).
    ocr_enable_mkldnn: bool = True

    # Optional shared secret; if set, clients must send it in the X-API-Key header.
    api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
