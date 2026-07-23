from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ArticleModel(BaseModel):
    source_id: str
    source_name: str
    title: str = Field(..., min_length=1)
    url: str
    published_date: str          # event_time: when the article was published
    ingestion_time: str = Field(default_factory=_now_iso)  # when WE learned about it (point-in-time)
    abstract: str
    full_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('url')
    def validate_url_string(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('URL must be a non-empty string')
        return v
    
    class Config:
        arbitrary_types_allowed = True


class MetricPointModel(BaseModel):
    """
    A single point-in-time observation of a quantitative signal
    (pageviews, message volume, market probability, insider filings...).
    event_date is the day the value refers to; ingestion_time is when we captured it.
    Both are kept so backtests can be reconstructed without look-ahead bias.
    """
    source_id: str               # e.g. 'wikipedia', 'stocktwits', 'polymarket'
    entity: str                  # ticker, wiki page title, market slug, keyword
    metric: str                  # e.g. 'wiki_pageviews', 'st_bull_ratio', 'pm_prob_yes'
    event_date: str              # YYYY-MM-DD
    value: float
    ingestion_time: str = Field(default_factory=_now_iso)
    metadata: Dict[str, Any] = Field(default_factory=dict)
