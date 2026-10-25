"""One scheduled collection, one publication, independent Frame delivery retries."""
from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from artwork_store import ARCHIVE_DIR, CURRENT_DIR, artwork_id_for, publish_artwork
from art_style_rotation import get_style
from birdnet_go import detections
from compose import compose, filter_birds
from display import build_display_page
from frame_upload import frame_enabled, upload_to_frame, _run_samsungtv
from generation_settings import load_settings, next_boundary, scheduled_boundary
from manual_sightings import sightings_between
from gallery_library import artwork_image_path
from paths import DATA_DIR

LOCAL = ZoneInfo("Europe/London")
STATE_FILE = DATA_DIR / "generation_state.json"
LOCK_FILE = DATA_DIR / "generation.lock"


def _now():
    return datetime.now(LOCAL)


def _iso(value):
    return value.isoformat(timespec="seconds")


def load_state():
    if not STATE_FILE.exists():
        return {"last_end": None, "deliveries": [], "uploads": [], "frame_content": {}}
    value = json.loads(STATE_FILE.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError("Invalid generation state")
    return value


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, STATE_FILE)


@contextmanager
def exclusive():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_FILE.open('a+') as file:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(file, fcntl.LOCK_UN)


def status(now=None, include_birds=True):
    now = now or _now()
    settings = load_settings()
    state = load_state()
    frequency = settings['frequency']
    due = scheduled_boundary(now, frequency)
    last_end = datetime.fromisoformat(state['last_end']) if state.get('last_end') else None
    start = last_end or scheduled_boundary(due - timedelta(seconds=1), frequency)
    next_at = due if not last_end or due > last_end else next_boundary(now, frequency)
    result = {"settings": settings, "collecting_since": _iso(start), "next_generation": _iso(next_at), "pending_delivery": sum(not d.get('delivered_at') for d in state.get('deliveries', [])), "last_completed": state.get('last_end'), "last_error": state.get('last_error'), "last_result": state.get('last_result'), "last_delivery": state.get('last_delivery')}
    if include_birds:
        try:
            bird_data = detections(start, now)
            result.update({
                "species_detected": len(bird_data["species"]),
                "detections_total": bird_data["detections_total"],
                "last_detection": bird_data["last_detection"],
                "last_accepted_bird": bird_data.get("last_accepted_bird"),
                "latest_birdnet_detection": bird_data.get("latest_birdnet_detection"),
                "minimum_confidence": bird_data.get("minimum_confidence"),
                "birdnet_status": "ok",
            })
        except Exception as error:
            result.update({"species_detected": None, "birdnet_status": "error", "birdnet_error": str(error)})
    return result


def _observed_species(heard, sightings):
    """Keep detection counts separate and merge visual observations by species name."""
    observed = list(heard)
    seen = []
    keys = {name.casefold() for name in observed}
    for entry in sightings:
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        equivalent = next((bird for bird in observed if bird.casefold() == name.casefold()), None)
        seen_name = equivalent or name
        if seen_name.casefold() not in {bird.casefold() for bird in seen}:
            seen.append(seen_name)
        if name.casefold() not in keys:
            observed.append(name)
            keys.add(name.casefold())
    return observed, seen


def _remember_frame_content(state, artwork_id, content_id):
    state.setdefault('frame_content', {})[artwork_id] = content_id
    uploads = state.setdefault('uploads', [])
    if content_id in uploads:
        uploads.remove(content_id)
    uploads.append(content_id)


def _cleanup_frame_uploads(state):
    # Delete only uploads recorded by BirdCanvas, never other personal TV art.
    while len(state.get('uploads', [])) > 10:
        old = state['uploads'][0]
        try:
            _run_samsungtv('art-delete', old)
        except Exception as error:
            state['cleanup_error'] = str(error)
            save_state(state)
            break

        state['uploads'].pop(0)
        mapping = state.get('frame_content', {})
        if isinstance(mapping, dict):
            for artwork_id, content_id in list(mapping.items()):
                if content_id == old:
                    mapping.pop(artwork_id, None)
        save_state(state)


