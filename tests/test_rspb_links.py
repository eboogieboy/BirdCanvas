import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from rspb_links import RSPB_BASE, rspb_species_url


class RSPBLinkTests(unittest.TestCase):
    def test_scientific_name_resolves_birdnet_and_rsbp_naming_differences(self):
        self.assertEqual(rspb_species_url("European Robin", "Erithacus rubecula"), RSPB_BASE + "robin")
        self.assertEqual(rspb_species_url("Common Magpie", "Pica pica"), RSPB_BASE + "magpie")
        self.assertEqual(rspb_species_url("Coot", "Fulica atra"), RSPB_BASE + "eurasian-coot")
        self.assertEqual(rspb_species_url("Ring-necked Parakeet", "Psittacula krameri"), RSPB_BASE + "ring-necked-parakeet")

    def test_name_fallback_is_for_known_species_only(self):
        self.assertEqual(rspb_species_url("Eurasian Blue Tit"), RSPB_BASE + "blue-tit")
        self.assertEqual(rspb_species_url("European Goldfinch"), RSPB_BASE + "goldfinch")
        self.assertEqual(rspb_species_url("Common Woodpigeon"), RSPB_BASE + "woodpigeon")
        self.assertIsNone(rspb_species_url("Unknown Mystery Bird", "Aves imaginaria"))
        self.assertIsNone(rspb_species_url("Unknown Gull"))

    def test_assembled_links_are_explicit_valid_species_slugs(self):
        for scientific, (common, slug) in __import__("rspb_links")._SPECIES.items():
            self.assertEqual(rspb_species_url(common, scientific), RSPB_BASE + slug)
            self.assertEqual(rspb_species_url(common), RSPB_BASE + slug)


if __name__ == "__main__":
    unittest.main()
