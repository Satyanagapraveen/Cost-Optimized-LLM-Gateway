import yaml
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class ModelsConfig(BaseModel):
    high_tier: str
    mid_tier: str
    low_tier: str
    embedding: str
class CachingConfig(BaseModel):
    enabled: bool=True
    similarity_threshold: float= Field(default=0.95, ge=0.0, le=1.0)
    ttl_seconds: int=Field(default=86400, gt=0)

class RoutingRuleConfig(BaseModel):
    name: str
    condition: str
    keywords: Optional[List[str]]=None
    threshold: Optional[int]=None
    target_tier: str

class FallbackConfig(BaseModel):
    primary: str
    backup: str


class YAMLConfig(BaseModel):
    models: ModelsConfig
    caching: CachingConfig
    routing_rules: List[RoutingRuleConfig]
    fallbacks: List[FallbackConfig]

class EnvSettings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env", extra="ignore")
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None


class AppConfig(BaseModel):
    yaml: YAMLConfig
    env: EnvSettings


def load_config(yaml_file_path: str = "config.yaml") -> AppConfig:
    resolved_path = Path(yaml_file_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as file:
        raw_yaml_data = yaml.safe_load(file)

    parsed_yaml = YAMLConfig(**raw_yaml_data)
    loaded_env = EnvSettings()

    return AppConfig(yaml=parsed_yaml, env=loaded_env)


config = load_config()