def retry_deliveries(state):
    if not frame_enabled():
        return
    for delivery in state.get('deliveries', []):
        if delivery.get('delivered_at'):
            continue
        image = ARCHIVE_DIR / delivery['id'] / 'artwork.png'
        if not image.is_file():
            delivery['error'] = f"Missing archived artwork: {image}"
            save_state(state)
            continue
        try:
            def remember(content_id):
                delivery['content_id'] = content_id
                _remember_frame_content(state, delivery['id'], content_id)
                save_state(state)  # Survive a display failure without paying for another upload.

            result = upload_to_frame(image, content_id=delivery.get('content_id'), on_uploaded=remember)
            delivery['content_id'] = result['content_id']
            _remember_frame_content(state, delivery['id'], result['content_id'])
            delivery['delivered_at'] = _iso(_now())
            delivery.pop('error', None)
            state['last_delivery'] = delivery['delivered_at']
            save_state(state)
        except Exception as error:
            delivery['error'] = str(error)
            save_state(state)
            break  # Avoid repeating a costly failure for every queued image.
    _cleanup_frame_uploads(state)


def send_artwork_to_frame(artwork_id):
    """Display an existing GalleryOS artwork on the Samsung Frame."""
    cleaned_id = str(artwork_id).strip()
    if not cleaned_id:
        raise ValueError("Artwork ID is required.")
    if not frame_enabled():
        raise RuntimeError("Samsung Frame integration is currently disabled.")

    with exclusive():
        image = artwork_image_path(cleaned_id)
        state = load_state()
        uploads = state.setdefault('uploads', [])
        mapping = state.setdefault('frame_content', {})

        content_id = mapping.get(cleaned_id)
        if content_id not in uploads:
            content_id = None

        # Backward compatibility for generated artwork uploaded before frame_content
        # was introduced.
        if not content_id:
            for delivery in state.get('deliveries', []):
                candidate = delivery.get('content_id')
                if delivery.get('id') == cleaned_id and candidate in uploads:
                    content_id = candidate
                    break

        reused = bool(content_id)

        def remember(new_content_id):
            _remember_frame_content(state, cleaned_id, new_content_id)
            save_state(state)

        result = upload_to_frame(
            image,
            content_id=content_id,
            on_uploaded=remember,
        )
        if result is None:
            raise RuntimeError("Samsung Frame integration is currently disabled.")

        _remember_frame_content(state, cleaned_id, result['content_id'])
        delivered_at = _iso(_now())
        state['last_delivery'] = delivered_at
        state['last_manual_delivery'] = {
            "artwork_id": cleaned_id,
            "content_id": result['content_id'],
            "delivered_at": delivered_at,
        }
        save_state(state)
        _cleanup_frame_uploads(state)

        return {
            "artwork_id": cleaned_id,
            "content_id": result['content_id'],
            "delivered_at": delivered_at,
            "reused": reused,
        }



