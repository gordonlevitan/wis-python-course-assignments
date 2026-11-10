import unittest

from app import app


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_empty_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<form", response.data)

    def test_caffeine(self):
        response = self.client.post("/", data={"formula": "C8H10N4O2"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"194.19", response.data)
        self.assertIn(b"194.0804", response.data)

    def test_formula_in_url(self):
        response = self.client.get("/?formula=CH3(CH2)4CH3")
        self.assertIn(b"C6H14", response.data)

    def test_invalid_formula(self):
        response = self.client.post("/", data={"formula": "Xx2"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unknown element", response.data)

    def test_compound_list(self):
        response = self.client.get("/compounds")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"caffeine", response.data)
        self.assertIn(b"C24H8O6", response.data)  # PTCDA

    def test_api(self):
        response = self.client.get("/api/C9H8O4")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["molecular_weight"], 180.16)

    def test_api_error(self):
        response = self.client.get("/api/C6H7")  # fractional DBE
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
