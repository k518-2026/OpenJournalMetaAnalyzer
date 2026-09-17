"""Meta-analysis module package."""
from .statistics import calculate_meta_analysis, MetaAnalysisResult, StudyEffect, ModelResult, HeterogeneityResult
from .extractor import extract_metrics_from_text, enrich_paper_with_extracted_metrics
from .synthesizer import EvidenceSynthesizer
from .forest_plot import generate_forest_plot_spec

__all__ = [
    "calculate_meta_analysis",
    "MetaAnalysisResult",
    "StudyEffect",
    "ModelResult",
    "HeterogeneityResult",
    "extract_metrics_from_text",
    "enrich_paper_with_extracted_metrics",
    "EvidenceSynthesizer",
    "generate_forest_plot_spec"
]
