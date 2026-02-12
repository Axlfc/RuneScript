import unittest
from bs4 import BeautifulSoup

class TestHTML(unittest.TestCase):
    def setUp(self):
        with open('index.html', 'r', encoding='utf-8') as f:
            self.soup = BeautifulSoup(f.read(), 'html.parser')

    def test_document_type(self):
        self.assertIsNotNone(self.soup.doctype)
        self.assertEqual(str(self.soup.doctype).strip(), '<!DOCTYPE html>')

    def test_language_attribute(self):
        html_tag = self.soup.html
        self.assertTrue(html_tag.has_attr('lang'))
        self.assertEqual(html_tag['lang'], 'en')

if __name__ == '__main__':
    unittest.main()
