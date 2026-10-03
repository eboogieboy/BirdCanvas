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


    def test_bird_plan_separates_light_art_cue_from_verifier_detail(self):
        reply = SimpleNamespace(
            output_text=json.dumps(
                {
                    "birds": [
                        {
                            "index": 1,
                            "species": "European Goldfinch",
                            "art_cue": "small finch rhythm with scarlet face spark and gold wing flash",
                            "recognition_cues": [
                                "bright red face within black-and-white head pattern",
                                "black wing crossed by a broad vivid yellow bar",
                            ],
                            "avoid_confusions": [
                                "avoid losing both red face and yellow wing bar"
                            ],
                        }
                    ]
                }
            )
        )
        client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: reply)
        )
        with patch.object(compose, "_client", return_value=client):
            plan = compose.create_bird_plan(["European Goldfinch"])

        self.assertEqual(
            plan[0]["art_cue"],
            "small finch rhythm with scarlet face spark and gold wing flash",
        )
        self.assertEqual(len(plan[0]["recognition_cues"]), 2)

    def test_image_prompt_uses_light_art_cues_not_detailed_verifier_notes(self):
        reply = SimpleNamespace(output_text="Create a transformed material artwork.")
        client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: reply)
        )
        bird_plan = [
            {
                "index": 1,
                "species": "European Goldfinch",
                "art_cue": "small finch rhythm with scarlet spark and gold wing flash",
                "recognition_cues": [
                    "bright red face within black-and-white head pattern",
                    "black wing crossed by a broad vivid yellow bar",
                ],
                "avoid_confusions": [
                    "avoid losing both red face and yellow wing bar"
                ],
            }
        ]
        brief = {
            "collection": "Test",
            "style": "Material abstraction",
            "style_guidance": "Transform the subject into the medium.",
            "curator_notes": "",
            "mood": "quiet",
            "visual_language": "layered mineral forms",
            "palette": "restrained",
            "composition": "open portrait field",
            "bird_integration": "The bird is transformed into layered mineral form.",
            "materials": "pigment and plaster",
            "visual_focus": "material rhythm",
            "hero_birds": ["European Goldfinch"],
            "supporting_birds": [],
            "avoid": [],
        }

        with patch.object(compose, "_client", return_value=client):
            prompt = compose.create_image_prompt(
                ["European Goldfinch"],
                brief,
                bird_plan,
            )

        self.assertIn("small finch rhythm with scarlet spark and gold wing flash", prompt)
        self.assertNotIn("bright red face within black-and-white head pattern", prompt)
        self.assertNotIn("avoid losing both red face and yellow wing bar", prompt)
        self.assertIn("normally rendered naturalistic bird", prompt)

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
