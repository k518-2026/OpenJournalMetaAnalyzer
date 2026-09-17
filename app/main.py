"""FastAPI web server and API routes for OpenJournalMetaAnalyzer."""
import csv
import io
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import config
from .search.base import SearchQuery, SearchResponse, Paper, PrismaIdentification
from .search.aggregator import PaperSearchAggregator
from .meta_analysis.statistics import calculate_meta_analysis, MetaAnalysisResult
from .meta_analysis.extractor import enrich_paper_with_extracted_metrics
from .meta_analysis.synthesizer import EvidenceSynthesizer
from .meta_analysis.forest_plot import generate_forest_plot_spec

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Open-Access Journal Search, PRISMA 2020 Flow Tracking & Meta-Analysis Web Application"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Search aggregator instance
aggregator = PaperSearchAggregator()

# Pydantic request models
class ScreenUpdateRequest(BaseModel):
    papers: List[Paper]

class MetaAnalysisRequest(BaseModel):
    studies: List[Dict[str, Any]]
    effect_metric: str = "OR"

class SynthesisRequest(BaseModel):
    keyword: str
    papers: List[Paper]
    meta_result: Optional[MetaAnalysisResult] = None
    gemini_api_key: Optional[str] = None

class PrismaFlowCounts(BaseModel):
    records_identified: int
    duplicates_removed: int
    records_screened: int
    records_excluded_screening: int
    full_text_assessed: int
    full_text_excluded: int
    studies_included_qualitative: int
    studies_included_quantitative: int
    exclusion_reasons: Dict[str, int]

from .search.translator import translate_query

@app.post("/api/search", response_model=SearchResponse)
async def api_search(query: SearchQuery):
    """Search open-access papers and extract preliminary statistical indicators."""
    orig_kw = query.keyword.strip()
    if not orig_kw:
        raise HTTPException(status_code=400, detail="Search keyword cannot be empty.")
    
    # Auto-translate Japanese query to English if needed
    eng_kw, was_trans = translate_query(orig_kw)
    query.keyword = eng_kw
    
    resp = await aggregator.search(query)
    resp.original_query = orig_kw
    resp.was_translated = was_trans
    
    # Enrich each paper with automatic metric extraction
    enriched_papers = []
    for idx, p in enumerate(resp.papers, 1):
        enriched = enrich_paper_with_extracted_metrics(p, fallback_index=idx)
        enriched_papers.append(enriched)
    
    resp.papers = enriched_papers
    return resp

@app.post("/api/prisma/counts", response_model=PrismaFlowCounts)
async def api_prisma_counts(papers: List[Paper] = Body(...), duplicates_removed: int = 0):
    """Compute PRISMA 2020 flow diagram box counts based on paper inclusion states."""
    total_screened = len(papers)
    total_identified = total_screened + duplicates_removed
    
    # 1. Screening stage
    excluded_screening = [p for p in papers if not p.is_included_screening]
    passed_screening = [p for p in papers if p.is_included_screening]
    
    # 2. Eligibility stage
    excluded_eligibility = [p for p in passed_screening if not p.is_included_eligibility]
    passed_eligibility = [p for p in passed_screening if p.is_included_eligibility]
    
    # 3. Included stage
    included_qual = [p for p in passed_eligibility if p.is_included_synthesis]
    included_quant = [p for p in included_qual if p.effect_size is not None]

    reasons: Dict[str, int] = {}
    for p in papers:
        if p.exclusion_reason:
            r = p.exclusion_reason.strip()
            reasons[r] = reasons.get(r, 0) + 1

    return PrismaFlowCounts(
        records_identified=total_identified,
        duplicates_removed=duplicates_removed,
        records_screened=total_screened,
        records_excluded_screening=len(excluded_screening),
        full_text_assessed=len(passed_screening),
        full_text_excluded=len(excluded_eligibility),
        studies_included_qualitative=len(included_qual),
        studies_included_quantitative=len(included_quant),
        exclusion_reasons=reasons
    )

@app.post("/api/meta-analysis/calculate")
async def api_calculate_meta_analysis(req: MetaAnalysisRequest):
    """Run Fixed and Random effects meta-analysis and generate Plotly forest plot spec."""
    if not req.studies:
        raise HTTPException(status_code=400, detail="No study effect data provided for meta-analysis.")

    result = calculate_meta_analysis(req.studies, effect_metric=req.effect_metric)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Unable to compute meta-analysis. Ensure study effect sizes and confidence intervals are valid numbers (e.g. Lower < Upper)."
        )

    forest_spec = generate_forest_plot_spec(result)
    return {
        "statistics": result.model_dump(),
        "forest_plot_spec": forest_spec
    }

@app.post("/api/meta-analysis/synthesize")
async def api_synthesize(req: SynthesisRequest):
    """Generate PRISMA 2020 compliant qualitative evidence synthesis report."""
    synthesizer = EvidenceSynthesizer(api_key=req.gemini_api_key)
    report_md = await synthesizer.generate_prisma_synthesis(
        keyword=req.keyword,
        included_papers=req.papers,
        meta_result=req.meta_result
    )
    return {"report_markdown": report_md}

@app.post("/api/export/csv")
async def api_export_csv(papers: List[Paper] = Body(...)):
    """Export selected papers dataset as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Title", "Authors", "Year", "Journal", "DOI", 
        "OpenAccessURL", "PDF_URL", "Citations", "EffectType",
        "EffectSize", "CI_Lower", "CI_Upper", "SampleSize", "IncludedInSynthesis"
    ])
    for p in papers:
        writer.writerow([
            p.id, p.title, "; ".join(p.authors), p.year or "", p.journal or "", p.doi or "",
            p.oa_url or "", p.pdf_url or "", p.citations, p.effect_type or "",
            p.effect_size or "", p.ci_lower or "", p.ci_upper or "", p.sample_size or "",
            p.is_included_synthesis
        ])
    
    csv_bytes = output.getvalue().encode("utf-8-sig")  # utf-8 with BOM for Excel compatibility
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=open_journal_meta_analysis_data.csv"}
    )

@app.post("/api/export/bibtex")
async def api_export_bibtex(papers: List[Paper] = Body(...)):
    """Export papers as BibTeX citation entries."""
    bib_entries = []
    for i, p in enumerate(papers, 1):
        cite_key = f"paper_{p.year or 2024}_{i}"
        authors_bib = " and ".join(p.authors) if p.authors else "Unknown"
        title_clean = p.title.replace("{", "").replace("}", "")
        
        entry = (
            f"@article{{{cite_key},\n"
            f"  title = {{{{{title_clean}}}}},\n"
            f"  author = {{{authors_bib}}},\n"
            f"  journal = {{{p.journal or 'Open Access Journal'}}},\n"
            f"  year = {{{p.year or '2024'}}},\n"
            f"  doi = {{{p.doi or ''}}},\n"
            f"  url = {{{p.oa_url or ''}}}\n"
            f"}}"
        )
        bib_entries.append(entry)

    bib_text = "\n\n".join(bib_entries)
    return Response(
        content=bib_text.encode("utf-8"),
        media_type="application/x-bibtex",
        headers={"Content-Disposition": "attachment; filename=open_journal_references.bib"}
    )

# Static Files mount
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def serve_index():
    """Serve main SPA web dashboard."""
    return FileResponse("app/static/index.html")
