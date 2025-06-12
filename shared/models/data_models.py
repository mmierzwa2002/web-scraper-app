from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ScrapedData:
    url: str
    timestamp: datetime
    emails: List[str]
    addresses: List[str]
    phone_numbers: List[str]
    links: List[str]
    raw_content: Optional[str] = None

@dataclass
class ScrapeJob:
    job_id: str
    urls: List[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    results_count: int = 0