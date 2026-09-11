from __future__ import annotations

import hashlib
import html
import importlib
import json
import math
import os
import traceback
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"

import pandas as pd
import streamlit as st

import aegisultra_enginev2 as aegis


# Always synchronize the in-memory engine module
# with the current engine file on disk.
importlib.invalidate_caches()

aegis = importlib.reload(
    aegis
)


# ============================================================
# AEGIS ULTRA — STREAMLIT COMMAND CENTER + PORTAL PUBLISHER
# ============================================================

APP_NAME = "AEGIS ULTRA"
APP_VERSION = "2.3.0"

ENGINE_NAME = getattr(
    aegis,
    "ENGINE_NAME",
    "AEGIS ULTRA ENGINE",
)

ENGINE_VERSION = getattr(
    aegis,
    "ENGINE_VERSION",
    "Unknown",
)

DEFAULT_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwhceZ9-Z-n4R7U-ctJsLrmZuSiy98MtCPgUIw26ZOM9tv2Y5WPt7af56mJJ8M4pbqfww/"
    "exec"
)

PERIOD_ORDER = {
    "FT": 0,
    "HT": 1,
    "2H": 2,
}

MARKETS = [
    "1X2",
    "AH",
    "OU",
    "HHAD",
    "TEAM_OU",
]