def run_style_test(style_name="Geometric abstraction", now=None):
    """Generate a fresh artistic interpretation of existing, genuinely heard birds.

    Unlike Generate now, this does NOT advance the observation cursor or affect
    the next scheduled daily collection. It requires a recent BirdCanvas manifest
    and never substitutes an invented species.
    """
    selected_style = get_style(style_name)
    with exclusive():
        now = now or _now()
        settings = load_settings()
        state = load_state()
        current_manifest = CURRENT_DIR / "manifest.json"
        if not current_manifest.is_file():
            raise ValueError("A previous BirdCanvas artwork is needed for a style test.")
        source = json.loads(current_manifest.read_text(encoding="utf-8"))
        if source.get("collection") != "birdcanvas":
            raise ValueError("Current artwork is not a BirdCanvas observation.")
        heard_species = list(source.get("species_detected") or [])
        seen_species = list(source.get("species_sighted") or [])
        original = source.get("species_observed") or (heard_species + seen_species) or source.get("species_eligible") or source.get("species") or []
        observed_species, priorities = _observed_species(original, [{"name": name} for name in seen_species])
        eligible_species = filter_birds(observed_species, settings["excluded_birds"])
        priorities = [name for name in priorities if name in eligible_species]
        if not eligible_species:
            raise ValueError("No eligible recorded birds are available for the style test.")

        # Unique archive name even when multiple manually requested on one day.
        edition = f"style-test-{now.strftime('%Y%m%d-%H%M%S-%f')}"
        original_window = str(source.get("observation_window") or source.get("observation_date") or "")
        try:
            result = compose(
                source="style_test",
                birds=eligible_species,
                edition="style_test",
                observation_window=f"Style test; reusing heard and seen species from {original_window}",
                excluded_terms=settings["excluded_birds"],
                priority_birds=priorities,
                style_override=selected_style["name"],
            )
            if not result:
                raise RuntimeError("Style test returned no image.")
            featured = list(result.get("birds") or eligible_species)
            manifest = publish_artwork(
                source_image=Path(result["output"]),
                observation_date=now.date().isoformat(),
                birds=featured,
                brief=result["brief"],
                edition=edition,
                title=f"Style Test — {selected_style['name']} — {now:%-d %b %Y}",
                observation_window=f"Style interpretation of existing detections: {original_window}",
                observation_started_at=str(source.get("observation_started_at") or ""),
                observation_ended_at=str(source.get("observation_ended_at") or ""),
                detections_total=int(source.get("detections_total") or 0),
                species_detected=heard_species if seen_species else (heard_species or observed_species),
                species_sighted=seen_species,
                species_observed=observed_species,
                sightings_total=int(source.get("sightings_total") or 0),
                species_eligible=eligible_species,
                species_used=featured,
                species_not_featured=[bird for bird in eligible_species if bird not in featured],
                species_excluded=[bird for bird in observed_species if bird not in eligible_species],
                generation_frequency="style_test",
                generation=result.get("generation"),
            )
            build_display_page()
            state.setdefault("deliveries", []).append({"id": manifest["id"]})
            state["last_error"] = None
            state["last_result"] = f"Published {manifest['id']} ({selected_style['name']} style test)"
            # Intentionally preserve state['last_end'] and the normal schedule.
            save_state(state)
            retry_deliveries(state)
            return {
                "status": "published",
                "artwork_id": manifest["id"],
                "art_style": selected_style["name"],
                "reused_observation_date": source.get("observation_date"),
                "next_collection_unchanged": True,
            }
        except Exception as error:
            state["last_error"] = str(error)
            save_state(state)
            raise



# Do not hide a prolonged BirdNET outage by recycling old birds indefinitely.
FALLBACK_MAX_AGE = timedelta(days=7)


def _previous_observations(cutoff, excluded_terms):
    """Find recent, genuinely heard/seen species in a prior BirdCanvas edition.

    Never mistake a style test, another fallback, or an uploaded image for
    fresh observations. Archive history takes precedence over the current
    display selection, which may be unrelated artwork.
    """
    candidates = list(ARCHIVE_DIR.glob("*/manifest.json"))
    current = CURRENT_DIR / "manifest.json"
    if current.is_file():
        candidates.append(current)
    best = None
    for path in candidates:
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(source, dict) or source.get("collection") != "birdcanvas":
            continue
        if source.get("observation_fallback") or source.get("generation_frequency") == "style_test":
            continue
        heard = source.get("species_detected") or []
        seen = source.get("species_sighted") or []
        if not isinstance(heard, list) or not isinstance(seen, list):
            continue
        combined, original_seen = _observed_species(heard, [{"name": name} for name in seen])
        eligible = filter_birds(combined, excluded_terms)
        if not eligible:
            continue
        try:
            if source.get("observation_ended_at"):
                observed_at = datetime.fromisoformat(source["observation_ended_at"])
            else:
                # Older manifests only identify the edition's observation date.
                observed_at = datetime.fromisoformat(source["observation_date"] + "T04:00:00")
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=LOCAL)
            observed_at = observed_at.astimezone(LOCAL)
        except (TypeError, ValueError, KeyError):
            continue
        if observed_at > cutoff or cutoff - observed_at > FALLBACK_MAX_AGE:
            continue
        if best is None or observed_at > best["observed_at"]:
            best = {
                "observed_at": observed_at,
                "source_observation_date": source.get("observation_date") or observed_at.date().isoformat(),
                "source_artwork_id": source.get("id") or "",
                "source_observation_window": source.get("observation_window") or "",
                "species": eligible,
                "priority": [name for name in original_seen if name in eligible],
            }
    return best


