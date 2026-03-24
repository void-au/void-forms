import json
from pathlib import Path

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
            data = json.load(fp)

        config = SitesConfig.model_validate(data)
        if not config.sites:
            raise ValueError("At least one site must be configured")
        return cls(config.sites)

    def get_site(self, site_id: str) -> SiteConfig | None:
        return self._sites_by_id.get(site_id)