# ============================================================
# 1. Streamlit configuration
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. Styling
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --ultra-bg: #080a11;
        --ultra-surface: rgba(255,255,255,0.045);
        --ultra-border: rgba(255,255,255,0.09);
        --ultra-green: #32d9a1;
        --ultra-blue: #7388ff;
        --ultra-purple: #ae72ff;
        --ultra-amber: #ffbd59;
        --ultra-red: #ff6577;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 10% 5%,
                rgba(81,102,255,0.15),
                transparent 29%
            ),
            radial-gradient(
                circle at 90% 2%,
                rgba(172,81,255,0.12),
                transparent 26%
            ),
            radial-gradient(
                circle at 65% 75%,
                rgba(0,211,164,0.06),
                transparent 30%
            ),
            linear-gradient(
                180deg,
                #090b13 0%,
                #0d1019 48%,
                #080a11 100%
            );
    }

    .block-container {
        max-width: 1540px;
        padding-top: 1.25rem;
        padding-bottom: 4rem;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                rgba(16,19,31,0.99),
                rgba(8,10,17,0.99)
            );
        border-right: 1px solid var(--ultra-border);
    }

    .ultra-hero {
        padding: 2rem 2.15rem;
        margin-bottom: 1.25rem;
        border-radius: 24px;
        background:
            linear-gradient(
                120deg,
                rgba(76,95,255,0.23),
                rgba(150,68,255,0.16),
                rgba(0,214,170,0.09)
            );
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow:
            0 18px 60px rgba(0,0,0,0.36),
            inset 0 1px 0 rgba(255,255,255,0.08);
    }

    .ultra-badge {
        display: inline-block;
        padding: 0.37rem 0.75rem;
        margin-bottom: 0.9rem;
        border-radius: 999px;
        color: #c6ffee;
        background: rgba(0,214,163,0.12);
        border: 1px solid rgba(0,214,163,0.27);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .ultra-title {
        margin: 0;
        color: white;
        font-size: 3rem;
        font-weight: 850;
        letter-spacing: -0.055em;
        line-height: 1.05;
    }

    .ultra-subtitle {
        max-width: 980px;
        margin-top: 0.72rem;
        margin-bottom: 0;
        color: rgba(255,255,255,0.70);
        font-size: 1.02rem;
        line-height: 1.6;
    }

    .section-label {
        margin-top: 1.2rem;
        margin-bottom: 0.75rem;
        color: rgba(255,255,255,0.50);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }

    .info-panel,
    .format-panel,
    .publish-panel {
        padding: 0.9rem 1.05rem;
        margin-bottom: 1rem;
        border-radius: 14px;
        line-height: 1.55;
    }

    .info-panel {
        color: rgba(255,255,255,0.76);
        background: rgba(115,136,255,0.08);
        border: 1px solid rgba(115,136,255,0.20);
    }

    .format-panel {
        color: rgba(255,255,255,0.69);
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.075);
        font-size: 0.88rem;
    }

    .publish-panel {
        color: #caffef;
        background: rgba(0,214,163,0.09);
        border: 1px solid rgba(0,214,163,0.22);
    }

    .summary-card {
        min-height: 126px;
        padding: 1.05rem 1.15rem;
        border-radius: 17px;
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.085);
        box-shadow: 0 10px 32px rgba(0,0,0,0.20);
    }

    .summary-label {
        color: rgba(255,255,255,0.50);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .summary-value {
        margin-top: 0.42rem;
        color: white;
        font-size: 1.55rem;
        font-weight: 850;
        letter-spacing: -0.035em;
    }

    .summary-note {
        margin-top: 0.35rem;
        color: rgba(255,255,255,0.48);
        font-size: 0.8rem;
        line-height: 1.35;
    }

    .status-pass {
        color: var(--ultra-green);
    }

    .status-caution {
        color: var(--ultra-amber);
    }

    .status-fail {
        color: var(--ultra-red);
    }

    .recommendation-card {
        padding: 1.25rem 1.35rem;
        margin-bottom: 0.9rem;
        border-radius: 18px;
        background:
            linear-gradient(
                120deg,
                rgba(0,214,163,0.10),
                rgba(255,255,255,0.035)
            );
        border: 1px solid rgba(0,214,163,0.22);
        box-shadow: 0 12px 34px rgba(0,0,0,0.23);
    }

    .recommendation-rank {
        color: #7fffd3;
        font-size: 0.77rem;
        font-weight: 850;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    .recommendation-name {
        margin-top: 0.32rem;
        color: white;
        font-size: 1.35rem;
        font-weight: 850;
        letter-spacing: -0.025em;
    }

    .recommendation-stats {
        margin-top: 0.55rem;
        color: rgba(255,255,255,0.66);
        font-size: 0.91rem;
        line-height: 1.6;
    }

    .period-ft,
    .period-ht,
    .period-2h {
        display: inline-block;
        margin-right: 0.4rem;
        padding: 0.28rem 0.62rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 850;
    }

    .period-ft {
        color: #bae6fd;
        background: rgba(56,189,248,0.11);
        border: 1px solid rgba(56,189,248,0.24);
    }

    .period-ht {
        color: #f0abfc;
        background: rgba(217,70,239,0.11);
        border: 1px solid rgba(217,70,239,0.24);
    }

    .period-2h {
        color: #fde68a;
        background: rgba(245,158,11,0.11);
        border: 1px solid rgba(245,158,11,0.24);
    }

    .score-card {
        text-align: center;
        min-height: 145px;
        padding: 1.35rem 0.85rem;
        border-radius: 19px;
        background:
            linear-gradient(
                145deg,
                rgba(130,91,255,0.16),
                rgba(255,255,255,0.035)
            );
        border: 1px solid rgba(151,120,255,0.22);
        box-shadow: 0 12px 34px rgba(0,0,0,0.23);
    }

    .score-value {
        color: white;
        font-size: 2.1rem;
        font-weight: 850;
    }

    .score-probability {
        margin-top: 0.35rem;
        color: #d7ceff;
        font-size: 0.92rem;
        font-weight: 750;
    }

    [data-testid="stMetric"] {
        padding: 0.95rem 1rem;
        border-radius: 15px;
        background: rgba(255,255,255,0.042);
        border: 1px solid rgba(255,255,255,0.075);
        box-shadow: 0 8px 26px rgba(0,0,0,0.16);
    }

    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.043);
        border-color: rgba(255,255,255,0.10);
    }

    textarea {
        font-family:
            "SFMono-Regular",
            Consolas,
            "Liberation Mono",
            monospace !important;
        font-size: 0.88rem !important;
        line-height: 1.5 !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 3rem;
        border-radius: 13px;
        border: 1px solid rgba(255,255,255,0.12);
        font-weight: 760;
    }

    [data-testid="stDataFrame"] {
        overflow: hidden;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.075);
    }

    div[data-testid="stExpander"] {
        border-radius: 15px;
        border-color: rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.018);
    }

    hr {
        border-color: rgba(255,255,255,0.075);
    }

    @media (max-width: 700px) {
        .ultra-title {
            font-size: 2.15rem;
        }

        .ultra-hero {
            padding: 1.4rem 1.3rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. Generic helpers
# ============================================================

def tokenize(value: Any) -> List[str]:
    return (
        str(value)
        .replace(",", " ")
        .replace("\t", " ")
        .split()
    )


def is_skip_token(value: Any) -> bool:
    return str(value).strip().lower() in {
        "",
        "-",
        "x",
        "na",
        "n/a",
        "none",
        "null",
    }


def optional_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def safe_float(
    value: Any,
    default: Optional[float] = None,
) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(result):
        return default

    return result


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    number = safe_float(value)

    if number is None:
        return default

    return int(number)


def safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    return optional_text(value).lower() in {
        "true",
        "1",
        "yes",
        "y",
        "on",
        "heavy",
        "重心",
    }


def validate_float(
    value: Any,
    label: str,
) -> float:
    result = safe_float(value)

    if result is None:
        raise ValueError(
            f"{label} 必須是有效數值。"
        )

    return result


def validate_odds(
    value: Any,
    label: str,
) -> float:
    result = validate_float(
        value,
        label,
    )

    if result <= 1.0:
        raise ValueError(
            f"{label} 必須大於 1.00。"
        )

    return result


def validate_quarter_line(
    value: Any,
    label: str,
) -> float:
    result = validate_float(
        value,
        label,
    )

    if not math.isclose(
        result * 4.0,
        round(result * 4.0),
        abs_tol=1e-8,
    ):
        raise ValueError(
            f"{label} 必須以 0.25 為單位。"
        )

    return result


def validate_integer_line(
    value: Any,
    label: str,
) -> float:
    result = validate_float(
        value,
        label,
    )

    if not math.isclose(
        result,
        round(result),
        abs_tol=1e-8,
    ):
        raise ValueError(
            f"{label} 必須是整數讓球。"
        )

    return result


def format_probability(
    value: Any,
    digits: int = 1,
) -> str:
    number = safe_float(value)

    if number is None:
        return "—"

    if number > 1 and number <= 100:
        number /= 100.0

    return f"{number * 100:.{digits}f}%"


def format_odds(
    value: Any,
    digits: int = 3,
) -> str:
    number = safe_float(value)

    if number is None:
        return "—"

    return f"{number:.{digits}f}"


def format_ev(
    value: Any,
    digits: int = 2,
) -> str:
    number = safe_float(value)

    if number is None:
        return "—"

    if abs(number) > 1:
        number /= 100.0

    return f"{number * 100:+.{digits}f}%"


def probability_value(
    record: Dict[str, Any],
    metric: str,
    statistic: str = "minimum",
) -> Any:
    probability = record.get(
        "probability",
        {},
    )

    if not isinstance(probability, dict):
        return None

    metric_record = probability.get(
        metric,
        {},
    )

    if not isinstance(metric_record, dict):
        return None

    return metric_record.get(statistic)


def summary_value(
    record: Dict[str, Any],
    field: str,
    statistic: str = "minimum",
) -> Any:
    section = record.get(
        field,
        {},
    )

    if isinstance(section, dict):
        return section.get(statistic)

    return section


def html_escape(value: Any) -> str:
    return html.escape(
        str(
            value
            if value is not None
            else "—"
        )
    )


def json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()

    if hasattr(value, "tolist"):
        return value.tolist()

    if isinstance(value, set):
        return list(value)

    return str(value)


def json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=json_default,
    )


def download_name(prefix: str) -> str:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"{prefix}_{timestamp}.json"


def normalize_period(
    value: Any,
    *,
    allow_blank: bool = False,
) -> str:
    normalized = (
        optional_text(value)
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )

    aliases = {
        "FT": "FT",
        "FULL_TIME": "FT",
        "FULLTIME": "FT",
        "MATCH": "FT",
        "90_MIN": "FT",
        "90_MINUTES": "FT",
        "HT": "HT",
        "HALF_TIME": "HT",
        "HALFTIME": "HT",
        "FIRST_HALF": "HT",
        "1H": "HT",
        "H1": "HT",
        "2H": "2H",
        "H2": "2H",
        "SECOND_HALF": "2H",
    }

    if not normalized:
        return "" if allow_blank else "FT"

    return aliases.get(
        normalized,
        normalized,
    )


def normalize_market(value: Any) -> str:
    normalized = (
        optional_text(value)
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )

    aliases = {
        "MATCH_ODDS": "1X2",
        "MONEYLINE": "1X2",
        "THREE_WAY": "1X2",
        "ASIAN_HANDICAP": "AH",
        "HANDICAP": "AH",
        "HDP": "AH",
        "OVER_UNDER": "OU",
        "TOTAL": "OU",
        "TOTALS": "OU",
        "GOALS": "OU",
        "HANDICAP_1X2": "HHAD",
        "HOME_HANDICAP_DRAW_AWAY": "HHAD",
        "TEAM_TOTAL": "TEAM_OU",
        "TEAM_TOTALS": "TEAM_OU",
        "TEAM_OVER_UNDER": "TEAM_OU",
        "CORRECT_SCORE": "CORRECT_SCORE",
        "SCORE": "CORRECT_SCORE",
        "CS": "CORRECT_SCORE",
    }

    return aliases.get(
        normalized,
        normalized,
    )


def status_chinese(status: Any) -> str:
    translations = {
        "PASS": "通過",
        "CAUTION": "注意",
        "FAIL": "失敗",
        "COMPLETED": "已完成",
        "NOT_AVAILABLE": "不適用",
        "NOT_TESTABLE": "無法測試",
        "DISABLED": "已停用",
        "ROBUST": "穩健",
        "FRAGILE": "脆弱",
        "OFFICIAL": "正式推薦",
        "REFERENCE_ONLY": "僅供參考",
        "FAIR_OR_BETTER": "價格合理或更佳",
        "MIXED_PRICE": "價格訊號混合",
        "SLIGHTLY_UNDERPAID": "輕微回報不足",
        "POOR_PRICE": "價格偏差",
        "SEVERELY_UNDERPAID": "嚴重回報不足",
        "UNKNOWN": "未知",
    }

    text = optional_text(
        status
    ) or "UNKNOWN"

    return translations.get(
        text,
        text.replace("_", " "),
    )


def status_css_class(status: Any) -> str:
    normalized = optional_text(
        status
    ).upper()

    if normalized in {
        "PASS",
        "COMPLETED",
        "ROBUST",
        "OFFICIAL",
        "FAIR_OR_BETTER",
    }:
        return "status-pass"

    if normalized in {
        "CAUTION",
        "FRAGILE",
        "MIXED_PRICE",
        "SLIGHTLY_UNDERPAID",
        "NOT_AVAILABLE",
        "NOT_TESTABLE",
        "DISABLED",
    }:
        return "status-caution"

    return "status-fail"


def translate_reason(reason: Any) -> str:
    translations = {
        "BELOW_MINIMUM_ODDS": "賠率低於最低限制",
        "ABOVE_MAXIMUM_ODDS": "賠率高於最高限制",
        "NO_VALID_RECONSTRUCTION": "沒有有效市場重建情境",
        "PRIMARY_SOURCE_SCENARIOS_INCOMPLETE": "主要尖銳來源情境不完整",
        "MODEL_QUALITY_GATE_FAILED": "模型品質閘門未通過",
        "HT_UNDERIDENTIFIED_REFERENCE_ONLY": "半場市場辨識不足，只供參考",
        "HT_FT_COHERENCE_FAILED": "半場與全場一致性測試失敗",
        "BELOW_OPTIONAL_EV_FLOOR": "低於自訂期望值下限",
        "PERIOD_MODEL_UNAVAILABLE": "該時段模型不可用",
        "BASE_CANDIDATE_INELIGIBLE": "候選盤本身不合資格",
        "NO_CONSERVATIVE_HIT_PROBABILITY": "沒有保守命中概率",
        "BELOW_MINIMUM_OFFICIAL_HIT_PROBABILITY": "低於正式推薦最低命中率",
        "CONFLICTS_WITH_HIGHER_RANKED_OFFICIAL_PICK": "與較高排名推薦衝突",
        "MAXIMUM_RECOMMENDATIONS_REACHED": "已達正式推薦數目上限",
    }

    text = optional_text(reason)

    return translations.get(
        text,
        text.replace("_", " "),
    )


def nested_value(
    record: Dict[str, Any],
    paths: List[Tuple[str, ...]],
) -> Any:
    for path in paths:
        current: Any = record

        valid = True

        for key in path:
            if not isinstance(current, dict):
                valid = False
                break

            if key not in current:
                valid = False
                break

            current = current[key]

        if valid and current is not None:
            return current

    return None


# ============================================================
# 4. Input parsers
# ============================================================

def parse_triplet(
    text: str,
    label: str,
    *,
    required: bool,
    allow_skips: bool,
) -> Optional[Dict[str, Optional[float]]]:
    if not optional_text(text):
        if required:
            raise ValueError(
                f"{label} 不可留空。"
            )

        return None

    tokens = tokenize(text)

    if len(tokens) != 3:
        raise ValueError(
            f"{label} 必須輸入三個賠率：主／和／客。"
        )

    values: List[Optional[float]] = []

    for index, token in enumerate(tokens):
        position = ["主", "和", "客"][index]

        if is_skip_token(token):
            if not allow_skips:
                raise ValueError(
                    f"{label} 的{position}賠率不可留空。"
                )

            values.append(None)
        else:
            values.append(
                validate_odds(
                    token,
                    f"{label} {position}",
                )
            )

    if all(value is None for value in values):
        return None

    return {
        "home": values[0],
        "draw": values[1],
        "away": values[2],
    }


def parse_two_way_ladder(
    text: str,
    label: str,
    *,
    market: str,
    allow_skips: bool,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen_lines = set()

    for row_number, raw_row in enumerate(
        str(text).splitlines(),
        start=1,
    ):
        raw_row = raw_row.strip()

        if not raw_row:
            continue

        tokens = tokenize(raw_row)

        if len(tokens) != 3:
            raise ValueError(
                f"{label} 第 {row_number} 行格式錯誤。"
                "每行必須有：盤口 賠率1 賠率2。"
            )

        line = validate_quarter_line(
            tokens[0],
            f"{label} 第 {row_number} 行盤口",
        )

        if line in seen_lines:
            raise ValueError(
                f"{label} 出現重複盤口 {line:g}。"
            )

        seen_lines.add(line)
        prices: List[Optional[float]] = []

        for index, token in enumerate(tokens[1:]):
            if is_skip_token(token):
                if not allow_skips:
                    raise ValueError(
                        f"{label} 第 {row_number} 行"
                        "的兩邊賠率都必須提供。"
                    )

                prices.append(None)
            else:
                prices.append(
                    validate_odds(
                        token,
                        (
                            f"{label} 第 {row_number} 行"
                            f"賠率 {index + 1}"
                        ),
                    )
                )

        if all(price is None for price in prices):
            raise ValueError(
                f"{label} 第 {row_number} 行"
                "最少需要一個賠率。"
            )

        if market == "AH":
            rows.append({
                "line": line,
                "home": prices[0],
                "away": prices[1],
            })
        else:
            rows.append({
                "line": line,
                "over": prices[0],
                "under": prices[1],
            })

    return rows


def parse_hhad_ladder(
    text: str,
    label: str,
    *,
    allow_skips: bool,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen_lines = set()

    for row_number, raw_row in enumerate(
        str(text).splitlines(),
        start=1,
    ):
        raw_row = raw_row.strip()

        if not raw_row:
            continue

        tokens = tokenize(raw_row)

        if len(tokens) != 4:
            raise ValueError(
                f"{label} 第 {row_number} 行格式錯誤。"
                "每行必須有：讓球 主勝 和 客勝。"
            )

        line = validate_integer_line(
            tokens[0],
            f"{label} 第 {row_number} 行讓球",
        )

        if line in seen_lines:
            raise ValueError(
                f"{label} 出現重複讓球 {line:g}。"
            )

        seen_lines.add(line)
        prices: List[Optional[float]] = []

        for index, token in enumerate(tokens[1:]):
            if is_skip_token(token):
                if not allow_skips:
                    raise ValueError(
                        f"{label} 第 {row_number} 行"
                        "的三個賠率都必須提供。"
                    )

                prices.append(None)
            else:
                prices.append(
                    validate_odds(
                        token,
                        (
                            f"{label} 第 {row_number} 行"
                            f"賠率 {index + 1}"
                        ),
                    )
                )

        if all(price is None for price in prices):
            raise ValueError(
                f"{label} 第 {row_number} 行"
                "最少需要一個賠率。"
            )

        rows.append({
            "line": line,
            "home": prices[0],
            "draw": prices[1],
            "away": prices[2],
        })

    return rows


def parse_team_ou_ladder(
    text: str,
    label: str,
    *,
    allow_skips: bool,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen_keys = set()

    for row_number, raw_row in enumerate(
        str(text).splitlines(),
        start=1,
    ):
        raw_row = raw_row.strip()

        if not raw_row:
            continue

        tokens = tokenize(raw_row)

        if len(tokens) != 4:
            raise ValueError(
                f"{label} 第 {row_number} 行格式錯誤。"
                "每行必須有：HOME/AWAY 盤口 大賠率 細賠率。"
            )

        team = tokens[0].upper()

        if team not in {
            "HOME",
            "AWAY",
        }:
            raise ValueError(
                f"{label} 第 {row_number} 行球隊"
                "必須是 HOME 或 AWAY。"
            )

        line = validate_quarter_line(
            tokens[1],
            f"{label} 第 {row_number} 行盤口",
        )

        key = (
            team,
            line,
        )

        if key in seen_keys:
            raise ValueError(
                f"{label} 出現重複盤口："
                f"{team} {line:g}。"
            )

        seen_keys.add(key)
        prices: List[Optional[float]] = []

        for index, token in enumerate(tokens[2:]):
            if is_skip_token(token):
                if not allow_skips:
                    raise ValueError(
                        f"{label} 第 {row_number} 行"
                        "的大細賠率都必須提供。"
                    )

                prices.append(None)
            else:
                prices.append(
                    validate_odds(
                        token,
                        (
                            f"{label} 第 {row_number} 行"
                            f"賠率 {index + 1}"
                        ),
                    )
                )

        if all(price is None for price in prices):
            raise ValueError(
                f"{label} 第 {row_number} 行"
                "最少需要一個賠率。"
            )

        rows.append({
            "team": team,
            "line": line,
            "over": prices[0],
            "under": prices[1],
        })

    return rows


# ============================================================
# 5. Default JSON
# ============================================================

def example_json_input() -> Dict[str, Any]:
    return {
        "match": {
            "name": "主隊 vs 客隊",
            "home": "主隊",
            "away": "客隊",
            "competition": "賽事名稱",
            "kickoff": "",
            "snapshot_time": "",
        },
        "sharp_books": [
            {
                "key": "pinnacle",
                "title": "Pinnacle",
                "markets": {
                    "FT": {
                        "1X2": {
                            "home": 2.12,
                            "draw": 3.35,
                            "away": 3.55,
                        },
                        "AH": [
                            {
                                "line": -0.25,
                                "home": 1.95,
                                "away": 1.95,
                            }
                        ],
                        "OU": [
                            {
                                "line": 2.25,
                                "over": 1.92,
                                "under": 1.98,
                            }
                        ],
                        "HHAD": [],
                        "TEAM_OU": [],
                    },
                    "HT": {
                        "1X2": {
                            "home": 2.75,
                            "draw": 2.10,
                            "away": 4.10,
                        },
                        "AH": [
                            {
                                "line": 0.0,
                                "home": 1.62,
                                "away": 2.28,
                            }
                        ],
                        "OU": [
                            {
                                "line": 1.0,
                                "over": 1.92,
                                "under": 1.98,
                            }
                        ],
                        "HHAD": [],
                        "TEAM_OU": [],
                    },
                },
            }
        ],
        "hkjc_markets": [
            {
                "id": "M001",
                "period": "FT",
                "market": "AH",
                "selection": "HOME",
                "line": -0.25,
                "odds": 1.95,
                "label": "主隊 全場 AH -0.25",
            },
            {
                "id": "M002",
                "period": "HT",
                "market": "OU",
                "selection": "UNDER",
                "line": 1.0,
                "odds": 1.90,
                "label": "半場入球細 1.0",
            },
        ],
        "settings": {
            "minimum_odds": 1.5,
            "maximum_odds": None,
            "max_recommendations": 3,
            "minimum_official_hit_probability": 0.5,
            "correct_score_count": 2,
            "devig_methods": [
                "MULTIPLICATIVE",
                "POWER",
            ],
            "primary_source": "pinnacle",
            "ev_rejection_floor": None,
            "features": {
                "quality_gate": True,
                "stress_audit": True,
                "family_out_audit": True,
                "adaptive_grids": True,
                "ht_ft_coherence": True,
            },
        },
    }


# ============================================================
# 6. Session state
# ============================================================

SESSION_DEFAULTS = {
    "ultra_result": None,
    "ultra_input": None,
    "ultra_analysis_hash": None,
    "ultra_error": None,
    "ultra_traceback": None,
    "ultra_json_text": json_text(
        example_json_input()
    ),
    "portal_last_response": None,
}

for state_key, state_value in SESSION_DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = state_value


# ============================================================
# 7. Cached engine execution
# ============================================================

@st.cache_data(
    show_spinner=False,
    max_entries=32,
)
def cached_engine_run(
    canonical_json: str,
    engine_fingerprint: str,
) -> Dict[str, Any]:
    del engine_fingerprint

    return aegis.run_engine(
        json.loads(canonical_json)
    )


def execute_engine(
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    canonical_json = json.dumps(
        input_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
    )

    try:
        with open(
            aegis.__file__,
            "rb",
        ) as engine_file:
            engine_file_bytes = (
                engine_file.read()
            )

        coherence_code = (
            aegis
            .minimum_ht_ft_violation
            .__code__
        )

        runtime_code_bytes = (
            coherence_code.co_code
            + repr(
                coherence_code.co_consts
            ).encode("utf-8")
        )

        engine_fingerprint = (
            hashlib.sha256(
                engine_file_bytes
                + runtime_code_bytes
            ).hexdigest()
        )

    except (
        OSError,
        AttributeError,
    ):
        engine_fingerprint = str(
            ENGINE_VERSION
        )

    analysis_hash = hashlib.sha256(
        (
            canonical_json
            + engine_fingerprint
        ).encode("utf-8")
    ).hexdigest()

    if (
        st.session_state.ultra_analysis_hash
        == analysis_hash
        and st.session_state.ultra_result
        is not None
    ):
        return st.session_state.ultra_result

    result = cached_engine_run(
        canonical_json,
        engine_fingerprint,
    )

    st.session_state.ultra_analysis_hash = (
        analysis_hash
    )

    st.session_state.ultra_result = result

    st.session_state.ultra_input = result.get(
        "input_snapshot",
        deepcopy(input_data),
    )

    return result


# ============================================================
# 8. Bulk input rendering
# ============================================================

def render_sharp_period(
    source_index: int,
    period: str,
    *,
    enabled_default: bool,
) -> Optional[Dict[str, str]]:
    period_name = (
        "全場 FT"
        if period == "FT"
        else "半場 HT"
    )

    enabled = st.checkbox(
        f"啟用{period_name}市場",
        value=enabled_default,
        key=f"sharp_enable_{source_index}_{period}",
    )

    if not enabled:
        st.info(
            f"此來源未啟用{period_name}。"
        )

        return None

    one_x_two = st.text_input(
        f"{period} 1X2 — 主勝／和／客勝",
        placeholder="2.20 3.60 3.40",
        key=f"sharp_1x2_{source_index}_{period}",
    )

    first, second = st.columns(2)

    with first:
        ah = st.text_area(
            f"{period} 亞洲讓球 AH",
            placeholder=(
                "主隊讓球線 主隊賠率 客隊賠率\n"
                "0.00 1.65 2.30\n"
                "-0.25 1.98 1.92\n"
                "-0.50 2.20 1.72"
            ),
            height=220,
            key=f"sharp_ah_{source_index}_{period}",
        )

    with second:
        ou = st.text_area(
            f"{period} 入球大細 O/U",
            placeholder=(
                "入球線 大盤賠率 細盤賠率\n"
                "1.00 1.88 2.02\n"
                "1.25 2.15 1.75"
                if period == "HT"
                else
                "入球線 大盤賠率 細盤賠率\n"
                "2.00 1.75 2.15\n"
                "2.25 2.02 1.88\n"
                "2.50 2.35 1.68"
            ),
            height=220,
            key=f"sharp_ou_{source_index}_{period}",
        )

    third, fourth = st.columns(2)

    with third:
        if period == "FT":
            hhad = st.text_area(
                "FT 讓球主客和 HHAD",
                placeholder=(
                    "主隊讓球 主勝 和 客勝\n"
                    "-1 3.60 3.75 1.72\n"
                    "+1 1.45 4.20 5.80"
                ),
                height=170,
                key=f"sharp_hhad_{source_index}_{period}",
            )
        else:
            hhad = ""

    with fourth:
        team_ou = st.text_area(
            f"{period} 球隊入球大細",
            placeholder=(
                "球隊 入球線 大盤賠率 細盤賠率\n"
                "HOME 0.50 1.85 2.00\n"
                "AWAY 0.50 2.05 1.78"
                if period == "HT"
                else
                "球隊 入球線 大盤賠率 細盤賠率\n"
                "HOME 1.50 2.05 1.78\n"
                "AWAY 1.00 1.85 2.00"
            ),
            height=170,
            key=f"sharp_team_ou_{source_index}_{period}",
        )

    return {
        "1X2": one_x_two,
        "AH": ah,
        "OU": ou,
        "HHAD": hhad,
        "TEAM_OU": team_ou,
    }


def render_hkjc_period(
    period: str,
) -> Dict[str, str]:
    period_name = (
        "全場 FT"
        if period == "FT"
        else "半場 HT"
    )

    st.markdown(
        f"### {period_name}"
    )

    st.caption(
        "沒有提供的賠率可輸入 X 或 -。"
        "每一項均會保留正確 period，不會把 HT 強制當成 FT。"
    )

    one_x_two = st.text_input(
        f"HKJC {period} 1X2 — 主勝／和／客勝",
        placeholder="2.25 3.45 3.25",
        key=f"hkjc_1x2_{period}",
    )

    first, second = st.columns(2)

    with first:
        ah = st.text_area(
            f"HKJC {period} AH",
            placeholder=(
                "主隊讓球線 主隊賠率 客隊賠率\n"
                "0.00 1.75 2.10\n"
                "-0.25 2.05 1.80"
            ),
            height=225,
            key=f"hkjc_ah_{period}",
        )

    with second:
        ou = st.text_area(
            f"HKJC {period} O/U",
            placeholder=(
                "入球線 大盤賠率 細盤賠率\n"
                "1.00 1.95 1.85\n"
                "1.25 2.18 1.70"
                if period == "HT"
                else
                "入球線 大盤賠率 細盤賠率\n"
                "2.25 1.95 1.85\n"
                "2.50 2.18 1.70\n"
                "2.75 X 1.55"
            ),
            height=225,
            key=f"hkjc_ou_{period}",
        )

    third, fourth = st.columns(2)

    with third:
        if period == "FT":
            hhad = st.text_area(
                "HKJC FT 讓球主客和 HHAD",
                placeholder=(
                    "主隊讓球 主勝 和 客勝\n"
                    "-1 3.60 3.75 1.72\n"
                    "+1 1.45 X 5.80"
                ),
                height=180,
                key=f"hkjc_hhad_{period}",
            )
        else:
            hhad = ""

    with fourth:
        team_ou = st.text_area(
            f"HKJC {period} 球隊入球大細",
            placeholder=(
                "球隊 入球線 大盤賠率 細盤賠率\n"
                "HOME 0.50 1.85 2.00\n"
                "AWAY 0.50 X 1.78"
                if period == "HT"
                else
                "球隊 入球線 大盤賠率 細盤賠率\n"
                "HOME 1.50 2.05 1.78\n"
                "AWAY 1.00 X 2.00"
            ),
            height=180,
            key=f"hkjc_team_ou_{period}",
        )

    return {
        "1X2": one_x_two,
        "AH": ah,
        "OU": ou,
        "HHAD": hhad,
        "TEAM_OU": team_ou,
    }


# ============================================================
# 9. Input construction
# ============================================================

def build_sharp_period(
    raw: Dict[str, str],
    source_title: str,
    period: str,
) -> Dict[str, Any]:
    return {
        "1X2": parse_triplet(
            raw["1X2"],
            f"{source_title} {period} 1X2",
            required=False,
            allow_skips=False,
        ),
        "AH": parse_two_way_ladder(
            raw["AH"],
            f"{source_title} {period} AH",
            market="AH",
            allow_skips=False,
        ),
        "OU": parse_two_way_ladder(
            raw["OU"],
            f"{source_title} {period} O/U",
            market="OU",
            allow_skips=False,
        ),
        "HHAD": (
            parse_hhad_ladder(
                raw["HHAD"],
                f"{source_title} {period} HHAD",
                allow_skips=False,
            )
            if period == "FT"
            else []
        ),
        "TEAM_OU": parse_team_ou_ladder(
            raw["TEAM_OU"],
            f"{source_title} {period} 球隊入球大細",
            allow_skips=False,
        ),
    }


def period_has_market(
    markets: Dict[str, Any],
) -> bool:
    return any(
        bool(markets.get(market))
        for market in MARKETS
    )


def build_hkjc_candidates(
    *,
    home_name: str,
    away_name: str,
    raw_periods: Dict[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    counter = 1

    def add_candidate(
        *,
        period: str,
        market: str,
        selection: str,
        odds: float,
        label: str,
        line: Optional[float] = None,
        team: Optional[str] = None,
    ) -> None:
        nonlocal counter

        normalized_period = normalize_period(
            period,
            allow_blank=True,
        )

        if normalized_period not in {
            "FT",
            "HT",
            "2H",
        }:
            raise ValueError(
                f"候選盤時段無效：{period}"
            )

        candidate: Dict[str, Any] = {
            "id": f"M{counter:03d}",
            "label": label,
            "period": normalized_period,
            "market": normalize_market(market),
            "selection": optional_text(
                selection
            ).upper(),
            "odds": odds,
        }

        if line is not None:
            candidate["line"] = line

        if team is not None:
            candidate["team"] = team
            candidate["market_scope"] = team

        candidates.append(candidate)
        counter += 1

    for period in [
        "FT",
        "HT",
    ]:
        raw = raw_periods[period]
        period_label = (
            "全場"
            if period == "FT"
            else "半場"
        )

        one_x_two = parse_triplet(
            raw["1X2"],
            f"HKJC {period} 1X2",
            required=False,
            allow_skips=True,
        )

        if one_x_two:
            specs = [
                (
                    "home",
                    "HOME",
                    f"{home_name} {period_label}勝",
                ),
                (
                    "draw",
                    "DRAW",
                    f"{period_label}和",
                ),
                (
                    "away",
                    "AWAY",
                    f"{away_name} {period_label}勝",
                ),
            ]

            for key, selection, label in specs:
                odds = one_x_two.get(key)

                if odds is not None:
                    add_candidate(
                        period=period,
                        market="1X2",
                        selection=selection,
                        odds=odds,
                        label=label,
                    )

        ah_rows = parse_two_way_ladder(
            raw["AH"],
            f"HKJC {period} AH",
            market="AH",
            allow_skips=True,
        )

        for row in ah_rows:
            if row["home"] is not None:
                add_candidate(
                    period=period,
                    market="AH",
                    selection="HOME",
                    line=row["line"],
                    odds=row["home"],
                    label=(
                        f"{home_name} "
                        f"{period_label} AH "
                        f"{row['line']:+g}"
                    ),
                )

            if row["away"] is not None:
                add_candidate(
                    period=period,
                    market="AH",
                    selection="AWAY",
                    line=row["line"],
                    odds=row["away"],
                    label=(
                        f"{away_name} "
                        f"{period_label} AH "
                        f"{-row['line']:+g}"
                    ),
                )

        ou_rows = parse_two_way_ladder(
            raw["OU"],
            f"HKJC {period} O/U",
            market="OU",
            allow_skips=True,
        )

        for row in ou_rows:
            if row["over"] is not None:
                add_candidate(
                    period=period,
                    market="OU",
                    selection="OVER",
                    line=row["line"],
                    odds=row["over"],
                    label=(
                        f"{period_label}入球大 "
                        f"{row['line']:g}"
                    ),
                )

            if row["under"] is not None:
                add_candidate(
                    period=period,
                    market="OU",
                    selection="UNDER",
                    line=row["line"],
                    odds=row["under"],
                    label=(
                        f"{period_label}入球細 "
                        f"{row['line']:g}"
                    ),
                )

        if period == "FT":
            hhad_rows = parse_hhad_ladder(
                raw["HHAD"],
                "HKJC FT HHAD",
                allow_skips=True,
            )

            for row in hhad_rows:
                specs = [
                    (
                        "home",
                        "HOME",
                        f"{home_name} 讓球主勝 {row['line']:+g}",
                    ),
                    (
                        "draw",
                        "DRAW",
                        f"讓球和 {row['line']:+g}",
                    ),
                    (
                        "away",
                        "AWAY",
                        f"{away_name} 讓球客勝 {row['line']:+g}",
                    ),
                ]

                for key, selection, label in specs:
                    odds = row.get(key)

                    if odds is not None:
                        add_candidate(
                            period="FT",
                            market="HHAD",
                            selection=selection,
                            line=row["line"],
                            odds=odds,
                            label=label,
                        )

        team_rows = parse_team_ou_ladder(
            raw["TEAM_OU"],
            f"HKJC {period} 球隊入球大細",
            allow_skips=True,
        )

        for row in team_rows:
            team_name = (
                home_name
                if row["team"] == "HOME"
                else away_name
            )

            if row["over"] is not None:
                add_candidate(
                    period=period,
                    market="TEAM_OU",
                    selection="OVER",
                    team=row["team"],
                    line=row["line"],
                    odds=row["over"],
                    label=(
                        f"{team_name} {period_label}"
                        f"入球大 {row['line']:g}"
                    ),
                )

            if row["under"] is not None:
                add_candidate(
                    period=period,
                    market="TEAM_OU",
                    selection="UNDER",
                    team=row["team"],
                    line=row["line"],
                    odds=row["under"],
                    label=(
                        f"{team_name} {period_label}"
                        f"入球細 {row['line']:g}"
                    ),
                )

    if not candidates:
        raise ValueError(
            "最少需要輸入一個 HKJC 候選盤。"
        )

    return candidates


# ============================================================
# 10. Portal API configuration
# ============================================================

def configured_api_url() -> str:
    try:
        value = optional_text(
            st.secrets["portal_api"]["url"]
        )

        if value:
            return value

    except Exception:
        pass

    environment_value = optional_text(
        os.getenv("AEGIS_API_URL")
    )

    return environment_value or DEFAULT_API_URL


def configured_api_token() -> str:
    try:
        token = optional_text(
            st.secrets["portal_api"]["token"]
        )

        if token:
            return token

    except Exception:
        pass

    return optional_text(
        os.getenv("AEGIS_API_TOKEN")
    )


def portal_request(
    payload: Dict[str, Any],
    *,
    timeout: int = 40,
) -> Dict[str, Any]:
    url = configured_api_url()
    token = configured_api_token()

    if not url:
        raise ValueError(
            "AEGIS API URL 未設定。"
        )

    if not token:
        raise ValueError(
            "AEGIS API token 未設定。"
        )

    request_payload = deepcopy(payload)
    request_payload["token"] = token

    encoded = json.dumps(
        request_payload,
        ensure_ascii=False,
        default=json_default,
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": (
                f"AEGIS-ULTRA/{APP_VERSION}"
            ),
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            response_text = (
                response.read()
                .decode(
                    "utf-8-sig",
                    errors="replace",
                )
            )

    except urllib.error.HTTPError as error:
        response_text = (
            error.read()
            .decode(
                "utf-8-sig",
                errors="replace",
            )
        )

        raise RuntimeError(
            f"API HTTP {error.code}: "
            f"{response_text}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"無法連接 AEGIS API：{error.reason}"
        ) from error

    try:
        result = json.loads(
            response_text
        )

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "AEGIS API 回傳的不是有效 JSON："
            + response_text[:500]
        ) from error

    if not isinstance(result, dict):
        raise RuntimeError(
            "AEGIS API 回傳格式錯誤。"
        )

    if result.get("ok") is not True:
        raise RuntimeError(
            "AEGIS API 拒絕要求："
            + optional_text(
                result.get("error")
            )
        )

    return result


# ============================================================
# 11. Portal bundle generation
# ============================================================

def item_identity(
    item: Dict[str, Any],
) -> str:
    for key in [
        "id",
        "candidate_id",
        "market_id",
        "rec_id",
    ]:
        value = optional_text(
            item.get(key)
        )

        if value:
            return value

    return ""


def build_input_candidate_lookup(
    input_snapshot: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    markets = input_snapshot.get(
        "hkjc_markets",
        [],
    )

    if not isinstance(markets, list):
        return lookup

    for item in markets:
        if not isinstance(item, dict):
            continue

        identity = item_identity(item)

        if identity:
            lookup[identity] = item

    return lookup


def merged_candidate(
    item: Dict[str, Any],
    input_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    identity = item_identity(item)

    original = input_lookup.get(
        identity,
        {},
    )

    merged = deepcopy(original)
    merged.update(item)

    return merged


def resolve_candidate_period(
    item: Dict[str, Any],
    input_lookup: Dict[str, Dict[str, Any]],
) -> str:
    identity = item_identity(item)

    direct_period = normalize_period(
        item.get("period"),
        allow_blank=True,
    )

    if direct_period:
        return direct_period

    original = input_lookup.get(
        identity,
        {},
    )

    original_period = normalize_period(
        original.get("period"),
        allow_blank=True,
    )

    if original_period:
        return original_period

    raise ValueError(
        "候選盤缺少明確 period，"
        f"不能任意當成 FT：{identity or item.get('label', 'unknown')}"
    )


def stable_match_id(
    result: Dict[str, Any],
    input_snapshot: Dict[str, Any],
) -> str:
    result_match = result.get(
        "match",
        {},
    )

    input_match = input_snapshot.get(
        "match",
        {},
    )

    for record in [
        result_match,
        input_match,
    ]:
        if not isinstance(record, dict):
            continue

        for key in [
            "match_id",
            "id",
            "fixture_id",
        ]:
            explicit = optional_text(
                record.get(key)
            )

            if explicit:
                return explicit

    identity = "|".join([
        optional_text(
            result_match.get(
                "home",
                input_match.get("home"),
            )
        ).casefold(),
        optional_text(
            result_match.get(
                "away",
                input_match.get("away"),
            )
        ).casefold(),
        optional_text(
            result_match.get(
                "competition",
                input_match.get(
                    "competition"
                ),
            )
        ).casefold(),
        optional_text(
            result_match.get(
                "kickoff",
                input_match.get("kickoff"),
            )
        ),
    ])

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:20]

    return f"match_{digest}"


def stable_rec_id(
    match_id: str,
    source_key: str,
    period: str,
    market: str,
    selection: str,
    line: Any,
) -> str:
    identity = "|".join([
        match_id,
        source_key,
        period,
        market,
        selection,
        optional_text(line),
    ])

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:22]

    return f"rec_{digest}"


def candidate_commentary(
    item: Dict[str, Any],
) -> str:
    for key in [
        "commentary",
        "analysis",
        "summary",
        "explanation",
        "reason",
    ]:
        value = item.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    reasons: List[str] = []

    for key in [
        "official_exclusion_reasons",
        "exclusion_reasons",
    ]:
        values = item.get(
            key,
            [],
        )

        if isinstance(values, list):
            reasons.extend(
                translate_reason(value)
                for value in values
                if optional_text(value)
            )

    if reasons:
        return "；".join(
            dict.fromkeys(reasons)
        )

    return ""


def conflict_source_ids(
    item: Dict[str, Any],
) -> List[str]:
    output: List[str] = []

    explicit_ids = item.get(
        "conflict_ids"
    )

    if isinstance(explicit_ids, str):
        output.extend(
            part.strip()
            for part in explicit_ids.split(",")
            if part.strip()
        )

    elif isinstance(explicit_ids, list):
        output.extend(
            optional_text(value)
            for value in explicit_ids
            if optional_text(value)
        )

    conflicts = item.get(
        "conflicts_with",
        [],
    )

    if isinstance(conflicts, list):
        for conflict in conflicts:
            if isinstance(conflict, dict):
                identity = item_identity(
                    conflict
                )

                if identity:
                    output.append(identity)

            elif optional_text(conflict):
                output.append(
                    optional_text(conflict)
                )

    return list(
        dict.fromkeys(output)
    )


def official_identity_set(
    result: Dict[str, Any],
) -> set:
    identities = set()

    for item in result.get(
        "recommendations",
        [],
    ):
        if not isinstance(item, dict):
            continue

        identity = item_identity(item)

        if identity:
            identities.add(identity)

    return identities


def official_record_lookup(
    result: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    for item in result.get(
        "recommendations",
        [],
    ):
        if not isinstance(item, dict):
            continue

        identity = item_identity(item)

        if identity:
            lookup[identity] = item

    return lookup


def actual_model_direction(
    result: Dict[str, Any],
    input_lookup: Dict[str, Dict[str, Any]],
) -> str:
    parts: List[str] = []

    for item in result.get(
        "recommendations",
        [],
    ):
        if not isinstance(item, dict):
            continue

        period = resolve_candidate_period(
            item,
            input_lookup,
        )

        label = optional_text(
            item.get("label")
        ) or item_identity(item)

        if label:
            parts.append(
                f"{period}｜{label}"
            )

    if not parts:
        return "本場沒有候選盤通過正式推薦條件。"

    return "正式方向：" + "；".join(parts)


def actual_model_summary(
    result: Dict[str, Any],
) -> str:
    quality = optional_text(
        result.get(
            "model_quality",
            {},
        ).get("status")
        if isinstance(
            result.get("model_quality"),
            dict,
        )
        else ""
    )

    coherence = optional_text(
        result.get(
            "ht_ft_coherence",
            {},
        ).get("status")
        if isinstance(
            result.get("ht_ft_coherence"),
            dict,
        )
        else ""
    )

    candidates = result.get(
        "candidate_markets",
        [],
    )

    recommendations = result.get(
        "recommendations",
        [],
    )

    parts = [
        f"Engine V{ENGINE_VERSION}",
        f"候選盤 {len(candidates) if isinstance(candidates, list) else 0}",
        f"正式推薦 {len(recommendations) if isinstance(recommendations, list) else 0}",
    ]

    if quality:
        parts.append(
            "模型品質 "
            + status_chinese(quality)
        )

    if coherence:
        parts.append(
            "HT–FT 一致性 "
            + status_chinese(coherence)
        )

    return "｜".join(parts)


def top_scores_text(
    result: Dict[str, Any],
) -> str:
    correct_scores = result.get(
        "correct_scores",
        {},
    )

    if not isinstance(
        correct_scores,
        dict,
    ):
        return ""

    records = correct_scores.get(
        "recommendations",
        [],
    )

    if not isinstance(records, list):
        return ""

    values: List[str] = []

    for score in records:
        if not isinstance(score, dict):
            continue

        score_value = optional_text(
            score.get("score")
        )

        probability = (
            score.get(
                "probability",
                {},
            ).get("minimum")
            if isinstance(
                score.get("probability"),
                dict,
            )
            else None
        )

        if score_value:
            values.append(
                score_value
                + (
                    f" ({format_probability(probability, 1)})"
                    if probability is not None
                    else ""
                )
            )

    return "；".join(values)


def candidate_to_portal_record(
    *,
    match_id: str,
    item: Dict[str, Any],
    input_lookup: Dict[str, Dict[str, Any]],
    tier: str,
    rank: int,
    publish_status: str,
) -> Tuple[
    Dict[str, Any],
    str,
    List[str],
]:
    merged = merged_candidate(
        item,
        input_lookup,
    )

    source_key = (
        item_identity(merged)
        or optional_text(
            merged.get("label")
        )
    )

    period = resolve_candidate_period(
        merged,
        input_lookup,
    )

    market = normalize_market(
        merged.get("market")
    )

    selection = optional_text(
        merged.get("selection")
    ).upper()

    if not market:
        raise ValueError(
            f"候選盤缺少 market：{source_key}"
        )

    if not selection:
        raise ValueError(
            f"候選盤缺少 selection：{source_key}"
        )

    line = merged.get("line")

    rec_id = stable_rec_id(
        match_id=match_id,
        source_key=source_key,
        period=period,
        market=market,
        selection=selection,
        line=line,
    )

    market_scope = optional_text(
        merged.get("market_scope")
        or merged.get("team")
        or merged.get("scope")
    ).upper()

    conservative_hit = probability_value(
        merged,
        "hit",
        "minimum",
    )

    median_hit = probability_value(
        merged,
        "hit",
        "median",
    )

    nonloss = probability_value(
        merged,
        "nonloss",
        "minimum",
    )

    full_loss = probability_value(
        merged,
        "full_loss",
        "maximum",
    )

    fair_odds = summary_value(
        merged,
        "fair_odds",
        "maximum",
    )

    expected_value = nested_value(
        merged,
        [
            (
                "expected_return",
                "minimum",
            ),
            (
                "expected_value",
                "minimum",
            ),
            (
                "expected_value",
            ),
        ],
    )

    edge = nested_value(
        merged,
        [
            (
                "edge",
                "minimum",
            ),
            (
                "edge",
                "median",
            ),
            (
                "edge",
            ),
        ],
    )

    record = {
        "rec_id": rec_id,
        "match_id": match_id,
        "tier": tier,
        "rank": rank,
        "rec_title": (
            optional_text(
                merged.get("label")
            )
            or source_key
        ),
        "market": market,
        "selection": selection,
        "line": line,
        "odds": (
            merged.get("hkjc_odds")
            if merged.get("hkjc_odds")
            is not None
            else merged.get("odds")
        ),
        "conservative_hit": (
            conservative_hit
            if conservative_hit is not None
            else ""
        ),
        "median_hit": (
            median_hit
            if median_hit is not None
            else ""
        ),
        "nonloss_probability": (
            nonloss
            if nonloss is not None
            else ""
        ),
        "full_loss_probability": (
            full_loss
            if full_loss is not None
            else ""
        ),
        "fair_odds": (
            fair_odds
            if fair_odds is not None
            else ""
        ),
        "price_status": optional_text(
            merged.get("price_status")
        ),
        "commentary": candidate_commentary(
            merged
        ),
        "stars": max(
            1,
            min(
                5,
                safe_int(
                    merged.get("stars"),
                    3,
                ),
            ),
        ),
        "is_heavy": safe_bool(
            merged.get("is_heavy")
        ),
        "compatibility_group": optional_text(
            merged.get(
                "compatibility_group"
            )
        ),
        "conflict_ids": "",
        "result": (
            optional_text(
                merged.get("result")
            )
            or "pending"
        ),
        "status": publish_status,
        "period": period,
        "market_scope": market_scope,
        "edge": (
            edge
            if edge is not None
            else ""
        ),
        "expected_value": (
            expected_value
            if expected_value is not None
            else ""
        ),
    }

    return (
        record,
        source_key,
        conflict_source_ids(merged),
    )


def correct_score_portal_records(
    *,
    match_id: str,
    result: Dict[str, Any],
    publish_status: str,
    starting_rank: int,
) -> List[Dict[str, Any]]:
    correct_scores = result.get(
        "correct_scores",
        {},
    )

    if not isinstance(
        correct_scores,
        dict,
    ):
        return []

    records = correct_scores.get(
        "recommendations",
        [],
    )

    if not isinstance(records, list):
        return []

    output: List[Dict[str, Any]] = []

    for index, score in enumerate(
        records,
        start=starting_rank,
    ):
        if not isinstance(score, dict):
            continue

        selection = optional_text(
            score.get("score")
        )

        if not selection:
            continue

        probability = score.get(
            "probability",
            {},
        )

        if not isinstance(
            probability,
            dict,
        ):
            probability = {}

        fair_odds = (
            score.get(
                "central_fair_odds"
            )
            if score.get(
                "central_fair_odds"
            ) is not None
            else score.get("fair_odds")
        )

        rec_id = stable_rec_id(
            match_id=match_id,
            source_key=(
                "correct_score_"
                + selection
            ),
            period="FT",
            market="CORRECT_SCORE",
            selection=selection,
            line="",
        )

        output.append({
            "rec_id": rec_id,
            "match_id": match_id,
            "tier": "CORRECT_SCORE",
            "rank": index,
            "rec_title": f"波膽 {selection}",
            "market": "CORRECT_SCORE",
            "selection": selection,
            "line": "",
            "odds": "",
            "conservative_hit": (
                probability.get("minimum", "")
            ),
            "median_hit": (
                probability.get("median", "")
            ),
            "nonloss_probability": "",
            "full_loss_probability": "",
            "fair_odds": (
                fair_odds
                if fair_odds is not None
                else ""
            ),
            "price_status": "REFERENCE_ONLY",
            "commentary": (
                "高風險波膽參考；"
                "不同波膽結果互相排斥。"
            ),
            "stars": 2,
            "is_heavy": False,
            "compatibility_group": (
                f"{match_id}:FT:CORRECT_SCORE"
            ),
            "conflict_ids": "",
            "result": "pending",
            "status": publish_status,
            "period": "FT",
            "market_scope": "SCORE",
            "edge": "",
            "expected_value": "",
        })

    score_ids = [
        record["rec_id"]
        for record in output
    ]

    for record in output:
        record["conflict_ids"] = ",".join(
            rec_id
            for rec_id in score_ids
            if rec_id != record["rec_id"]
        )

    return output


def build_portal_bundle(
    result: Dict[str, Any],
    input_snapshot: Dict[str, Any],
    *,
    publish_alternatives: bool,
    publish_correct_scores: bool,
    publish_status: str,
    match_id_override: str = "",
    model_direction_override: str = "",
) -> Dict[str, Any]:
    input_lookup = build_input_candidate_lookup(
        input_snapshot
    )

    match_id = (
        optional_text(match_id_override)
        or stable_match_id(
            result,
            input_snapshot,
        )
    )

    result_match = result.get(
        "match",
        {},
    )

    input_match = input_snapshot.get(
        "match",
        {},
    )

    if not isinstance(result_match, dict):
        result_match = {}

    if not isinstance(input_match, dict):
        input_match = {}

    home = optional_text(
        result_match.get(
            "home",
            input_match.get("home"),
        )
    )

    away = optional_text(
        result_match.get(
            "away",
            input_match.get("away"),
        )
    )

    match_name = (
        optional_text(
            result_match.get(
                "name",
                input_match.get("name"),
            )
        )
        or (
            f"{home} vs {away}"
            if home and away
            else match_id
        )
    )

    candidates = result.get(
        "candidate_markets",
        [],
    )

    if not isinstance(candidates, list):
        candidates = []

    official_lookup = official_record_lookup(
        result
    )

    official_ids = official_identity_set(
        result
    )

    if not candidates:
        candidates = [
            item
            for item in result.get(
                "recommendations",
                [],
            )
            if isinstance(item, dict)
        ]

    portal_records: List[
        Dict[str, Any]
    ] = []

    source_to_rec_id: Dict[str, str] = {}
    pending_conflicts: Dict[
        str,
        List[str],
    ] = {}

    official_rank = 1
    alternative_rank = 1

    for raw_candidate in candidates:
        if not isinstance(
            raw_candidate,
            dict,
        ):
            continue

        source_identity = item_identity(
            raw_candidate
        )

        is_official = bool(
            raw_candidate.get("official")
        ) or (
            source_identity
            and source_identity
            in official_ids
        )

        if is_official:
            official_version = (
                official_lookup.get(
                    source_identity
                )
            )

            if official_version:
                merged_item = deepcopy(
                    raw_candidate
                )
                merged_item.update(
                    official_version
                )
            else:
                merged_item = raw_candidate

            tier = "OFFICIAL"

            candidate_rank = safe_int(
                merged_item.get(
                    "rank",
                    merged_item.get(
                        "official_rank"
                    ),
                ),
                official_rank,
            )

            official_rank = max(
                official_rank + 1,
                candidate_rank + 1,
            )

        else:
            if not publish_alternatives:
                continue

            merged_item = raw_candidate
            tier = "ALTERNATIVE"

            candidate_rank = safe_int(
                merged_item.get(
                    "reference_rank"
                ),
                alternative_rank,
            )

            alternative_rank += 1

        record, source_key, conflicts = (
            candidate_to_portal_record(
                match_id=match_id,
                item=merged_item,
                input_lookup=input_lookup,
                tier=tier,
                rank=candidate_rank,
                publish_status=publish_status,
            )
        )

        portal_records.append(record)

        source_to_rec_id[
            source_key
        ] = record["rec_id"]

        if source_identity:
            source_to_rec_id[
                source_identity
            ] = record["rec_id"]

        pending_conflicts[
            record["rec_id"]
        ] = conflicts

    for record in portal_records:
        source_conflicts = (
            pending_conflicts.get(
                record["rec_id"],
                [],
            )
        )

        resolved_ids = []

        for source_id in source_conflicts:
            resolved = source_to_rec_id.get(
                source_id
            )

            if (
                resolved
                and resolved
                != record["rec_id"]
            ):
                resolved_ids.append(
                    resolved
                )

        record["conflict_ids"] = ",".join(
            dict.fromkeys(resolved_ids)
        )

    if publish_correct_scores:
        portal_records.extend(
            correct_score_portal_records(
                match_id=match_id,
                result=result,
                publish_status=publish_status,
                starting_rank=1,
            )
        )

    portal_records.sort(
        key=lambda record: (
            {
                "OFFICIAL": 0,
                "ALTERNATIVE": 1,
                "CORRECT_SCORE": 2,
            }.get(
                record.get("tier"),
                9,
            ),
            PERIOD_ORDER.get(
                record.get("period"),
                9,
            ),
            safe_int(
                record.get("rank"),
                999,
            ),
        )
    )

    match_record = {
        "match_id": match_id,
        "match_name": match_name,
        "home_team": home,
        "away_team": away,
        "competition": optional_text(
            result_match.get(
                "competition",
                input_match.get(
                    "competition"
                ),
            )
        ),
        "kickoff": optional_text(
            result_match.get(
                "kickoff",
                input_match.get("kickoff"),
            )
        ),
        "status": publish_status,
        # Never automatically publish the engine's original
        # betting direction. The publisher must enter the
        # final direction manually, or leave it blank.
        "model_direction": optional_text(
            model_direction_override
        ),
        "model_summary": actual_model_summary(
            result
        ),
        "top_scores": top_scores_text(
            result
        ),
        "final_score": "",
    }

    return {
        "action": "publish_bundle",
        "replace_recommendations": True,
        "match": match_record,
        "recommendations": portal_records,
    }


# ============================================================
# 12. Results helpers
# ============================================================

def result_summary_card(
    label: str,
    value: str,
    note: str,
    css_class: str = "",
) -> None:
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">
                {html_escape(label)}
            </div>
            <div class="summary-value {css_class}">
                {html_escape(value)}
            </div>
            <div class="summary-note">
                {html_escape(note)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def period_badge(period: Any) -> str:
    normalized = normalize_period(
        period
    )

    css_class = {
        "FT": "period-ft",
        "HT": "period-ht",
        "2H": "period-2h",
    }.get(
        normalized,
        "period-ft",
    )

    label = {
        "FT": "FT 全場",
        "HT": "HT 半場",
        "2H": "2H 下半場",
    }.get(
        normalized,
        normalized,
    )

    return (
        f'<span class="{css_class}">'
        f"{html_escape(label)}"
        "</span>"
    )


def recommendation_card(
    recommendation: Dict[str, Any],
) -> None:
    rank = recommendation.get(
        "rank",
        recommendation.get(
            "official_rank",
            "—",
        ),
    )

    label = recommendation.get(
        "label",
        recommendation.get(
            "id",
            "—",
        ),
    )

    period = recommendation.get(
        "period",
        "FT",
    )

    hit_min = probability_value(
        recommendation,
        "hit",
        "minimum",
    )

    hit_median = probability_value(
        recommendation,
        "hit",
        "median",
    )

    nonloss_min = probability_value(
        recommendation,
        "nonloss",
        "minimum",
    )

    full_loss_max = probability_value(
        recommendation,
        "full_loss",
        "maximum",
    )

    ev_min = summary_value(
        recommendation,
        "expected_return",
        "minimum",
    )

    st.markdown(
        f"""
        <div class="recommendation-card">
            <div>
                {period_badge(period)}
            </div>
            <div class="recommendation-rank">
                OFFICIAL PICK #{html_escape(rank)}
            </div>
            <div class="recommendation-name">
                {html_escape(label)}
            </div>
            <div class="recommendation-stats">
                HKJC 賠率：
                <b>{format_odds(recommendation.get("hkjc_odds"))}</b>
                &nbsp;｜&nbsp;
                保守命中率：
                <b>{format_probability(hit_min)}</b>
                &nbsp;｜&nbsp;
                中位命中率：
                <b>{format_probability(hit_median)}</b>
                &nbsp;｜&nbsp;
                保守不輸率：
                <b>{format_probability(nonloss_min)}</b>
                <br>
                最大全輸率：
                <b>{format_probability(full_loss_max)}</b>
                &nbsp;｜&nbsp;
                保守 EV：
                <b>{format_ev(ev_min)}</b>
                &nbsp;｜&nbsp;
                價格：
                <b>{html_escape(
                    status_chinese(
                        recommendation.get("price_status")
                    )
                )}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def candidate_dataframe(
    candidates: List[Dict[str, Any]],
) -> pd.DataFrame:
    rows = []

    for candidate in candidates:
        reasons = (
            candidate.get(
                "official_exclusion_reasons",
                [],
            )
            + candidate.get(
                "exclusion_reasons",
                [],
            )
        )

        conflicts = []

        for conflict in candidate.get(
            "conflicts_with",
            [],
        ):
            if isinstance(conflict, dict):
                label = (
                    conflict.get(
                        "selected_label"
                    )
                    or conflict.get("label")
                    or item_identity(conflict)
                )
            else:
                label = optional_text(
                    conflict
                )

            if label:
                conflicts.append(
                    str(label)
                )

        rows.append({
            "狀態": (
                "✅ 正式推薦"
                if candidate.get("official")
                else "參考"
            ),
            "排名": candidate.get(
                "official_rank",
                candidate.get("rank"),
            ),
            "ID": item_identity(candidate),
            "候選盤": candidate.get("label"),
            "時段": normalize_period(
                candidate.get("period")
            ),
            "市場": normalize_market(
                candidate.get("market")
            ),
            "HKJC 賠率": candidate.get(
                "hkjc_odds",
                candidate.get("odds"),
            ),
            "保守命中率": format_probability(
                probability_value(
                    candidate,
                    "hit",
                    "minimum",
                )
            ),
            "中位命中率": format_probability(
                probability_value(
                    candidate,
                    "hit",
                    "median",
                )
            ),
            "保守不輸率": format_probability(
                probability_value(
                    candidate,
                    "nonloss",
                    "minimum",
                )
            ),
            "最大全輸率": format_probability(
                probability_value(
                    candidate,
                    "full_loss",
                    "maximum",
                )
            ),
            "保守公平賠率": format_odds(
                summary_value(
                    candidate,
                    "fair_odds",
                    "maximum",
                )
            ),
            "保守 EV": format_ev(
                summary_value(
                    candidate,
                    "expected_return",
                    "minimum",
                )
            ),
            "價格": status_chinese(
                candidate.get(
                    "price_status"
                )
            ),
            "衝突項目": "、".join(
                conflicts
            ),
            "排除原因": "；".join(
                translate_reason(reason)
                for reason in reasons
            ),
        })

    return pd.DataFrame(rows)


def stress_dataframe(
    candidate: Dict[str, Any],
) -> pd.DataFrame:
    stress = candidate.get(
        "stress_audit",
        {},
    )

    rows = []

    for key, label in [
        (
            "light",
            "輕度",
        ),
        (
            "medium",
            "中度",
        ),
        (
            "heavy",
            "重度",
        ),
    ]:
        record = stress.get(
            key,
            {},
        )

        rows.append({
            "壓力程度": label,
            "最低命中率": format_probability(
                record.get(
                    "minimum_hit_probability"
                )
            ),
            "中位命中率": format_probability(
                record.get(
                    "median_hit_probability"
                )
            ),
            "有效情境數": record.get(
                "scenario_count"
            ),
        })

    return pd.DataFrame(rows)


# ============================================================
# 13. Header
# ============================================================

st.markdown(
    f"""
    <div class="ultra-hero">
        <div class="ultra-badge">
            Engine + Portal Publisher · App V{APP_VERSION}
        </div>
        <h1 class="ultra-title">
            🛡️ AEGIS ULTRA
        </h1>
        <p class="ultra-subtitle">
            批量輸入 FT、HT 尖銳市場及 HKJC 候選盤，
            執行 Aegis Ultra V2 分析，並把正式推薦、
            參考選擇、波膽、period、market scope、
            edge、EV 及衝突資料直接發佈到 VIP Match Centre。
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 14. Sidebar
# ============================================================

with st.sidebar:
    st.markdown("## 🛡️ AEGIS ULTRA")

    st.caption(
        f"App V{APP_VERSION} · Engine V{ENGINE_VERSION}"
    )

    st.success(
        "FT／HT 分開處理\n\n"
        "可直接發佈到 VIP App"
    )

    st.divider()

    input_mode = st.radio(
        "輸入模式",
        options=[
            "🎛️ 批量貼上",
            "📋 貼上 JSON",
            "📁 上載 JSON",
        ],
        index=0,
    )

    st.divider()

    st.markdown("### Portal API")

    st.caption(
        configured_api_url()
    )

    if configured_api_token():
        st.success(
            "Portal API secrets 已載入。"
        )
    else:
        st.error(
            "無法讀取 Streamlit secret："
            "portal_api.token"
        )

    if st.button(
        "🔌 測試 Portal API",
        use_container_width=True,
    ):
        try:
            response = portal_request({
                "action": "ping",
            })

            st.session_state[
                "portal_last_response"
            ] = response

            st.success(
                "Portal API 連接成功。"
            )

        except Exception as error:
            st.error(str(error))

    st.divider()

    st.markdown("### 分析原則")

    st.write("• FT 與 HT 使用明確 period")
    st.write("• 不會把缺失 period 任意當成 FT")
    st.write("• Target-line-out 重建")
    st.write("• 保守命中率優先")
    st.write("• EV 只作價格審核")
    st.write("• conflict_ids 保留到會員 App")

    st.divider()

    if st.button(
        "🗑️ 清除目前分析",
        use_container_width=True,
    ):
        cached_engine_run.clear()

        st.session_state.ultra_result = None
        st.session_state.ultra_input = None
        st.session_state.ultra_analysis_hash = None
        st.session_state.ultra_error = None
        st.session_state.ultra_traceback = None
        st.session_state.portal_last_response = None

        st.rerun()


# ============================================================
# 15. Input interface
# ============================================================

input_to_run = None
input_preview = None


if input_mode == "🎛️ 批量貼上":
    st.markdown(
        '<div class="section-label">Bulk input workflow</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-panel">
            <b>直接貼上整批賠率。</b><br>
            FT 與 HT 分開輸入及保存。
            候選盤的 period 會由輸入一路保留到引擎結果、
            Google Sheets 及 VIP App。
        </div>
        """,
        unsafe_allow_html=True,
    )

    match_tab, sharp_tab, hkjc_tab, policy_tab = st.tabs([
        "① 賽事資料",
        "② 尖銳市場",
        "③ HKJC 候選盤",
        "④ 推薦設定",
    ])

    with match_tab:
        st.subheader("賽事資料")

        first, second = st.columns(2)

        with first:
            home_name = st.text_input(
                "主隊",
                key="ultra_home_name",
            )

            competition = st.text_input(
                "賽事",
                placeholder="例如：英格蘭超級聯賽",
                key="ultra_competition",
            )

            kickoff = st.text_input(
                "開賽時間",
                placeholder="例如：2026-08-15T22:00:00+08:00",
                key="ultra_kickoff",
            )

        with second:
            away_name = st.text_input(
                "客隊",
                key="ultra_away_name",
            )

            custom_match_name = st.text_input(
                "自訂賽事名稱",
                placeholder="留空時使用「主隊 vs 客隊」",
                key="ultra_match_name",
            )

            snapshot_time = st.text_input(
                "市場快照時間",
                value=(
                    datetime.now()
                    .astimezone()
                    .isoformat(
                        timespec="minutes"
                    )
                ),
                key="ultra_snapshot_time",
            )

    sharp_sources_raw = []

    with sharp_tab:
        st.subheader("尖銳市場來源")

        st.markdown(
            """
            <div class="format-panel">
                <b>AH：</b>主隊讓球線　主隊賠率　客隊賠率<br>
                <b>O/U：</b>入球線　大盤賠率　細盤賠率<br>
                <b>HHAD：</b>主隊整數讓球　主勝　和　客勝<br>
                <b>球隊 O/U：</b>HOME/AWAY　入球線　大盤賠率　細盤賠率
            </div>
            """,
            unsafe_allow_html=True,
        )

        source_count = st.number_input(
            "尖銳來源數目",
            min_value=1,
            max_value=5,
            value=1,
            step=1,
            key="ultra_source_count",
        )

        for source_index in range(
            int(source_count)
        ):
            default_key = (
                "pinnacle"
                if source_index == 0
                else f"source_{source_index + 1}"
            )

            default_title = (
                "Pinnacle"
                if source_index == 0
                else f"Sharp Source {source_index + 1}"
            )

            with st.container(border=True):
                st.markdown(
                    f"### ⚡ 尖銳來源 {source_index + 1}"
                )

                first, second = st.columns(2)

                with first:
                    source_key = st.text_input(
                        "來源識別碼",
                        value=default_key,
                        key=f"source_key_{source_index}",
                    )

                with second:
                    source_title = st.text_input(
                        "來源名稱",
                        value=default_title,
                        key=f"source_title_{source_index}",
                    )

                ft_source_tab, ht_source_tab = st.tabs([
                    "全場 FT",
                    "半場 HT",
                ])

                with ft_source_tab:
                    ft_raw = render_sharp_period(
                        source_index,
                        "FT",
                        enabled_default=True,
                    )

                with ht_source_tab:
                    ht_raw = render_sharp_period(
                        source_index,
                        "HT",
                        enabled_default=False,
                    )

                sharp_sources_raw.append({
                    "key": source_key,
                    "title": source_title,
                    "FT": ft_raw,
                    "HT": ht_raw,
                })

        available_source_keys = [
            optional_text(
                source["key"]
            ).lower()
            for source in sharp_sources_raw
            if optional_text(source["key"])
        ]

        primary_source = st.selectbox(
            "主要尖銳來源",
            options=(
                available_source_keys
                or ["pinnacle"]
            ),
            index=0,
            key="ultra_primary_source",
        )

    with hkjc_tab:
        st.subheader("HKJC 候選盤")

        st.markdown(
            """
            <div class="format-panel">
                使用 <b>X</b> 或 <b>-</b> 表示沒有賠率。
                FT 候選盤會保存 period=FT；
                HT 候選盤會保存 period=HT。
            </div>
            """,
            unsafe_allow_html=True,
        )

        ft_hkjc_tab, ht_hkjc_tab = st.tabs([
            "全場 FT",
            "半場 HT",
        ])

        with ft_hkjc_tab:
            hkjc_ft_raw = render_hkjc_period(
                "FT"
            )

        with ht_hkjc_tab:
            hkjc_ht_raw = render_hkjc_period(
                "HT"
            )

    with policy_tab:
        st.subheader("正式推薦設定")

        first, second, third = st.columns(3)

        with first:
            minimum_odds = st.number_input(
                "最低 HKJC 賠率",
                min_value=1.01,
                max_value=1000.0,
                value=1.50,
                step=0.05,
                format="%.2f",
                key="ultra_minimum_odds",
            )

        with second:
            maximum_recommendations = st.selectbox(
                "正式推薦數目上限",
                options=list(range(1, 11)),
                index=2,
                key="ultra_max_recommendations",
            )

        with third:
            minimum_hit_probability_pct = (
                st.number_input(
                    "最低保守命中率 (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=50.0,
                    step=1.0,
                    format="%.1f",
                    key="ultra_minimum_hit_pct",
                )
            )

        first, second = st.columns(2)

        with first:
            use_maximum_odds = st.checkbox(
                "設定最高 HKJC 賠率",
                value=False,
                key="ultra_use_maximum_odds",
            )

            maximum_odds = (
                st.number_input(
                    "最高 HKJC 賠率",
                    min_value=1.01,
                    max_value=1000.0,
                    value=10.00,
                    step=0.10,
                    format="%.2f",
                    key="ultra_maximum_odds",
                )
                if use_maximum_odds
                else None
            )

        with second:
            correct_score_count = st.selectbox(
                "波膽參考數目",
                options=[
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                ],
                index=2,
                key="ultra_correct_score_count",
            )

        devig_methods = st.multiselect(
            "去水情境",
            options=[
                "MULTIPLICATIVE",
                "POWER",
            ],
            default=[
                "MULTIPLICATIVE",
                "POWER",
            ],
            key="ultra_devig_methods",
        )

        use_ev_floor = st.checkbox(
            "拒絕嚴重回報不足的價格",
            value=False,
            key="ultra_use_ev_floor",
        )

        ev_floor_pct = (
            st.number_input(
                "最低容許 EV (%)",
                min_value=-100.0,
                max_value=500.0,
                value=-10.0,
                step=1.0,
                format="%.1f",
                key="ultra_ev_floor_pct",
            )
            if use_ev_floor
            else -10.0
        )

        with st.expander(
            "進階引擎功能",
            expanded=True,
        ):
            quality_gate = st.checkbox(
                "模型品質閘門",
                value=True,
                key="ultra_quality_gate",
            )

            stress_audit = st.checkbox(
                "輕／中／重壓力測試",
                value=True,
                key="ultra_stress_audit",
            )

            family_out_audit = st.checkbox(
                "整個市場族群移除測試",
                value=True,
                key="ultra_family_out_audit",
            )

            adaptive_grids = st.checkbox(
                "自適應入球網格",
                value=True,
                key="ultra_adaptive_grids",
            )

            ht_ft_coherence = st.checkbox(
                "半場－全場一致性測試",
                value=True,
                key="ultra_ht_ft_coherence",
            )

    st.divider()

    run_manual = st.button(
        "🚀 開始 AEGIS ULTRA 分析",
        type="primary",
        use_container_width=True,
        key="ultra_manual_run",
    )

    if run_manual:
        try:
            clean_home = optional_text(
                home_name
            )

            clean_away = optional_text(
                away_name
            )

            if not clean_home or not clean_away:
                raise ValueError(
                    "主隊及客隊不可留空。"
                )

            if (
                clean_home.casefold()
                == clean_away.casefold()
            ):
                raise ValueError(
                    "主隊及客隊不可相同。"
                )

            if not devig_methods:
                raise ValueError(
                    "最少需要選擇一種去水方法。"
                )

            sharp_books = []
            seen_source_keys = set()

            for source_index, source in enumerate(
                sharp_sources_raw,
                start=1,
            ):
                source_key = optional_text(
                    source["key"]
                ).lower()

                source_title = (
                    optional_text(
                        source["title"]
                    )
                    or source_key
                )

                if not source_key:
                    raise ValueError(
                        f"尖銳來源 {source_index} "
                        "缺少識別碼。"
                    )

                if source_key in seen_source_keys:
                    raise ValueError(
                        f"尖銳來源識別碼重複："
                        f"{source_key}。"
                    )

                seen_source_keys.add(
                    source_key
                )

                markets = {}

                for period in [
                    "FT",
                    "HT",
                ]:
                    raw_period = source.get(
                        period
                    )

                    if raw_period is None:
                        continue

                    parsed_markets = (
                        build_sharp_period(
                            raw_period,
                            source_title,
                            period,
                        )
                    )

                    if not period_has_market(
                        parsed_markets
                    ):
                        raise ValueError(
                            f"{source_title} {period} "
                            "已啟用，但沒有輸入任何市場。"
                        )

                    markets[period] = (
                        parsed_markets
                    )

                if not markets:
                    raise ValueError(
                        f"{source_title} 沒有啟用"
                        "任何 FT 或 HT 市場。"
                    )

                sharp_books.append({
                    "key": source_key,
                    "title": source_title,
                    "timestamp": optional_text(
                        snapshot_time
                    ),
                    "markets": markets,
                })

            if primary_source not in {
                source["key"]
                for source in sharp_books
            }:
                raise ValueError(
                    "主要尖銳來源不在已建立的來源中。"
                )

            hkjc_markets = (
                build_hkjc_candidates(
                    home_name=clean_home,
                    away_name=clean_away,
                    raw_periods={
                        "FT": hkjc_ft_raw,
                        "HT": hkjc_ht_raw,
                    },
                )
            )

            match_name = (
                optional_text(
                    custom_match_name
                )
                or (
                    f"{clean_home} vs "
                    f"{clean_away}"
                )
            )

            input_to_run = {
                "match": {
                    "name": match_name,
                    "home": clean_home,
                    "away": clean_away,
                    "competition": optional_text(
                        competition
                    ),
                    "kickoff": optional_text(
                        kickoff
                    ),
                    "snapshot_time": optional_text(
                        snapshot_time
                    ),
                },
                "sharp_books": sharp_books,
                "hkjc_markets": hkjc_markets,
                "settings": {
                    "primary_source": primary_source,
                    "minimum_odds": float(
                        minimum_odds
                    ),
                    "maximum_odds": (
                        float(maximum_odds)
                        if maximum_odds
                        is not None
                        else None
                    ),
                    "max_recommendations": int(
                        maximum_recommendations
                    ),
                    "minimum_official_hit_probability": (
                        float(
                            minimum_hit_probability_pct
                        )
                        / 100.0
                    ),
                    "correct_score_count": int(
                        correct_score_count
                    ),
                    "devig_methods": list(
                        devig_methods
                    ),
                    "ev_rejection_floor": (
                        float(ev_floor_pct)
                        / 100.0
                        if use_ev_floor
                        else None
                    ),
                    "features": {
                        "quality_gate": bool(
                            quality_gate
                        ),
                        "stress_audit": bool(
                            stress_audit
                        ),
                        "family_out_audit": bool(
                            family_out_audit
                        ),
                        "adaptive_grids": bool(
                            adaptive_grids
                        ),
                        "ht_ft_coherence": bool(
                            ht_ft_coherence
                        ),
                    },
                },
            }

            input_preview = deepcopy(
                input_to_run
            )

        except Exception as input_error:
            st.session_state.ultra_error = str(
                input_error
            )

            st.session_state.ultra_traceback = (
                traceback.format_exc()
            )

            st.error(
                f"輸入錯誤：{input_error}"
            )


elif input_mode == "📋 貼上 JSON":
    st.markdown(
        '<div class="section-label">Direct JSON input</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-panel">
            直接貼上完整 AEGIS ULTRA V2 輸入 JSON。
            period 必須明確保留於每個 HKJC 候選盤。
        </div>
        """,
        unsafe_allow_html=True,
    )

    json_input_value = st.text_area(
        "AEGIS ULTRA 輸入 JSON",
        key="ultra_json_text",
        height=650,
    )

    run_json = st.button(
        "🚀 執行貼上的 JSON",
        type="primary",
        use_container_width=True,
        key="ultra_json_run",
    )

    if run_json:
        try:
            parsed_json = json.loads(
                json_input_value
            )

            if not isinstance(
                parsed_json,
                dict,
            ):
                raise ValueError(
                    "JSON 最外層必須是物件。"
                )

            input_to_run = parsed_json
            input_preview = deepcopy(
                parsed_json
            )

        except Exception as json_error:
            st.session_state.ultra_error = str(
                json_error
            )

            st.session_state.ultra_traceback = (
                traceback.format_exc()
            )

            st.error(
                f"JSON 錯誤：{json_error}"
            )


else:
    st.markdown(
        '<div class="section-label">JSON file input</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "上載 AEGIS ULTRA JSON",
        type=["json"],
    )

    uploaded_preview = None

    if uploaded_file is not None:
        try:
            uploaded_text = (
                uploaded_file
                .getvalue()
                .decode("utf-8-sig")
            )

            uploaded_preview = json.loads(
                uploaded_text
            )

            st.success(
                f"已讀取：{uploaded_file.name}"
            )

            with st.expander(
                "檢查上載內容",
                expanded=False,
            ):
                st.json(uploaded_preview)

        except Exception as preview_error:
            uploaded_preview = None

            st.error(
                f"無法讀取 JSON：{preview_error}"
            )

    run_uploaded = st.button(
        "🚀 執行上載的 JSON",
        type="primary",
        use_container_width=True,
        key="ultra_upload_run",
    )

    if run_uploaded:
        try:
            if uploaded_preview is None:
                raise ValueError(
                    "請先上載有效的 JSON 檔案。"
                )

            if not isinstance(
                uploaded_preview,
                dict,
            ):
                raise ValueError(
                    "JSON 最外層必須是物件。"
                )

            input_to_run = uploaded_preview
            input_preview = deepcopy(
                uploaded_preview
            )

        except Exception as upload_error:
            st.session_state.ultra_error = str(
                upload_error
            )

            st.session_state.ultra_traceback = (
                traceback.format_exc()
            )

            st.error(
                f"JSON 錯誤：{upload_error}"
            )


# ============================================================
# 16. Execute engine
# ============================================================

if input_preview is not None:
    with st.expander(
        "檢查提交給引擎的完整資料",
        expanded=False,
    ):
        st.json(input_preview)

    st.download_button(
        "⬇️ 下載本次輸入 JSON",
        data=json_text(input_preview),
        file_name=download_name(
            "aegis_ultra_input"
        ),
        mime="application/json",
        use_container_width=True,
    )


if input_to_run is not None:
    st.session_state.ultra_error = None
    st.session_state.ultra_traceback = None

    try:
        with st.spinner(
            "正在重建 FT／HT 尖銳市場、"
            "執行 target-line-out、壓力測試、"
            "HT–FT 一致性及推薦衝突檢查……"
        ):
            execute_engine(input_to_run)
            st.success("AEGIS ULTRA 分析完成！")
    except Exception as exec_error:
        st.session_state.ultra_error = str(exec_error)
        st.session_state.ultra_traceback = traceback.format_exc()
        st.error(f"引擎執行錯誤：{exec_error}")


# ============================================================
# 17. Results Display & Portal Publisher
# ============================================================

if st.session_state.ultra_error:
    st.error(f"分析時發生錯誤：{st.session_state.ultra_error}")
    with st.expander("查看錯誤 Call Stack", expanded=True):
        st.code(st.session_state.ultra_traceback)

result = st.session_state.get("ultra_result")
input_snapshot = st.session_state.get("ultra_input") or {}

if result:
    st.divider()
    st.markdown(
        '<div class="section-label">Analysis Results</div>',
        unsafe_allow_html=True,
    )

    match_info = result.get("match", {})
    home_team = match_info.get("home", "主隊")
    away_team = match_info.get("away", "客隊")
    match_display = match_info.get("name", f"{home_team} vs {away_team}")

    recs = result.get("recommendations", [])
    candidates = result.get("candidate_markets", [])
    quality_info = result.get("model_quality", {})
    coherence_info = result.get("ht_ft_coherence", {})

    quality_status = quality_info.get("status", "N/A") if isinstance(quality_info, dict) else "N/A"
    coherence_status = coherence_info.get("status", "N/A") if isinstance(coherence_info, dict) else "N/A"

    # Summary Cards Grid
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        result_summary_card(
            "賽事",
            match_display,
            match_info.get("competition", "未指定"),
        )

    with col2:
        result_summary_card(
            "候選盤數目",
            f"{len(candidates)} 個",
            "已被分析盤口",
        )

    with col3:
        result_summary_card(
            "正式推薦",
            f"{len(recs)} 項",
            "符合品質閘門及下限",
            css_class="status-pass" if recs else "status-caution",
        )

    with col4:
        result_summary_card(
            "模型品質閘門",
            status_chinese(quality_status),
            "模型擬合與驗證",
            css_class=status_css_class(quality_status),
        )

    with col5:
        result_summary_card(
            "HT–FT 一致性",
            status_chinese(coherence_status),
            "半全場結構審核",
            css_class=status_css_class(coherence_status),
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Tabs
    tab_official, tab_candidates, tab_scores, tab_audit, tab_publish, tab_export = st.tabs([
        "🎯 正式推薦",
        "📊 所有候選盤",
        "⚽ 波膽預測",
        "🧪 壓力與一致性審核",
        "🚀 VIP Portal 發佈",
        "💾 導出 JSON",
    ])

    with tab_official:
        st.markdown("### 🎯 正式推薦項目 (Official Picks)")
        if not recs:
            st.info("本場賽事沒有候選盤達到正式推薦標準。")
        else:
            for rec in recs:
                recommendation_card(rec)

    with tab_candidates:
        st.markdown("### 📊 所有候選盤詳細數據")
        if candidates:
            df_candidates = candidate_dataframe(candidates)
            st.dataframe(
                df_candidates,
                use_container_width=True,
                height=450,
            )
        else:
            st.info("沒有候選盤數據。")

    with tab_scores:
        st.markdown("### ⚽ 波膽與比分概率")
        correct_scores = result.get("correct_scores", {})
        if isinstance(correct_scores, dict) and "recommendations" in correct_scores:
            score_recs = correct_scores.get("recommendations", [])
            if score_recs:
                score_cols = st.columns(min(len(score_recs), 4))
                for idx, score_item in enumerate(score_recs):
                    col_idx = idx % min(len(score_recs), 4)
                    with score_cols[col_idx]:
                        s_val = score_item.get("score", "—")
                        s_prob = score_item.get("probability", {}).get("minimum")
                        st.markdown(
                            f"""
                            <div class="score-card">
                                <div class="summary-label">波膽推介 #{idx + 1}</div>
                                <div class="score-value">{html_escape(s_val)}</div>
                                <div class="score-probability">保守概率：{format_probability(s_prob)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.markdown("<br>", unsafe_allow_html=True)

            score_grid = correct_scores.get("matrix") or correct_scores.get("probabilities")
            if score_grid and isinstance(score_grid, list):
                st.markdown("#### 波膽概率矩陣")
                st.dataframe(pd.DataFrame(score_grid), use_container_width=True)
        else:
            st.info("無波膽模型數據。")

    with tab_audit:
        st.markdown("### 🧪 模型品質與壓力測試審核")

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 模型品質 Gate")
            if isinstance(quality_info, dict):
                st.json(quality_info)
            else:
                st.write("無品質審核數據。")

        with c_right:
            st.markdown("#### 半全場 HT–FT 一致性")
            if isinstance(coherence_info, dict):
                st.json(coherence_info)
            else:
                st.write("無半全場一致性數據。")

        st.markdown("#### 個別候選盤壓力測試")
        if candidates:
            selected_cand_id = st.selectbox(
                "選擇候選盤查看壓力測試",
                options=[item_identity(c) or c.get("label", f"Candidate {i}") for i, c in enumerate(candidates)],
                key="audit_cand_select",
            )
            selected_cand = next(
                (c for c in candidates if (item_identity(c) or c.get("label")) == selected_cand_id),
                None,
            )
            if selected_cand and "stress_audit" in selected_cand:
                st.dataframe(stress_dataframe(selected_cand), use_container_width=True)
            else:
                st.info("選擇的候選盤沒有壓力測試數據。")

    with tab_publish:
        st.markdown("### 🚀 發佈至 VIP Match Centre")
        st.markdown(
            """
            <div class="publish-panel">
                將此場賽事的分析結果打包發佈到 VIP App Portal。<br>
                將包含比賽資料、正式推薦、參考盤口、波膽預測及衝突關聯等。
            </div>
            """,
            unsafe_allow_html=True,
        )

        p_col1, p_col2 = st.columns(2)

        with p_col1:
            match_id_inp = st.text_input(
                "Match ID (留空自動生成)",
                value="",
                help="自訂或留空自動導出 stable_match_id",
                key="pub_match_id",
            )

            pub_status = st.selectbox(
                "發佈狀態 (Status)",
                options=["published", "draft", "archived"],
                index=0,
                key="pub_status",
            )

            pub_alts = st.checkbox(
                "包含參考盤口 (Alternative Picks)",
                value=True,
                key="pub_alts",
            )

            pub_cs = st.checkbox(
                "包含波膽推介 (Correct Score Picks)",
                value=True,
                key="pub_cs",
            )

        with p_col2:
            model_dir_inp = st.text_area(
                "自訂 VIP 賽事方向 / 獨家分析 (Model Direction)",
                value="",
                placeholder="例如：主隊近況強勁，全場讓球及大球值得關注……（留空則不會強行覆蓋）",
                height=150,
                key="pub_model_dir",
            )

        st.markdown("#### 預覽即將發佈的 Bundle Payload")
        try:
            bundle_preview = build_portal_bundle(
                result=result,
                input_snapshot=input_snapshot,
                publish_alternatives=pub_alts,
                publish_correct_scores=pub_cs,
                publish_status=pub_status,
                match_id_override=match_id_inp,
                model_direction_override=model_dir_inp,
            )
            with st.expander("檢視完整發佈 JSON Bundle", expanded=False):
                st.json(bundle_preview)
        except Exception as bundle_err:
            bundle_preview = None
            st.error(f"Bundle 生成失敗：{bundle_err}")

        if st.button("🚀 立即發佈到 VIP App Portal", type="primary", use_container_width=True, key="pub_submit_btn"):
            if bundle_preview:
                try:
                    with st.spinner("正在將 Bundle 發佈到 VIP Match Centre API..."):
                        api_res = portal_request(bundle_preview)
                        st.session_state.portal_last_response = api_res
                        st.success("🎉 發佈成功！VIP Match Centre 已更新。")
                        st.json(api_res)
                except Exception as pub_err:
                    st.error(f"發佈失敗：{pub_err}")

        if st.session_state.get("portal_last_response"):
            with st.expander("上次 API 回傳結果", expanded=False):
                st.json(st.session_state.portal_last_response)

    with tab_export:
        st.markdown("### 💾 導出完整分析 JSON")
        st.caption("您可以下載完整分析結果 JSON 檔案以備存檔或進行離線分析。")

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                "⬇️ 下載引擎分析結果 (Result JSON)",
                data=json_text(result),
                file_name=download_name("aegis_ultra_result"),
                mime="application/json",
                use_container_width=True,
            )
        with d_col2:
            st.download_button(
                "⬇️ 下載輸入數據快照 (Input JSON)",
                data=json_text(input_snapshot),
                file_name=download_name("aegis_ultra_input_snapshot"),
                mime="application/json",
                use_container_width=True,
            )
