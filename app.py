"""
เว็บแสดงอัตราแลกเปลี่ยนเงินตรา ด้วย Streamlit
ดึงข้อมูลจาก ExchangeRate-API (https://www.exchangerate-api.com/)
ใช้ Open Access Endpoint: https://open.er-api.com/v6/latest/{BASE}  (ไม่ต้องใช้ API Key)

วิธีรัน:
    pip install streamlit requests pandas
    streamlit run app.py
"""

from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import streamlit as st

API_URL = "https://open.er-api.com/v6/latest/{base}"

# รหัสสกุลเงิน -> (ธงชาติ, ชื่อภาษาไทย)
CURRENCIES = {
    "THB": ("🇹🇭", "บาทไทย"),
    "USD": ("🇺🇸", "ดอลลาร์สหรัฐ"),
    "EUR": ("🇪🇺", "ยูโร"),
    "JPY": ("🇯🇵", "เยนญี่ปุ่น"),
    "GBP": ("🇬🇧", "ปอนด์สเตอร์ลิง"),
    "CNY": ("🇨🇳", "หยวนจีน"),
    "KRW": ("🇰🇷", "วอนเกาหลีใต้"),
    "SGD": ("🇸🇬", "ดอลลาร์สิงคโปร์"),
    "MYR": ("🇲🇾", "ริงกิตมาเลเซีย"),
    "HKD": ("🇭🇰", "ดอลลาร์ฮ่องกง"),
    "AUD": ("🇦🇺", "ดอลลาร์ออสเตรเลีย"),
    "CAD": ("🇨🇦", "ดอลลาร์แคนาดา"),
    "CHF": ("🇨🇭", "ฟรังก์สวิส"),
    "INR": ("🇮🇳", "รูปีอินเดีย"),
    "IDR": ("🇮🇩", "รูเปียห์อินโดนีเซีย"),
    "PHP": ("🇵🇭", "เปโซฟิลิปปินส์"),
    "VND": ("🇻🇳", "ดองเวียดนาม"),
    "LAK": ("🇱🇦", "กีบลาว"),
    "MMK": ("🇲🇲", "จั๊ตเมียนมา"),
    "KHR": ("🇰🇭", "เรียลกัมพูชา"),
    "TWD": ("🇹🇼", "ดอลลาร์ไต้หวัน"),
    "NZD": ("🇳🇿", "ดอลลาร์นิวซีแลนด์"),
    "RUB": ("🇷🇺", "รูเบิลรัสเซีย"),
    "AED": ("🇦🇪", "ดีแรห์มยูเออี"),
    "SAR": ("🇸🇦", "ริยัลซาอุดีอาระเบีย"),
}


def flag(code: str) -> str:
    return CURRENCIES.get(code, ("🏳️", ""))[0]


def thai_name(code: str) -> str:
    return CURRENCIES.get(code, ("", ""))[1]


def label(code: str) -> str:
    """ข้อความในตัวเลือกสกุลเงิน เช่น 🇹🇭 THB · บาทไทย"""
    name = thai_name(code)
    return f"{flag(code)}  {code} · {name}" if name else f"{flag(code)}  {code}"


def fmt(x: float) -> str:
    """จัดรูปแบบตัวเลข: ค่าน้อยแสดงทศนิยมมากขึ้น"""
    if x == 0:
        return "0"
    if abs(x) >= 1:
        return f"{x:,.2f}"
    return f"{x:,.6f}".rstrip("0").rstrip(".")


