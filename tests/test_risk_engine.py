import unittest

from risk_engine import YES, NO, UNKNOWN, FACTOR_DEFINITIONS, evaluate, fuzzy_activation


def base(**kwargs):
    a = {key: NO for key in FACTOR_DEFINITIONS}
    a.update({
        "sudden_pain": NO,
        "lump": NO,
        "fever_urinary": NO,
        "trying_duration": "Not trying / not applicable",
    })
    a.update(kwargs)
    return a


class TestMenCareEngine(unittest.TestCase):
    def test_emergency_overrides_all_scores(self):
        r = evaluate(base(sudden_pain=YES))
        self.assertTrue(r.emergency)
        self.assertEqual(r.referral_key, "emergency")

    def test_lump_needs_prompt_assessment(self):
        self.assertEqual(evaluate(base(lump=YES)).referral_key, "prompt")

    def test_fever_urinary_needs_prompt_assessment(self):
        self.assertEqual(evaluate(base(fever_urinary=YES)).referral_key, "prompt")

    def test_twelve_months_specialist(self):
        self.assertEqual(evaluate(base(trying_duration="12 months or longer")).referral_key, "specialist")

    def test_abnormal_semen_specialist(self):
        self.assertEqual(evaluate(base(abnormal_semen=YES)).referral_key, "specialist")

    def test_cancer_treatment_referral(self):
        r = evaluate(base(cancer_treatment=YES))
        self.assertEqual(r.referral_key, "specialist")
        self.assertIn("fertility preservation", " ".join(r.action_items))

    def test_persistent_symptoms_routine(self):
        self.assertEqual(evaluate(base(persistent_symptoms=YES)).referral_key, "routine")

    def test_no_trigger_cannot_claim_no_risk(self):
        r = evaluate(base())
        self.assertEqual(r.referral_key, "educate")
        self.assertIn("does not mean fertility", r.referral_message)

    def test_unknown_answers_are_not_negative(self):
        r = evaluate(base(smoking=UNKNOWN, lump=UNKNOWN))
        self.assertGreaterEqual(r.uncertain_answers, 2)
        self.assertEqual(r.factors_reported, 0)

    def test_fuzzy_membership_bounded(self):
        for x in [0, 0.5, 1.5, 2.6, 4, 5.5, 9]:
            a = fuzzy_activation(x)
            self.assertTrue(all(0 <= v <= 1 for v in a.values()))

    def test_no_false_cancer_mri_inference(self):
        # No field suggesting MRI directly diagnoses fertility.
        self.assertNotIn("mri_prediction", FACTOR_DEFINITIONS)


if __name__ == "__main__":
    unittest.main()
