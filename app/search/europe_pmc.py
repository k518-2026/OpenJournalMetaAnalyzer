"""Europe PMC API client for searching open access biomedical and life sciences papers."""
import logging
from typing import List, Optional
import httpx
from .base import Paper
from ..config import config

logger = logging.getLogger(__name__)

class EuropePmcClient:
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
        """Search Europe PMC for Open Access articles."""
        query_parts = [f"({keyword})", "OPEN_ACCESS:Y"]
        if year_start and year_end:
            query_parts.append(f"PUB_YEAR:[{year_start} TO {year_end}]")
        elif year_start:
            query_parts.append(f"PUB_YEAR:[{year_start} TO 2099]")
        elif year_end:
            query_parts.append(f"PUB_YEAR:[1900 TO {year_end}]")

        full_query = " AND ".join(query_parts)
        params = {
            "query": full_query,
            "format": "json",
            "pageSize": min(max_results, 50),
            "resultType": "core"
        }

        if sort_by == "citations":
            params["sort"] = "CITED desc"
        elif sort_by == "year":
            params["sort"] = "P_PD_DATE desc"

        papers: List[Paper] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(config.EUROPE_PMC_API_URL, params=params, headers=self.headers)
                if resp.status_code != 200:
                    logger.warning(f"Europe PMC returned status {resp.status_code}: {resp.text[:200]}")
                    return []
                data = resp.json()
                results = data.get("resultList", {}).get("result", [])

                for item in results:
                    paper_id = item.get("id") or item.get("pmcid") or item.get("doi") or str(len(papers))
                    title = item.get("title", "Untitled Paper").rstrip(".")
                    
                    # Authors
                    authors_str = item.get("authorString", "")
                    authors = [a.strip() for a in authors_str.split(",") if a.strip()] if authors_str else []
                    
                    year = None
                    if item.get("pubYear"):
                        try:
                            year = int(item.get("pubYear"))
                        except ValueError:
                            pass
                    
                    journal = item.get("journalTitle") or "Europe PMC Open Access"
                    doi = item.get("doi")
                    abstract = item.get("abstractText", "")
                    
                    # OA links
                    pmcid = item.get("pmcid")
                    oa_url = f"https://europepmc.org/article/PMC/{pmcid}" if pmcid else None
                    if not oa_url and doi:
                        oa_url = f"https://doi.org/{doi}"
                        
                    pdf_url = None
                    for url_obj in item.get("fullTextUrlList", {}).get("fullTextUrl", []):
                        if url_obj.get("documentStyle") == "pdf":
                            pdf_url = url_obj.get("url")
                            break

                    citations = item.get("citedByCount", 0)
                    
                    papers.append(
                        Paper(
                            id=f"europepmc_{paper_id}",
                            title=title,
                            authors=authors,
                            year=year,
                            journal=journal,
                            doi=doi,
                            abstract=abstract,
                            oa_url=oa_url,
                            pdf_url=pdf_url,
                            citations=citations,
                            source="Europe PMC (Open Access)",
                            is_open_access=True,
                            open_access_status="gold"
                        )
                    )
        except Exception as e:
            logger.error(f"Error querying Europe PMC API: {e}", exc_info=True)
            return []
            
        return papers
