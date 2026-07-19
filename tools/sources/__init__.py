"""External job source adapters (WWR, YC, future Wellfound/Otta)."""

from tools.sources.wwr import fetch_wwr_jobs
from tools.sources.yc_jobs import fetch_yc_jobs

__all__ = ["fetch_wwr_jobs", "fetch_yc_jobs"]
