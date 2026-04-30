import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

st.set_page_config(page_title="Loan Analyzer Pro", layout="wide")

st.title("💰 Loan Analyzer Pro (FINAL STABLE VERSION)")

# =========================
# SESSION STATE
# =========================
if "run" not in st.session_state:
    st.session_state.run = False

# =========================
# FUNCTIONS (FIXED DEFINITIONS)
# =========================

def car_loan(price, dp, rate, years):
    loan = price - dp
    interest_total = loan * (rate / 100) * years
    total_pay = loan + interest_total
    monthly = total_pay / (years * 12)
    m_interest = interest_total / (years * 12)
    m_principal = loan / (years * 12)
    balances, i_watch, p_watch = [], [], []
    curr = total_pay
    for _ in range(int(years * 12)):
        curr -= monthly
        balances.append(max(curr, 0))
        i_watch.append(m_interest)
        p_watch.append(m_principal)
    return loan, interest_total, total_pay, monthly, balances, i_watch, p_watch

def housing_loan(amount, rate, years, extra=0):
    if amount <= 0 or rate <= 0: return 0,0,0,0,[],[],[]
    r = (rate / 100) / 12
    n = int(years * 12)
    monthly_scheduled = amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    balance = amount
    balances, i_watch, p_watch = [], [], []
    total_interest_paid = 0
    months_taken = 0
    for _ in range(n):
        if balance <= 0: break
        interest_m = balance * r
        principal_m = (monthly_scheduled - interest_m) + extra
        balance -= principal_m
        balances.append(max(balance, 0))
        i_watch.append(interest_m)
        p_watch.append(principal_m)
        total_interest_paid += interest_m
        months_taken += 1
    total_pay = (monthly_scheduled * months_taken) + (extra * months_taken)
    return amount, total_interest_paid, total_pay, monthly_scheduled, balances, i_watch, p_watch

def floating_loan(amount, base_rate, years):
    if amount <= 0: return 0,0,0,0,[],[],[]
    months = int(years * 12)
    balance = amount
    balances, interest_watch, principal_watch = [], [], [] # FIXED: Added definitions
    r1, r2 = (base_rate / 100) / 12, ((base_rate + 0.75) / 100) / 12 
    monthly = amount * (r1 * (1 + r1) ** months) / ((1 + r1) ** months - 1)
    for m in range(1, months + 1):
        r = r1 if m <= 36 else r2
        interest_m = balance * r
        principal_m = monthly - interest_m
        balance -= principal_m
        balances.append(max(balance, 0))
        interest_watch.append(interest_m)
        principal_watch.append(principal_m)
    total_pay = monthly * months
    interest_total = total_pay - amount
    return amount, interest_total, total_pay, monthly, balances, interest_watch, principal_watch

def calculate_borrowing_power(monthly_budget, rate, years, type="Housing"):
    if monthly_budget <= 0: return 0
    if type == "Housing":
        r = (rate / 100) / 12
        n = years * 12
        max_loan = monthly_budget / ((r * (1 + r) ** n) / ((1 + r) ** n - 1))
    else:
        max_loan = (monthly_budget * years * 12) / (1 + (rate / 100 * years))
    return max_loan

# =========================
# SIDEBAR
# =========================
st.sidebar.header("🛡️ Affordability Master")
income = st.sidebar.number_input("Gaji Bersih (RM)", min_value=0.0, value=5000.0)
commit = st.sidebar.number_input("Komitmen Luar (RM)", min_value=0.0, value=500.0)
target_dsr = st.sidebar.slider("Had DSR (%)", 30, 70, 60)

safe_budget = (income * (target_dsr/100)) - commit
st.sidebar.info(f"Bajet Bulanan Maksimum: RM {max(safe_budget, 0.0):,.2f}")

with st.sidebar.expander("🔍 Lihat Kelayakan Harga"):
    est_rate = st.number_input("Estimasi Rate (%)", 3.0, 5.0, 4.0)
    est_years = st.number_input("Estimasi Tahun", 1, 35, 30)
    max_h = calculate_borrowing_power(safe_budget, est_rate, est_years, "Housing")
    max_c = calculate_borrowing_power(safe_budget, 3.0, 9, "Car")
    st.write(f"🏠 **Harga Rumah:** RM {max_h:,.0f}")
    st.write(f"🚗 **Harga Kereta:** RM {max_c:,.0f}")

st.sidebar.divider()
st.sidebar.header("🚀 Simulation Settings")
extra_pay = st.sidebar.number_input("Extra Payment Sebulan (RM)", 0.0, 5000.0, 0.0, 50.0)
opr_hike = st.sidebar.slider("OPR Hike Simulation (+%)", 0.0, 2.0, 0.25)
loan_type = st.sidebar.selectbox("Loan Type", ["Car Loan", "Housing Loan"])

