from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TLE_QUERY_BASE_URL: str = (
        "https://celestrak.org/NORAD/elements/gp.php?FORMAT=tle&GROUP=ACTIVE"
    )

    TLE_DATA_FILENAME: str = "satellites.tle"
    TLE_DATA_DIRECTORY: str = "data/"

    class Config:
        env_file = ".env"


settings: Settings = Settings()
