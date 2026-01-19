from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator

class ArticleModel(BaseModel):
    source_id: str
    source_name: str
    title: str = Field(..., min_length=1)
    url: str
    published_date: str
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
