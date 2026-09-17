"""Base models and interfaces for paper search and PRISMA tracking."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Paper(BaseModel):
    id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = ""
    oa_url: Optional[str] = None
    pdf_url: Optional[str] = None
    citations: int = 0
    source: str = "Unknown"
    is_open_access: bool = True
    open_access_status: Optional[str] = "gold"  # gold, green, bronze, hybrid, etc.
    
    # PRISMA 2020 Screening fields
    is_included_screening: bool = True
    is_included_eligibility: bool = True
    is_included_synthesis: bool = True
    exclusion_stage: Optional[str] = None  # "screening", "eligibility", or None
    exclusion_reason: Optional[str] = None  # e.g., "Wrong population", "No control group", "Insufficient data"
    
    # Quantitative Meta-Analysis Extraction fields
    effect_type: Optional[str] = "Odds Ratio (OR)"  # OR, RR, SMD, MD, HR
    effect_size: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    standard_error: Optional[float] = None
    sample_size: Optional[int] = None
    intervention_name: Optional[str] = None
    control_name: Optional[str] = None
    outcome_measure: Optional[str] = None

class SearchQuery(BaseModel):
    keyword: str
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    max_results: int = 20
    sources: List[str] = Field(default_factory=lambda: ["openalex", "europe_pmc"])
    sort_by: str = "relevance"  # relevance, citations, year

class PrismaIdentification(BaseModel):
    total_records_identified: int = 0
    records_per_source: Dict[str, int] = Field(default_factory=dict)
    duplicate_records_removed: int = 0
    unique_records_screened: int = 0

class SearchResponse(BaseModel):
    query: str
    prisma_identification: PrismaIdentification
    papers: List[Paper] = Field(default_factory=list)
