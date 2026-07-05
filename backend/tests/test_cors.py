import unittest

from fastapi.testclient import TestClient

from app.main import create_app


class CorsTest(unittest.TestCase):
    def test_local_vite_origins_are_allowed(self):
        client = TestClient(create_app())

        for origin in ["http://localhost:5173", "http://127.0.0.1:5173"]:
            with self.subTest(origin=origin):
                response = client.options(
                    "/health",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "GET",
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["access-control-allow-origin"], origin)


if __name__ == "__main__":
    unittest.main()
