import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import generation_ai


class GenerationAITests(unittest.TestCase):
    def setUp(self):
        generation_ai.reset_usage()

    def test_feature_selection_uses_cheap_model_and_no_reasoning(self):
        reply = SimpleNamespace(
            output_text=json.dumps({
                "birds": ["Curlew", "Blackbird"],
                "reason": "Strong contrast.",
            }),
            usage=SimpleNamespace(model_dump=lambda: {"input_tokens": 10, "output_tokens": 5}),
        )
        calls = []

        def create(**kwargs):
            calls.append(kwargs)
            return reply

        client = SimpleNamespace(responses=SimpleNamespace(create=create))
        with patch.object(generation_ai, "_client", return_value=client):
            selected, _ = generation_ai.select_featured_birds(
                ["Curlew", "Blackbird", "Robin"],
                history=[],
            )

        self.assertEqual(selected, ["Curlew", "Blackbird"])
        self.assertEqual(calls[0]["model"], generation_ai.UTILITY_MODEL)
        self.assertEqual(calls[0]["reasoning"], {"effort": "none"})

    def test_recognition_guide_is_reused_from_local_cache(self):
        reply = SimpleNamespace(
            output_text=json.dumps({
                "birds": [{
                    "species": "Robin",
                    "art_cue": "compact warm-breasted form with alert upright posture",
                    "recognition_cues": ["orange-red breast", "small rounded brown form"],
                    "avoid_confusions": ["avoid a finch-like bill"],
                }]
            }),
            usage=None,
        )
        calls = []
        client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: calls.append(kwargs) or reply)
        )

        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder) / "bird-cache.json"
            with patch.object(generation_ai, "_client", return_value=client):
                first = generation_ai.create_bird_plan(["Robin"], cache_path=cache)
                second = generation_ai.create_bird_plan(["Robin"], cache_path=cache)

        self.assertEqual(len(calls), 1)
        self.assertEqual(first, second)
        self.assertIn("orange-red breast", second[0]["recognition_cues"])

    def test_creative_direction_forces_requested_subject_balance(self):
        reply = SimpleNamespace(
            output_text=json.dumps({
                "movement_options": [{
                    "name": "Architectural Quiet",
                    "creative_direction": "Interior-led composition",
                    "materials": "wood and glass",
                    "composition": "vertical room study",
                    "why_it_is_distinct": "environment first",
                }],
                "selected_index": 1,
                "selection_reason": "Best contrast.",
                "brief": {
                    "collection": "Room and Wing",
                    "style": "material interior study",
                    "style_guidance": "Keep the room dominant.",
                    "curator_notes": "",
                    "mood": "quiet",
                    "visual_language": "architectural",
                    "palette": "muted",
                    "composition": "vertical",
                    "subject_balance": "wrong-value",
                    "bird_integration": "birds integrated into the room",
                    "materials": "wood and glass",
                    "visual_focus": "light and structure",
                    "hero_birds": [],
                    "supporting_birds": ["Robin"],
                    "avoid": [],
                },
                "creative_dna": {"dominant_family": "interior"},
                "image_prompt": "Create a quiet architectural interior with one transformed robin.",
            }),
            usage=None,
        )
        client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: reply))
        plan = [{
            "index": 1,
            "species": "Robin",
            "art_cue": "compact warm-breasted form",
            "recognition_cues": ["orange breast"],
            "avoid_confusions": [],
        }]
        with patch.object(generation_ai, "_client", return_value=client):
            result = generation_ai.create_art_direction(
                ["Robin"],
                plan,
                history=[],
                season="autumn",
                edition="twice_weekly",
                observation_window="test",
                subject_balance="environment-led",
            )

        self.assertEqual(result["brief"]["subject_balance"], "environment-led")

    def test_retry_reuses_original_art_direction(self):
        base = "Original art direction."
        retry = generation_ai.build_retry_prompt(base, "- Curlew: missing.")
        self.assertTrue(retry.startswith(base))
        self.assertIn("same artwork", retry)
        self.assertIn("Curlew: missing", retry)


if __name__ == "__main__":
    unittest.main()
