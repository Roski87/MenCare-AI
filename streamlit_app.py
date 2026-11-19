"""MenCare AI | Streamlit working demonstration for innovation judges.

Run: streamlit run streamlit_app.py
Not a medical device, clinical predictor, or connected referral service.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import streamlit as st

from risk_engine import FACTOR_DEFINITIONS, NO, UNKNOWN, YES, REFERENCES, evaluate

st.set_page_config(
    page_title="MenCare AI | Men's Reproductive Health",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
    .stApp {background: #F7FAFC;}
    .block-container {padding-top: 2rem; padding-bottom: 3.5rem; max-width: 1160px;}
    h1,h2,h3 {color: #183047; letter-spacing: -.025em;}
    [data-testid="stSidebar"] {background: #EAF3F4; border-right: 1px solid #D8E6E9;}
    [data-testid="stSidebar"] h2 {color: #144E56;}
    .hero {padding: 2.4rem 2.6rem; border-radius: 25px; color: #fff;
       background: linear-gradient(120deg,#123E50 0%,#126A71 55%,#27A28E 100%);
       box-shadow: 0 12px 35px rgba(11,55,68,.13); margin-bottom: 1.2rem;}
    .hero .eyebrow {text-transform: uppercase; letter-spacing:.19em; font-weight:700;
       font-size:.77rem; color:#BEF2E6; margin-bottom:.65rem;}
    .hero h1 {color:white; font-size:clamp(2.3rem,5vw,3.65rem); font-weight:800; margin:0 0 .55rem;}
    .hero p {color:#E2F6F4; font-size:1.08rem; max-width:780px; margin-bottom:1.2rem;}
    .hero .pill {display:inline-block; margin:.2rem .5rem .2rem 0;
      border-radius:30px; padding:.35rem .8rem; border:1px solid #77CFC2;
      font-size:.8rem; color:#F1FFFD; background:#ffffff19;}
    .soft-card {background:#fff; padding:1.25rem 1.35rem; border:1px solid #E2EBED;
      border-radius:18px; margin-bottom:.65rem; min-height:146px;}
    .soft-card h4 {margin:.2rem 0 .55rem; font-size:1.09rem; color:#17565F;}
    .soft-card p {color:#506573; margin:.15rem 0; font-size:.95rem;}
    .step-badge {display:inline-block; font-weight:700; color:#0D776E; background:#DBF3EE;
      padding:.25rem .65rem; border-radius:30px; font-size:.78rem; margin-bottom:.65rem;}
    .section-kicker {text-transform:uppercase; font-size:.75rem; font-weight:800;
       letter-spacing:.13em; color:#198076; margin-top:.5rem;}
    .result-heading {border-radius:16px; padding:1.25rem 1.5rem; margin:.8rem 0 1.2rem;
       border:1px solid #DAE6E7; background:white;}
    .result-heading h3 {margin:0 0 .4rem;}
    .result-heading p {color:#465D6A; margin:.2rem 0 0;}
    .tiny-note {font-size:.83rem; color:#697D87;}
    div[data-testid="stMetric"] {background:#FFFFFF; border:1px solid #E1EAEB;
      padding:.9rem 1rem; border-radius:15px;}
    [data-testid="stAlert"] {border-radius:14px;}
    div.stButton > button[kind="primary"] {background:#166E70;border-color:#166E70;color:white;}
    div.stButton > button {border-radius:11px; font-weight:650;}
    a {color:#137D79;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PAGES = ["Overview", "Start screening", "My results", "How it works", "Evidence & safety"]

def get_state() -> None:
    defaults = {"nav": PAGES[0], "step": 1, "answers": {}, "result": None,
                "referral_ack": False, "referral_planned": False, "referral_contacted": False}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "pending_nav" in st.session_state:
        st.session_state.nav = st.session_state.pop("pending_nav")


def route(page: str) -> None:
    # Updating nav before its widget is created avoids Streamlit widget-state conflicts.
    st.session_state.pending_nav = page
    st.rerun()


def start_fresh() -> None:
    # Remove prior widget answers so a new participant never inherits selections.
    for key in list(st.session_state.keys()):
        if key.startswith("f_"):
            del st.session_state[key]
    for key in ("answers", "result", "referral_ack", "referral_planned", "referral_contacted"):
        if key in ("answers", "result"):
            st.session_state[key] = {} if key == "answers" else None
        else:
            st.session_state[key] = False
    st.session_state.step = 1
    route("Start screening")


DEMO_CASES = {
    "A · Preventive check (few factors)": {
        "age_band": "30–39", "goal": "Preventive health check",
        "trying_duration": "Not trying / not applicable",
        "sudden_pain": NO, "lump": NO, "fever_urinary": NO,
        "smoking": NO, "metabolic": NO, "surgery": NO,
        "abnormal_semen": NO, "exposure": NO,
        "persistent_symptoms": NO, "cancer_treatment": NO,
    },
    "B · Fertility assessment recommended": {
        "age_band": "30–39", "goal": "Trying to conceive",
        "trying_duration": "12 months or longer",
        "sudden_pain": NO, "lump": NO, "fever_urinary": NO,
        "smoking": YES, "metabolic": NO, "surgery": NO,
        "abnormal_semen": YES, "exposure": UNKNOWN,
        "persistent_symptoms": NO, "cancer_treatment": NO,
    },
    "C · Emergency symptom override": {
        "age_band": "18–29", "goal": "Symptoms or reproductive health concerns",
        "trying_duration": "Not trying / not applicable",
        "sudden_pain": YES, "lump": NO, "fever_urinary": NO,
        "smoking": NO, "metabolic": NO, "surgery": NO,
        "abnormal_semen": NO, "exposure": NO,
        "persistent_symptoms": NO, "cancer_treatment": NO,
    },
    "D · Oncofertility conversation": {
        "age_band": "40–49", "goal": "Cancer treatment and fertility planning",
        "trying_duration": "Not trying / not applicable",
        "sudden_pain": NO, "lump": NO, "fever_urinary": NO,
        "smoking": NO, "metabolic": UNKNOWN, "surgery": NO,
        "abnormal_semen": UNKNOWN, "exposure": UNKNOWN,
        "persistent_symptoms": NO, "cancer_treatment": YES,
    },
}


def load_demo(name: str) -> None:
    st.session_state.answers = DEMO_CASES[name].copy()
    st.session_state.result = evaluate(st.session_state.answers).as_dict()
    st.session_state.step = 3
    st.session_state.referral_ack = False
    st.session_state.referral_planned = False
    st.session_state.referral_contacted = False
    route("My results")


def page_heading(kicker: str, title: str, description: str) -> None:
    st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.write(description)


def feature_card(title: str, description: str, symbol: str) -> None:
    st.markdown(
        f'<div class="soft-card"><div style="font-size:1.55rem">{symbol}</div>'
        f'<h4>{title}</h4><p>{description}</p></div>', unsafe_allow_html=True
    )


def select_yn(label: str, key: str, *, help_text: str | None = None) -> str:
    return st.selectbox(label, [NO, YES, UNKNOWN], index=2, key=key, help=help_text)


def report_text(result: dict, answers: dict) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "MENCARE AI | PROTOTYPE SCREENING SUMMARY", "=" * 49,
        f"Generated: {generated}",
        "Status: DEMONSTRATION / NOT CLINICALLY VALIDATED",
        "No name, email, address, or patient identifier included.", "",
        "RECOMMENDED PATHWAY", result["referral_title"], result["referral_message"], "",
        "SUGGESTED ACTIONS",
    ]
    lines.extend(f"- {a}" for a in result["action_items"])
    lines.extend(["", "SELF-REPORTED FACTORS"])
    lines.extend(f"- {a}" for a in (result["explanations"] or ["No contributing factors reported."]))
    lines.extend(["", "KNOWLEDGE GAPS"])
    lines.extend(f"- {a}" for a in (result["missing_items"] or ["None reported."]))
    lines.extend(["", "ENGINEERING DEMONSTRATION (NOT A MEDICAL RISK ESTIMATE)"])
    lines.extend(f"- {k}: {v:.2f} fuzzy activation" for k,v in result["fuzzy_memberships"].items())
    lines.extend(["", "SAFETY NOTICES"])
    lines.extend(f"- {n}" for n in result["safety_notices"])
    lines.extend(["", "Educational references:"])
    lines.extend(f"- {r['name']}: {r['url']}" for r in REFERENCES)
    return "\n".join(lines)


get_state()
with st.sidebar:
    st.markdown("## 🩺 MenCare AI")
    st.caption("Explainable reproductive health navigator")
    st.markdown("---")
    st.radio("Navigation", PAGES, key="nav", label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Try an interactive demo**")
    selected_case = st.selectbox("Simulated patient scenario", list(DEMO_CASES), key="demo_case")
    if st.button("Load demo case", use_container_width=True):
        load_demo(selected_case)
    if st.button("Clear session & restart", use_container_width=True):
        start_fresh()
    st.markdown("---")
    st.caption("Research prototype · English interface")
    st.caption("Demonstration only. Never use for diagnosis or emergencies.")

nav = st.session_state.nav

if nav == "Overview":
    st.markdown(
        """<div class="hero">
        <div class="eyebrow">Digital Health Innovation Challenge · Abu Dhabi</div>
        <h1>MenCare AI</h1>
        <p>See the signal. Understand the uncertainty. Take the next step.
        An explainable, privacy-conscious screening-to-care prototype for men's reproductive health.</p>
        <span class="pill">Adaptive assessment</span>
        <span class="pill">Fuzzy explainability</span>
        <span class="pill">Safety-first navigation</span>
        </div>""", unsafe_allow_html=True
    )
    st.info("**Prototype disclaimer:** Educational demonstration using illustrative, non-validated rules. No diagnosis, fertility probability, or real hospital booking.")
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.subheader("From late diagnosis to earlier conversations")
        st.write(
            "Many men seek reproductive healthcare only after prolonged difficulty conceiving. "
            "MenCare AI demonstrates a lower-friction entry point: a private, short assessment "
            "that explains reported factors and proposes the next healthcare conversation."
        )
        if st.button("Begin private screening  →", type="primary", use_container_width=True):
            start_fresh()
    with right:
        st.markdown(
            '<div class="soft-card"><h4>What you can test today</h4>'
            '<p>01 — Answer a two-stage assessment</p>'
            '<p>02 — Receive an explainable factor-pattern summary</p>'
            '<p>03 — See safety-first referral guidance</p>'
            '<p>04 — Track next steps within your session</p>'
            '<p>05 — Export an identifier-free summary</p></div>',
            unsafe_allow_html=True,
        )
    st.markdown("### Why this approach is different")
    a,b,c = st.columns(3, gap="medium")
    with a:
        feature_card("Explainable by design", "Reported factors and missing information stay visible; no opaque infertility percentage.", "🧠")
    with b:
        feature_card("Safety comes first", "Urgent symptoms override the fuzzy demonstration. Referral rules are separate from factor patterns.", "🛡️")
    with c:
        feature_card("Actionable next step", "Educational guidance, suggested clinical conversations, and session-only follow-up tracking.", "🧭")
    st.markdown("### Experience the prototype")
    st.write("Use **Start screening** or load any simulated case in the sidebar. No account, login, or personal identifier is required.")

elif nav == "Start screening":
    page_heading("Step-by-step assessment", "Private reproductive health screening",
                 "For adults aged 18+. Please use simulated information when testing a public deployment.")
    st.warning("If you have **sudden, severe testicular pain**, seek emergency medical care now rather than completing this form.")
    step = st.session_state.step
    st.progress(0.33 if step == 1 else 0.66 if step == 2 else 1.0, text=f"Step {step} of 3")

    if step == 1:
        st.markdown('<span class="step-badge">01 · Goals and urgent symptoms</span>', unsafe_allow_html=True)
        st.write("The questions below identify the purpose of your visit and any symptoms that should bypass ordinary screening.")
        with st.form("intake_form"):
            left,right = st.columns(2)
            with left:
                age_band = st.selectbox("Age range (adults only)", ["18–29", "30–39", "40–49", "50+"], index=None,
                                        placeholder="Choose an age range")
                goal = st.selectbox("Primary reason for checking in", [
                    "Preventive health check", "Planning pregnancy", "Trying to conceive",
                    "Symptoms or reproductive health concerns", "Cancer treatment and fertility planning",
                    "Prefer not to say"], index=None, placeholder="Choose a goal")
                trying_duration = st.selectbox("If trying to conceive, for how long?", [
                    "Not trying / not applicable", "Less than 6 months", "6–11 months",
                    "12 months or longer", "Not sure / prefer not to say"],
                    index=None, placeholder="Select the best answer")
            with right:
                sudden_pain = st.selectbox("Do you currently have sudden, severe testicular pain?", [NO, YES, UNKNOWN],
                                           index=None, placeholder="Choose an answer")
                lump = st.selectbox("Have you noticed a testicular lump or persistent swelling?", [NO, YES, UNKNOWN],
                                     index=None, placeholder="Choose an answer")
                fever_urinary = st.selectbox("Do you have fever with painful urination or genital symptoms?", [NO, YES, UNKNOWN],
                                             index=None, placeholder="Choose an answer")
            st.caption("You may choose 'Not sure / prefer not to say' for sensitive symptom questions.")
            submitted = st.form_submit_button("Continue to tailored questions  →", type="primary", use_container_width=True)
        if submitted:
            items = [age_band, goal, trying_duration, sudden_pain, lump, fever_urinary]
            if any(v is None for v in items):
                st.error("Please choose an answer for each field. 'Not sure' is available if needed.")
            else:
                st.session_state.answers = dict(age_band=age_band, goal=goal,
                    trying_duration=trying_duration, sudden_pain=sudden_pain,
                    lump=lump, fever_urinary=fever_urinary)
                if sudden_pain == YES:
                    st.session_state.answers.update({k: UNKNOWN for k in FACTOR_DEFINITIONS})
                    st.session_state.result = evaluate(st.session_state.answers).as_dict()
                    st.session_state.step = 3
                    route("My results")
                else:
                    st.session_state.step = 2
                    st.rerun()
    elif step == 2:
        st.markdown('<span class="step-badge">02 · Adaptive risk-factor questions</span>', unsafe_allow_html=True)
        a = st.session_state.answers
        goal = a.get("goal", "")
        st.write(f"**Assessment pathway:** {goal}")
        if goal == "Cancer treatment and fertility planning":
            st.info("Oncofertility pathway: consider asking your oncology team about fertility preservation before planned treatment.")
        elif goal == "Trying to conceive":
            st.info("Fertility planning pathway: a clinician can discuss history, examination, and semen analysis where appropriate.")
        elif goal == "Symptoms or reproductive health concerns":
            st.info("Symptom pathway: this questionnaire cannot identify the cause of pain, swelling, or other symptoms.")
        else:
            st.info("Prevention pathway: lifestyle context and known medical history can guide a conversation with a clinician.")

        with st.form("factors_form"):
            st.markdown("#### Core questions")
            left,right = st.columns(2)
            with left:
                smoking = select_yn("Do you currently smoke or use nicotine?", "f_smoking")
                metabolic = select_yn("Do you have a metabolic or long-term health condition?", "f_metabolic",
                                      help_text="Examples: diabetes and some other chronic conditions.")
                abnormal_semen = select_yn("Have you had an abnormal semen test or fertility concern?", "f_semen")
            with right:
                surgery = select_yn("Have you had testicular injury or reproductive surgery?", "f_surgery")
                cancer_treatment = select_yn("Have you undergone, or are you planning, cancer treatment?", "f_cancer",
                    help_text="Some cancer treatments may affect fertility; ask your treating team about individual implications.")

            st.markdown("#### Tailored optional questions")
            if goal in ("Trying to conceive", "Planning pregnancy", "Preventive health check"):
                exposure = select_yn("Possible occupational chemical or prolonged heat exposure?", "f_exposure")
                persistent_symptoms = select_yn("Any persistent reproductive or urinary symptoms?", "f_symptoms")
            elif goal == "Symptoms or reproductive health concerns":
                persistent_symptoms = select_yn("Are you experiencing persistent reproductive or urinary symptoms?", "f_symptoms")
                exposure = UNKNOWN
            elif goal == "Cancer treatment and fertility planning":
                persistent_symptoms = select_yn("Any persistent reproductive or urinary symptoms?", "f_symptoms")
                exposure = UNKNOWN
            else:
                st.caption("Additional questions are intentionally minimized for this preference. Unasked fields remain unknown.")
                persistent_symptoms = UNKNOWN
                exposure = UNKNOWN
            st.caption("Unknown answers remain unknown; they are not interpreted as 'No'. No names or personal identifiers are collected.")
            submit = st.form_submit_button("Generate explainable pathway  →", type="primary", use_container_width=True)
        if st.button("← Back to step 1"):
            st.session_state.step = 1
            st.rerun()
        if submit:
            a.update({
                "smoking": smoking, "metabolic": metabolic, "abnormal_semen": abnormal_semen,
                "surgery": surgery, "cancer_treatment": cancer_treatment,
                "exposure": exposure, "persistent_symptoms": persistent_symptoms,
            })
            st.session_state.answers = a
            st.session_state.result = evaluate(a).as_dict()
            st.session_state.step = 3
            st.session_state.referral_ack = False
            st.session_state.referral_planned = False
            st.session_state.referral_contacted = False
            route("My results")
    else:
        st.success("The assessment is complete. Your results are ready.")
        if st.button("View results", type="primary"):
            route("My results")

elif nav == "My results":
    result = st.session_state.result
    page_heading("Your assessment", "Explainable results & next steps",
                 "A demonstration of referral navigation based on your answers—not a fertility diagnosis or validated risk prediction.")
    if not result:
        st.info("No screening result yet. Start an assessment or load one of the sample cases in the sidebar.")
        if st.button("Start screening", type="primary"):
            start_fresh()
    else:
        if result["referral_key"] == "emergency":
            st.error("**TIME-CRITICAL SYMPTOM FLAG** — Seek emergency care immediately. Do not rely on this app for emergency decisions.")
        elif result["referral_key"] == "prompt":
            st.warning("**IN-PERSON ASSESSMENT FLAG** — Please arrange prompt professional medical care.")
        else:
            st.info("**Personalized next-step pathway** — Based on rule-based self-reported information, not a clinical test.")
        st.markdown(f'<div class="result-heading"><h3>{result["referral_title"]}</h3>'
                    f'<p>{result["referral_message"]}</p></div>', unsafe_allow_html=True)

        k1,k2,k3 = st.columns(3, gap="small")
        with k1:
            st.metric("Factors reported", f"{result['factors_reported']} / {result['factors_asked']}")
        with k2:
            st.metric("Knowledge gaps", result["uncertain_answers"])
        with k3:
            st.metric("Referral path", {
                "emergency": "Emergency", "prompt": "Prompt review", "specialist": "Specialist",
                "routine": "Routine visit", "educate": "Prevention"
            }.get(result["referral_key"], "Review"))

        st.markdown("### Your recommended next steps")
        for idx, item in enumerate(result["action_items"], start=1):
            st.markdown(f"**{idx}.** {item}")

        st.markdown("### Explainable factor review")
        left, right = st.columns([1.1,1], gap="large")
        with left:
            st.markdown("**Factors you reported**")
            if result["explanations"]:
                for factor in result["explanations"]:
                    st.markdown(f"- {factor}")
            else:
                st.write("No contributing factor was reported. This is not a medical clearance.")
        with right:
            st.markdown("**Unanswered / unasked information**")
            if result["missing_items"]:
                for item in result["missing_items"]:
                    st.markdown(f"- {item}")
            else:
                st.write("No knowledge gaps flagged in this demonstration.")

        with st.expander("See the fuzzy reasoning (engineering demonstration)", expanded=True):
            st.write("These degrees describe overlapping **reported-factor patterns only**. "
                     "They are **not infertility probabilities, diagnostic confidence, or clinically validated risk scores**.")
            for label, value in result["fuzzy_memberships"].items():
                st.progress(float(value), text=f"{label}: {value:.2f} activation")
            st.caption(f"Illustrative weighted factor load = {result['factor_load']:.2f}. "
                       "Weights and fuzzy membership shapes are prototype assumptions, not clinical estimates.")
            st.caption("Safety rule priority: emergency flag → prompt assessment flag → fertility history → "
                       "persistent symptoms → general education. The fuzzy model never suppresses safety flags.")

        st.markdown("### Personalized preventive guidance")
        for action in result["supportive_actions"]:
            st.markdown(f"- {action}")

        st.markdown("### Referral journey · session-only demo")
        st.caption("Mark milestones to demonstrate the closed-loop experience. "
                   "This prototype does **not** contact, book, or verify any clinic appointments.")
        st.checkbox("I reviewed my suggested next steps", key="referral_ack")
        st.checkbox("I plan to discuss my results with a healthcare professional", key="referral_planned")
        st.checkbox("I contacted a healthcare professional (self-reported)", key="referral_contacted")
        completed = sum(bool(st.session_state[k]) for k in
                        ["referral_ack", "referral_planned", "referral_contacted"])
        st.progress(completed/3, text=f"Session follow-up checklist: {completed} of 3 marked")

        st.markdown("### Export summary")
        st.write("Download an **identifier-free** educational summary. It describes reported factors; "
                 "only download to a device you control.")
        txt = report_text(result, st.session_state.answers)
        st.download_button("⬇ Download assessment summary (.txt)", data=txt,
                           file_name="mencare_ai_demo_summary.txt", mime="text/plain", type="primary")
        colx,coly = st.columns(2)
        with colx:
            if st.button("Start a new assessment", use_container_width=True):
                start_fresh()
        with coly:
            if st.button("Review how the model works", use_container_width=True):
                route("How it works")
        st.warning("This prototype does not establish fertility status or replace medical examination. "
                   "For symptoms or fertility concerns, see a qualified clinician.")

elif nav == "How it works":
    page_heading("Architecture & novelty", "How MenCare AI works",
                 "A transparent, modular research prototype with explainable rules and an auditable safety pathway.")
    st.markdown("### Four-stage screening-to-care pipeline")
    columns = st.columns(4, gap="small")
    steps = [
        ("01 · Intake", "Goal, planning context, emergency symptom check", "📝"),
        ("02 · Adaptive", "Questions tailored to reproductive goals", "🎯"),
        ("03 · Explain", "Fuzzy factor activation + missing-information report", "🧠"),
        ("04 · Navigate", "Safety-first action advice + referral checklist", "🧭"),
    ]
    for col,(title,description,symbol) in zip(columns,steps):
        with col:
            feature_card(title, description, symbol)

    st.markdown("### Two separate decision layers")
    col_a,col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown("**Layer A · Safety-first clinical routing (demonstration)**")
        st.markdown("""
        1. Sudden, severe testicular pain → emergency assessment.
        2. Lump/swelling or fever with genital/urinary symptoms → prompt in-person review.
        3. Prolonged infertility concern, abnormal semen history, cancer treatment or surgery → fertility discussion.
        4. Persistent symptoms → routine clinical review.
        5. No trigger reported → preventive health discussion, **not a diagnosis**.
        """)
    with col_b:
        st.markdown("**Layer B · Interpretability of self-reported patterns**")
        st.write("Each reported factor activates an illustrative weight. Overlapping fuzzy functions describe "
                 "few, some, or multiple reported factors. Unknown answers are flagged, not treated as negative. "
                 "These patterns never replace Layer A or estimate the probability of infertility.")
        st.code("""factor_load = sum(weight for each reported factor)
