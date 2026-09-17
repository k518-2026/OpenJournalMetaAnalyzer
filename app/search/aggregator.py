"""Aggregator for multi-source academic search and PRISMA 2020 Identification metrics."""
import asyncio
import re
from typing import List, Dict, Set
from .base import Paper, SearchQuery, SearchResponse, PrismaIdentification
from .openalex import OpenAlexClient
from .europe_pmc import EuropePmcClient

def normalize_title(title: str) -> str:
    """Normalize paper title for fuzzy duplicate detection."""
    return re.sub(r"[^a-zA-Z0-9]", "", title.lower())

def normalize_doi(doi: str) -> str:
    """Normalize DOI string."""
    if not doi:
        return ""
    d = doi.strip().lower()
    for prefix in ["https://doi.org/", "http://doi.org/", "doi:"]:
        if d.startswith(prefix):
            d = d[len(prefix):]
    return d.strip()

class PaperSearchAggregator:
    def __init__(self):
        self.openalex = OpenAlexClient()
        self.europe_pmc = EuropePmcClient()

    async def search(self, query: SearchQuery) -> SearchResponse:
        tasks = []
        source_keys = []
        
        if "openalex" in query.sources:
            tasks.append(
                self.openalex.search(
                    keyword=query.keyword,
                    max_results=query.max_results,
                    year_start=query.year_start,
                    year_end=query.year_end,
                    sort_by=query.sort_by
                )
            )
            source_keys.append("OpenAlex")

        if "europe_pmc" in query.sources:
            tasks.append(
                self.europe_pmc.search(
                    keyword=query.keyword,
                    max_results=query.max_results,
                    year_start=query.year_start,
                    year_end=query.year_end,
                    sort_by=query.sort_by
                )
            )
            source_keys.append("Europe PMC")

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        records_per_source: Dict[str, int] = {}
        all_papers: List[Paper] = []
        
        for key, res in zip(source_keys, results):
            if isinstance(res, list):
                records_per_source[key] = len(res)
                all_papers.extend(res)
            else:
                records_per_source[key] = 0

        total_identified = len(all_papers)

        # Deduplication using normalized DOI and normalized Title
        seen_dois: Set[str] = set()
        seen_titles: Set[str] = set()
        unique_papers: List[Paper] = []
        duplicate_count = 0

        for paper in all_papers:
            norm_doi = normalize_doi(paper.doi) if paper.doi else None
            norm_tit = normalize_title(paper.title) if paper.title else None

            is_dup = False
            if norm_doi and norm_doi in seen_dois:
                is_dup = True
            elif norm_tit and len(norm_tit) > 15 and norm_tit in seen_titles:
                is_dup = True

            if is_dup:
                duplicate_count += 1
                # Try to enrich existing paper if PDF url was missing
                for existing in unique_papers:
                    if (norm_doi and normalize_doi(existing.doi) == norm_doi) or \
                       (norm_tit and normalize_title(existing.title) == norm_tit):
                        if not existing.pdf_url and paper.pdf_url:
                            existing.pdf_url = paper.pdf_url
                        if not existing.oa_url and paper.oa_url:
                            existing.oa_url = paper.oa_url
                        if not existing.abstract and paper.abstract:
                            existing.abstract = paper.abstract
                        if paper.citations > existing.citations:
                            existing.citations = paper.citations
                        break
            else:
                if norm_doi:
                    seen_dois.add(norm_doi)
                if norm_tit and len(norm_tit) > 15:
                    seen_titles.add(norm_tit)
                unique_papers.append(paper)

        # Sorting
        if query.sort_by == "citations":
            unique_papers.sort(key=lambda p: p.citations, reverse=True)
        elif query.sort_by == "year":
            unique_papers.sort(key=lambda p: p.year or 0, reverse=True)

        prisma_id = PrismaIdentification(
            total_records_identified=total_identified,
            records_per_source=records_per_source,
            duplicate_records_removed=duplicate_count,
            unique_records_screened=len(unique_papers)
        )

        return SearchResponse(
            query=query.keyword,
            prisma_identification=prisma_id,
            papers=unique_papers
        )
