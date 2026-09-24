from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class Source(BaseModel):
    id: int = Field(description="Unique citation identifier e.g. 1, 2, 3")
    title: str = Field(description="Title or domain of the source")
    url: str = Field(description="Original URL for citation")
    snippet: str = Field(description="Extracted textual content/evidence")

class SearchQuery(BaseModel):
    query: str = Field(description="Search engine query")
    purpose: str = Field(description="Why this query is needed for the section")

class ResearchPlan(BaseModel):
    topic: str
    target_audience: str
    sections: List[str] = Field(description="Report outline section titles")
    search_queries: List[SearchQuery] = Field(description="List of targeted queries for web research")

class ResearchState(BaseModel):
    topic: str
    report_type: str = "Technical Report"
    plan: Optional[ResearchPlan] = None
    sources: Dict[int, Source] = Field(default_factory=dict)
    draft_report: str = ""
    final_report: str = ""
    critique_notes: str = ""
    is_approved: bool = False
    logs: List[str] = Field(default_factory=list)