def run(manual=False, now=None):
    with exclusive():
        now = now or _now()
        settings = load_settings()
        frequency = settings['frequency']
        state = load_state()
        retry_deliveries(state)
        due = scheduled_boundary(now, frequency)
        last_end = datetime.fromisoformat(state['last_end']) if state.get('last_end') else None
        if not manual and last_end and due <= last_end:
            return {"status": "not_due", "next_generation": _iso(next_boundary(now, frequency))}
        end = now if manual else due
        if last_end and end <= last_end:
            return {"status": "not_due"}
        start = last_end or scheduled_boundary(due - timedelta(seconds=1), frequency)
        # A deterministic ID allows recovery if a process stops after publishing
        # but before committing the window cursor.
        edition = f"{frequency}-{end.strftime('%Y%m%d-%H%M%S')}"
        artwork_id = artwork_id_for(end.date().isoformat(), edition)
        manifest_path = ARCHIVE_DIR / artwork_id / 'manifest.json'
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        else:
            try:
                observed = detections(start, end)
                species = observed['species']
                sightings = sightings_between(start, end)
                combined, seen = _observed_species(species, sightings)
                used = filter_birds(combined, settings['excluded_birds'])
                priority = [name for name in seen if name in used]
                observation_window = f"{_iso(start)} to {_iso(end)}"
                observation_fallback = None
                if not used and frequency == "daily":
                    previous = _previous_observations(start, settings["excluded_birds"])
                    if previous:
                        used = previous["species"]
                        priority = previous["priority"]
                        observation_fallback = {
                            "reason": "no_eligible_birds_in_collection",
                            "source_artwork_id": previous["source_artwork_id"],
                            "source_observation_date": previous["source_observation_date"],
                            "source_observation_window": previous["source_observation_window"],
                        }
                        observation_window += (
                            f"; no eligible species this collection; reusing real observations"
                            f" from {previous['source_observation_date']}"
                        )
                if not used:
                    state["last_result"] = f"No eligible birds in collection ending {_iso(end)}"
                    save_state(state)
                    return {"status": "no_birds", "window_start": _iso(start), "window_end": _iso(end)}
                result = compose(source='birdnet_go', birds=used, edition=frequency,
                                 observation_window=observation_window,
                                 excluded_terms=settings['excluded_birds'],
                                 priority_birds=priority)
                if not result:
                    raise RuntimeError("Artwork generation returned no image")
                featured = list(result.get('birds') or used)
                manifest = publish_artwork(
                    source_image=Path(result['output']), observation_date=end.date().isoformat(),
                    birds=featured, brief=result['brief'], edition=edition,
                    title=(f"Garden Birds — {end:%-d %b %Y} (previous observations)"
                           if observation_fallback else
                           f"Garden Birds — {start:%-d %b}–{end:%-d %b %Y}"),
                    observation_window=observation_window,
                    observation_fallback=observation_fallback,
                    generation=result.get('generation'),
                    observation_started_at=_iso(start), observation_ended_at=_iso(end),
                    detections_total=observed['detections_total'], species_detected=species,
                    species_sighted=seen, species_observed=combined,
                    sightings_total=len(sightings),
                    species_eligible=used, species_used=featured,
                    species_not_featured=[s for s in used if s not in featured],
                    species_excluded=[s for s in combined if s not in used],
                    generation_frequency=frequency)
                build_display_page()
            except Exception as error:
                state['last_error'] = str(error)
                save_state(state)
                raise
        if not any(d['id'] == artwork_id for d in state.get('deliveries', [])):
            state.setdefault('deliveries', []).append({"id": artwork_id})
        state['last_end'] = _iso(end)
        state['last_error'] = None
        state['last_result'] = f"Published {artwork_id}"
        save_state(state)
        retry_deliveries(state)
        return {"status": "published", "artwork_id": artwork_id,
                "pending_delivery": sum(not d.get('delivered_at') for d in state['deliveries'])}
