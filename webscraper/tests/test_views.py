from django.test import TestCase


class TestIndex(TestCase):

    def test_call_view_loads(self):
        response = self.client.get('/webscraper/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('webscraper', str(response.content))

    def test_call_root_redirects(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'webscraper/')