@st.cache_data(ttl=3600, show_spinner=False)
def get_rates(base: str) -> dict:
    """เรียก API เพื่อดึงอัตราแลกเปลี่ยนเทียบกับสกุลเงินฐาน (เก็บแคช 1 ชั่วโมง)"""
    response = requests.get(API_URL.format(base=base), timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("result") != "success":
        raise ValueError(data.get("error-type", "ไม่ทราบสาเหตุ"))
    return data


# ---------------- ตั้งค่าหน้าเว็บ + CSS ----------------
st.set_page_config(page_title="อัตราแลกเปลี่ยนเงินตรา", page_icon="💱", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700&display=swap');

    html, body, [class*="css"], .stMarkdown, .stTextInput, .stNumberInput, .stSelectbox,
    button, input, label, p, h1, h2, h3 {
        font-family: 'Prompt', sans-serif !important;
    }
    .block-container { padding-top: 2rem; max-width: 820px; }

    .hero {
        background: linear-gradient(135deg, #0f766e 0%, #14b8a6 55%, #5eead4 100%);
        border-radius: 22px;
        padding: 28px 30px;
        color: #ffffff;
        box-shadow: 0 12px 30px rgba(15, 118, 110, 0.25);
        margin-bottom: 1.4rem;
    }
    .hero h1 { color: #ffffff; font-size: 2rem; font-weight: 700; margin: 0; padding: 0; }
    .hero p  { color: #ecfeff; margin: 6px 0 0 0; font-size: 0.95rem; opacity: 0.95; }

    .result-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 24px 26px;
        margin: 1rem 0 0.6rem 0;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        text-align: center;
    }
    .result-from { color: #64748b; font-size: 1.05rem; }
    .result-to   { color: #0f766e; font-size: 2.4rem; font-weight: 700; line-height: 1.25;
                   margin: 4px 0 2px 0; word-break: break-word; }
    .result-name { color: #94a3b8; font-size: 0.9rem; }

    .rate-row { display: flex; gap: 12px; margin-bottom: 0.4rem; }
    .rate-pill {
        flex: 1;
        background: #f0fdfa;
        border: 1px solid #ccfbf1;
        color: #134e4a;
        border-radius: 14px;
        padding: 10px 14px;
        font-size: 0.92rem;
        text-align: center;
    }
    .updated { color: #94a3b8; font-size: 0.82rem; text-align: center; margin-top: 4px; }

    .section-title { font-size: 1.25rem; font-weight: 600; margin: 1.6rem 0 0.6rem 0; }

    /* ช่องกรอกจำนวนเงินให้ใหญ่และเด่น */
    div[data-testid="stNumberInput"] input {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 0.9rem !important;
    }
    div[data-testid="stNumberInput"] label p { font-weight: 600; font-size: 1rem; }

    /* ปุ่มสลับสกุลเงิน */
    div[data-testid="stButton"] button {
        border-radius: 999px;
        width: 100%;
        font-size: 1.2rem;
        border: 1px solid #14b8a6;
        color: #0f766e;
    }
    div[data-testid="stButton"] button:hover { background: #14b8a6; color: #ffffff; }

    /* แท็บ */
    button[data-baseweb="tab"][aria-selected="true"] p { color: #0f766e; font-weight: 600; }
    div[data-baseweb="tab-highlight"] { background-color: #14b8a6 !important; }

    @media (max-width: 640px) {
        .hero h1 { font-size: 1.5rem; }
        .result-to { font-size: 1.8rem; }
        .rate-row { flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>💱 อัตราแลกเปลี่ยนเงินตรา</h1>
        <p>แปลงสกุลเงินแบบเรียลไทม์ · ข้อมูลจาก ExchangeRate-API (www.exchangerate-api.com)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- โหลดรายชื่อสกุลเงิน ----------------
try:
    all_codes = sorted(get_rates("USD")["rates"].keys())
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ API ได้: {e}")
    st.stop()

# ให้สกุลเงินที่มีชื่อไทยขึ้นก่อน แล้วตามด้วยสกุลอื่นๆ
popular = [c for c in CURRENCIES if c in all_codes]
options = popular + [c for c in all_codes if c not in popular]

if "from_cur" not in st.session_state:
    st.session_state.from_cur = "USD"
if "to_cur" not in st.session_state:
    st.session_state.to_cur = "THB"
if "amount" not in st.session_state:
    st.session_state.amount = 100.0


def swap():
    st.session_state.from_cur, st.session_state.to_cur = (
        st.session_state.to_cur,
        st.session_state.from_cur,
    )


def set_amount(value: float):
    st.session_state.amount = value


# ---------------- ส่วนแปลงสกุลเงิน ----------------
with st.container(border=True):
    st.number_input(
        "💰 กรอกจำนวนเงินที่ต้องการแปลง",
        min_value=0.0,
        step=100.0,
        format="%.2f",
        key="amount",
    )

    quick = st.columns(5)
    for col, val in zip(quick, [1, 100, 500, 1000, 10000]):
        col.button(f"{val:,}", key=f"q{val}", on_click=set_amount, args=(float(val),), width="stretch")

    c1, c2, c3 = st.columns([5, 1.2, 5], vertical_alignment="bottom")
    with c1:
        st.selectbox("จากสกุลเงิน", options, format_func=label, key="from_cur")
    with c2:
        st.button("⇄", on_click=swap, help="สลับสกุลเงิน", key="swap")
    with c3:
        st.selectbox("เป็นสกุลเงิน", options, format_func=label, key="to_cur")

amount = st.session_state.amount
from_cur = st.session_state.from_cur
to_cur = st.session_state.to_cur

try:
    data = get_rates(from_cur)
except Exception as e:
    st.error(f"ดึงข้อมูลอัตราแลกเปลี่ยนไม่สำเร็จ: {e}")
    st.stop()

rates = data["rates"]
rate = rates[to_cur]
result = amount * rate

st.markdown(
    f"""
    <div class="result-card">
        <div class="result-from">{flag(from_cur)} {fmt(amount)} {from_cur} เท่ากับ</div>
        <div class="result-to">{flag(to_cur)} {fmt(result)} {to_cur}</div>
        <div class="result-name">{thai_name(to_cur)}</div>
    </div>
    <div class="rate-row">
        <div class="rate-pill">1 {from_cur} = <b>{fmt(rate)}</b> {to_cur}</div>
        <div class="rate-pill">1 {to_cur} = <b>{fmt(1 / rate) if rate else '-'}</b> {from_cur}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

updated = datetime.fromtimestamp(data["time_last_update_unix"], tz=timezone(timedelta(hours=7)))
st.markdown(
    f'<div class="updated">🕒 อัปเดตข้อมูลล่าสุด {updated.strftime("%d/%m/%Y %H:%M")} น. (เวลาประเทศไทย)</div>',
    unsafe_allow_html=True,
)

# ---------------- ตารางอัตราแลกเปลี่ยนทั้งหมด ----------------
tab1, tab2 = st.tabs(["📋 อัตราแลกเปลี่ยนทั้งหมด", "📊 กราฟเปรียบเทียบ"])

with tab1:
    st.markdown(
        f'<div class="section-title">{flag(from_cur)} {fmt(amount)} {from_cur} แลกเป็นสกุลอื่นได้เท่าไร</div>',
        unsafe_allow_html=True,
    )
    df = pd.DataFrame(
        {
            "สกุลเงิน": [label(c) for c in rates],
            f"อัตรา (ต่อ 1 {from_cur})": list(rates.values()),
            f"จำนวนที่ได้ (จาก {fmt(amount)} {from_cur})": [amount * r for r in rates.values()],
        }
    )
    search = st.text_input("🔍 ค้นหาสกุลเงิน", placeholder="เช่น THB, JPY, ยูโร, เยน")
    if search:
        q = search.strip()
        df = df[df["สกุลเงิน"].str.contains(q, case=False)]
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=420,
        column_config={
            f"อัตรา (ต่อ 1 {from_cur})": st.column_config.NumberColumn(format="%.4f"),
            f"จำนวนที่ได้ (จาก {fmt(amount)} {from_cur})": st.column_config.NumberColumn(format="%.2f"),
        },
    )

with tab2:
    st.markdown(
        f'<div class="section-title">1 {from_cur} เทียบกับสกุลเงินหลัก</div>',
        unsafe_allow_html=True,
    )
    main = [c for c in ["USD", "EUR", "GBP", "JPY", "CNY", "SGD", "THB", "KRW"] if c in rates and c != from_cur]
    chart_df = pd.DataFrame({"สกุลเงิน": main, "อัตรา": [rates[c] for c in main]}).set_index("สกุลเงิน")
    st.bar_chart(chart_df, color="#14b8a6", height=360)

st.caption("ข้อมูลอัตราแลกเปลี่ยนใช้เพื่อการศึกษา อัตราจริงของธนาคารอาจแตกต่างเล็กน้อย")
