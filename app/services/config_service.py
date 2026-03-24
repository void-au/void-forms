import os
from pathlib import Path

import yaml

from app.models.config import SiteConfig, SitesConfig


class SiteRegistry:
    def __init__(self, sites: list[SiteConfig]):
        self._sites_by_id = {site.site_id: site for site in sites}

    @classmethod
    def from_file(cls, file_path: str) -> "SiteRegistry":
        config_path = Path(file_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Sites config file not found: {file_path}")

        with config_path.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}

        config = SitesConfig.model_validate(data)
        if not config.sites:
            raise ValueError("At least one site must be configured")

        resolved_sites = [cls._resolve_site_secrets(site) for site in config.sites]
        return cls(resolved_sites)

    @staticmethod
    def _resolve_site_secrets(site: SiteConfig) -> SiteConfig:
        if site.turnstile_secret_env:
            secret = os.getenv(site.turnstile_secret_env)
            if not secret:
                raise ValueError(
                    f"Turnstile secret env var '{site.turnstile_secret_env}' is missing for site '{site.site_id}'"
                )
            return site.model_copy(update={"turnstile_secret": secret})

        if site.turnstile_secret:
            return site

        raise ValueError(
            f"Site '{site.site_id}' must define either turnstile_secret or turnstile_secret_env"
        )

    def get_site(self, site_id: str) -> SiteConfig | None:
        return self._sites_by_id.get(site_id)
