"""
PathogenBreak - farmer advisory app (Streamlit)

Run (from this folder, with the pbenv environment switched on):
    pip install streamlit
    streamlit run app.py

The app runs the SAME model as PathogenBreak_final.ipynb: it executes the notebook's code
once at start-up (about 15 seconds), so the numbers always match the notebook.
"""
import contextlib
import io
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
os.chdir(HERE)

st.set_page_config(page_title="PathogenBreak - Indore crop advisor", page_icon="🌾", layout="wide")


@st.cache_resource(show_spinner="Running the PathogenBreak model on 7 datasets (about 15 seconds)...")
def load_engine():
    nb = json.loads((HERE / "PathogenBreak_final.ipynb").read_text(encoding="utf-8"))
    ns = {"display": lambda *a, **k: None, "__name__": "pathogenbreak_engine"}
    with contextlib.redirect_stdout(io.StringIO()):
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            src = "".join(cell["source"])
            src = src.replace("from IPython.display import display", "")
            # skip the notebook-only live slider block
            src = src.split("# ---- 3. Live slider for the demo")[0]
            exec(compile(src, "PathogenBreak_final.ipynb", "exec"), ns)
    return ns


E = load_engine()

# ------------------------------------------------------------------ language
LANG = st.sidebar.radio("भाषा / Language", ["English", "हिंदी"], horizontal=True)
HI = LANG == "हिंदी"
CROP_HI = {"Soybean": "सोयाबीन", "Maize": "मक्का", "Cotton": "कपास", "Groundnut": "मूंगफली", "Pigeonpea": "अरहर",
           "Wheat": "गेहूं", "Gram": "चना", "Mustard": "सरसों", "Lentil": "मसूर", "Barley": "जौ"}
MONTH_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
STATE_HI = {"DRY": "सूखी", "NORMAL": "सामान्य", "WET": "गीली", "WATERLOGGED": "जलभराव"}
DEC_HI = {"Recommend": "अनुशंसित", "Qualify": "शर्तों के साथ", "Withhold": "रोकें"}
SOWING_HI = {"timely": "समय पर", "late": "देर से", "early": "जल्दी"}
WATER_HI = {"Gram": "यह मिट्टी में जमा नमी पर उगता है (अधिकतम 1-2 हल्की सिंचाई)",
            "Lentil": "यह मिट्टी में जमा नमी पर उगती है",
            "Mustard": "इसे कम पानी चाहिए (1-2 सिंचाई)",
            "Barley": "यह सूखी मिट्टी सह लेता है (1-2 सिंचाई)"}

def T(en, hi):
    return hi if HI else en

def crop_t(c):
    return CROP_HI.get(c, c) if HI else c

def plan_t(p):
    return " → ".join(crop_t(c) for c in p.split(" → "))

