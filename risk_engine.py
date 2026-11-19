"""MenCare AI demonstration rule engine.

All weights and membership functions are illustrative engineering choices.
They are NOT derived from / validated against clinical outcome data and
must NOT be presented as clinical risk probabilities or diagnostic scores.
Safety/referral rules take priority over fuzzy presentation.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Mapping, Any

YES = "Yes"
NO = "No"
UNKNOWN = "Not sure / prefer not to say"

FACTOR_DEFINITIONS = {
    "smoking": ("Smoking or nicotine use", 1.0,
                "Discuss smoking cessation support with a qualified clinician."),
    "metabolic": ("Existing metabolic or long-term health condition", 0.8,
                  "Review your existing health conditions and medications with your doctor."),
    "surgery": ("Previous testicular injury or reproductive surgery", 1.1,
                 "A reproductive health specialist can assess whether prior injury or surgery is relevant."),
    "abnormal_semen": ("Previous abnormal semen analysis or known fertility concern", 1.5,
                       "Consider a reproductive specialist consultation; semen test results need clinical interpretation."),
    "exposure": ("Possible reproductive workplace or heat exposure", 0.6,
                 "Ask a clinician about relevant occupational or environmental exposures."),
    "persistent_symptoms": ("Persistent reproductive or urinary symptoms", 1.1,
                            "Arrange an in-person medical assessment for persistent symptoms."),
    "cancer_treatment": ("Past or planned cancer treatment", 1.4,
                         "Discuss reproductive goals and fertility-preservation options with your oncology team."),
}

REFERENCES = [
    {"name": "WHO – Infertility fact sheet", "url": "https://www.who.int/news-room/fact-sheets/detail/infertility"},
    {"name": "AUA/ASRM – Male Infertility Guideline", "url": "https://www.auanet.org/guidelines-and-quality/guidelines/male-infertility"},
    {"name": "EAU – Male Infertility Guidelines", "url": "https://uroweb.org/guidelines/sexual-and-reproductive-health/chapter/male-infertility"},
    {"name": "NHS – Testicle pain", "url": "https://www.nhs.uk/symptoms/testicle-pain/"},
]


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def triangular(value: float, left: float, peak: float, right: float) -> float:
    """Simple triangular fuzzy activation; no clinical calibration."""
    if left >= peak or peak >= right:
        raise ValueError("Expected left < peak < right")
    if value <= left or value >= right:
        return 0.0
    if value == peak:
        return 1.0
    return clamp((value-left)/(peak-left) if value < peak else (right-value)/(right-peak))


def fuzzy_activation(factor_load: float) -> Dict[str, float]:
    """Interpretable overlapping descriptions of reported factor *load*.

    This is not a probability of infertility and not a medically validated scale.
    """
    return {
        "Few reported factors": clamp((3.0 - factor_load) / 3.0),
        "Some reported factors": triangular(factor_load, 0.5, 2.6, 5.2),
        "Multiple reported factors": clamp((factor_load - 2.8) / 3.0),
    }


@dataclass
class ScreeningResult:
    referral_key: str
    referral_title: str
    referral_message: str
    action_items: List[str]
    explanations: List[str]
    supportive_actions: List[str]
    missing_items: List[str]
    factors_reported: int
    factors_asked: int
    factor_load: float
    fuzzy_memberships: Dict[str, float]
    dominant_description: str
    uncertain_answers: int
    emergency: bool
    safety_notices: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate(answers: Mapping[str, str]) -> ScreeningResult:
    """Return conservative, deterministic *demonstration* routing.

    - Treat unknown as unknown, never as absent.
    - Emergency flags are checked independently of factor count.
    - Recommendations are for clinician discussion, not diagnostic advice.
    """
    explanations: List[str] = []
    supportive: List[str] = []
    unknown: List[str] = []
    total_load = 0.0
    count_yes = 0

    for field, (label, weight, action) in FACTOR_DEFINITIONS.items():
        value = answers.get(field, UNKNOWN)
        if value == YES:
            explanations.append(label)
            supportive.append(action)
            total_load += weight
            count_yes += 1
        elif value != NO:
            unknown.append(label)

    trying = answers.get("trying_duration", "Not trying / not applicable")
    if trying == "12 months or longer":
        explanations.append("Reported 12 or more months of trying to conceive without success")
    elif trying == "Not sure / prefer not to say":
        unknown.append("Duration of trying to conceive")

    sudden_pain = answers.get("sudden_pain", UNKNOWN)
    lump = answers.get("lump", UNKNOWN)
    fever_urinary = answers.get("fever_urinary", UNKNOWN)
    if sudden_pain == UNKNOWN:
        unknown.append("Sudden severe testicular pain")
    if lump == UNKNOWN:
        unknown.append("Testicular lump or persistent swelling")
    if fever_urinary == UNKNOWN:
        unknown.append("Fever with urinary or genital symptoms")

    emergency = sudden_pain == YES
    prompt_review = lump == YES or fever_urinary == YES
    indicated_fertility_review = (
        trying == "12 months or longer"
        or answers.get("abnormal_semen") == YES
        or answers.get("cancer_treatment") == YES
        or answers.get("surgery") == YES
    )
    symptoms_or_significant_concerns = answers.get("persistent_symptoms") == YES

    if emergency:
        key, title = "emergency", "Seek emergency medical assessment now"
        message = (
            "Sudden, severe testicular pain can signal a time-critical condition such as "
            "testicular torsion. Do not wait for a screening score or online advice."
        )
        actions = [
            "Go to the nearest emergency department immediately or contact local emergency services.",
            "Do not delay to complete further assessment or obtain a routine fertility appointment.",
        ]
    elif prompt_review:
        key, title = "prompt", "Arrange prompt in-person medical assessment"
        message = (
            "A reported testicular lump/swelling or fever with urinary/genital symptoms "
            "requires professional clinical assessment; a questionnaire cannot determine its cause."
        )
        actions = [
            "Contact a qualified healthcare professional promptly for an in-person assessment.",
            "If severe pain develops, seek emergency care immediately.",
        ]
    elif indicated_fertility_review:
        key, title = "specialist", "Arrange a reproductive health consultation"
        message = (
            "Your history contains a reason to discuss a fertility assessment with a qualified "
            "clinician, regardless of the illustrative fuzzy activation below."
        )
        actions = [
            "Book a consultation with a primary care clinician, urologist, or fertility specialist.",
            "Discuss whether a semen analysis, examination, and directed investigations are appropriate.",
        ]
    elif symptoms_or_significant_concerns:
        key, title = "routine", "Book a routine clinical appointment"
        message = (
            "Persistent symptoms are best reviewed by a healthcare professional, "
            "even when other factors are not reported."
        )
        actions = [
            "Book a primary care or urology appointment to discuss the reported symptoms.",
            "If symptoms worsen rapidly, obtain more urgent care.",
        ]
    else:
        key, title = "educate", "Review preventive health and consider a clinical discussion"
        message = (
            "No specific referral trigger was reported in this demonstration. "
            "This does not mean fertility or reproductive health is normal."
        )
        actions = [
            "Consider routine preventive healthcare and discuss reproductive concerns with a clinician.",
            "If trying to conceive without success or symptoms emerge, seek appropriate assessment.",
        ]

    if answers.get("cancer_treatment") == YES:
        actions.append(
            "If cancer treatment is upcoming, ask your oncology team about fertility preservation "
            "before treatment begins, when feasible."
        )

    if unknown:
        actions.append(
            "Several answers are unknown or withheld; a clinician may need additional information "
            "before deciding whether testing is useful."
        )
    if not supportive:
        supportive = [
            "Avoid smoking, support general health, and seek individualized advice when considering pregnancy."
        ]

    fuzzy = fuzzy_activation(total_load)
    dominant = max(fuzzy, key=fuzzy.get)
    if max(fuzzy.values()) == 0.0:
        dominant = "No clear fuzzy pattern"

    return ScreeningResult(
        referral_key=key,
        referral_title=title,
        referral_message=message,
        action_items=actions,
        explanations=explanations,
        supportive_actions=supportive,
        missing_items=unknown,
        factors_reported=count_yes,
        factors_asked=len(FACTOR_DEFINITIONS),
        factor_load=round(total_load, 2),
        fuzzy_memberships={k: round(v, 3) for k, v in fuzzy.items()},
        dominant_description=dominant,
        uncertain_answers=len(unknown),
        emergency=emergency,
        safety_notices=[
            "Illustrative prototype only — not a medical device, diagnosis, infertility prediction, "
            "or a substitute for professional care.",
            "Fuzzy outputs represent self-reported factor patterns, not infertility probabilities "
            "or validated clinical risk categories.",
            "No health information is intentionally stored in a database by this prototype; "
            "avoid real patient data on public demo hosting."
        ],
    )
