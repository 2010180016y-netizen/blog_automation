import unittest

from app.seo.internal_link_validator import validate_internal_links


class TestInternalLinkValidator(unittest.TestCase):
    def test_orphan_and_crawl_simulation(self):
        posts = [
            {
                "slug": "home",
                "content": '<a href="/guide-phone">폰 가이드 보기</a>',
            },
            {
                "slug": "guide-phone",
                "content": '<a href="/review-phone">리뷰 확인</a>',
            },
            {
                "slug": "review-phone",
                "content": "<p>done</p>",
            },
            {
                "slug": "orphan-page",
                "content": "<p>no inbound</p>",
            },
        ]

        report = validate_internal_links(posts, start_slugs=["home"], max_depth=4)
        self.assertEqual(report["status"], "WARN")
        self.assertIn("orphan-page", report["orphans"])
        self.assertIn("home", report["crawl"]["visited"])
        self.assertIn("review-phone", report["crawl"]["visited"])

    def test_anchor_quality_issue(self):
        posts = [
            {"slug": "a", "content": '<a href="/b">x</a><a href="/b">y</a><a href="/b">z</a>'},
            {"slug": "b", "content": "<p>ok</p>"},
        ]
        report = validate_internal_links(posts, start_slugs=["a"], min_anchor_chars=2)
        self.assertEqual(report["status"], "REJECT")
        self.assertGreaterEqual(len(report["anchor_issues"]), 3)


if __name__ == "__main__":
    unittest.main()