def hindi_advice(a, last_kharif, day):
    """Builds the Hindi action + reason from the same model outputs the English text uses."""
    crop, pct, pctl, state = crop_t(a["crop"]), a["pct"], a["pctl"], a["state"]
    crop_obl = {"Gram": "चने के"}.get(a["crop"], f"{crop} के")      # oblique case: "चने के बीज"
    month = MONTH_HI[day.month - 1]
    timing = a["table"].iloc[0]["Sowing"] if len(a["table"]) else "timely"
    late = " (देर से बुवाई: कम अवधि वाली किस्म लें और बीज दर बढ़ाएँ)" if timing == "late" else ""
    if state == "WATERLOGGED":
        action = "रुकिए – अभी बुवाई न करें"
        rot = (f"{crop_obl[:-3]} की फसल जलभराव वाली काली मिट्टी में सड़ जाती है। " if a["crop"] in E["WATERLOG_SENSITIVE"]
               else "बीज सड़ सकते हैं या मिट्टी पर पपड़ी जम सकती है। ")
        why = (f"मिट्टी में पानी भरा है ({pct:.0f}%)। " + rot +
               f"फफूंद रोग का खतरा {int((E['DISEASE_MULT'][state]-1)*100)}% बढ़ा है। खेत से पानी निकालें, "
               f"बुवाई से पहले {crop_obl} बीज का ट्राइकोडर्मा से उपचार करें, और 3-4 दिन बाद मिट्टी फिर जाँचें।")
    elif state == "WET":
        action = f"{crop} बोएँ, जब ऊपर की मिट्टी जुताई लायक हो जाए (1-2 दिन)"
        why = (f"मिट्टी पिछले वर्षों के {month} के {pctl:.0%} दिनों से ज़्यादा गीली है। नमी अच्छी है, पर फफूंद का "
               f"खतरा ज़्यादा है: बीज का ट्राइकोडर्मा से उपचार करें{late}।")
    elif state == "DRY":
        action = ("गेहूं तभी बोएँ जब सिंचाई उपलब्ध हो" if a["crop"] == "Wheat"
                  else f"{crop} अभी बोएँ – {WATER_HI.get(a['crop'], 'यह इस मिट्टी के लिए ठीक है')}")
        why = (f"मिट्टी पिछले वर्षों के {month} के {1-pctl:.0%} दिनों से ज़्यादा सूखी है। ज़्यादा पानी वाली फसलें न चुनें; "
               f"गेहूं को नियमित सिंचाई चाहिए{late}।")
    else:
        action = f"{crop} अभी बोएँ"
        why = f"{month} के हिसाब से मिट्टी की नमी सामान्य है (पिछले {pctl:.0%} दिनों से ज़्यादा गीली){late}।"
    if a.get("goal") == "Keep income" and not a.get("income_safe", True):
        why += (f" {crop_t(last_kharif)} के बाद कोई योजना आज की आय के 5% के भीतर नहीं रहती – "
                "यह सबसे अच्छी कमाई वाला विकल्प है।")
    return action, why

# ------------------------------------------------------------------ sidebar
st.sidebar.title("🌾 PathogenBreak")
st.sidebar.caption(T("Disease-aware crop rotation advisor · Indore, Madhya Pradesh",
                     "रोग-जागरूक फसल-चक्र सलाहकार · इंदौर, मध्य प्रदेश"))
crop_opts = [k for k in E["kharif_candidates"] if k not in E["NO_RABI_AFTER"]]
last_kharif = st.sidebar.selectbox(T("What did you just harvest (Kharif)?", "आपने अभी (खरीफ़ में) क्या काटा?"),
                                   crop_opts, index=crop_opts.index("Soybean"), format_func=crop_t)
GOAL_T = {"Strongest break": T("Strongest break", "रोग की कड़ी तोड़ना"),
          "Keep income": T("Keep income", "आय बनाए रखना")}
goal = st.sidebar.radio(T("What matters most to you?", "आपके लिए सबसे ज़रूरी क्या है?"),
                        ["Strongest break", "Keep income"], format_func=GOAL_T.get,
                        captions=[T("Least disease carried over, saves groundwater",
                                    "सबसे कम रोग आगे जाता है, भूजल की बचत"),
                                  T("Stay within 5% of today's income", "आज की आय के 5% के भीतर रहना")])
pct = st.sidebar.slider(T("Soil moisture from sensor (%)", "सेंसर से मिट्टी की नमी (%)"), 0, 100, 62)
day = pd.Timestamp(st.sidebar.date_input(T("Date", "तारीख़"), pd.Timestamp.now().date()))
st.sidebar.divider()
st.sidebar.caption(T("Sensor demo mode: drag the slider. With the Arduino connected, the notebook (Cell 11) "
                     "reads the real probe over Bluetooth/USB.",
                     "डेमो मोड: स्लाइडर खिसकाएँ। Arduino जुड़ा होने पर नोटबुक (Cell 11) असली सेंसर को "
                     "Bluetooth/USB से पढ़ती है।"))

# ------------------------------------------------------------------ advice
a = E["field_advice"](pct, last_kharif, day=day, goal=goal)

st.title(T("What should I sow now?", "अभी क्या बोएँ?"))
if a is None:
    st.warning(T("No 2-year plan starts with that crop.", "इस फसल से शुरू होने वाली कोई 2-साल की योजना नहीं है।"))
    st.stop()