# =========================
# MAIN INPUTS
# =========================
col1, col2 = st.columns(2)
with col1:
    st.subheader("📌 Loan A")
    if loan_type == "Car Loan":
        pA, dA = st.number_input("Harga A", value=70000.0), st.number_input("DP A", value=7000.0)
    else:
        lA = st.number_input("Loan A", value=400000.0)
    rA, rtA, yA = st.number_input("Rate A", value=3.0, key="ra"), st.selectbox("Type A", ["Fixed", "Floating"], key="rta"), st.number_input("Years A", value=9, key="ya")

with col2:
    st.subheader("📌 Loan B")
    if loan_type == "Car Loan":
        pB, dB = st.number_input("Harga B", value=70000.0), st.number_input("DP B", value=15000.0)
    else:
        lB = st.number_input("Loan B", value=400000.0)
    rB, rtB, yB = st.number_input("Rate B", value=3.0, key="rb"), st.selectbox("Type B", ["Fixed", "Floating"], key="rtb"), st.number_input("Years B", value=7, key="yb")

if st.button("RUN COMPARISON 🚀", use_container_width=True):
    st.session_state.run = True

# =========================
# RESULTS
# =========================
if st.session_state.run:
    if loan_type == "Car Loan":
        A, B = car_loan(pA, dA, rA, yA), car_loan(pB, dB, rB, yB)
        SimA = car_loan(pA, dA + (extra_pay * yA * 12), rA, yA)
    else:
        A = floating_loan(lA, rA, yA) if rtA == "Floating" else housing_loan(lA, rA, yA)
        B = floating_loan(lB, rB, yB) if rtB == "Floating" else housing_loan(lB, rB, yB)
        SimA = housing_loan(lA, rA, yA, extra=extra_pay)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Comparison", "📉 Breakdown", "🥧 Structure", "🛡️ OPR Test", "🚀 Snowball"])

    with tab1:
        st.table({"Item": ["Loan Amount", "Interest", "Total", "Monthly"], "A": [f"RM {x:,.2f}" for x in A[:4]], "B": [f"RM {x:,.2f}" for x in B[:4]]})
        fig1, ax1 = plt.subplots(figsize=(10, 3.5)); ax1.plot(A[4], label="A"); ax1.plot(B[4], linestyle="--", label="B"); ax1.legend(); st.pyplot(fig1)

    with tab2:
        choice = st.radio("Pilih:", ["A", "B"], horizontal=True)
        sel = A if choice == "A" else B
        df_b = pd.DataFrame({'Principal': sel[6], 'Interest': sel[5]}) 
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        df_b.plot(kind='bar', stacked=True, ax=ax2, color=['#4CAF50', '#FF5252'], width=0.8)
        n = len(df_b); xt = np.linspace(0, n-1, 8, dtype=int)
        ax2.set_xticks(xt); ax2.set_xticklabels([f"Bln {i}" for i in xt], rotation=0); st.pyplot(fig2)

    with tab3:
        c1, c2 = st.columns(2)
        with c1: 
            f, ax = plt.subplots(); ax.pie([A[0], A[1]], labels=['P', 'I'], autopct='%1.1f%%', colors=['#4CAF50', '#FF5252']); st.pyplot(f)
        with c2: 
            f, ax = plt.subplots(); ax.pie([B[0], B[1]], labels=['P', 'I'], autopct='%1.1f%%', colors=['#4CAF50', '#FF5252']); st.pyplot(f)

    with tab4:
        if loan_type == "Housing Loan":
            # A[0] is original amount
            _, _, _, m_new_A, _, _, _ = housing_loan(A[0], rA + opr_hike, yA)
            _, _, _, m_new_B, _, _, _ = housing_loan(B[0], rB + opr_hike, yB)
            c_opr1, c_opr2 = st.columns(2)
            with c_opr1: st.metric(f"Ansuran A (+{opr_hike}%)", f"RM {m_new_A:,.2f}", f"+RM {m_new_A-A[3]:,.2f}")
            with c_opr2: st.metric(f"Ansuran B (+{opr_hike}%)", f"RM {m_new_B:,.2f}", f"+RM {m_new_B-B[3]:,.2f}")
        else: st.warning("Not for Car Loan.")

    with tab5:
        if extra_pay > 0:
            st.success(f"Faedah Dijimatkan: RM {A[1]-SimA[1]:,.2f} | Cepat: {len(A[4])-len(SimA[4])} Bulan")
            f3, ax3 = plt.subplots(figsize=(10, 3.5)); ax3.plot(A[4], alpha=0.3, label="Asal"); ax3.plot(SimA[4], color='green', label="Extra"); ax3.legend(); st.pyplot(f3)
        else: st.info("Sila set Extra Payment di Sidebar.")

    st.divider()
    dsr_val = ((A[3] + commit) / income) * 100
    st.subheader(f"Verdict: {'✅ Selamat' if dsr_val < 60 else '❌ Bahaya'} (Total DSR: {dsr_val:.1f}%)")

