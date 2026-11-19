# MenCare AI — Streamlit Prototype

**MenCare AI: An Explainable AI-Based Early Risk Screening and Referral System for Male Reproductive Health**

A **working, interactive, English-language research demonstration** designed for a digital health innovation challenge. It uses a transparent fuzzy *factor-pattern* demonstration and a separate safety-first referral ruleset. **This is not a diagnostic model, clinical screening instrument, or medical device.**

## Features that are implemented

- Professional landing page and English navigation
- Two-stage intake, followed by a results screen
- Adaptive optional questions based on the user's reproductive-health goal
- Conservative safety-first flag for sudden, severe testicular pain
- Referral guidance for persistent symptoms, possible testicular lump/swelling, fertility concerns, and cancer-treatment history
- Transparent fuzzy activations indicating **reported factors**, not infertility probability
- Explicit representation of unknown and unasked information
- In-session next-step tracking (no external appointment booking)
- Identifier-free downloadable text summary
- Four synthetic scenarios for live demonstrations
- No intentional database or file storage of submitted health information
- Automated unit tests for risk logic

## Run locally

Requires **Python 3.10+**.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit (typically `http://localhost:8501`).

## Deploy to Streamlit Community Cloud

1. Create an **empty GitHub repository**, e.g. `mencare-ai`.
2. Upload **all files** from this project into the repository. Keep `streamlit_app.py`, `risk_engine.py`, and `requirements.txt` at the repository root, including the `.streamlit/config.toml` subfolder.
3. Visit [Streamlit Community Cloud](https://share.streamlit.io/), sign in and select **Create app / Deploy app**.
4. Choose the GitHub repository and branch; set **Main file path** to `streamlit_app.py`.
5. Deploy. Once published, use the **actual generated URL** in the competition's `Prototype / Deployment Link` field.
6. Open the link in a private/incognito browser window and test all four demo scenarios.

Official documentation: [Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

**Important:** Do **not** submit a guessed `*.streamlit.app` URL. The actual public URL exists only after successful deployment. Streamlit Community Cloud is appropriate for a **synthetic-data demonstration only** without further data-protection and governance work.

## Test the logic

```bash
python -m unittest discover -s tests -v
```

## Judge demonstration (about 3 minutes)

1. Open **Overview**, explain the screening-to-care value proposition.
2. Open **Start screening**, show step 1 and the tailored second stage.
3. Load **Case B**: fertility concern and lifestyle factors. Show explainability and suggested specialist discussion.
4. Load **Case C**: demonstrate the emergency override **independent of fuzzy factor load**.
5. Load **Case D**: demonstrate oncofertility referral conversation.
6. Mark steps in the session-only checklist and download the educational summary.

## Architecture and novelty

```text
User → Goal + safety intake → Tailored factor questions
             ↓
    [Safety referral rules]  <-- highest priority
             ↓
    [Illustrative fuzzy factor activation]
             ↓
    Explanations + missing-data notice
             ↓
    Suggested next actions + session follow-up tracker
```

`risk_engine.py` contains all auditable logic. Unknown or unasked values are not treated as negatives. Referral logic is a set of prototype recommendations, not a validated clinical triage tool. In particular, the fuzzy scores **do not estimate infertility**; their engineering weights were chosen only to demonstrate interpretable fuzzy membership functions.

## Clinical and privacy constraints

- Never rely on this app to diagnose disease or decide that a person is fertile/infertile.
- Sudden severe testicular pain may require emergency care regardless of the questionnaire.
- The code stores answers in ephemeral Streamlit session state, not a database. However, the hosting server processes entries, and hosting providers may retain infrastructure logs. **Do not enter real patient data in the publicly deployed demo.**
- No clinic booking, clinical integration, patient record processing, automated tracking, Arabic localization, or trained MRI/ML model is implemented.
- Clinical content and scoring must be reviewed and prospectively validated before deployment for genuine patient care.

### Informational sources (not a validation of the score)

- [WHO: Infertility](https://www.who.int/news-room/fact-sheets/detail/infertility)
- [AUA/ASRM: Male Infertility Guideline](https://www.auanet.org/guidelines-and-quality/guidelines/male-infertility)
- [EAU: Male Infertility](https://uroweb.org/guidelines/sexual-and-reproductive-health/chapter/male-infertility)
- [NHS: Testicle pain](https://www.nhs.uk/symptoms/testicle-pain/)

## Files

```text
MenCare_AI_Streamlit_Prototype/
├── .streamlit/
│   └── config.toml             # App theme and server settings
├── tests/
│   └── test_risk_engine.py     # Unit tests for the risk engine
├── streamlit_app.py            # Streamlit frontend
├── risk_engine.py              # Explainable fuzzy demonstration and routing
├── requirements.txt            # Runtime dependencies
├── README.md                   # Project documentation
└── DEPLOYMENT_GUIDE_ID.md      # Deployment guide in Bahasa Indonesia
```

## For challenge submission

**What has been built?**

> We built a working English-language MenCare AI demonstration with adaptive questionnaire flow, transparent fuzzy factor activation, safety-first referral guidance, four synthetic test scenarios, follow-up checklist and downloadable summaries. The current prototype uses interpretable demonstration rules rather than a trained or clinically validated risk model. No live healthcare integration or patient data collection is claimed.

**Prototype link:** Paste your actual deployed `https://<your-app>.streamlit.app` address once verified live.
