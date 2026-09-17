"""Unit tests for search aggregation, normalization, and PRISMA identification."""
import pytest
from app.search.aggregator import normalize_title, normalize_doi, PaperSearchAggregator
from app.search.base import Paper, SearchQuery

def test_normalize_title_and_doi():
    title1 = "Impact of COVID-19 on Global Mental Health: A Systematic Review!"
    title2 = "impact of covid-19 on global mental health: a systematic review"
    assert normalize_title(title1) == normalize_title(title2)

    doi1 = "https://doi.org/10.1016/j.jclinepi.2021.04.018"
    doi2 = "10.1016/j.jclinepi.2021.04.018"
    doi3 = "doi:10.1016/J.JCLINEPI.2021.04.018"
    assert normalize_doi(doi1) == normalize_doi(doi2) == normalize_doi(doi3)

def test_paper_model_validation():
    p = Paper(
        id="test_1",
        title="Test Open Access Study",
        authors=["Alice Smith", "Bob Jones"],
        year=2024,
        journal="PLOS ONE",
        doi="10.1371/journal.pone.0000000",
        oa_url="https://doi.org/10.1371/journal.pone.0000000",
        pdf_url="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0000000&type=printable"
    )
    assert p.is_open_access is True
    assert p.is_included_screening is True
