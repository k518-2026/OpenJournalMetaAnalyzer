"""Unit tests for statistical meta-analysis calculations and extraction."""
import pytest
from app.meta_analysis.statistics import calculate_meta_analysis
from app.meta_analysis.extractor import extract_metrics_from_text
from app.meta_analysis.forest_plot import generate_forest_plot_spec

def test_fixed_and_random_effects_meta_analysis():
    # Benchmark dataset of 4 studies
    studies = [
        {"study_id": "s1", "study_label": "Smith (2021)", "effect_size": 1.50, "ci_lower": 1.10, "ci_upper": 2.05, "sample_size": 300},
        {"study_id": "s2", "study_label": "Johnson (2022)", "effect_size": 1.35, "ci_lower": 1.05, "ci_upper": 1.74, "sample_size": 520},
        {"study_id": "s3", "study_label": "Williams (2023)", "effect_size": 1.62, "ci_lower": 1.15, "ci_upper": 2.28, "sample_size": 210},
        {"study_id": "s4", "study_label": "Brown (2024)", "effect_size": 1.20, "ci_lower": 0.85, "ci_upper": 1.70, "sample_size": 180},
    ]

    result = calculate_meta_analysis(studies, effect_metric="OR")
    assert result is not None
    assert result.num_studies == 4
    assert result.total_sample_size == 1210

    # Pooled effect size should lie within reasonable bounds (around 1.30 - 1.50)
    assert 1.20 < result.fixed_effect.pooled_effect < 1.60
    assert 1.20 < result.random_effects.pooled_effect < 1.60
    assert result.fixed_effect.ci_lower < result.fixed_effect.pooled_effect < result.fixed_effect.ci_upper

    # Check study weights sum up to ~100%
    sum_fixed_weights = sum(s.weight_fixed_percent for s in result.studies)
    assert abs(sum_fixed_weights - 100.0) < 1.0

    # Check heterogeneity statistics
    assert result.heterogeneity.q_value >= 0
    assert 0.0 <= result.heterogeneity.i_squared <= 100.0
    assert result.heterogeneity.df == 3

def test_difference_metric_meta_analysis():
    # Mean difference (MD / SMD) scale (not log scale)
    studies = [
        {"study_id": "s1", "study_label": "Study A", "effect_size": -0.40, "ci_lower": -0.70, "ci_upper": -0.10, "sample_size": 100},
        {"study_id": "s2", "study_label": "Study B", "effect_size": -0.55, "ci_lower": -0.95, "ci_upper": -0.15, "sample_size": 80},
    ]
    result = calculate_meta_analysis(studies, effect_metric="SMD")
    assert result is not None
    assert not result.is_ratio_metric
    assert -0.80 < result.fixed_effect.pooled_effect < -0.20

def test_metric_extraction_from_abstract():
    sample_text = (
        "In this randomized controlled trial of 1,450 patients, the intervention significantly reduced "
        "the primary outcome (odds ratio: 1.42; 95% CI 1.15-1.76, p = 0.001)."
    )
    extracted = extract_metrics_from_text(sample_text)
    assert extracted["sample_size"] == 1450
    assert extracted["effect_type"] == "OR"
    assert extracted["effect_size"] == 1.42
    assert extracted["ci_lower"] == 1.15
    assert extracted["ci_upper"] == 1.76

def test_forest_plot_generation():
    studies = [
        {"study_id": "s1", "study_label": "Alpha (2023)", "effect_size": 1.5, "ci_lower": 1.1, "ci_upper": 2.0, "sample_size": 200},
        {"study_id": "s2", "study_label": "Beta (2024)", "effect_size": 1.3, "ci_lower": 0.9, "ci_upper": 1.8, "sample_size": 300},
    ]
    meta = calculate_meta_analysis(studies, effect_metric="RR")
    spec = generate_forest_plot_spec(meta)

    assert "data" in spec
    assert "layout" in spec
    assert len(spec["data"]) >= 3  # Studies scatter + Random diamond + Fixed diamond
