import unittest


from scrapers.joonggonara import JoonggonaraScraper


class TestJoonggonaraId(unittest.TestCase):
    def test_extract_articleid_query_param(self):
        url = "https://cafe.naver.com/joonggonara/ArticleRead.nhn?clubid=10050146&articleid=12345"
        self.assertEqual(JoonggonaraScraper.extract_article_id(url), "12345")

    def test_extract_numeric_path(self):
        url = "https://cafe.naver.com/joonggonara/12345678?ref=foo"
        self.assertEqual(JoonggonaraScraper.extract_article_id(url), "12345678")

    def test_hash_fallback_is_deterministic(self):
        url = "https://example.com/some/path/noid?x=y#frag"
        id1 = JoonggonaraScraper.extract_article_id(url)
        id2 = JoonggonaraScraper.extract_article_id(url)
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("hash_"))
        self.assertEqual(len(id1), len("hash_") + 12)


if __name__ == "__main__":
    unittest.main()

