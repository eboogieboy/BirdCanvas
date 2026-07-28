from dataclasses import dataclass, field
from typing import List


@dataclass
class CreativeDNA:
    dominant_family: str
    materials: List[str]
    palette_type: str
    energy: str
    complexity: str
    surface: str
    geometry: str
    overall_character: str


@dataclass
class CreativePlan:
    movement: str
    curator_brief: str
    image_prompt: str
    negative_prompt: str
    creative_dna: CreativeDNA


@dataclass
class ArtworkReview:
    passed: bool
    originality: int
    art_quality: int
    bird_integration: int
    movement_score: int
    summary: str


@dataclass
class ArtworkResult:
    birds: List[str]
    image_path: str
    plan: CreativePlan
    review: ArtworkReview