activation = {
    'few': decreasing_membership(factor_load),
    'some': triangular_membership(factor_load),
    'multiple': increasing_membership(factor_load)
}
# NOT a clinical risk probability
# Emergency routing always overrides activation""", language="python")

    st.markdown("### Research roadmap to a real-world product")
    st.markdown("""
    - **Phase 1 — This demo:** Stable UI, rule traceability, explainability, simulated case walkthroughs.
    - **Phase 2 — Expert review:** Multidisciplinary review of questionnaire, safety flags, thresholds, referral wording, and cultural adaptation.
    - **Phase 3 — Evaluation:** Usability, missing-data robustness, accessibility, fairness, and agreement with expert triage on representative cases.
    - **Phase 4 — Clinical integration:** Only after ethics approval and suitable governance, validate with clinical data, perform security reviews, and integrate authorized appointment/referral services.
    """)
    st.markdown("### What is NOT implemented")
    st.write("No trained ML model, MRI analysis, medical-device certification, hospital booking, "
             "electronic health record integration, secure patient account, Arabic localization, "
             "or real-world clinical validation. These are future development items, not claimed features.")

elif nav == "Evidence & safety":
    page_heading("Clinical boundaries", "Evidence, privacy & responsible AI",
                 "Medical sources inform the selection of topics and safety notices. They do not validate this prototype's arbitrary fuzzy weights.")
    st.error("**Emergency reminder:** Sudden, severe testicular pain requires emergency medical assessment. "
             "Do not use this demonstration to delay care.")
    st.markdown("### Educational and clinical references")
    for ref in REFERENCES:
        st.markdown(f"- [{ref['name']}]({ref['url']})")
    st.markdown("### Privacy approach for the demonstration")
    st.markdown("""
    - No user account, name, email address, location, or medical record identifier is requested.
    - The code does not write screening answers to a database or local file.
    - Session answers and results are held in Streamlit session memory until cleared / disconnected.
    - Information is still processed by the hosting server. Deployment operators may have logs, telemetry or platform-level access. **This is not a privacy certification.**
    - **Do not use real patient information on a public Streamlit demo.** Use the built-in simulated cases.
    - The export is initiated by the user and contains educational result details, not an identity.
    """)
    st.markdown("### Medical and scientific limitations")
    st.markdown("""
    - No diagnostic, predictive, sensitivity, specificity, accuracy, or external validation claims are made.
    - Questions and fuzzy weights are not established clinical guidelines or validated scoring instruments.
    - Infertility and cancer risk **cannot** be determined from this questionnaire.
    - Prostate MRI / Mask R-CNN cancer detection is **not** used to infer fertility.
    - A trained clinical team must review the content, safety wording, data governance, and triage before use with real people.
    """)
    st.markdown("### Responsible deployment checklist")
    for item in [
        "Use synthetic/simulated cases for public demonstrations.",
        "Require human clinical oversight before real screening or referrals.",
        "Complete privacy impact and information-security assessment for real patient data.",
        "Conduct local clinical, cultural, accessibility, and language validation.",
        "Evaluate triage performance and failure modes across diverse user groups.",
    ]:
        st.markdown(f"- {item}")

st.markdown("---")
st.caption("MenCare AI © Research prototype | Developed for a health innovation demonstration | "
           "Educational information only · No clinical validation · No real referral service")
