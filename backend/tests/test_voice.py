"""Offline safety and API smoke tests: no paid phone calls are placed."""
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.twilio_calls import instructions
from app.models import Lead


class ApiTests(unittest.TestCase):
    def test_health(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").json(), {"status": "ok"})

    def test_legacy_dialer_disabled(self):
        with TestClient(app) as client:
            self.assertEqual(client.post("/calls/start/1").status_code, 410)

    def test_leads_require_private_admin_key(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/leads").status_code, 401)
            self.assertEqual(client.post("/leads", json={
                "company_name": "Example", "phone": "+15551234567"
            }).status_code, 401)

    def test_outbound_dialing_is_inactive_without_configuration(self):
        with TestClient(app) as client:
            response = client.post("/twilio/call/1", headers={"X-Admin-Key": "example-test-key"})
            self.assertIn(response.status_code, (403, 503))
            self.assertNotEqual(response.status_code, 202)

    def test_unsigned_twilio_webhook_rejected(self):
        with TestClient(app) as client:
            self.assertEqual(client.post("/twilio/voice?lead_id=1").status_code, 403)

    def test_agent_instructions_limit_sales_claims(self):
        lead = Lead(company_name="Acme", contact_name="Alex", phone="+15551234567")
        prompt = instructions(lead)
        self.assertIn("Never invent prices", prompt)
        self.assertIn("mark_do_not_call", prompt)
        self.assertIn("human sales follow-up", prompt)


if __name__ == "__main__":
    unittest.main()
