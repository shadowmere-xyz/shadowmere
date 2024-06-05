from django.test import TestCase


class QRGenerationTest(TestCase):
    fixtures = ["proxies.json"]

    def test_qr_generated_correctly(self):
        response = self.client.get("/74/qr")
        self.assertEqual(
            response.status_code,
            200,
            "qr generation failed",
        )
        self.assertEqual(response.headers.get("Content-Type"), "image/png")
        self.assertEqual(
            response.headers.get("Content-Disposition"),
            'attachment; filename="qr_74.png"',
        )

    def test_qr_inexistent_proxy_fails(self):
        response = self.client.get("/20/qr")
        self.assertEqual(
            response.status_code,
            404,
            "qr generation for non existent proxy should return Not Found",
        )
