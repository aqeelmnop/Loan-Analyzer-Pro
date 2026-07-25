import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Calculator App",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
        .stFormSubmitButton > button {
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
        }

        .saved-card {
            padding: 18px;
            border-radius: 15px;
            background: rgba(15, 29, 46, 0.88);
            border: 1px solid rgba(123, 160, 207, 0.18);
            margin-bottom: 10px;
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

if "result" not in st.session_state:
    st.session_state.result = None

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = []

# =========================================================
# NAVIGATION
# =========================================================

def open_page(page_name):
    st.session_state.page = page_name
    st.session_state.result = None


def go_home():
    st.session_state.page = "home"
    st.session_state.result = None


# =========================================================
# BASIC HELPERS
# =========================================================

def rm(value):
    return f"RM {value:,.2f}"


def percentage(value):
    return f"{value:.2f}%"


def monthly_payment_reducing_balance(principal, annual_rate, months):
    if principal <= 0 or months <= 0:
        return 0.0

    monthly_rate = annual_rate / 100 / 12

    if monthly_rate == 0:
        return principal / months

    factor = (1 + monthly_rate) ** months

    return principal * monthly_rate * factor / (factor - 1)


def calculate_dsr(monthly_payment, income, commitments):
    if income <= 0:
        return 0.0

    return ((monthly_payment + commitments) / income) * 100


def affordability_label(dsr):
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


def safe_min_max_score(value, minimum, maximum, lower_is_better=True):
    """
    Menghasilkan score 0 hingga 100.

    Untuk komponen seperti bayaran dan kos:
    nilai lebih rendah = score lebih tinggi.
    """
    if maximum == minimum:
        return 100.0

    normalized = (value - minimum) / (maximum - minimum)

    if lower_is_better:
        normalized = 1 - normalized

    return max(0.0, min(100.0, normalized * 100))


# =========================================================
# SMART RECOMMENDATION
# =========================================================

def calculate_smart_scores(A, B, income, commitments):
    dsr_a = calculate_dsr(
        A["comparison_payment"],
        income,
        commitments,
    )

    dsr_b = calculate_dsr(
        B["comparison_payment"],
        income,
        commitments,
    )

    monthly_values = [
        A["comparison_payment"],
        B["comparison_payment"],
    ]

    total_values = [
        A["total_payment"],
        B["total_payment"],
    ]

    dsr_values = [dsr_a, dsr_b]
    tenure_values = [A["months"], B["months"]]

    monthly_score_a = safe_min_max_score(
        A["comparison_payment"],
        min(monthly_values),
        max(monthly_values),
    )

    monthly_score_b = safe_min_max_score(
        B["comparison_payment"],
        min(monthly_values),
        max(monthly_values),
    )

    total_score_a = safe_min_max_score(
        A["total_payment"],
        min(total_values),
        max(total_values),
    )

    total_score_b = safe_min_max_score(
        B["total_payment"],
        min(total_values),
        max(total_values),
    )

    dsr_score_a = safe_min_max_score(
        dsr_a,
        min(dsr_values),
        max(dsr_values),
    )

    dsr_score_b = safe_min_max_score(
        dsr_b,
        min(dsr_values),
        max(dsr_values),
    )

    tenure_score_a = safe_min_max_score(
        A["months"],
        min(tenure_values),
        max(tenure_values),
    )

    tenure_score_b = safe_min_max_score(
        B["months"],
        min(tenure_values),
        max(tenure_values),
    )

    final_score_a = (
        monthly_score_a * 0.40
        + dsr_score_a * 0.30
        + total_score_a * 0.20
        + tenure_score_a * 0.10
    )

    final_score_b = (
        monthly_score_b * 0.40
        + dsr_score_b * 0.30
        + total_score_b * 0.20
        + tenure_score_b * 0.10
    )

    if abs(final_score_a - final_score_b) < 1:
        recommended = "Kedua-dua pilihan hampir setara"
    elif final_score_a > final_score_b:
        recommended = "Loan A"
    else:
        recommended = "Loan B"

    return {
        "score_a": final_score_a,
        "score_b": final_score_b,
        "dsr_a": dsr_a,
        "dsr_b": dsr_b,
        "recommended": recommended,
        "breakdown_a": {
            "Monthly": monthly_score_a,
            "DSR": dsr_score_a,
            "Total Cost": total_score_a,
            "Tenure": tenure_score_a,
        },
        "breakdown_b": {
            "Monthly": monthly_score_b,
            "DSR": dsr_score_b,
            "Total Cost": total_score_b,
            "Tenure": tenure_score_b,
        },
    }


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
    Return list of:
    [(start_month_index, annual_rate), ...]

    Month index bermula dari 0.
    """
    timeline = [(0, starting_rate)]

    if scenario == "Stable":
        return timeline

    if scenario == "Moderate Increase":
        change_month = min(3 * 12, total_months - 1)
        timeline.append((change_month, starting_rate + 0.25))

    elif scenario == "High Rate Scenario":
        first_month = min(2 * 12, total_months - 1)
        second_month = min(5 * 12, total_months - 1)

        timeline.append((first_month, starting_rate + 0.50))

        if second_month > first_month:
            timeline.append((second_month, starting_rate + 1.00))

    elif scenario == "Custom":
        first_month = min(custom_year_1 * 12, total_months - 1)
        second_month = min(custom_year_2 * 12, total_months - 1)

        first_rate = max(starting_rate + custom_change_1, 0.0)
        second_rate = max(first_rate + custom_change_2, 0.0)

        timeline.append((first_month, first_rate))

        if second_month > first_month:
            timeline.append((second_month, second_rate))

    timeline = sorted(
        list(set(timeline)),
        key=lambda item: item[0],
    )

    return timeline


# =========================================================
# HOUSING CALCULATIONS
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
):
    validate_general_loan(amount, starting_rate, years)
    validate_extra_payment(extra_payment, amount)

    months = int(years * 12)

    if rate_type == "Fixed Rate":
        timeline = [(0, starting_rate)]
    else:
        timeline = build_rate_timeline(
            starting_rate,
            months,
            rate_scenario,
            custom_change_1,
            custom_year_1,
            custom_change_2,
            custom_year_2,
        )

    balance = amount
    balances = [amount]
    payments = []
    interest_parts = []
    principal_parts = []
    rates = []

    timeline_lookup = {
        month_index: annual_rate
        for month_index, annual_rate in timeline
    }

    active_rate = timeline[0][1]

    scheduled_payment = monthly_payment_reducing_balance(
        balance,
        active_rate,
        months,
    )

    starting_payment = scheduled_payment + extra_payment
    current_payment = starting_payment

    for month_index in range(months):
        if balance <= 0.005:
            break

        if month_index in timeline_lookup:
            active_rate = timeline_lookup[month_index]
            remaining_months = months - month_index

            scheduled_payment = monthly_payment_reducing_balance(
                balance,
                active_rate,
                remaining_months,
            )

            current_payment = scheduled_payment + extra_payment

        monthly_rate = active_rate / 100 / 12
        interest = balance * monthly_rate

        planned_payment = scheduled_payment + extra_payment
        actual_payment = min(
            planned_payment,
            balance + interest,
        )

        principal_paid = actual_payment - interest
        principal_paid = min(principal_paid, balance)

        balance -= principal_paid

        payments.append(actual_payment)
        interest_parts.append(interest)
        principal_parts.append(principal_paid)
        rates.append(active_rate)
        balances.append(max(balance, 0.0))

    rate_description = "Fixed Rate"

    if rate_type == "Floating Rate":
        rate_steps = " → ".join(
            f"{rate:.2f}%"
            for _, rate in timeline
        )

        rate_description = f"Floating: {rate_steps}"

    return {
        "calculator": "Housing Loan",
        "rate_type": rate_description,
        "principal": amount,
        "starting_payment": starting_payment,
        "comparison_payment": current_payment,
        "total_interest": sum(interest_parts),
        "total_payment": sum(payments),
        "fees": 0.0,
        "months": len(payments),
        "balances": balances,
        "payments": payments,
        "interest_parts": interest_parts,
        "principal_parts": principal_parts,
        "rates": rates,
        "rate_timeline": timeline,
        "extra_payment": extra_payment,
    }


# =========================================================
# CAR CALCULATION
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

    validate_general_loan(
        price - down_payment,
        rate,
        years,
    )

    if years > 9:
        raise ValueError(
            "Tempoh car loan dalam calculator ini terhad kepada 9 tahun."
        )

    principal = price - down_payment
    months = int(years * 12)

    total_interest = principal * rate / 100 * years
    total_payment = principal + total_interest
    monthly_payment = total_payment / months

    monthly_principal = principal / months
    monthly_interest = total_interest / months

    balance = principal
    balances = [principal]
    payments = []
    interest_parts = []
    principal_parts = []

    for _ in range(months):
        actual_principal = min(monthly_principal, balance)

        balance -= actual_principal

        principal_parts.append(actual_principal)
        interest_parts.append(monthly_interest)
        payments.append(actual_principal + monthly_interest)
        balances.append(max(balance, 0.0))

    financing_margin = principal / price * 100

    return {
        "calculator": "Car Loan",
        "rate_type": f"Flat Rate · {financing_margin:.1f}% financed",
        "principal": principal,
        "starting_payment": monthly_payment,
        "comparison_payment": monthly_payment,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "fees": 0.0,
        "months": months,
        "balances": balances,
        "payments": payments,
        "interest_parts": interest_parts,
        "principal_parts": principal_parts,
        "car_price": price,
        "down_payment": down_payment,
        "financing_margin": financing_margin,
    }


# =========================================================
# PERSONAL LOAN CALCULATIONS
# =========================================================

def personal_flat_loan(
    amount,
    rate,
    years,
    processing_fee_percentage,
):
    validate_general_loan(amount, rate, years)

    if years > 10:
        raise ValueError(
            "Tempoh personal loan dalam calculator ini terhad kepada 10 tahun."
        )

    if processing_fee_percentage < 0:
        raise ValueError("Processing fee tidak boleh bernilai negatif.")

    if processing_fee_percentage > 20:
        raise ValueError(
            "Processing fee melebihi 20%. Sila semak semula input."
        )

    months = int(years * 12)

    total_interest = amount * rate / 100 * years
    processing_fee = amount * processing_fee_percentage / 100

    if processing_fee >= amount:
        raise ValueError(
            "Processing fee tidak boleh sama atau melebihi jumlah pinjaman."
        )

    total_payment = amount + total_interest + processing_fee
    monthly_payment = total_payment / months
    net_cash_received = amount - processing_fee

    monthly_principal = amount / months
    monthly_interest = total_interest / months
    balance = amount

    balances = [amount]
    payments = []
    principal_parts = []
    interest_parts = []

    for _ in range(months):
        actual_principal = min(monthly_principal, balance)
        balance -= actual_principal

        payments.append(actual_principal + monthly_interest)
        principal_parts.append(actual_principal)
        interest_parts.append(monthly_interest)
        balances.append(max(balance, 0.0))

    return {
        "calculator": "Personal Loan",
        "rate_type": "Flat Rate",
        "principal": amount,
        "starting_payment": monthly_payment,
        "comparison_payment": monthly_payment,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "fees": processing_fee,
        "months": months,
        "balances": balances,
        "payments": payments,
        "principal_parts": principal_parts,
        "interest_parts": interest_parts,
        "net_cash_received": net_cash_received,
    }


def personal_reducing_loan(
    amount,
    rate,
    years,
    processing_fee_percentage,
):
    validate_general_loan(amount, rate, years)

    if years > 10:
        raise ValueError(
            "Tempoh personal loan dalam calculator ini terhad kepada 10 tahun."
        )

    if processing_fee_percentage < 0:
        raise ValueError("Processing fee tidak boleh bernilai negatif.")

    if processing_fee_percentage > 20:
        raise ValueError(
            "Processing fee melebihi 20%. Sila semak semula input."
        )

    months = int(years * 12)

    monthly_payment = monthly_payment_reducing_balance(
        amount,
        rate,
        months,
    )

    processing_fee = amount * processing_fee_percentage / 100

    if processing_fee >= amount:
        raise ValueError(
            "Processing fee tidak boleh sama atau melebihi jumlah pinjaman."
        )

    monthly_rate = rate / 100 / 12
    balance = amount

    balances = [amount]
    payments = []
    principal_parts = []
    interest_parts = []

    for _ in range(months):
        if balance <= 0.005:
            break

        interest = balance * monthly_rate

        actual_payment = min(
            monthly_payment,
            balance + interest,
        )

        principal_paid = actual_payment - interest
        principal_paid = min(principal_paid, balance)

        balance -= principal_paid

        payments.append(actual_payment)
        principal_parts.append(principal_paid)
        interest_parts.append(interest)
        balances.append(max(balance, 0.0))

    total_interest = sum(interest_parts)
    total_payment = sum(payments) + processing_fee
    net_cash_received = amount - processing_fee

    return {
        "calculator": "Personal Loan",
        "rate_type": "Reducing Balance",
        "principal": amount,
        "starting_payment": monthly_payment,
        "comparison_payment": monthly_payment,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "fees": processing_fee,
        "months": len(payments),
        "balances": balances,
        "payments": payments,
        "principal_parts": principal_parts,
        "interest_parts": interest_parts,
        "net_cash_received": net_cash_received,
    }


# =========================================================
# HUMAN-LANGUAGE SUMMARY
# =========================================================

def generate_comparison_summary(A, B):
    monthly_difference = abs(
        A["comparison_payment"] - B["comparison_payment"]
    )

    total_difference = abs(
        A["total_payment"] - B["total_payment"]
    )

    if A["comparison_payment"] < B["comparison_payment"]:
        monthly_sentence = (
            f"Loan A mempunyai ansuran semasa {rm(monthly_difference)} "
            "lebih rendah berbanding Loan B."
        )

    elif B["comparison_payment"] < A["comparison_payment"]:
        monthly_sentence = (
            f"Loan B mempunyai ansuran semasa {rm(monthly_difference)} "
            "lebih rendah berbanding Loan A."
        )

    else:
        monthly_sentence = (
            "Kedua-dua pinjaman mempunyai ansuran semasa yang sama."
        )

    if A["total_payment"] < B["total_payment"]:
        total_sentence = (
            f"Sepanjang tempoh pinjaman, Loan A menjimatkan sekitar "
            f"{rm(total_difference)} dari segi jumlah bayaran keseluruhan."
        )

    elif B["total_payment"] < A["total_payment"]:
        total_sentence = (
            f"Sepanjang tempoh pinjaman, Loan B menjimatkan sekitar "
            f"{rm(total_difference)} dari segi jumlah bayaran keseluruhan."
        )

    else:
        total_sentence = (
            "Jumlah bayaran keseluruhan kedua-dua pinjaman adalah sama."
        )

    if A["months"] < B["months"]:
        tenure_sentence = (
            f"Loan A juga selesai {B['months'] - A['months']} bulan "
            "lebih awal."
        )

    elif B["months"] < A["months"]:
        tenure_sentence = (
            f"Loan B juga selesai {A['months'] - B['months']} bulan "
            "lebih awal."
        )

    else:
        tenure_sentence = (
            "Kedua-dua pinjaman mempunyai tempoh pembayaran yang sama."
        )

    return f"{monthly_sentence} {total_sentence} {tenure_sentence}"


def generate_quick_summary(result, income, commitments):
    dsr = calculate_dsr(
        result["comparison_payment"],
        income,
        commitments,
    )

    label, _ = affordability_label(dsr)

    return (
        f"Anggaran ansuran ialah {rm(result['comparison_payment'])} sebulan. "
        f"Jumlah faedah atau keuntungan pembiayaan dianggarkan "
        f"{rm(result['total_interest'])}, manakala jumlah keseluruhan "
        f"bayaran ialah {rm(result['total_payment'])}. "
        f"Selepas mengambil kira komitmen sedia ada, DSR dianggarkan "
        f"{dsr:.1f}% dan dikategorikan sebagai {label}."
    )


# =========================================================
# GRAPHS
# =========================================================

def plot_balance_graph(A, B=None, title="Remaining Principal"):
    figure, axis = plt.subplots(figsize=(11, 4.5))

    axis.plot(
        range(len(A["balances"])),
        A["balances"],
        linewidth=2.4,
        label="Loan A" if B else "Loan",
    )

    if B is not None:
        axis.plot(
            range(len(B["balances"])),
            B["balances"],
            linewidth=2.4,
            linestyle="--",
            label="Loan B",
        )

    axis.set_xlabel("Bulan")
    axis.set_ylabel("Baki Prinsipal (RM)")
    axis.set_title(title)
    axis.grid(alpha=0.18)
    axis.legend()
    axis.ticklabel_format(style="plain", axis="y")

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def plot_payment_graph(A, B=None, title="Monthly Payment Trend"):
    figure, axis = plt.subplots(figsize=(11, 4.5))

    axis.plot(
        range(1, len(A["payments"]) + 1),
        A["payments"],
        linewidth=2.4,
        label="Loan A" if B else "Loan",
    )

    if B is not None:
        axis.plot(
            range(1, len(B["payments"]) + 1),
            B["payments"],
            linewidth=2.4,
            linestyle="--",
            label="Loan B",
        )

    axis.set_xlabel("Bulan")
    axis.set_ylabel("Bayaran Bulanan (RM)")
    axis.set_title(title)
    axis.grid(alpha=0.18)
    axis.legend()

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def plot_cost_comparison(A, B=None, title="Cost Structure"):
    labels = ["Principal", "Interest", "Fees"]

    values_a = [
        A["principal"],
        A["total_interest"],
        A.get("fees", 0.0),
    ]

    figure, axis = plt.subplots(figsize=(10, 4.5))

    if B is None:
        axis.bar(labels, values_a)
    else:
        values_b = [
            B["principal"],
            B["total_interest"],
            B.get("fees", 0.0),
        ]

        positions = range(len(labels))
        width = 0.35

        axis.bar(
            [position - width / 2 for position in positions],
            values_a,
            width=width,
            label="Loan A",
        )

        axis.bar(
            [position + width / 2 for position in positions],
            values_b,
            width=width,
            label="Loan B",
        )

        axis.set_xticks(list(positions))
        axis.set_xticklabels(labels)
        axis.legend()

    axis.set_ylabel("RM")
    axis.set_title(title)
    axis.grid(axis="y", alpha=0.18)

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


# =========================================================
# SAVE SCENARIO
# =========================================================

def save_scenario(
    scenario_name,
    calculator_type,
    mode,
    A,
    B=None,
):
    if not scenario_name.strip():
        raise ValueError(
            "Masukkan nama scenario sebelum menyimpan."
        )

    record = {
        "name": scenario_name.strip(),
        "calculator": calculator_type,
        "mode": mode,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "A": {
            "rate_type": A["rate_type"],
            "principal": A["principal"],
            "monthly": A["comparison_payment"],
            "interest": A["total_interest"],
            "total": A["total_payment"],
            "months": A["months"],
        },
        "B": None,
    }

    if B is not None:
        record["B"] = {
            "rate_type": B["rate_type"],
            "principal": B["principal"],
            "monthly": B["comparison_payment"],
            "interest": B["total_interest"],
            "total": B["total_payment"],
            "months": B["months"],
        }

    st.session_state.saved_scenarios.append(record)


def show_save_section(calculator_type, mode, A, B=None):
    st.markdown("### 💾 Simpan Scenario")

    save_column, button_column = st.columns([4, 1])

    with save_column:
        scenario_name = st.text_input(
            "Nama scenario",
            placeholder="Contoh: Rumah Maybank 30 Tahun",
            key=f"scenario_name_{calculator_type}_{mode}",
        )

    with button_column:
        st.write("")

        if st.button(
            "Save",
            use_container_width=True,
            key=f"save_{calculator_type}_{mode}",
        ):
            try:
                save_scenario(
                    scenario_name,
                    calculator_type,
                    mode,
                    A,
                    B,
                )

                st.success("Scenario berjaya disimpan.")

            except ValueError as error:
                st.error(str(error))


def show_saved_scenarios():
    st.markdown("## 💾 Saved Scenarios")

    if not st.session_state.saved_scenarios:
        st.info("Belum ada scenario yang disimpan.")
        return

    for index, scenario in enumerate(
        st.session_state.saved_scenarios
    ):
        with st.expander(
            f"{scenario['name']} · {scenario['calculator']} "
            f"· {scenario['saved_at']}"
        ):
            A = scenario["A"]

            st.write(f"**Mode:** {scenario['mode']}")
            st.write(f"**Loan A:** {A['rate_type']}")
            st.write(f"Monthly: **{rm(A['monthly'])}**")
            st.write(f"Total payment: **{rm(A['total'])}**")

            if scenario["B"] is not None:
                B = scenario["B"]

                st.divider()
                st.write(f"**Loan B:** {B['rate_type']}")
                st.write(f"Monthly: **{rm(B['monthly'])}**")
                st.write(f"Total payment: **{rm(B['total'])}**")

            if st.button(
                "Delete Scenario",
                key=f"delete_scenario_{index}",
            ):
                st.session_state.saved_scenarios.pop(index)
                st.rerun()


# =========================================================
# COMMON RESULT DISPLAY
# =========================================================

def display_quick_result(
    result,
    income,
    commitments,
    calculator_type,
):
    dsr = calculate_dsr(
        result["comparison_payment"],
        income,
        commitments,
    )

    label, message = affordability_label(dsr)

    st.markdown("## 📌 Result")

    column_1, column_2, column_3, column_4 = st.columns(4)

    column_1.metric(
        "Monthly Payment",
        rm(result["comparison_payment"]),
    )

    column_2.metric(
        "Total Interest",
        rm(result["total_interest"]),
    )

    column_3.metric(
        "Total Payment",
        rm(result["total_payment"]),
    )

    column_4.metric(
        "DSR",
        f"{dsr:.1f}%",
    )

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

    graph_tab_1, graph_tab_2 = st.tabs(
        [
            "📉 Remaining Balance",
            "📊 Cost Structure",
        ]
    )

    with graph_tab_1:
        plot_balance_graph(
            result,
            title=f"{calculator_type} Remaining Principal",
        )

    with graph_tab_2:
        if calculator_type == "Housing Loan":
            plot_payment_graph(
                result,
                title="Housing Monthly Payment Trend",
            )
        else:
            plot_cost_comparison(
                result,
                title=f"{calculator_type} Cost Structure",
            )

    show_save_section(
        calculator_type,
        "Quick Calculation",
        result,
    )


def display_compare_result(
    A,
    B,
    income,
    commitments,
    calculator_type,
):
    recommendation = calculate_smart_scores(
        A,
        B,
        income,
        commitments,
    )

    st.markdown("## 📌 Comparison Result")

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    metric_1.metric(
        "Loan A Monthly",
        rm(A["comparison_payment"]),
    )

    metric_2.metric(
        "Loan B Monthly",
        rm(B["comparison_payment"]),
    )

    metric_3.metric(
        "Loan A Score",
        f"{recommendation['score_a']:.0f}/100",
    )

    metric_4.metric(
        "Loan B Score",
        f"{recommendation['score_b']:.0f}/100",
    )

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
                "Starting Payment",
                "Current / Comparison Payment",
                "Total Interest",
                "Fees",
                "Total Payment",
                "Loan Period",
                "DSR",
                "Smart Score",
            ],
            "Loan A": [
                A["rate_type"],
                rm(A["principal"]),
                rm(A["starting_payment"]),
                rm(A["comparison_payment"]),
                rm(A["total_interest"]),
                rm(A.get("fees", 0.0)),
                rm(A["total_payment"]),
                f"{A['months']} bulan",
                f"{recommendation['dsr_a']:.1f}%",
                f"{recommendation['score_a']:.0f}/100",
            ],
            "Loan B": [
                B["rate_type"],
                rm(B["principal"]),
                rm(B["starting_payment"]),
                rm(B["comparison_payment"]),
                rm(B["total_interest"]),
                rm(B.get("fees", 0.0)),
                rm(B["total_payment"]),
                f"{B['months']} bulan",
                f"{recommendation['dsr_b']:.1f}%",
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
        st.dataframe(
            comparison_table,
            use_container_width=True,
            hide_index=True,
        )

    with graph_tab:
        graph_1, graph_2 = st.tabs(
            [
                "Remaining Principal",
                (
                    "Monthly Payment Trend"
                    if calculator_type == "Housing Loan"
                    else "Cost Structure"
                ),
            ]
        )

        with graph_1:
            plot_balance_graph(
                A,
                B,
                title=f"{calculator_type} Remaining Principal",
            )

        with graph_2:
            if calculator_type == "Housing Loan":
                plot_payment_graph(
                    A,
                    B,
                    title="Housing Monthly Payment Trend",
                )
            else:
                plot_cost_comparison(
                    A,
                    B,
                    title=f"{calculator_type} Cost Comparison",
                )

    with smart_tab:
        score_a_column, score_b_column = st.columns(2)

        with score_a_column:
            st.metric(
                "Loan A Smart Score",
                f"{recommendation['score_a']:.0f}/100",
            )

            st.write(
                pd.DataFrame(
                    {
                        "Component": recommendation[
                            "breakdown_a"
                        ].keys(),
                        "Score": [
                            f"{value:.0f}/100"
                            for value in recommendation[
                                "breakdown_a"
                            ].values()
                        ],
                    }
                )
            )

        with score_b_column:
            st.metric(
                "Loan B Smart Score",
                f"{recommendation['score_b']:.0f}/100",
            )

            st.write(
                pd.DataFrame(
                    {
                        "Component": recommendation[
                            "breakdown_b"
                        ].keys(),
                        "Score": [
                            f"{value:.0f}/100"
                            for value in recommendation[
                                "breakdown_b"
                            ].values()
                        ],
                    }
                )
            )

        st.markdown(
            f"""
            <div class="smart-card">
                <h3>🏆 Suggested Option:
                    {recommendation['recommended']}
                </h3>

                <p>
                    Smart Score menggunakan empat komponen:
                </p>

                <p>
                    • 40% monthly affordability<br>
                    • 30% DSR<br>
                    • 20% total financing cost<br>
                    • 10% loan tenure
                </p>

                <p class="small-note">
                    Recommendation ini ialah rule-based financial
                    analysis, bukan keputusan kelulusan bank atau
                    artificial intelligence model.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    show_save_section(
        calculator_type,
        "Compare Two Loans",
        A,
        B,
    )


# =========================================================
# PAGE HEADER
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

        if st.button(
            "← Home",
            use_container_width=True,
            key=f"home_{title}",
        ):
            go_home()
            st.rerun()


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

    housing_column, car_column, personal_column = st.columns(3)

    with housing_column:
        st.markdown(
            """
            <div class="calculator-card">
                <div style="font-size:2.5rem;">🏠</div>
                <h2>Housing Loan</h2>
                <p>
                    Fixed dan floating rate, multiple rate scenarios,
                    extra payment serta payment trend.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Housing Calculator",
            use_container_width=True,
            type="primary",
        ):
            open_page("housing")
            st.rerun()

    with car_column:
        st.markdown(
            """
            <div class="calculator-card">
                <div style="font-size:2.5rem;">🚗</div>
                <h2>Car Loan</h2>
                <p>
                    Flat-rate financing, down payment,
                    financing margin dan affordability analysis.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Car Calculator",
            use_container_width=True,
        ):
            open_page("car")
            st.rerun()

    with personal_column:
        st.markdown(
            """
            <div class="calculator-card">
                <div style="font-size:2.5rem;">💳</div>
                <h2>Personal Loan</h2>
                <p>
                    Flat atau reducing balance, processing fee,
                    net cash received dan total repayment.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Open Personal Calculator",
            use_container_width=True,
        ):
            open_page("personal")
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

def show_housing_calculator():
    calculator_header(
        "🏠",
        "Housing Loan Calculator",
        "Fixed dan floating housing financing dengan multiple rate scenarios.",
    )

    calculation_mode = st.radio(
        "Calculation Mode",
        ["Quick Calculation", "Compare Two Loans"],
        horizontal=True,
        key="housing_mode",
    )

    with st.form("housing_form"):
        financial_column, scenario_column = st.columns(2)

        with financial_column:
            st.markdown("### Financial Profile")

            income = st.number_input(
                "Monthly Net Income (RM)",
                min_value=0.0,
                value=7000.0,
                step=100.0,
            )

            commitments = st.number_input(
                "Other Monthly Commitments (RM)",
                min_value=0.0,
                value=800.0,
                step=50.0,
            )

        with scenario_column:
            st.markdown("### Housing Settings")

            rate_scenario = st.selectbox(
                "Floating Rate Scenario",
                [
                    "Stable",
                    "Moderate Increase",
                    "High Rate Scenario",
                    "Custom",
                ],
            )

            extra_payment = st.number_input(
                "Extra Monthly Payment for Loan A (RM)",
                min_value=0.0,
                value=0.0,
                step=50.0,
            )

        custom_change_1 = 0.0
        custom_year_1 = 3
        custom_change_2 = 0.0
        custom_year_2 = 5

        if rate_scenario == "Custom":
            st.markdown("### Custom Floating Rate Timeline")

            custom_1, custom_2 = st.columns(2)

            with custom_1:
                custom_year_1 = st.number_input(
                    "First Change After Year",
                    min_value=1,
                    max_value=30,
                    value=3,
                )

                custom_change_1 = st.number_input(
                    "First Rate Change (%)",
                    min_value=-5.0,
                    max_value=10.0,
                    value=0.25,
                    step=0.05,
                )

            with custom_2:
                custom_year_2 = st.number_input(
                    "Second Change After Year",
                    min_value=1,
                    max_value=30,
                    value=5,
                )

                custom_change_2 = st.number_input(
                    "Second Rate Change (%)",
                    min_value=-5.0,
                    max_value=10.0,
                    value=0.25,
                    step=0.05,
                )

        st.divider()

        if calculation_mode == "Quick Calculation":
            st.markdown("### Loan Details")

            amount_a = st.number_input(
                "Loan Amount (RM)",
                min_value=0.0,
                value=400000.0,
                step=5000.0,
            )

            rate_type_a = st.selectbox(
                "Rate Type",
                ["Fixed Rate", "Floating Rate"],
            )

            rate_a = st.number_input(
                "Starting Interest Rate (%)",
                min_value=0.0,
                value=4.00,
                step=0.05,
            )

            years_a = st.number_input(
                "Tenure (Years)",
                min_value=1,
                max_value=35,
                value=30,
            )

        else:
            loan_a_column, loan_b_column = st.columns(2)

            with loan_a_column:
                st.markdown("### Loan A")

                amount_a = st.number_input(
                    "Loan Amount A (RM)",
                    min_value=0.0,
                    value=400000.0,
                    step=5000.0,
                )

                rate_type_a = st.selectbox(
                    "Rate Type A",
                    ["Fixed Rate", "Floating Rate"],
                )

                rate_a = st.number_input(
                    "Starting Rate A (%)",
                    min_value=0.0,
                    value=4.00,
                    step=0.05,
                )

                years_a = st.number_input(
                    "Tenure A (Years)",
                    min_value=1,
                    max_value=35,
                    value=30,
                )

            with loan_b_column:
                st.markdown("### Loan B")

                amount_b = st.number_input(
                    "Loan Amount B (RM)",
                    min_value=0.0,
                    value=400000.0,
                    step=5000.0,
                )

                rate_type_b = st.selectbox(
                    "Rate Type B",
                    ["Fixed Rate", "Floating Rate"],
                    index=1,
                )

                rate_b = st.number_input(
                    "Starting Rate B (%)",
                    min_value=0.0,
                    value=4.00,
                    step=0.05,
                )

                years_b = st.number_input(
                    "Tenure B (Years)",
                    min_value=1,
                    max_value=35,
                    value=30,
                )

        submitted = st.form_submit_button(
            "Calculate Housing Loan",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        try:
            validate_income(income, commitments)

            A = housing_loan(
                amount_a,
                rate_a,
                int(years_a),
                rate_type_a,
                rate_scenario,
                custom_change_1,
                int(custom_year_1),
                custom_change_2,
                int(custom_year_2),
                extra_payment,
            )

            B = None

            if calculation_mode == "Compare Two Loans":
                B = housing_loan(
                    amount_b,
                    rate_b,
                    int(years_b),
                    rate_type_b,
                    rate_scenario,
                    custom_change_1,
                    int(custom_year_1),
                    custom_change_2,
                    int(custom_year_2),
                    0.0,
                )

            st.session_state.result = {
                "page": "housing",
                "mode": calculation_mode,
                "A": A,
                "B": B,
                "income": income,
                "commitments": commitments,
            }

        except ValueError as error:
            st.error(str(error))

    result = st.session_state.result

    if result and result["page"] == "housing":
        if result["mode"] == "Quick Calculation":
            display_quick_result(
                result["A"],
                result["income"],
                result["commitments"],
                "Housing Loan",
            )
        else:
            display_compare_result(
                result["A"],
                result["B"],
                result["income"],
                result["commitments"],
                "Housing Loan",
            )


# =========================================================
# CAR PAGE
# =========================================================

def show_car_calculator():
    calculator_header(
        "🚗",
        "Car Loan Calculator",
        "Flat-rate car financing dengan down payment dan financing margin.",
    )

    calculation_mode = st.radio(
        "Calculation Mode",
        ["Quick Calculation", "Compare Two Loans"],
        horizontal=True,
        key="car_mode",
    )

    st.info(
        "Car loan menggunakan flat-rate estimate. "
        "Graf baki bukan early-settlement quotation rasmi."
    )

    with st.form("car_form"):
        financial_1, financial_2 = st.columns(2)

        with financial_1:
            income = st.number_input(
                "Monthly Net Income (RM)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
            )

        with financial_2:
            commitments = st.number_input(
                "Other Monthly Commitments (RM)",
                min_value=0.0,
                value=500.0,
                step=50.0,
            )

        st.divider()

        if calculation_mode == "Quick Calculation":
            price_a = st.number_input(
                "Car Price (RM)",
                min_value=0.0,
                value=90000.0,
                step=1000.0,
            )

            down_payment_a = st.number_input(
                "Down Payment (RM)",
                min_value=0.0,
                value=9000.0,
                step=500.0,
            )

            rate_a = st.number_input(
                "Flat Rate (%)",
                min_value=0.0,
                value=3.00,
                step=0.05,
            )

            years_a = st.number_input(
                "Tenure (Years)",
                min_value=1,
                max_value=9,
                value=9,
            )

        else:
            loan_a_column, loan_b_column = st.columns(2)

            with loan_a_column:
                st.markdown("### Loan A")

                price_a = st.number_input(
                    "Car Price A (RM)",
                    min_value=0.0,
                    value=90000.0,
                    step=1000.0,
                )

                down_payment_a = st.number_input(
                    "Down Payment A (RM)",
                    min_value=0.0,
                    value=9000.0,
                    step=500.0,
                )

                rate_a = st.number_input(
                    "Flat Rate A (%)",
                    min_value=0.0,
                    value=3.00,
                    step=0.05,
                )

                years_a = st.number_input(
                    "Tenure A (Years)",
                    min_value=1,
                    max_value=9,
                    value=9,
                )

            with loan_b_column:
                st.markdown("### Loan B")

                price_b = st.number_input(
                    "Car Price B (RM)",
                    min_value=0.0,
                    value=90000.0,
                    step=1000.0,
                )

                down_payment_b = st.number_input(
                    "Down Payment B (RM)",
                    min_value=0.0,
                    value=18000.0,
                    step=500.0,
                )

                rate_b = st.number_input(
                    "Flat Rate B (%)",
                    min_value=0.0,
                    value=2.80,
                    step=0.05,
                )

                years_b = st.number_input(
                    "Tenure B (Years)",
                    min_value=1,
                    max_value=9,
                    value=7,
                )

        submitted = st.form_submit_button(
            "Calculate Car Loan",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        try:
            validate_income(income, commitments)

            A = car_flat_loan(
                price_a,
                down_payment_a,
                rate_a,
                int(years_a),
            )

            B = None

            if calculation_mode == "Compare Two Loans":
                B = car_flat_loan(
                    price_b,
                    down_payment_b,
                    rate_b,
                    int(years_b),
                )

            st.session_state.result = {
                "page": "car",
                "mode": calculation_mode,
                "A": A,
                "B": B,
                "income": income,
                "commitments": commitments,
            }

        except ValueError as error:
            st.error(str(error))

    result = st.session_state.result

    if result and result["page"] == "car":
        if result["mode"] == "Quick Calculation":
            display_quick_result(
                result["A"],
                result["income"],
                result["commitments"],
                "Car Loan",
            )
        else:
            display_compare_result(
                result["A"],
                result["B"],
                result["income"],
                result["commitments"],
                "Car Loan",
            )


# =========================================================
# PERSONAL LOAN PAGE
# =========================================================

def show_personal_calculator():
    calculator_header(
        "💳",
        "Personal Loan Calculator",
        "Flat atau reducing-balance personal financing dengan processing fee.",
    )

    calculation_mode = st.radio(
        "Calculation Mode",
        ["Quick Calculation", "Compare Two Loans"],
        horizontal=True,
        key="personal_mode",
    )

    with st.form("personal_form"):
        financial_1, financial_2 = st.columns(2)

        with financial_1:
            income = st.number_input(
                "Monthly Net Income (RM)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
            )

        with financial_2:
            commitments = st.number_input(
                "Other Monthly Commitments (RM)",
                min_value=0.0,
                value=500.0,
                step=50.0,
            )

        st.divider()

        if calculation_mode == "Quick Calculation":
            amount_a = st.number_input(
                "Loan Amount (RM)",
                min_value=0.0,
                value=30000.0,
                step=1000.0,
            )

            rate_type_a = st.selectbox(
                "Rate Type",
                ["Flat Rate", "Reducing Balance"],
            )

            rate_a = st.number_input(
                "Interest Rate (%)",
                min_value=0.0,
                value=6.00,
                step=0.10,
            )

            years_a = st.number_input(
                "Tenure (Years)",
                min_value=1,
                max_value=10,
                value=5,
            )

            fee_a = st.number_input(
                "Processing Fee (%)",
                min_value=0.0,
                value=1.00,
                step=0.10,
            )

        else:
            loan_a_column, loan_b_column = st.columns(2)

            with loan_a_column:
                st.markdown("### Loan A")

                amount_a = st.number_input(
                    "Loan Amount A (RM)",
                    min_value=0.0,
                    value=30000.0,
                    step=1000.0,
                )

                rate_type_a = st.selectbox(
                    "Rate Type A",
                    ["Flat Rate", "Reducing Balance"],
                )

                rate_a = st.number_input(
                    "Interest Rate A (%)",
                    min_value=0.0,
                    value=6.00,
                    step=0.10,
                )

                years_a = st.number_input(
                    "Tenure A (Years)",
                    min_value=1,
                    max_value=10,
                    value=5,
                )

                fee_a = st.number_input(
                    "Processing Fee A (%)",
                    min_value=0.0,
                    value=1.00,
                    step=0.10,
                )

            with loan_b_column:
                st.markdown("### Loan B")

                amount_b = st.number_input(
                    "Loan Amount B (RM)",
                    min_value=0.0,
                    value=30000.0,
                    step=1000.0,
                )

                rate_type_b = st.selectbox(
                    "Rate Type B",
                    ["Flat Rate", "Reducing Balance"],
                    index=1,
                )

                rate_b = st.number_input(
                    "Interest Rate B (%)",
                    min_value=0.0,
                    value=8.00,
                    step=0.10,
                )

                years_b = st.number_input(
                    "Tenure B (Years)",
                    min_value=1,
                    max_value=10,
                    value=5,
                )

                fee_b = st.number_input(
                    "Processing Fee B (%)",
                    min_value=0.0,
                    value=1.00,
                    step=0.10,
                )

        submitted = st.form_submit_button(
            "Calculate Personal Loan",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        try:
            validate_income(income, commitments)

            if rate_type_a == "Flat Rate":
                A = personal_flat_loan(
                    amount_a,
                    rate_a,
                    int(years_a),
                    fee_a,
                )
            else:
                A = personal_reducing_loan(
                    amount_a,
                    rate_a,
                    int(years_a),
                    fee_a,
                )

            B = None

            if calculation_mode == "Compare Two Loans":
                if rate_type_b == "Flat Rate":
                    B = personal_flat_loan(
                        amount_b,
                        rate_b,
                        int(years_b),
                        fee_b,
                    )
                else:
                    B = personal_reducing_loan(
                        amount_b,
                        rate_b,
                        int(years_b),
                        fee_b,
                    )

            st.session_state.result = {
                "page": "personal",
                "mode": calculation_mode,
                "A": A,
                "B": B,
                "income": income,
                "commitments": commitments,
            }

        except ValueError as error:
            st.error(str(error))

    result = st.session_state.result

    if result and result["page"] == "personal":
        if result["mode"] == "Quick Calculation":
            st.metric(
                "Net Cash Received",
                rm(result["A"]["net_cash_received"]),
                f"Fee {rm(result['A']['fees'])}",
            )

            display_quick_result(
                result["A"],
                result["income"],
                result["commitments"],
                "Personal Loan",
            )

        else:
            net_a, net_b = st.columns(2)

            net_a.metric(
                "Net Cash Received A",
                rm(result["A"]["net_cash_received"]),
            )

            net_b.metric(
                "Net Cash Received B",
                rm(result["B"]["net_cash_received"]),
            )

            display_compare_result(
                result["A"],
                result["B"],
                result["income"],
                result["commitments"],
                "Personal Loan",
            )


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
