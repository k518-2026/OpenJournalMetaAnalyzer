"""OpenAlex API client for searching open access scientific papers."""
import logging
from typing import List, Optional
import httpx
from .base import Paper
from ..config import config

logger = logging.getLogger(__name__)

def reconstruct_abstract(inverted_index: Optional[dict]) -> str:
    """Reconstruct text from OpenAlex abstract_inverted_index."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    pos_word_pairs = []
    for word, positions in inverted_index.items():
        for pos in positions:
            pos_word_pairs.append((pos, word))
    pos_word_pairs.sort(key=lambda x: x[0])
    return " ".join(word for _, word in pos_word_pairs)

class OpenAlexClient:
    def __init__(self, timeout: float = config.HTTP_TIMEOUT_SECONDS):
        self.timeout = timeout
        self.headers = {
            "User-Agent": config.USER_AGENT,
            "Accept": "application/json"
        }

    async def search(
        self,
        keyword: str,
        max_results: int = 20,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        sort_by: str = "relevance"
    ) -> List[Paper]:
        """Search OpenAlex for Open-Access papers."""
        filters = ["is_oa:true"]
        if year_start and year_end:
            filters.append(f"publication_year:{year_start}-{year_end}")
        elif year_start:
            filters.append(f"publication_year:>{year_start - 1}")
        elif year_end:
            filters.append(f"publication_year:<{year_end + 1}")

        params = {
            "search": keyword,
            "filter": ",".join(filters),
            "per_page": min(max_results, 50)
        }

        if sort_by == "citations":
            params["sort"] = "cited_by_count:desc"
        elif sort_by == "year":
            params["sort"] = "publication_year:desc"

        papers: List[Paper] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(config.OPENALEX_API_URL, params=params, headers=self.headers)
                if resp.status_code != 200:
                    logger.warning(f"OpenAlex returned status {resp.status_code}: {resp.text[:200]}")
                    return []
                data = resp.json()
                results = data.get("results", [])

                for item in results:
                    paper_id = item.get("id", "").replace("https://openalex.org/", "")
                    title = item.get("title") or "Untitled Paper"
                    
                    # Authors
                    authors = []
                    for auth in item.get("authorships", []):
                        author_obj = auth.get("author", {})
                        if author_obj.get("display_name"):
                            authors.append(author_obj.get("display_name"))
                    
                    year = item.get("publication_year")
                    
                    # Journal / Venue
                    primary_loc = item.get("primary_location") or {}
                    source_obj = primary_loc.get("source") or {}
                    journal = source_obj.get("display_name") or "Open Access Repository"
                    
                    doi = item.get("doi")
                    if doi and doi.startswith("https://doi.org/"):
                        doi = doi.replace("https://doi.org/", "")
                    
                    abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
                    
                    # Open Access URLs
                    oa_info = item.get("open_access", {})
                    oa_url = oa_info.get("oa_url") or primary_loc.get("landing_page_url")
                    pdf_url = primary_loc.get("pdf_url")
                    oa_status = oa_info.get("oa_status", "gold")
                    
                    citations = item.get("cited_by_count", 0)
                    
                    papers.append(
                        Paper(
                            id=f"openalex_{paper_id}",
                            title=title,
                            authors=authors,
                            year=year,
                            journal=journal,
                            doi=doi,
                            abstract=abstract,
                            oa_url=oa_url,
                            pdf_url=pdf_url,
                            citations=citations,
                            source="OpenAlex (Open Access)",
                            is_open_access=True,
                            open_access_status=oa_status
                        )
                    )
        except Exception as e:
            logger.error(f"Error querying OpenAlex API: {e}", exc_info=True)
            return []
            
        return papers
