"""Live integration test for OpenAlex and Europe PMC APIs."""
import pytest
from app.search.aggregator import PaperSearchAggregator
from app.search.base import SearchQuery

@pytest.mark.anyio
async def test_live_search_aggregation():
    agg = PaperSearchAggregator()
    query = SearchQuery(
        keyword="crispr cas9",
        max_results=5,
        sources=["openalex", "europe_pmc"],
        sort_by="relevance"
    )
    resp = await agg.search(query)
    assert resp is not None
    assert len(resp.papers) > 0
    assert resp.prisma_identification.total_records_identified > 0
    assert resp.prisma_identification.unique_records_screened > 0

    first_paper = resp.papers[0]
    assert first_paper.title
    assert first_paper.is_open_access is True