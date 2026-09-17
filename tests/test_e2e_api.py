"""End-to-end FastAPI endpoint integration test."""
import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_index_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "OpenJournalMetaAnalyzer" in res.text
    assert "PRISMA 2020" in res.text

def test_search_and_prisma_endpoints():
    # 1. Search endpoint
    search_payload = {
        "keyword": "crispr cas9",
        "year_start": 2021,
        "year_end": 2024,
        "max_results": 3,
        "sources": ["openalex", "europe_pmc"],
        "sort_by": "relevance"
    }
    res_search = client.post("/api/search", json=search_payload)
    assert res_search.status_code == 200
    data = res_search.json()
    assert "papers" in data
    assert len(data["papers"]) > 0
    papers = data["papers"]

    # 2. PRISMA counts endpoint
    res_counts = client.post("/api/prisma/counts?duplicates_removed=1", json=papers)
    assert res_counts.status_code == 200
    counts = res_counts.json()
    assert counts["records_identified"] >= len(papers)
    assert counts["studies_included_qualitative"] == len(papers)

    # 3. Meta-analysis calculation endpoint
    studies = [
        {"study_id": p["id"], "study_label": p["authors"][0] if p["authors"] else "Study", "effect_size": 1.4, "ci_lower": 1.1, "ci_upper": 1.8, "sample_size": 150}
        for p in papers
    ]
    res_meta = client.post("/api/meta-analysis/calculate", json={"studies": studies, "effect_metric": "OR"})
    assert res_meta.status_code == 200
    meta_json = res_meta.json()
    assert "statistics" in meta_json
    assert "forest_plot_spec" in meta_json
    assert meta_json["statistics"]["fixed_effect"]["pooled_effect"] > 0

    # 4. Evidence synthesis endpoint
    res_synth = client.post("/api/meta-analysis/synthesize", json={
        "keyword": "crispr cas9",
        "papers": papers,
        "meta_result": meta_json["statistics"]
    })
    assert res_synth.status_code == 200
    synth_json = res_synth.json()
    assert "PRISMA 2020" in synth_json["report_markdown"]
    assert "PICO" in synth_json["report_markdown"]

    # 5. Export CSV
    res_csv = client.post("/api/export/csv", json=papers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]

    # 6. Export BibTeX
    res_bib = client.post("/api/export/bibtex", json=papers)
    assert res_bib.status_code == 200
    assert "@article" in res_bib.text
