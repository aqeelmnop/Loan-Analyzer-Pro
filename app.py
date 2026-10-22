import inspect
import json
import uuid
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.ticker import FuncFormatter

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Calculator App",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Serasi dengan versi Streamlit lama (use_container_width)
# dan baharu (width="stretch").
if "width" in inspect.signature(st.button).parameters:
    STRETCH = {"width": "stretch"}
else:
    STRETCH = {"use_container_width": True}

MODE_QUICK = "Quick Calculation"
MODE_COMPARE = "Compare Two Loans"

COLOR_A = "#4da3ff"
COLOR_B = "#ffb347"
COLOR_INTEREST = "#ff7a7a"
PLOT_BG = "#0d1a2b"
PLOT_TEXT = "#c9d8ea"
PLOT_GRID = "#7ba0cf"

# =========================================================
# UI STYLE
# =========================================================

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top right, #16283f 0%, #0b1422 38%, #070b12 100%);
        }

        .block-container {
            max-width: 1280px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        .hero {
            padding: 42px 30px;
            border-radius: 24px;
            text-align: center;
            background:
                linear-gradient(
                    135deg,
                    rgba(33, 82, 143, 0.88),
                    rgba(14, 28, 49, 0.95)
                );
            border: 1px solid rgba(132, 180, 240, 0.22);
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.28);
            margin-bottom: 28px;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.7rem;
            color: white;
        }

        .hero p {
            max-width: 720px;
            margin: 12px auto 0 auto;
            color: #c9d8ea;
            font-size: 1.04rem;
        }

        .calculator-card {
            min-height: 225px;
            padding: 26px;
            border-radius: 20px;
            background:
                linear-gradient(
                    145deg,
                    rgba(21, 38, 60, 0.96),
                    rgba(11, 21, 35, 0.96)
                );
            border: 1px solid rgba(123, 160, 207, 0.18);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
            margin-bottom: 12px;
        }

        .calculator-card h2 {
            margin-top: 8px;
            margin-bottom: 8px;
            color: #ffffff;
        }

        .calculator-card p {
            color: #aebfd3;
            line-height: 1.6;
        }

        .page-title {
            padding: 22px 26px;
            border-radius: 18px;
            background: rgba(18, 34, 54, 0.84);
            border: 1px solid rgba(128, 166, 215, 0.18);
            margin-bottom: 22px;
        }

        .page-title h1 {
            margin: 0;
            color: white;
        }

        .page-title p {
            margin: 7px 0 0 0;
            color: #aebed2;
        }

        div[data-testid="stMetric"] {
            padding: 18px;
            border-radius: 16px;
            background:
                linear-gradient(
                    145deg,
                    rgba(24, 43, 66, 0.96),
                    rgba(13, 25, 40, 0.96)
                );
            border: 1px solid rgba(126, 164, 215, 0.18);
            box-shadow: 0 10px 22px rgba(0, 0, 0, 0.18);
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 46px;
            border-radius: 12px;
            font-weight: 700;
        }

        .smart-card {
            padding: 22px;
            border-radius: 17px;
            background:
                linear-gradient(
                    135deg,
                    rgba(27, 105, 72, 0.32),
                    rgba(12, 39, 32, 0.94)
                );
            border: 1px solid rgba(53, 201, 122, 0.35);
            margin-top: 16px;
        }

        .summary-card {
            padding: 20px;
            border-radius: 16px;
            background: rgba(17, 32, 50, 0.90);
            border-left: 4px solid #4da3ff;
            margin-top: 14px;
            margin-bottom: 14px;
            line-height: 1.65;
        }

        .small-note {
            color: #9dafc5;
            font-size: 0.86rem;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = []


def open_page(page_name):
    st.session_state.page = page_name


def go_home():
    st.session_state.page = "home"


# =========================================================
# BASIC HELPERS
# =========================================================

def rm(value):
    return f"RM {value:,.2f}"


def pct(value):
    return "N/A" if value is None else f"{value:.2f}%"


def format_months(months):
    years, remainder = divmod(int(months), 12)

    if years == 0:
        return f"{months} bulan"

    if remainder == 0:
        return f"{months} bulan ({years} tahun)"

    return f"{months} bulan ({years} tahun {remainder} bulan)"


def monthly_payment_reducing_balance(principal, annual_rate, months):
    if principal <= 0 or months <= 0:
        return 0.0

    monthly_rate = annual_rate / 100 / 12

    if monthly_rate == 0:
        return principal / months

    factor = (1 + monthly_rate) ** months

    return principal * monthly_rate * factor / (factor - 1)


def calculate_dsr(monthly_payment, income, commitments):
    """Return DSR (%), atau None jika pendapatan tidak diisi."""
    if income <= 0:
        return None

    return ((monthly_payment + commitments) / income) * 100


def fmt_dsr(dsr):
    return "N/A" if dsr is None else f"{dsr:.1f}%"


def affordability_label(dsr):
    if dsr is None:
        return (
            "⚪ DSR tidak dikira",
            "Isi pendapatan bulanan untuk melihat tahap affordability.",
        )

    if dsr <= 35:
        return (
            "🟢 Sangat selesa",
            "Komitmen masih rendah dan aliran tunai dijangka lebih fleksibel.",
        )

    if dsr <= 45:
        return (
            "🟡 Terkawal",
            "Masih berada pada tahap terkawal, tetapi dana kecemasan perlu dijaga.",
        )

    if dsr <= 60:
        return (
            "🟠 Agak ketat",
            "Komitmen agak tinggi dan mungkin mengehadkan perbelanjaan bulanan.",
        )

    return (
        "🔴 Risiko tinggi",
        "Jumlah komitmen berpotensi memberi tekanan besar kepada kewangan.",
    )


def effective_annual_rate(net_cash, payments):
    """
    Kadar efektif tahunan (nominal, kompaun bulanan) berdasarkan
    wang yang benar-benar diterima dan jadual bayaran sebenar.

    Ini membolehkan flat rate dan reducing balance dibandingkan
    secara adil. Menggunakan bisection pada kadar bulanan.
    """
    if net_cash <= 0 or not payments:
        return None

    if sum(payments) <= net_cash + 1e-9:
        return 0.0

    low, high = 0.0, 1.0

    for _ in range(80):
        mid = (low + high) / 2

        present_value = sum(
            payment / (1 + mid) ** (index + 1)
            for index, payment in enumerate(payments)
        )

        if present_value > net_cash:
            low = mid
        else:
            high = mid

    return (low + high) / 2 * 12 * 100


# =========================================================
# VALIDATION
# =========================================================

def validate_income(income, commitments):
    if income < 0:
        raise ValueError("Pendapatan tidak boleh bernilai negatif.")

    if commitments < 0:
        raise ValueError("Komitmen bulanan tidak boleh bernilai negatif.")

    if income > 0 and commitments > income * 3:
        raise ValueError(
            "Komitmen bulanan kelihatan terlalu tinggi berbanding pendapatan. "
            "Sila semak semula input."
        )


def validate_general_loan(amount, rate, years):
    if amount <= 0:
        raise ValueError("Jumlah pinjaman mesti melebihi RM0.")

    if rate < 0:
        raise ValueError("Interest rate tidak boleh bernilai negatif.")

    if rate > 30:
        raise ValueError(
            "Interest rate melebihi 30%. Sila semak semula input."
        )

    if years <= 0:
        raise ValueError("Tempoh pinjaman mesti melebihi 0 tahun.")


def validate_extra_payment(extra_payment, amount):
    if extra_payment < 0:
        raise ValueError("Extra payment tidak boleh bernilai negatif.")

    if extra_payment > amount:
        raise ValueError(
            "Extra payment bulanan tidak boleh melebihi jumlah pinjaman."
        )


def validate_processing_fee(fee_percentage):
    if fee_percentage < 0:
        raise ValueError("Processing fee tidak boleh bernilai negatif.")

    if fee_percentage > 20:
        raise ValueError(
            "Processing fee melebihi 20%. Sila semak semula input."
        )


# =========================================================
# CORE AMORTIZATION ENGINE
# =========================================================

def build_result(
    calculator,
    rate_type,
    principal,
    payments,
    interest_parts,
    principal_parts,
    balances,
    fees=0.0,
    **extra,
):
    """Bina dictionary keputusan yang seragam untuk semua jenis pinjaman."""
    total_interest = sum(interest_parts)
    net_cash = principal - fees

    result = {
        "calculator": calculator,
        "rate_type": rate_type,
        "principal": principal,
        "starting_payment": payments[0],
        "peak_payment": max(payments),
        "total_interest": total_interest,
        "total_payment": sum(payments),
        "fees": fees,
        "total_cost": total_interest + fees,
        "net_cash_received": net_cash,
        "months": len(payments),
        "balances": balances,
        "payments": payments,
        "interest_parts": interest_parts,
        "principal_parts": principal_parts,
        "effective_rate": effective_annual_rate(net_cash, payments),
        "is_flat": False,
        "warnings": [],
    }

    result.update(extra)

    return result


def amortize_reducing(amount, timeline, months, extra_payment=0.0):
    """
    Reducing balance dengan kadar yang boleh berubah.

    timeline: [(bulan_mula_indeks_0, kadar_tahunan), ...]
    Ansuran dikira semula setiap kali kadar berubah, berdasarkan
    baki semasa dan baki bulan.
    """
    lookup = dict(timeline)

    balance = amount
    balances = [amount]
    payments = []
    interest_parts = []
    principal_parts = []
    rates = []

    active_rate = timeline[0][1]
    scheduled_payment = 0.0

    for month_index in range(months):
        if balance <= 0.005:
            break

        if month_index == 0 or month_index in lookup:
            active_rate = lookup.get(month_index, active_rate)
            scheduled_payment = monthly_payment_reducing_balance(
                balance,
                active_rate,
                months - month_index,
            )

        interest = balance * active_rate / 100 / 12

        planned_payment = scheduled_payment + extra_payment
        actual_payment = min(planned_payment, balance + interest)

        principal_paid = min(actual_payment - interest, balance)

        balance -= principal_paid

        if balance < 0.005:
            balance = 0.0

        payments.append(interest + principal_paid)
        interest_parts.append(interest)
        principal_parts.append(principal_paid)
        rates.append(active_rate)
        balances.append(balance)

    return {
        "payments": payments,
        "interest_parts": interest_parts,
        "principal_parts": principal_parts,
        "balances": balances,
        "rates": rates,
    }


def amortize_flat(principal, rate, years):
    """Flat rate: faedah dikira atas prinsipal asal, bayaran sama rata."""
    months = int(years * 12)

    total_interest = principal * rate / 100 * years
    monthly_principal = principal / months
    monthly_interest = total_interest / months

    balance = principal
    balances = [principal]
    payments = []
    interest_parts = []
    principal_parts = []

    for _ in range(months):
        actual_principal = min(monthly_principal, balance)
        balance = max(balance - actual_principal, 0.0)

        payments.append(actual_principal + monthly_interest)
        interest_parts.append(monthly_interest)
        principal_parts.append(actual_principal)
        balances.append(balance)

    return {
        "payments": payments,
        "interest_parts": interest_parts,
        "principal_parts": principal_parts,
        "balances": balances,
        "rates": [rate] * months,
    }


# =========================================================
# HOUSING RATE SCENARIOS
# =========================================================

def build_rate_timeline(
    starting_rate,
    total_months,
    scenario,
    custom_change_1=0.0,
    custom_year_1=3,
    custom_change_2=0.0,
    custom_year_2=5,
):
    """
    Return [(start_month_index, annual_rate), ...] bermula bulan 0.

    Perubahan yang jatuh di luar tempoh pinjaman diabaikan.
    Jika dua perubahan jatuh pada bulan yang sama, yang terakhir menang.
    """
    changes = {}

    def add_change(month, rate):
        if 0 < month < total_months:
            changes[month] = max(rate, 0.0)

    if scenario == "Moderate Increase":
        add_change(3 * 12, starting_rate + 0.25)

    elif scenario == "High Rate Scenario":
        add_change(2 * 12, starting_rate + 0.50)
        add_change(5 * 12, starting_rate + 1.00)

    elif scenario == "Custom":
        first_rate = max(starting_rate + custom_change_1, 0.0)
        second_rate = max(first_rate + custom_change_2, 0.0)

        add_change(custom_year_1 * 12, first_rate)
        add_change(custom_year_2 * 12, second_rate)

    return [(0, starting_rate)] + sorted(changes.items())


# =========================================================
# HOUSING LOAN
# =========================================================

def housing_loan(
    amount,
    starting_rate,
    years,
    rate_type,
    rate_scenario="Stable",
    custom_change_1=0.0,
    custom_year_1=3,
    custom_change_2=0.0,
    custom_year_2=5,
    extra_payment=0.0,
    _with_baseline=True,
):
    validate_general_loan(amount, starting_rate, years)
    validate_extra_payment(extra_payment, amount)

    months = int(years * 12)
    warnings = []

    floating = rate_type == "Floating Rate"

    if floating and rate_scenario == "Custom":
        if custom_year_2 <= custom_year_1:
            raise ValueError(
                "Second change mesti berlaku selepas first change "
                "(tahun kedua mesti lebih besar)."
            )

        if custom_year_1 * 12 >= months:
            warnings.append(
                "Perubahan kadar pertama jatuh di luar tempoh pinjaman "
                "dan diabaikan."
            )

    if floating:
        timeline = build_rate_timeline(
            starting_rate,
            months,
            rate_scenario,
            custom_change_1,
            custom_year_1,
            custom_change_2,
            custom_year_2,
        )
    else:
        timeline = [(0, starting_rate)]

    schedule = amortize_reducing(
        amount,
        timeline,
        months,
        extra_payment,
    )

    if floating:
        steps = []

        for month, rate in timeline:
            if month == 0:
                steps.append(f"{rate:.2f}%")
            else:
                steps.append(f"{rate:.2f}% (thn {month // 12})")

        rate_description = "Floating: " + " → ".join(steps)
    else:
        rate_description = "Fixed Rate"

    result = build_result(
        "Housing Loan",
        rate_description,
        amount,
        schedule["payments"],
        schedule["interest_parts"],
        schedule["principal_parts"],
        schedule["balances"],
        rates=schedule["rates"],
        rate_timeline=timeline,
        extra_payment=extra_payment,
        quoted_rate=starting_rate,
    )

    result["warnings"].extend(warnings)

    if extra_payment > 0 and _with_baseline:
        baseline = housing_loan(
            amount,
            starting_rate,
            years,
            rate_type,
            rate_scenario,
            custom_change_1,
            custom_year_1,
            custom_change_2,
            custom_year_2,
            0.0,
            _with_baseline=False,
        )

        result["baseline_interest"] = baseline["total_interest"]
        result["baseline_months"] = baseline["months"]

    return result


# =========================================================
# CAR LOAN
# =========================================================

def car_flat_loan(price, down_payment, rate, years):
    if price <= 0:
        raise ValueError("Harga kereta mesti melebihi RM0.")

    if down_payment < 0:
        raise ValueError("Down payment tidak boleh bernilai negatif.")

    if down_payment >= price:
        raise ValueError(
            f"Down payment {rm(down_payment)} mesti lebih rendah "
            f"daripada harga kereta {rm(price)}."
        )

    principal = price - down_payment

    validate_general_loan(principal, rate, years)

    if years > 9:
        raise ValueError(
            "Tempoh car loan dalam calculator ini terhad kepada 9 tahun."
        )

    schedule = amortize_flat(principal, rate, years)
    financing_margin = principal / price * 100

    result = build_result(
        "Car Loan",
        f"Flat Rate · {financing_margin:.1f}% financed",
        principal,
        schedule["payments"],
        schedule["interest_parts"],
        schedule["principal_parts"],
        schedule["balances"],
        rates=schedule["rates"],
        is_flat=True,
        quoted_rate=rate,
        car_price=price,
        down_payment=down_payment,
        financing_margin=financing_margin,
    )

    if financing_margin > 90:
        result["warnings"].append(
            f"Financing margin {financing_margin:.1f}% melebihi 90%. "
            "Kebanyakan bank menghadkan margin pembiayaan kereta, "
            "jadi kelulusan tidak dijamin."
        )

    return result


# =========================================================
# PERSONAL LOAN
# =========================================================

def personal_loan(amount, rate, years, processing_fee_percentage, rate_type):
    """
    Processing fee dianggap dipotong terus daripada wang yang diterima
    (net cash received = pinjaman - fee), manakala ansuran dikira
    atas jumlah pinjaman penuh. Cara ini konsisten untuk flat dan
    reducing balance.
    """
    validate_general_loan(amount, rate, years)
    validate_processing_fee(processing_fee_percentage)

    if years > 10:
        raise ValueError(
            "Tempoh personal loan dalam calculator ini terhad kepada 10 tahun."
        )

    processing_fee = amount * processing_fee_percentage / 100

    if processing_fee >= amount:
        raise ValueError(
            "Processing fee tidak boleh sama atau melebihi jumlah pinjaman."
        )

    months = int(years * 12)

    if rate_type == "Flat Rate":
        schedule = amortize_flat(amount, rate, years)
        is_flat = True
    else:
        schedule = amortize_reducing(amount, [(0, rate)], months)
        is_flat = False

    return build_result(
        "Personal Loan",
        rate_type,
        amount,
        schedule["payments"],
        schedule["interest_parts"],
        schedule["principal_parts"],
        schedule["balances"],
        fees=processing_fee,
        rates=schedule["rates"],
        is_flat=is_flat,
        quoted_rate=rate,
    )


# =========================================================
# SMART RECOMMENDATION
# =========================================================

SCORE_COMPONENTS = ["Affordability", "Total Cost", "Debt-free Speed"]

DEFAULT_WEIGHTS = {
    "Affordability": 40,
    "Total Cost": 40,
    "Debt-free Speed": 20,
}

COMPONENT_REASON = {
    "Affordability": "ansuran dan DSR lebih selesa",
    "Total Cost": "kos pinjaman (faedah + fi) lebih rendah",
    "Debt-free Speed": "siap dibayar lebih cepat",
}


def ratio_score(value, best):
    """Lebih rendah = lebih baik. Skor mengikut nisbah, bukan jurang min-max."""
    if value <= 0:
        return 100.0

    return max(0.0, min(100.0, best / value * 100))


def dsr_to_score(dsr):
    """DSR <= 30% = 100 mata, DSR >= 80% = 0 mata (skala mutlak)."""
    return max(0.0, min(100.0, (80 - dsr) / 50 * 100))


def calculate_smart_scores(A, B, income, commitments, weights=None):
    weights = weights or DEFAULT_WEIGHTS

    total_weight = sum(max(weights.get(c, 0), 0) for c in SCORE_COMPONENTS)

    if total_weight <= 0:
        weights = DEFAULT_WEIGHTS
        total_weight = sum(weights.values())

    dsr_a = calculate_dsr(A["peak_payment"], income, commitments)
    dsr_b = calculate_dsr(B["peak_payment"], income, commitments)

    if dsr_a is not None and dsr_b is not None:
        affordability_a = dsr_to_score(dsr_a)
        affordability_b = dsr_to_score(dsr_b)
    else:
        best_payment = min(A["peak_payment"], B["peak_payment"])
        affordability_a = ratio_score(A["peak_payment"], best_payment)
        affordability_b = ratio_score(B["peak_payment"], best_payment)

    cost_ratio_a = A["total_cost"] / A["principal"]
    cost_ratio_b = B["total_cost"] / B["principal"]
    best_cost = min(cost_ratio_a, cost_ratio_b)

    best_months = min(A["months"], B["months"])

    breakdown_a = {
        "Affordability": affordability_a,
        "Total Cost": ratio_score(cost_ratio_a, best_cost),
        "Debt-free Speed": ratio_score(A["months"], best_months),
    }

    breakdown_b = {
        "Affordability": affordability_b,
        "Total Cost": ratio_score(cost_ratio_b, best_cost),
        "Debt-free Speed": ratio_score(B["months"], best_months),
    }

    score_a = sum(
        breakdown_a[c] * max(weights.get(c, 0), 0) / total_weight
        for c in SCORE_COMPONENTS
    )

    score_b = sum(
        breakdown_b[c] * max(weights.get(c, 0), 0) / total_weight
        for c in SCORE_COMPONENTS
    )

    if abs(score_a - score_b) < 3:
        recommended = "Kedua-dua pilihan hampir setara"
    elif score_a > score_b:
        recommended = "Loan A"
    else:
        recommended = "Loan B"

    reasons = []

    for component in SCORE_COMPONENTS:
        difference = breakdown_a[component] - breakdown_b[component]

        if abs(difference) < 1:
            continue

        winner = "Loan A" if difference > 0 else "Loan B"
        reasons.append(f"{winner}: {COMPONENT_REASON[component]}")

    return {
        "score_a": score_a,
        "score_b": score_b,
        "dsr_a": dsr_a,
        "dsr_b": dsr_b,
        "recommended": recommended,
        "breakdown_a": breakdown_a,
        "breakdown_b": breakdown_b,
        "reasons": reasons,
        "weights": weights,
        "total_weight": total_weight,
    }


# =========================================================
# HUMAN-LANGUAGE SUMMARY
# =========================================================

def generate_comparison_summary(A, B):
    sentences = []

    payment_difference = abs(A["peak_payment"] - B["peak_payment"])

    if payment_difference < 0.005:
        sentences.append(
            "Kedua-dua pinjaman mempunyai ansuran tertinggi yang sama."
        )
    else:
        lower = "A" if A["peak_payment"] < B["peak_payment"] else "B"
        sentences.append(
            f"Loan {lower} mempunyai ansuran tertinggi "
            f"{rm(payment_difference)} lebih rendah."
        )

    cost_difference = abs(A["total_cost"] - B["total_cost"])

    if cost_difference < 0.005:
        sentences.append(
            "Kos pinjaman (faedah + fi) kedua-duanya sama."
        )
    else:
        cheaper = "A" if A["total_cost"] < B["total_cost"] else "B"
        sentences.append(
            f"Dari segi kos pinjaman (faedah + fi), Loan {cheaper} "
            f"lebih murah sekitar {rm(cost_difference)}."
        )

    if A["months"] == B["months"]:
        sentences.append(
            "Kedua-dua pinjaman mempunyai tempoh pembayaran yang sama."
        )
    else:
        faster = "A" if A["months"] < B["months"] else "B"
        gap = abs(A["months"] - B["months"])
        sentences.append(
            f"Loan {faster} selesai {format_months(gap)} lebih awal."
        )

    if abs(A["principal"] - B["principal"]) > 0.5:
        sentences.append(
            "Nota: jumlah pinjaman berbeza, jadi baca kos mutlak "
            "bersama kadar efektif."
        )

    return " ".join(sentences)


def generate_quick_summary(result, income, commitments):
    dsr = calculate_dsr(result["peak_payment"], income, commitments)
    label, _ = affordability_label(dsr)

    start = result["starting_payment"]
    peak = result["peak_payment"]

    if peak - start > 0.005:
        payment_text = (
            f"Ansuran bermula {rm(start)} sebulan dan boleh mencecah "
            f"{rm(peak)} apabila kadar berubah."
        )
    else:
        payment_text = f"Anggaran ansuran ialah {rm(start)} sebulan."

    text = (
        f"{payment_text} Jumlah faedah dianggarkan "
        f"{rm(result['total_interest'])}, manakala jumlah keseluruhan "
        f"ansuran ialah {rm(result['total_payment'])}."
    )

    if result["fees"] > 0:
        text += (
            f" Fi pemprosesan {rm(result['fees'])} dipotong daripada "
            f"wang yang diterima ({rm(result['net_cash_received'])})."
        )

    if "baseline_interest" in result:
        saved = result["baseline_interest"] - result["total_interest"]
        months_saved = result["baseline_months"] - result["months"]

        if saved > 0.005:
            text += (
                f" Dengan extra payment, anda menjimatkan sekitar "
                f"{rm(saved)} faedah dan tamat {format_months(months_saved)} "
                f"lebih awal."
            )

    if dsr is None:
        text += " DSR tidak dikira kerana pendapatan tidak diisi."
    else:
        text += (
            f" Selepas mengambil kira komitmen sedia ada, DSR dianggarkan "
            f"{dsr:.1f}% ({label})."
        )

    return text


# =========================================================
# GRAPHS
# =========================================================

def _money_formatter():
    return FuncFormatter(lambda value, _: f"{value:,.0f}")


def _new_figure(width=11, height=4.5):
    figure, axis = plt.subplots(figsize=(width, height))
    figure.patch.set_facecolor(PLOT_BG)
    axis.set_facecolor(PLOT_BG)

    return figure, axis


def _finish_figure(figure, axis, title, xlabel, ylabel, money_axis=True):
    axis.set_title(title, color="white", fontsize=12, pad=12)
    axis.set_xlabel(xlabel, color=PLOT_TEXT)
    axis.set_ylabel(ylabel, color=PLOT_TEXT)
    axis.tick_params(colors=PLOT_TEXT)
    axis.grid(alpha=0.15, color=PLOT_GRID)

    for spine in axis.spines.values():
        spine.set_color("#2a3f5c")

    if money_axis:
        axis.yaxis.set_major_formatter(_money_formatter())

    legend = axis.get_legend()

    if legend:
        legend.get_frame().set_facecolor(PLOT_BG)
        legend.get_frame().set_edgecolor("#2a3f5c")

        for text in legend.get_texts():
            text.set_color(PLOT_TEXT)

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def plot_balance_graph(A, B=None, title="Remaining Principal"):
    figure, axis = _new_figure()

    axis.plot(
        range(len(A["balances"])),
        A["balances"],
        linewidth=2.4,
        color=COLOR_A,
        label="Loan A" if B else "Loan",
    )

    if B is not None:
        axis.plot(
            range(len(B["balances"])),
            B["balances"],
            linewidth=2.4,
            linestyle="--",
            color=COLOR_B,
            label="Loan B",
        )

    axis.set_ylim(bottom=0)
    axis.legend()

    _finish_figure(figure, axis, title, "Bulan", "Baki Prinsipal (RM)")


def plot_payment_graph(A, B=None, title="Monthly Payment Trend"):
    figure, axis = _new_figure()

    axis.plot(
        range(1, len(A["payments"]) + 1),
        A["payments"],
        linewidth=2.4,
        color=COLOR_A,
        label="Loan A" if B else "Loan",
    )

    if B is not None:
        axis.plot(
            range(1, len(B["payments"]) + 1),
            B["payments"],
            linewidth=2.4,
            linestyle="--",
            color=COLOR_B,
            label="Loan B",
        )

    axis.set_ylim(bottom=0)
    axis.legend()

    _finish_figure(figure, axis, title, "Bulan", "Bayaran Bulanan (RM)")


def plot_breakdown_graph(result, title="Principal vs Interest"):
    figure, axis = _new_figure()

    months = range(1, len(result["payments"]) + 1)

    axis.stackplot(
        months,
        result["principal_parts"],
        result["interest_parts"],
        labels=["Prinsipal", "Faedah"],
        colors=[COLOR_A, COLOR_INTEREST],
        alpha=0.85,
    )

    axis.legend(loc="upper right")

    _finish_figure(figure, axis, title, "Bulan", "Bayaran Bulanan (RM)")


def plot_cost_comparison(A, B=None, title="Cost Structure"):
    labels = ["Principal", "Interest", "Fees"]

    values_a = [A["principal"], A["total_interest"], A["fees"]]

    figure, axis = _new_figure(10, 4.5)

    if B is None:
        axis.bar(labels, values_a, color=[COLOR_A, COLOR_INTEREST, COLOR_B])
    else:
        values_b = [B["principal"], B["total_interest"], B["fees"]]

        positions = range(len(labels))
        width = 0.35

        axis.bar(
            [position - width / 2 for position in positions],
            values_a,
            width=width,
            color=COLOR_A,
            label="Loan A",
        )

        axis.bar(
            [position + width / 2 for position in positions],
            values_b,
            width=width,
            color=COLOR_B,
            label="Loan B",
        )

        axis.set_xticks(list(positions))
        axis.set_xticklabels(labels)
        axis.legend()

    _finish_figure(figure, axis, title, "", "RM")


# =========================================================
# AMORTIZATION SCHEDULE
# =========================================================

def schedule_dataframe(result):
    count = len(result["payments"])

    data = {
        "Bulan": list(range(1, count + 1)),
        "Kadar (%)": [round(rate, 2) for rate in result["rates"]],
        "Bayaran (RM)": [round(v, 2) for v in result["payments"]],
        "Prinsipal (RM)": [round(v, 2) for v in result["principal_parts"]],
        "Faedah (RM)": [round(v, 2) for v in result["interest_parts"]],
        "Baki (RM)": [round(v, 2) for v in result["balances"][1:]],
    }

    return pd.DataFrame(data)


def show_schedule(A, B, calculator_type):
    with st.expander("📋 Jadual Bayaran Bulanan"):
        if B is None:
            frames = [("Loan", A)]
            containers = [st.container()]
        else:
            tab_a, tab_b = st.tabs(["Loan A", "Loan B"])
            frames = [("Loan A", A), ("Loan B", B)]
            containers = [tab_a, tab_b]

        for container, (label, result) in zip(containers, frames):
            with container:
                dataframe = schedule_dataframe(result)

                st.dataframe(dataframe, hide_index=True, **STRETCH)

                st.download_button(
                    f"⬇️ Download CSV ({label})",
                    dataframe.to_csv(index=False).encode("utf-8"),
                    file_name=(
                        f"{calculator_type.lower().replace(' ', '_')}"
                        f"_{label.lower().replace(' ', '_')}_schedule.csv"
                    ),
                    mime="text/csv",
                    key=f"download_{calculator_type}_{label}",
                )


# =========================================================
# SAVED SCENARIOS
# =========================================================

def summarize_for_save(result):
    return {
        "rate_type": result["rate_type"],
        "principal": result["principal"],
        "starting": result["starting_payment"],
        "monthly": result["peak_payment"],
        "interest": result["total_interest"],
        "fees": result["fees"],
        "total": result["total_payment"],
        "months": result["months"],
        "effective_rate": result["effective_rate"],
    }


def save_scenario(scenario_name, calculator_type, mode, A, B=None):
    if not scenario_name.strip():
        raise ValueError("Masukkan nama scenario sebelum menyimpan.")

    st.session_state.saved_scenarios.append(
        {
            "id": uuid.uuid4().hex,
            "name": scenario_name.strip(),
            "calculator": calculator_type,
            "mode": mode,
            "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "A": summarize_for_save(A),
            "B": summarize_for_save(B) if B is not None else None,
        }
    )


def _save_callback(name_key, calculator_type, mode, A, B):
    try:
        save_scenario(
            st.session_state.get(name_key, ""),
            calculator_type,
            mode,
            A,
            B,
        )
        st.session_state[name_key] = ""
        st.toast("Scenario berjaya disimpan.", icon="✅")

    except ValueError as error:
        st.toast(str(error), icon="⚠️")


def _delete_callback(scenario_id):
    st.session_state.saved_scenarios = [
        scenario
        for scenario in st.session_state.saved_scenarios
        if scenario.get("id") != scenario_id
    ]


def show_save_section(calculator_type, mode, A, B=None):
    st.markdown("### 💾 Simpan Scenario")

    name_key = f"scenario_name_{calculator_type}_{mode}"

    name_column, button_column = st.columns([4, 1])

    with name_column:
        st.text_input(
            "Nama scenario",
            placeholder="Contoh: Rumah Maybank 30 Tahun",
            key=name_key,
        )

    with button_column:
        st.write("")

        st.button(
            "Save",
            key=f"save_{calculator_type}_{mode}",
            on_click=_save_callback,
            args=(name_key, calculator_type, mode, A, B),
            **STRETCH,
        )


def import_scenarios(raw_bytes):
    data = json.loads(raw_bytes.decode("utf-8"))

    if isinstance(data, dict):
        data = data.get("scenarios", [])

    if not isinstance(data, list):
        raise ValueError("Format fail tidak sah.")

    existing = {
        (s.get("name"), s.get("saved_at"), s.get("calculator"))
        for s in st.session_state.saved_scenarios
    }

    added = 0

    for record in data:
        if not isinstance(record, dict) or "name" not in record or "A" not in record:
            continue

        key = (
            record.get("name"),
            record.get("saved_at"),
            record.get("calculator"),
        )

        if key in existing:
            continue

        record.setdefault("id", uuid.uuid4().hex)
        record.setdefault("calculator", "Loan")
        record.setdefault("mode", "-")
        record.setdefault("saved_at", "-")
        record.setdefault("B", None)

        st.session_state.saved_scenarios.append(record)
        existing.add(key)
        added += 1

    return added


def _scenario_monthly(entry):
    if not entry:
        return "-"

    return rm(entry.get("monthly", 0.0))


def show_saved_scenarios():
    st.markdown("## 💾 Saved Scenarios")

    scenarios = st.session_state.saved_scenarios

    if not scenarios:
        st.info("Belum ada scenario yang disimpan.")
    else:
        overview = pd.DataFrame(
            [
                {
                    "Nama": s["name"],
                    "Calculator": s["calculator"],
                    "Mode": s["mode"],
                    "Loan A": _scenario_monthly(s["A"]),
                    "Loan B": _scenario_monthly(s["B"]),
                    "Disimpan": s["saved_at"],
                }
                for s in scenarios
            ]
        )

        st.dataframe(overview, hide_index=True, **STRETCH)

        for scenario in scenarios:
            with st.expander(
                f"{scenario['name']} · {scenario['calculator']} "
                f"· {scenario['saved_at']}"
            ):
                st.write(f"**Mode:** {scenario['mode']}")

                for label, entry in (
                    ("Loan A", scenario["A"]),
                    ("Loan B", scenario["B"]),
                ):
                    if entry is None:
                        continue

                    st.write(f"**{label}:** {entry['rate_type']}")
                    st.write(
                        f"Monthly (tertinggi): **{rm(entry['monthly'])}** · "
                        f"Total interest: **{rm(entry.get('interest', 0.0))}** · "
                        f"Total payment: **{rm(entry['total'])}**"
                    )

                    if entry.get("effective_rate") is not None:
                        st.caption(
                            f"Effective rate: {entry['effective_rate']:.2f}% p.a."
                        )

                st.button(
                    "Delete Scenario",
                    key=f"delete_{scenario.get('id', scenario['name'])}",
                    on_click=_delete_callback,
                    args=(scenario.get("id"),),
                )

    with st.expander("🔁 Backup & Restore"):
        st.caption(
            "Scenario hanya disimpan sepanjang sesi browser. "
            "Download fail JSON untuk simpan kekal, dan import semula bila perlu."
        )

        st.download_button(
            "⬇️ Download Scenarios (JSON)",
            json.dumps(scenarios, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="saved_scenarios.json",
            mime="application/json",
            disabled=not scenarios,
        )

        uploaded = st.file_uploader(
            "Import Scenarios (JSON)",
            type="json",
            key="import_scenarios_file",
        )

        if uploaded is not None and st.button("Import", key="import_scenarios_btn"):
            try:
                added = import_scenarios(uploaded.getvalue())
                st.success(f"{added} scenario diimport.")
            except (ValueError, json.JSONDecodeError):
                st.error("Fail JSON tidak sah atau format tidak dikenali.")


# =========================================================
# RESULT DISPLAY
# =========================================================

def payment_metric(column, label, result):
    start = result["starting_payment"]
    peak = result["peak_payment"]

    if peak - start > 0.005:
        column.metric(
            label,
            rm(start),
            f"puncak {rm(peak)}",
            delta_color="off",
        )
    else:
        column.metric(label, rm(start))


def flat_rate_note(result):
    if result["is_flat"] and result["effective_rate"] is not None:
        st.caption(
            f"💡 Kadar flat {result['quoted_rate']:.2f}% bersamaan kira-kira "
            f"{result['effective_rate']:.2f}% p.a. kadar efektif "
            "(reducing balance). Guna kadar efektif untuk bandingkan dengan "
            "pinjaman lain."
        )


def display_quick_result(result, income, commitments, calculator_type):
    dsr = calculate_dsr(result["peak_payment"], income, commitments)
    label, message = affordability_label(dsr)

    st.markdown("## 📌 Result")

    column_1, column_2, column_3, column_4 = st.columns(4)

    payment_metric(column_1, "Monthly Payment", result)
    column_2.metric("Total Interest", rm(result["total_interest"]))
    column_3.metric("Total Payment", rm(result["total_payment"]))
    column_4.metric("DSR", fmt_dsr(dsr))

    extras = [
        ("Effective Rate p.a.", pct(result["effective_rate"])),
        ("Cost of Credit", rm(result["total_cost"])),
    ]

    if result["fees"] > 0:
        extras.append(("Processing Fee", rm(result["fees"])))
        extras.append(("Net Cash Received", rm(result["net_cash_received"])))

    if "baseline_interest" in result:
        saved = result["baseline_interest"] - result["total_interest"]
        months_saved = result["baseline_months"] - result["months"]

        extras.append(("Faedah Dijimat", rm(max(saved, 0.0))))
        extras.append(("Tamat Lebih Awal", f"{max(months_saved, 0)} bulan"))

    for column, (name, value) in zip(st.columns(len(extras)), extras):
        column.metric(name, value)

    flat_rate_note(result)

    st.markdown(
        f"""
        <div class="summary-card">
            <b>Ringkasan:</b><br><br>
            {generate_quick_summary(result, income, commitments)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(f"### {label}")
    st.caption(message)

    balance_tab, payment_tab, breakdown_tab, cost_tab = st.tabs(
        [
            "📉 Remaining Balance",
            "💵 Monthly Payment",
            "🥧 Principal vs Interest",
            "📊 Cost Structure",
        ]
    )

    with balance_tab:
        plot_balance_graph(
            result,
            title=f"{calculator_type} Remaining Principal",
        )

    with payment_tab:
        plot_payment_graph(
            result,
            title=f"{calculator_type} Monthly Payment",
        )

    with breakdown_tab:
        plot_breakdown_graph(
            result,
            title=f"{calculator_type}: Principal vs Interest setiap bulan",
        )

    with cost_tab:
        plot_cost_comparison(
            result,
            title=f"{calculator_type} Cost Structure",
        )

    show_schedule(result, None, calculator_type)

    show_save_section(calculator_type, MODE_QUICK, result)


def display_compare_result(A, B, income, commitments, calculator_type):
    weights = {
        component: st.session_state.get(
            f"weight_{calculator_type}_{component}",
            DEFAULT_WEIGHTS[component],
        )
        for component in SCORE_COMPONENTS
    }

    recommendation = calculate_smart_scores(
        A,
        B,
        income,
        commitments,
        weights,
    )

    st.markdown("## 📌 Comparison Result")

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    payment_metric(metric_1, "Loan A Monthly", A)
    payment_metric(metric_2, "Loan B Monthly", B)
    metric_3.metric("Loan A Score", f"{recommendation['score_a']:.0f}/100")
    metric_4.metric("Loan B Score", f"{recommendation['score_b']:.0f}/100")

    st.markdown(
        f"""
        <div class="summary-card">
            <b>Ringkasan:</b><br><br>
            {generate_comparison_summary(A, B)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    comparison_table = pd.DataFrame(
        {
            "Item": [
                "Rate Type",
                "Loan Amount",
                "Net Cash Received",
                "Starting Payment",
                "Peak Payment",
                "Total Interest",
                "Fees",
                "Cost of Credit",
                "Total Payment",
                "Effective Rate p.a.",
                "Loan Period",
                "DSR (peak)",
                "Smart Score",
            ],
            "Loan A": [
                A["rate_type"],
                rm(A["principal"]),
                rm(A["net_cash_received"]),
                rm(A["starting_payment"]),
                rm(A["peak_payment"]),
                rm(A["total_interest"]),
                rm(A["fees"]),
                rm(A["total_cost"]),
                rm(A["total_payment"]),
                pct(A["effective_rate"]),
                format_months(A["months"]),
                fmt_dsr(recommendation["dsr_a"]),
                f"{recommendation['score_a']:.0f}/100",
            ],
            "Loan B": [
                B["rate_type"],
                rm(B["principal"]),
                rm(B["net_cash_received"]),
                rm(B["starting_payment"]),
                rm(B["peak_payment"]),
                rm(B["total_interest"]),
                rm(B["fees"]),
                rm(B["total_cost"]),
                rm(B["total_payment"]),
                pct(B["effective_rate"]),
                format_months(B["months"]),
                fmt_dsr(recommendation["dsr_b"]),
                f"{recommendation['score_b']:.0f}/100",
            ],
        }
    )

    comparison_tab, graph_tab, smart_tab = st.tabs(
        [
            "📊 Comparison",
            "📈 Graphs",
            "🧠 Smart Recommendation",
        ]
    )

    with comparison_tab:
        st.dataframe(comparison_table, hide_index=True, **STRETCH)

        for label, result in (("Loan A", A), ("Loan B", B)):
            if result["is_flat"]:
                st.caption(
                    f"💡 {label}: kadar flat {result['quoted_rate']:.2f}% "
                    f"≈ {pct(result['effective_rate'])} p.a. kadar efektif."
                )

    with graph_tab:
        balance_tab, payment_tab, cost_tab = st.tabs(
            [
                "Remaining Principal",
                "Monthly Payment Trend",
                "Cost Structure",
            ]
        )

        with balance_tab:
            plot_balance_graph(
                A,
                B,
                title=f"{calculator_type} Remaining Principal",
            )

        with payment_tab:
            plot_payment_graph(
                A,
                B,
                title=f"{calculator_type} Monthly Payment",
            )

        with cost_tab:
            plot_cost_comparison(
                A,
                B,
                title=f"{calculator_type} Cost Comparison",
            )

    with smart_tab:
        with st.expander("⚙️ Laraskan wajaran skor"):
            st.caption(
                "Ubah mengikut keutamaan anda. Wajaran dinormalkan "
                "secara automatik (jumlah tak perlu 100)."
            )

            for component in SCORE_COMPONENTS:
                st.slider(
                    component,
                    min_value=0,
                    max_value=100,
                    value=DEFAULT_WEIGHTS[component],
                    step=5,
                    key=f"weight_{calculator_type}_{component}",
                )

        score_a_column, score_b_column = st.columns(2)

        for column, label, score, breakdown in (
            (score_a_column, "Loan A", recommendation["score_a"], recommendation["breakdown_a"]),
            (score_b_column, "Loan B", recommendation["score_b"], recommendation["breakdown_b"]),
        ):
            with column:
                st.metric(f"{label} Smart Score", f"{score:.0f}/100")

                st.dataframe(
                    pd.DataFrame(
                        {
                            "Component": list(breakdown.keys()),
                            "Score": [f"{v:.0f}/100" for v in breakdown.values()],
                        }
                    ),
                    hide_index=True,
                    **STRETCH,
                )

        reasons_html = "<br>".join(
            f"• {reason}" for reason in recommendation["reasons"]
        ) or "• Tiada perbezaan ketara antara kedua-dua pilihan."

        weight_total = recommendation["total_weight"]
        weight_html = "<br>".join(
            f"• {recommendation['weights'][c] / weight_total * 100:.0f}% "
            f"{c.lower()}"
            for c in SCORE_COMPONENTS
        )

        st.markdown(
            f"""
            <div class="smart-card">
                <h3>🏆 Suggested Option: {recommendation['recommended']}</h3>

                <p><b>Kenapa:</b><br>{reasons_html}</p>

                <p><b>Wajaran semasa:</b><br>{weight_html}</p>

                <p class="small-note">
                    Affordability dinilai pada skala mutlak DSR
                    (30% atau kurang = 100 mata, 80% atau lebih = 0 mata)
                    menggunakan ansuran tertinggi. Kos dan tempoh dinilai
                    mengikut nisbah kepada pilihan terbaik. Ini analisis
                    rule-based, bukan keputusan kelulusan bank atau model AI.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    show_schedule(A, B, calculator_type)

    show_save_section(calculator_type, MODE_COMPARE, A, B)


def render_outcome(calculator_type, mode, A, B, income, commitments):
    for label, result in (("Loan A", A), ("Loan B", B)):
        if result is None:
            continue

        for warning in result["warnings"]:
            st.warning(f"{label}: {warning}" if B is not None else warning)

    if mode == MODE_QUICK:
        display_quick_result(A, income, commitments, calculator_type)
    else:
        display_compare_result(A, B, income, commitments, calculator_type)


# =========================================================
# SHARED INPUT WIDGETS
# =========================================================

def calculator_header(icon, title, description):
    left, right = st.columns([5, 1])

    with left:
        st.markdown(
            f"""
            <div class="page-title">
                <h1>{icon} {title}</h1>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.write("")

        if st.button("← Home", key=f"home_{title}", **STRETCH):
            go_home()
            st.rerun()


def mode_selector(key):
    return st.radio(
        "Calculation Mode",
        [MODE_QUICK, MODE_COMPARE],
        horizontal=True,
        key=key,
    )


def financial_inputs(prefix, income_default, commitments_default):
    st.markdown("### Financial Profile")

    left, right = st.columns(2)

    income = left.number_input(
        "Monthly Income (RM)",
        min_value=0.0,
        value=income_default,
        step=100.0,
        key=f"{prefix}_income",
        help=(
            "Bank biasanya guna pendapatan kasar untuk DSR. "
            "Biar 0 jika tidak mahu kira DSR."
        ),
    )

    commitments = right.number_input(
        "Other Monthly Commitments (RM)",
        min_value=0.0,
        value=commitments_default,
        step=50.0,
        key=f"{prefix}_commitments",
    )

    return income, commitments


# =========================================================
# LANDING PAGE
# =========================================================

def show_home():
    st.markdown(
        """
        <div class="hero">
            <h1>Hi, welcome to Calculator App 👋</h1>
            <p>
                Pilih calculator yang anda perlukan.
                Gunakan Quick Calculation untuk kiraan ringkas
                atau Compare Mode untuk membandingkan dua pilihan.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = [
        (
            "housing",
            "🏠",
            "Housing Loan",
            "Fixed dan floating rate, multiple rate scenarios, "
            "extra payment serta jimat faedah.",
            "Open Housing Calculator",
            "primary",
        ),
        (
            "car",
            "🚗",
            "Car Loan",
            "Flat-rate financing, down payment, financing margin "
            "dan kadar efektif.",
            "Open Car Calculator",
            "secondary",
        ),
        (
            "personal",
            "💳",
            "Personal Loan",
            "Flat atau reducing balance, processing fee, "
            "net cash received dan kadar efektif.",
            "Open Personal Calculator",
            "secondary",
        ),
    ]

    for column, (page, icon, title, description, button_label, button_type) in zip(
        st.columns(3),
        cards,
    ):
        with column:
            st.markdown(
                f"""
                <div class="calculator-card">
                    <div style="font-size:2.5rem;">{icon}</div>
                    <h2>{title}</h2>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                button_label,
                key=f"open_{page}",
                type=button_type,
                **STRETCH,
            ):
                open_page(page)
                st.rerun()

    st.divider()
    show_saved_scenarios()

    st.caption(
        "Semua pengiraan ialah anggaran untuk tujuan pendidikan "
        "dan perbandingan. Terma sebenar bergantung pada bank."
    )


# =========================================================
# HOUSING PAGE
# =========================================================

SCENARIO_DESCRIPTIONS = {
    "Stable": "Kadar kekal sepanjang tempoh pinjaman.",
    "Moderate Increase": "Kadar naik 0.25% pada tahun ke-3.",
    "High Rate Scenario": "Kadar naik 0.50% pada tahun ke-2 dan 1.00% (kumulatif) pada tahun ke-5.",
    "Custom": "Tetapkan sendiri dua perubahan kadar. Perubahan kedua dikira atas kadar selepas perubahan pertama.",
}


def housing_inputs(prefix, suffix, rate_type_index):
    amount = st.number_input(
        f"Loan Amount{suffix} (RM)",
        min_value=0.0,
        value=400000.0,
        step=5000.0,
        key=f"{prefix}_amount",
    )

    rate_type = st.selectbox(
        f"Rate Type{suffix}",
        ["Fixed Rate", "Floating Rate"],
        index=rate_type_index,
        key=f"{prefix}_rate_type",
    )

    rate = st.number_input(
        f"Starting Interest Rate{suffix} (%)",
        min_value=0.0,
        value=4.00,
        step=0.05,
        format="%.2f",
        key=f"{prefix}_rate",
    )

    years = st.number_input(
        f"Tenure{suffix} (Years)",
        min_value=1,
        max_value=35,
        value=30,
        step=1,
        key=f"{prefix}_years",
    )

    extra = st.number_input(
        f"Extra Monthly Payment{suffix} (RM)",
        min_value=0.0,
        value=0.0,
        step=50.0,
        key=f"{prefix}_extra",
    )

    return {
        "amount": amount,
        "rate_type": rate_type,
        "rate": rate,
        "years": int(years),
        "extra": extra,
    }


def show_housing_calculator():
    calculator_header(
        "🏠",
        "Housing Loan Calculator",
        "Fixed dan floating housing financing dengan multiple rate scenarios.",
    )

    mode = mode_selector("housing_mode")
    income, commitments = financial_inputs("housing", 7000.0, 800.0)

    st.divider()

    if mode == MODE_COMPARE:
        column_a, column_b = st.columns(2)

        with column_a:
            st.markdown("### Loan A")
            loan_a = housing_inputs("housing_a", " A", 0)

        with column_b:
            st.markdown("### Loan B")
            loan_b = housing_inputs("housing_b", " B", 1)
    else:
        st.markdown("### Loan Details")
        loan_a = housing_inputs("housing_a", "", 0)
        loan_b = None

    loans = [loan for loan in (loan_a, loan_b) if loan is not None]

    scenario = "Stable"
    custom_change_1, custom_year_1 = 0.25, 3
    custom_change_2, custom_year_2 = 0.25, 5

    if any(loan["rate_type"] == "Floating Rate" for loan in loans):
        st.divider()
        st.markdown("### Floating Rate Scenario")
        st.caption(
            "Scenario ini digunakan untuk semua pinjaman berjenis "
            "Floating Rate supaya perbandingan adil."
        )

        scenario = st.selectbox(
            "Floating Rate Scenario",
            list(SCENARIO_DESCRIPTIONS.keys()),
            key="housing_scenario",
        )

        st.caption(SCENARIO_DESCRIPTIONS[scenario])

        if scenario == "Custom":
            custom_1, custom_2 = st.columns(2)

            with custom_1:
                custom_year_1 = st.number_input(
                    "First Change After Year",
                    min_value=1,
                    max_value=34,
                    value=3,
                    step=1,
                    key="housing_custom_year_1",
                )

                custom_change_1 = st.number_input(
                    "First Rate Change (%)",
                    min_value=-5.0,
                    max_value=10.0,
                    value=0.25,
                    step=0.05,
                    format="%.2f",
                    key="housing_custom_change_1",
                )

            with custom_2:
                custom_year_2 = st.number_input(
                    "Second Change After Year",
                    min_value=1,
                    max_value=34,
                    value=5,
                    step=1,
                    key="housing_custom_year_2",
                )

                custom_change_2 = st.number_input(
                    "Second Rate Change (%)",
                    min_value=-5.0,
                    max_value=10.0,
                    value=0.25,
                    step=0.05,
                    format="%.2f",
                    key="housing_custom_change_2",
                )

    st.divider()

    def build(loan):
        return housing_loan(
            loan["amount"],
            loan["rate"],
            loan["years"],
            loan["rate_type"],
            scenario,
            custom_change_1,
            int(custom_year_1),
            custom_change_2,
            int(custom_year_2),
            loan["extra"],
        )

    try:
        validate_income(income, commitments)

        A = build(loan_a)
        B = build(loan_b) if loan_b is not None else None

    except ValueError as error:
        st.error(str(error))
        return

    render_outcome("Housing Loan", mode, A, B, income, commitments)


# =========================================================
# CAR PAGE
# =========================================================

def car_inputs(prefix, suffix, defaults):
    price = st.number_input(
        f"Car Price{suffix} (RM)",
        min_value=0.0,
        value=defaults["price"],
        step=1000.0,
        key=f"{prefix}_price",
    )

    down_payment = st.number_input(
        f"Down Payment{suffix} (RM)",
        min_value=0.0,
        value=defaults["down"],
        step=500.0,
        key=f"{prefix}_down",
    )

    rate = st.number_input(
        f"Flat Rate{suffix} (%)",
        min_value=0.0,
        value=defaults["rate"],
        step=0.05,
        format="%.2f",
        key=f"{prefix}_rate",
    )

    years = st.number_input(
        f"Tenure{suffix} (Years)",
        min_value=1,
        max_value=9,
        value=defaults["years"],
        step=1,
        key=f"{prefix}_years",
    )

    if price > 0 and down_payment < price:
        margin = (price - down_payment) / price * 100
        st.caption(
            f"Pinjaman {rm(price - down_payment)} · "
            f"financing margin {margin:.1f}%"
        )

    return {
        "price": price,
        "down": down_payment,
        "rate": rate,
        "years": int(years),
    }


def show_car_calculator():
    calculator_header(
        "🚗",
        "Car Loan Calculator",
        "Flat-rate car financing dengan down payment dan financing margin.",
    )

    mode = mode_selector("car_mode")

    st.info(
        "Car loan menggunakan flat-rate estimate. "
        "Graf baki ialah anggaran garis lurus, bukan "
        "early-settlement quotation rasmi."
    )

    income, commitments = financial_inputs("car", 5000.0, 500.0)

    st.divider()

    default_a = {"price": 90000.0, "down": 9000.0, "rate": 3.00, "years": 9}
    default_b = {"price": 90000.0, "down": 18000.0, "rate": 2.80, "years": 7}

    if mode == MODE_COMPARE:
        column_a, column_b = st.columns(2)

        with column_a:
            st.markdown("### Loan A")
            loan_a = car_inputs("car_a", " A", default_a)

        with column_b:
            st.markdown("### Loan B")
            loan_b = car_inputs("car_b", " B", default_b)
    else:
        loan_a = car_inputs("car_a", "", default_a)
        loan_b = None

    st.divider()

    try:
        validate_income(income, commitments)

        A = car_flat_loan(
            loan_a["price"],
            loan_a["down"],
            loan_a["rate"],
            loan_a["years"],
        )

        B = None

        if loan_b is not None:
            B = car_flat_loan(
                loan_b["price"],
                loan_b["down"],
                loan_b["rate"],
                loan_b["years"],
            )

    except ValueError as error:
        st.error(str(error))
        return

    render_outcome("Car Loan", mode, A, B, income, commitments)


# =========================================================
# PERSONAL LOAN PAGE
# =========================================================

def personal_inputs(prefix, suffix, defaults):
    amount = st.number_input(
        f"Loan Amount{suffix} (RM)",
        min_value=0.0,
        value=30000.0,
        step=1000.0,
        key=f"{prefix}_amount",
    )

    rate_type = st.selectbox(
        f"Rate Type{suffix}",
        ["Flat Rate", "Reducing Balance"],
        index=defaults["rate_type_index"],
        key=f"{prefix}_rate_type",
    )

    rate = st.number_input(
        f"Interest Rate{suffix} (%)",
        min_value=0.0,
        value=defaults["rate"],
        step=0.10,
        format="%.2f",
        key=f"{prefix}_rate",
    )

    years = st.number_input(
        f"Tenure{suffix} (Years)",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        key=f"{prefix}_years",
    )

    fee = st.number_input(
        f"Processing Fee{suffix} (%)",
        min_value=0.0,
        value=1.00,
        step=0.10,
        format="%.2f",
        key=f"{prefix}_fee",
    )

    return {
        "amount": amount,
        "rate_type": rate_type,
        "rate": rate,
        "years": int(years),
        "fee": fee,
    }


def show_personal_calculator():
    calculator_header(
        "💳",
        "Personal Loan Calculator",
        "Flat atau reducing-balance personal financing dengan processing fee.",
    )

    mode = mode_selector("personal_mode")

    st.info(
        "Processing fee dianggap dipotong daripada wang yang diterima "
        "(net cash received), manakala ansuran dikira atas jumlah "
        "pinjaman penuh."
    )

    income, commitments = financial_inputs("personal", 5000.0, 500.0)

    st.divider()

    if mode == MODE_COMPARE:
        column_a, column_b = st.columns(2)

        with column_a:
            st.markdown("### Loan A")
            loan_a = personal_inputs(
                "personal_a", " A", {"rate_type_index": 0, "rate": 6.00}
            )

        with column_b:
            st.markdown("### Loan B")
            loan_b = personal_inputs(
                "personal_b", " B", {"rate_type_index": 1, "rate": 8.00}
            )
    else:
        loan_a = personal_inputs(
            "personal_a", "", {"rate_type_index": 0, "rate": 6.00}
        )
        loan_b = None

    st.divider()

    def build(loan):
        return personal_loan(
            loan["amount"],
            loan["rate"],
            loan["years"],
            loan["fee"],
            loan["rate_type"],
        )

    try:
        validate_income(income, commitments)

        A = build(loan_a)
        B = build(loan_b) if loan_b is not None else None

    except ValueError as error:
        st.error(str(error))
        return

    render_outcome("Personal Loan", mode, A, B, income, commitments)


# =========================================================
# ROUTER
# =========================================================

if st.session_state.page == "home":
    show_home()

elif st.session_state.page == "housing":
    show_housing_calculator()

elif st.session_state.page == "car":
    show_car_calculator()

elif st.session_state.page == "personal":
    show_personal_calculator()