if a == "closed":
    st.warning(T("All Rabi sowing windows for these plans have closed. Plan for next season.",
                 "इन योजनाओं की रबी बुवाई का समय निकल चुका है। अगले मौसम की योजना बनाएँ।"))
    st.stop()

if HI:
    action_txt, why_txt = hindi_advice(a, last_kharif, day)
    soil_line = (f"मिट्टी: {STATE_HI[a['state']]} · {a['pct']:.0f}% · पिछले 13 वर्षों के {MONTH_HI[day.month-1]} के "
                 f"{a['pctl']:.0%} दिनों से ज़्यादा गीली (NASA)")
else:
    action_txt, why_txt = a["action"], a["why"]
    soil_line = (f"SOIL: {a['state']} · {a['pct']:.0f}% · wetter than {a['pctl']:.0%} of past {day:%B} days "
                 f"(NASA, 13 yrs)")
colour = {"WATERLOGGED": "#9a3b2e", "WET": "#b7791f", "DRY": "#2f6f8f", "NORMAL": "#2f7d4a"}[a["state"]]
left, right = st.columns([2.2, 1])
with left:
    st.markdown(
        f"""<div style="background:{colour};color:white;padding:22px 26px;border-radius:14px">
        <div style="font-size:15px;opacity:.85;letter-spacing:.04em">{soil_line}</div>
        <div style="font-size:34px;font-weight:700;margin:6px 0 10px">{action_txt}</div>
        <div style="font-size:18px;line-height:1.55">{why_txt}</div></div>""",
        unsafe_allow_html=True)
