import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from services.llm import _build_user_prompt, _redact_sensitive_text


class LLMPromptPrivacyTests(unittest.TestCase):
    def test_redacts_common_sensitive_values(self):
        raw = (
            "Email me at buyer@example.com, call +91 9876543210, "
            "aadhaar 1234 5678 9012, card 4111 1111 1111 1111, "
            "api_key=sk_secretvalue123"
        )

        redacted = _redact_sensitive_text(raw)

        self.assertNotIn("buyer@example.com", redacted)
        self.assertNotIn("9876543210", redacted)
        self.assertNotIn("1234 5678 9012", redacted)
        self.assertNotIn("4111 1111 1111 1111", redacted)
        self.assertNotIn("sk_secretvalue123", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)
        self.assertIn("[REDACTED_PHONE]", redacted)
        self.assertIn("[REDACTED_ID]", redacted)
        self.assertIn("[REDACTED_PAYMENT_CARD]", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)

    def test_user_prompt_redacts_query_draft_history_and_context(self):
        prompt = _build_user_prompt(
            query="Recommend car under 15 lakh, my phone is 9876543210",
            context_chunks=["Dealer note: contact buyer@example.com for follow-up"],
            history=[
                {"role": "user", "content": "My aadhaar is 1234 5678 9012"},
                {"role": "assistant", "content": "Keep token: abcdefghijk secret"},
            ],
            general_only=False,
            draft_answer="Use Tata Tiago EV. User email buyer@example.com should not be repeated.",
            query_type="decision",
            user_level="intermediate",
        )

        self.assertNotIn("9876543210", prompt)
        self.assertNotIn("buyer@example.com", prompt)
        self.assertNotIn("1234 5678 9012", prompt)
        self.assertIn("[REDACTED_PHONE]", prompt)
        self.assertIn("[REDACTED_EMAIL]", prompt)
        self.assertIn("[REDACTED_ID]", prompt)
        self.assertIn("Tata Tiago EV", prompt)


if __name__ == "__main__":
    unittest.main()
