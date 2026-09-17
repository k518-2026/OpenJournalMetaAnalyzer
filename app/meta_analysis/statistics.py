"""Statistical meta-analysis models (Fixed-Effect and Random-Effects models, heterogeneity testing)."""
import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from scipy import stats

class StudyEffect(BaseModel):
    study_id: str
    study_label: str
    effect_size: float
    ci_lower: float
    ci_upper: float
    weight_fixed_percent: float = 0.0
    weight_random_percent: float = 0.0
    sample_size: Optional[int] = None
    standard_error: float = 0.0
    is_log_scale: bool = True

class ModelResult(BaseModel):
    model_name: str
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    z_value: float
    p_value: float
    standard_error: float

class HeterogeneityResult(BaseModel):
    q_value: float
    df: int
    p_value: float
    i_squared: float  # Percentage (0 - 100%)
    tau_squared: float
    interpretation: str

class MetaAnalysisResult(BaseModel):
    effect_metric: str  # "OR", "RR", "HR", "SMD", "MD"
    is_ratio_metric: bool
    num_studies: int
    total_sample_size: int
    studies: List[StudyEffect]
    fixed_effect: ModelResult
    random_effects: ModelResult
    heterogeneity: HeterogeneityResult

def calculate_meta_analysis(
    studies_data: List[Dict[str, Any]],
    effect_metric: str = "OR"
) -> Optional[MetaAnalysisResult]:
    """Perform quantitative meta-analysis on study effect sizes.
    
    studies_data items must contain:
      - study_id: str
      - study_label: str
      - effect_size: float
      - ci_lower: float
      - ci_upper: float
      - sample_size: Optional[int]
    """
    is_ratio = effect_metric.upper() in ["OR", "RR", "HR", "ODDS RATIO", "RELATIVE RISK", "HAZARD RATIO"]
    valid_studies = []
    
    for s in studies_data:
        try:
            es = float(s.get("effect_size", 0))
            lower = float(s.get("ci_lower", 0))
            upper = float(s.get("ci_upper", 0))
            n = s.get("sample_size")
            n = int(n) if n is not None and str(n).isdigit() else None
            
            # Validation
            if is_ratio:
                if es <= 0 or lower <= 0 or upper <= 0 or lower >= upper:
                    continue
                # Work in log space for ratio metrics
                y_i = math.log(es)
                se_i = (math.log(upper) - math.log(lower)) / (2 * 1.95996)
            else:
                if lower >= upper:
                    continue
                y_i = es
                se_i = (upper - lower) / (2 * 1.95996)
                
            if se_i <= 0 or math.isnan(se_i):
                continue
                
            valid_studies.append({
                "id": str(s.get("study_id", f"study_{len(valid_studies)}")),
                "label": str(s.get("study_label", s.get("title", f"Study {len(valid_studies)+1}"))),
                "orig_es": es,
                "orig_lower": lower,
                "orig_upper": upper,
                "y": y_i,
                "se": se_i,
                "var": se_i ** 2,
                "n": n
            })
        except (ValueError, TypeError):
            continue

    k = len(valid_studies)
    if k == 0:
        return None

    # 1. Fixed-Effect Model (Inverse Variance Method)
    # Weights w_i = 1 / var_i
    w_fixed = [1.0 / s["var"] for s in valid_studies]
    sum_w_fixed = sum(w_fixed)
    
    if sum_w_fixed == 0:
        return None

    y_fixed = sum(w * s["y"] for w, s in zip(w_fixed, valid_studies)) / sum_w_fixed
    se_fixed = math.sqrt(1.0 / sum_w_fixed)
    z_fixed = y_fixed / se_fixed if se_fixed > 0 else 0.0
    p_fixed = 2.0 * (1.0 - stats.norm.cdf(abs(z_fixed)))
    ci_lower_fixed_y = y_fixed - 1.95996 * se_fixed
    ci_upper_fixed_y = y_fixed + 1.95996 * se_fixed

    # 2. Heterogeneity (Cochran's Q & DerSimonian-Laird tau^2)
    q_val = sum(w * ((s["y"] - y_fixed) ** 2) for w, s in zip(w_fixed, valid_studies))
    df = max(1, k - 1)
    p_q = float(stats.chi2.sf(q_val, df)) if k > 1 else 1.0
    
    if k > 1 and q_val > df:
        i2 = ((q_val - df) / q_val) * 100.0
    else:
        i2 = 0.0

    # DerSimonian-Laird estimator for tau^2
    sum_w_sq = sum(w ** 2 for w in w_fixed)
    c_factor = sum_w_fixed - (sum_w_sq / sum_w_fixed) if sum_w_fixed > 0 else 1.0
    tau2 = max(0.0, (q_val - df) / c_factor) if (k > 1 and c_factor > 0) else 0.0

    # Qualitative interpretation of I^2
    if i2 < 25:
        i2_interp = "Low heterogeneity (0 - 25%)"
    elif i2 < 50:
        i2_interp = "Moderate heterogeneity (25 - 50%)"
    elif i2 < 75:
        i2_interp = "Substantial heterogeneity (50 - 75%)"
    else:
        i2_interp = "Considerable heterogeneity (75 - 100%)"

    # 3. Random-Effects Model
    w_random = [1.0 / (s["var"] + tau2) for s in valid_studies]
    sum_w_random = sum(w_random)
    y_random = sum(w * s["y"] for w, s in zip(w_random, valid_studies)) / sum_w_random
    se_random = math.sqrt(1.0 / sum_w_random)
    z_random = y_random / se_random if se_random > 0 else 0.0
    p_random = 2.0 * (1.0 - stats.norm.cdf(abs(z_random)))
    ci_lower_random_y = y_random - 1.95996 * se_random
    ci_upper_random_y = y_random + 1.95996 * se_random

    # Study weights in %
    study_effects: List[StudyEffect] = []
    tot_sample = sum(s["n"] for s in valid_studies if s["n"] is not None)

    for i, s in enumerate(valid_studies):
        pct_fixed = (w_fixed[i] / sum_w_fixed) * 100.0
        pct_rand = (w_random[i] / sum_w_random) * 100.0
        study_effects.append(
            StudyEffect(
                study_id=s["id"],
                study_label=s["label"],
                effect_size=s["orig_es"],
                ci_lower=s["orig_lower"],
                ci_upper=s["orig_upper"],
                weight_fixed_percent=round(pct_fixed, 2),
                weight_random_percent=round(pct_rand, 2),
                sample_size=s["n"],
                standard_error=round(s["se"], 4),
                is_log_scale=is_ratio
            )
        )

    # Convert pooled results back to ratio scale if necessary
    if is_ratio:
        pooled_fixed = math.exp(y_fixed)
        ci_lower_fixed = math.exp(ci_lower_fixed_y)
        ci_upper_fixed = math.exp(ci_upper_fixed_y)
        
        pooled_random = math.exp(y_random)
        ci_lower_random = math.exp(ci_lower_random_y)
        ci_upper_random = math.exp(ci_upper_random_y)
    else:
        pooled_fixed = y_fixed
        ci_lower_fixed = ci_lower_fixed_y
        ci_upper_fixed = ci_upper_fixed_y
        
        pooled_random = y_random
        ci_lower_random = ci_lower_random_y
        ci_upper_random = ci_upper_random_y

    return MetaAnalysisResult(
        effect_metric=effect_metric.upper(),
        is_ratio_metric=is_ratio,
        num_studies=k,
        total_sample_size=tot_sample,
        studies=study_effects,
        fixed_effect=ModelResult(
            model_name="Fixed-Effect Model (Inverse Variance)",
            pooled_effect=round(pooled_fixed, 3),
            ci_lower=round(ci_lower_fixed, 3),
            ci_upper=round(ci_upper_fixed, 3),
            z_value=round(z_fixed, 3),
            p_value=round(p_fixed, 5),
            standard_error=round(se_fixed, 4)
        ),
        random_effects=ModelResult(
            model_name="Random-Effects Model (DerSimonian-Laird)",
            pooled_effect=round(pooled_random, 3),
            ci_lower=round(ci_lower_random, 3),
            ci_upper=round(ci_upper_random, 3),
            z_value=round(z_random, 3),
            p_value=round(p_random, 5),
            standard_error=round(se_random, 4)
        ),
        heterogeneity=HeterogeneityResult(
            q_value=round(q_val, 3),
            df=df,
            p_value=round(p_q, 5),
            i_squared=round(i2, 1),
            tau_squared=round(tau2, 4),
            interpretation=i2_interp
        )
    )