with right:
    st.markdown(T("**Field display (LCD)**", "**खेत का डिस्प्ले (LCD, अंग्रेज़ी में)**"))
    l1, l2 = (f"{line[:16]:<16}".replace(" ", "&nbsp;") for line in a["lcd"])
    st.markdown(
        f"""<div style="background:#2d5c9e;border:12px solid #10151d;border-radius:10px;padding:14px 20px;
        font-family:'Courier New',monospace;font-size:19px;font-weight:700;color:#e4f1ff;line-height:1.3;white-space:nowrap">
        {l1}<br>{l2}</div>""",
        unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric(T("Crop", "फसल"), crop_t(a["crop"])); st.caption(T("2-year plan: ", "2-साल की योजना: ") + plan_t(a["plan"]))
m2.metric(T("Decision", "निर्णय"), DEC_HI.get(a["decision"], a["decision"]) if HI else a["decision"])
m3.metric(T("Income vs today (MSP)", "आज की तुलना में आय (MSP)"), f"{a['income']:+.0%}")
m4.metric(T("Irrigation this Rabi", "इस रबी में सिंचाई"), f"~{a['irr']:.0f} mm")
if a["pilot"] is not None and goal != "Keep income":
    p = a["pilot"]
    if HI:
        st.info(f"**प्रयोग-प्लॉट विकल्प:** {crop_t(p['Sow_Now'])} ({plan_t(p['Rotation_Plan'])}) का स्कोर ज़्यादा है, "
                "पर इंदौर में इसका अनुभव कम है – पहले छोटे खेत में आज़माएँ"
                + (f"; अभी बुवाई {SOWING_HI.get(p['Sowing'], p['Sowing'])} है।" if p["Sowing"] != "timely" else "।"))
    else:
        st.info(f"**Pilot-plot option:** {p['Sow_Now']} ({p['Rotation_Plan']}) scores higher, but Indore has little "
                f"experience with it" + (f"; sowing is {p['Sowing']} now." if p["Sowing"] != "timely" else "."))

# ------------------------------------------------------------------ details
t1, t2, t3, t4, t5 = st.tabs([T("Other plans", "दूसरी योजनाएँ"), T("Three options", "तीन विकल्प"),
                              T("Disease map", "रोग नक्शा"), T("Real-data checks", "असली आँकड़ों से जाँच"),
                              T("Ranking", "रैंकिंग")])
with t1:
    t = a["table"][["Rotation_Plan", "Sow_Now", "Sowing", "Live_Score", "Income_vs_Today", "Decision"]].head(8).copy()
    t["Income_vs_Today"] = t["Income_vs_Today"].map(lambda v: f"{v:+.0%}")
    if HI:
        t["Rotation_Plan"] = t["Rotation_Plan"].map(plan_t); t["Sow_Now"] = t["Sow_Now"].map(crop_t)
        t["Sowing"] = t["Sowing"].map(lambda x: SOWING_HI.get(x, x)); t["Decision"] = t["Decision"].map(DEC_HI)
        t = t.rename(columns={"Rotation_Plan": "योजना", "Sow_Now": "अभी बोएँ", "Sowing": "बुवाई",
                              "Live_Score": "स्कोर", "Income_vs_Today": "आय (आज की तुलना में)", "Decision": "निर्णय"})
    st.dataframe(t.reset_index(drop=True), width="stretch", hide_index=True)
with t2:
    st.markdown(T("Same Indore field, three goals (normal year; net return over cost at 2026-27 MSP and at an "
                  "Indore-area mandi price snapshot):",
                  "इंदौर का वही खेत, तीन लक्ष्य (सामान्य वर्ष; 2026-27 MSP और इंदौर मंडी भाव पर लागत के बाद शुद्ध आय, "
                  "₹/हेक्टेयर, 2 साल):"))
    f = E["farm"].copy()
    if HI:
        f["Option"] = f["Option"].map({"Today": "आज की खेती", "Keep income": "आय बनाए रखना",
                                       "Strongest break": "रोग की कड़ी तोड़ना", "Pilot plot": "प्रयोग-प्लॉट"})
        f["Rotation"] = f["Rotation"].map(plan_t)
        f = f.rename(columns={"Option": "विकल्प", "Rotation": "फसल-चक्र", "Score": "स्कोर",
                              "Disease_vs_Today": "रोग (आज से)", "Irrigation_mm": "सिंचाई (mm)",
                              "Income_Rs_2yr": "आय MSP (₹)", "Income_vs_Today": "आय MSP (आज से)",
                              "Mandi_Income_Rs_2yr": "आय मंडी (₹)", "Mandi_vs_Today": "आय मंडी (आज से)"})
    st.dataframe(f, width="stretch", hide_index=True)
    st.caption(T("Disease = carry-over penalty vs Soybean→Wheat every year. Water = irrigation over two Rabi seasons.",
                 "रोग = हर साल सोयाबीन→गेहूं की तुलना में आगे जाने वाला रोग। पानी = दो रबी मौसमों की सिंचाई।"))
with t3:
    st.image("pathogen_heatmap.png", caption=T("Share of the next crop's disease load already hosted by the previous crop",
                                               "अगली फसल के रोगों का वह हिस्सा जो पिछली फसल पहले से रखती है"))
with t4:
    st.image("validation.png")
    st.image("rotation_evidence.png", caption=T("55 MP districts, 2013-2025: more repetition goes with slightly lower "
                                                "yields - right direction, not statistically significant. Field trial needed.",
                                                "मध्य प्रदेश के 55 ज़िले, 2013-2025: एक ही फसल दोहराने पर उपज थोड़ी कम दिखती है – "
                                                "दिशा सही है, पर सांख्यिकीय रूप से पक्का नहीं। खेत-परीक्षण ज़रूरी है।"))
with t5:
    st.image("dashboard.png")

st.caption(T("", "सलाह के पाठ हिंदी में अनुवादित हैं; किसी हिंदी-भाषी कृषि विशेषज्ञ से जाँच करवाना बेहतर रहेगा।"))
st.caption("Data: NASA POWER, GPM IMERG, MODIS MOD13A3, SoilGrids, UPAg (Govt. of India), USDA Fungus-Host, "
           "PHI-base v5.7, MSP 2026-27 (Govt. of India). Sowing windows and field actions are rule-based general "
           "advice for central India; the disease carry-over effect needs field trials.")
