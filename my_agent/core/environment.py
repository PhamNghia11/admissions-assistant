import os
from dataclasses import dataclass
from pathlib import Path


def load_local_env(env_file: str = ".env") -> None:
    env_path = Path(env_file)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class EnvironmentConfig:
    openrouter_api_key: str
    openrouter_base_url: str
    default_model: str
    embedding_model: str

    @classmethod
    def load(cls, env_file: str = ".env") -> "EnvironmentConfig":
        load_local_env(env_file)
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
        os.environ["OPENROUTER_API_BASE"] = base_url
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
            openrouter_base_url=base_url,
            default_model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-lite-001"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"),
        )

    def validate_openrouter(self) -> None:
        if not self.openrouter_api_key:
            raise RuntimeError("Thieu OPENROUTER_API_KEY trong bien moi truong hoac file .env.")
