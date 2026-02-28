import unittest

from app.ads.experiment import recommend_ad_experiment


class TestAdsExperiment(unittest.TestCase):
    def test_increase_step(self):
        rec = recommend_ad_experiment(rpm=8.0, rps=0.03, ads_per_page=3, bounce_rate=0.45)
        self.assertEqual(rec["recommendation"], "INCREASE_STEP")

    def test_decrease_on_bounce(self):
        rec = recommend_ad_experiment(rpm=15.0, rps=0.09, ads_per_page=3, bounce_rate=0.8)
        self.assertEqual(rec["recommendation"], "DECREASE")


if __name__ == "__main__":
    unittest.main()
