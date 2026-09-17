"""Forest plot data generator for interactive rendering with Plotly."""
from typing import Dict, Any, List
from .statistics import MetaAnalysisResult

def generate_forest_plot_spec(result: MetaAnalysisResult) -> Dict[str, Any]:
    """Generate Plotly figure configuration (data & layout) for interactive forest plot."""
    is_ratio = result.is_ratio_metric
    null_line = 1.0 if is_ratio else 0.0

    studies = result.studies
    k = len(studies)

    # Y-axis categories: Study labels in reverse order so top study appears at top
    # Bottom rows reserved for summary diamonds
    y_labels = []
    study_indices = []
    
    x_points = []
    err_plus = []
    err_minus = []
    marker_sizes = []
    hover_texts = []
    text_labels = []

    for i, s in enumerate(studies):
        y_pos = k - i  # 1-based vertical position
        y_labels.append(s.study_label)
        study_indices.append(y_pos)
        
        x_points.append(s.effect_size)
        err_plus.append(s.ci_upper - s.effect_size)
        err_minus.append(s.effect_size - s.ci_lower)
        
        # Marker size scaled by Random-effects weight (between 8 and 22 px)
        w = s.weight_random_percent
        msize = max(8, min(24, 8 + (w / 100.0) * 45))
        marker_sizes.append(msize)
        
        hover_texts.append(
            f"<b>{s.study_label}</b><br>"
            f"{result.effect_metric}: {s.effect_size:.2f}<br>"
            f"95% CI: [{s.ci_lower:.2f}, {s.ci_upper:.2f}]<br>"
            f"Random Weight: {s.weight_random_percent:.1f}%<br>"
            f"Fixed Weight: {s.weight_fixed_percent:.1f}%<br>"
            f"Sample Size: {s.sample_size or 'N/A'}"
        )
        text_labels.append(f"{s.effect_size:.2f} [{s.ci_lower:.2f}, {s.ci_upper:.2f}]")

    # Study Traces
    traces: List[Dict[str, Any]] = [
        {
            "type": "scatter",
            "name": "Studies",
            "x": x_points,
            "y": study_indices,
            "mode": "markers",
            "marker": {
                "size": marker_sizes,
                "color": "#2563eb",  # Royal blue
                "symbol": "square",
                "line": {"color": "#1e40af", "width": 1.5}
            },
            "error_x": {
                "type": "data",
                "symmetric": False,
                "array": err_plus,
                "arrayminus": err_minus,
                "color": "#1e3a8a",
                "thickness": 2,
                "width": 6
            },
            "text": hover_texts,
            "hoverinfo": "text"
        }
    ]

    # Summary diamonds:
    # Random-Effects Diamond at y = 0
    rand = result.random_effects
    # We draw the diamond polygon
    rand_diamond_x = [rand.ci_lower, rand.pooled_effect, rand.ci_upper, rand.pooled_effect, rand.ci_lower]
    rand_diamond_y = [0, 0.25, 0, -0.25, 0]
    traces.append({
        "type": "scatter",
        "name": "Random Effects (Summary)",
        "x": rand_diamond_x,
        "y": rand_diamond_y,
        "mode": "lines",
        "fill": "toself",
        "fillcolor": "rgba(220, 38, 38, 0.5)",  # Crimson fill
        "line": {"color": "#b91c1c", "width": 2},
        "hoverinfo": "text",
        "text": (
            f"<b>Pooled (Random Effects)</b><br>"
            f"{result.effect_metric}: {rand.pooled_effect:.2f}<br>"
            f"95% CI: [{rand.ci_lower:.2f}, {rand.ci_upper:.2f}]<br>"
            f"p-value: {rand.p_value:.4f}<br>"
            f"Z: {rand.z_value:.2f}"
        )
    })

    # Fixed-Effect Diamond at y = -0.7
    fix = result.fixed_effect
    fix_diamond_x = [fix.ci_lower, fix.pooled_effect, fix.ci_upper, fix.pooled_effect, fix.ci_lower]
    fix_diamond_y = [-0.7, -0.45, -0.7, -0.95, -0.7]
    traces.append({
        "type": "scatter",
        "name": "Fixed Effect (Summary)",
        "x": fix_diamond_x,
        "y": fix_diamond_y,
        "mode": "lines",
        "fill": "toself",
        "fillcolor": "rgba(16, 185, 129, 0.4)",  # Emerald fill
        "line": {"color": "#047857", "width": 2},
        "hoverinfo": "text",
        "text": (
            f"<b>Pooled (Fixed Effect)</b><br>"
            f"{result.effect_metric}: {fix.pooled_effect:.2f}<br>"
            f"95% CI: [{fix.ci_lower:.2f}, {fix.ci_upper:.2f}]<br>"
            f"p-value: {fix.p_value:.4f}<br>"
            f"Z: {fix.z_value:.2f}"
        )
    })

    # Compute sensible X-axis range
    all_x = [s.ci_lower for s in studies] + [s.ci_upper for s in studies] + [rand.ci_lower, rand.ci_upper, null_line]
    min_x = max(0.05, min(all_x) * 0.8) if is_ratio else min(all_x) - 0.5
    max_x = min(50.0, max(all_x) * 1.25) if is_ratio else max(all_x) + 0.5

    # Tick values for Y axis
    tick_vals = list(range(1, k + 1)) + [0, -0.7]
    tick_texts = [s.study_label for s in reversed(studies)] + [
        "<b>Random-Effects Pooled</b>",
        "<b>Fixed-Effect Pooled</b>"
    ]

    het = result.heterogeneity
    heterogeneity_subtext = (
        f"Heterogeneity: I² = {het.i_squared:.1f}%, Cochran's Q = {het.q_value:.2f} (df={het.df}, p={het.p_value:.4f}), τ² = {het.tau_squared:.4f} | {het.interpretation}"
    )

    layout: Dict[str, Any] = {
        "title": {
            "text": f"<b>Forest Plot: Meta-Analysis of {result.num_studies} Studies ({result.effect_metric})</b>",
            "x": 0.05,
            "xanchor": "left"
        },
        "xaxis": {
            "title": f"Effect Size ({result.effect_metric}) [Log scale: {is_ratio}]",
            "type": "log" if is_ratio else "linear",
            "range": [min_x, max_x] if not is_ratio else None,
            "zeroline": not is_ratio,
            "gridcolor": "#f1f5f9"
        },
        "yaxis": {
            "tickmode": "array",
            "tickvals": tick_vals,
            "ticktext": tick_texts,
            "automargin": True
        },
        "shapes": [
            # Line of no effect
            {
                "type": "line",
                "x0": null_line,
                "x1": null_line,
                "y0": -1.2,
                "y1": k + 0.8,
                "line": {
                    "color": "#94a3b8",
                    "width": 1.5,
                    "dash": "dash"
                }
            }
        ],
        "annotations": [
            {
                "text": heterogeneity_subtext,
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": -0.18,
                "showarrow": False,
                "font": {"size": 11, "color": "#475569"},
                "align": "left"
            },
            {
                "text": "← Favors Control",
                "xref": "paper",
                "yref": "paper",
                "x": 0.25,
                "y": -0.12,
                "showarrow": False,
                "font": {"size": 11, "color": "#64748b"}
            },
            {
                "text": "Favors Intervention →",
                "xref": "paper",
                "yref": "paper",
                "x": 0.75,
                "y": -0.12,
                "showarrow": False,
                "font": {"size": 11, "color": "#64748b"}
            }
        ],
        "showlegend": True,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1
        },
        "margin": {"l": 200, "r": 50, "t": 60, "b": 100},
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor": "#f8fafc",
        "height": max(420, 180 + (k * 40))
    }

    return {"data": traces, "layout": layout}
