import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import compose


class ArtCurationTests(unittest.TestCase):
    def test_small_collection_features_every_species_without_model_call(self):
        with patch.object(compose, "_client") as client:
            selected, reason = compose.select_featured_birds(["Robin", "Blackbird"])
        self.assertEqual(selected, ["Robin", "Blackbird"])
        self.assertIn("already small", reason)
        client.assert_not_called()

    def test_curator_can_choose_two_to_four_exact_species(self):
        reply = SimpleNamespace(
            output_text=json.dumps(
                {
                    "birds": ["Curlew", "European Goldfinch", "Blackbird"],
                    "reason": "Strong contrast of line, colour and mass.",
                }
            )
        )
        client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: reply)
        )
        with patch.object(compose, "_client", return_value=client):
            selected, reason = compose.select_featured_birds(
                [
                    "Common Magpie",
                    "Curlew",
                    "Blackbird",
                    "European Goldfinch",
                    "Eurasian Jackdaw",
                ]
            )

        self.assertEqual(
            selected,
            ["Curlew", "European Goldfinch", "Blackbird"],
        )
        self.assertIn("contrast", reason)

    def test_invalid_curator_selection_falls_back_without_inventing_species(self):
        with tempfile.TemporaryDirectory() as folder:
            history_file = Path(folder) / "creative_history.json"
            history_file.write_text(
                json.dumps(
                    [
                        {"featured_birds": ["Robin", "Blackbird"]},
                        {"featured_birds": ["Robin"]},
                    ]
                ),
                encoding="utf-8",
            )
            reply = SimpleNamespace(
                output_text=json.dumps(
                    {
                        "birds": ["Imaginary Bird", "Robin"],
                        "reason": "Invalid on purpose.",
                    }
                )
            )
            client = SimpleNamespace(
                responses=SimpleNamespace(create=lambda **kwargs: reply)
            )

            with patch.object(compose, "HISTORY_FILE", history_file), patch.object(
                compose, "_client", return_value=client
            ):
                selected, reason = compose.select_featured_birds(
                    ["Robin", "Blackbird", "Curlew", "Goldfinch", "Blue Tit"]
                )

        self.assertEqual(selected, ["Curlew", "Goldfinch", "Blue Tit"])
        self.assertIn("Fallback curation", reason)

    def test_minor_species_issue_does_not_spend_second_generation(self):
        verification = {
            "extra_birds": [],
            "bird_results": [
                {
                    "species": "Blackbird",
                    "status": "correct",
                    "severity": "minor",
                    "problems": ["Bill colour softened by abstraction."],
                }
            ],
        }
        self.assertFalse(compose.verification_has_major_failure(verification))

    def test_missing_featured_species_justifies_retry(self):
        verification = {
            "extra_birds": [],
            "bird_results": [
                {
                    "species": "Curlew",
                    "status": "missing",
                    "severity": "major",
                    "problems": [],
                }
            ],
        }
        self.assertTrue(compose.verification_has_major_failure(verification))


if __name__ == "__main__":
    unittest.main()
