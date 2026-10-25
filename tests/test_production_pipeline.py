import sys
import io
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import birdnet_go
import generation_settings
import production_pipeline as pipeline
from server import Handler

TZ = ZoneInfo('Europe/London')


class ProductionTests(unittest.TestCase):
    def test_multipart_upload_parser_without_deprecated_cgi(self):
        boundary = 'birdcanvas-test'
        body = (b'--birdcanvas-test\r\nContent-Disposition: form-data; name="title"\r\n\r\n'
                b'Garden\r\n--birdcanvas-test\r\nContent-Disposition: form-data; '
                b'name="image"; filename="bird.png"\r\nContent-Type: image/png\r\n\r\n'
                b'\x89PNGdata\r\n--birdcanvas-test--\r\n')
        handler = Handler.__new__(Handler)
        handler.rfile = io.BytesIO(body)
        form = handler.read_multipart(len(body), f'multipart/form-data; boundary={boundary}')
        self.assertEqual(handler.form_text(form, 'title', ''), 'Garden')
        self.assertEqual(form['image'].get_filename(), 'bird.png')
        self.assertEqual(form['image'].get_payload(decode=True), b'\x89PNGdata')

    def test_tv_cleanup_removes_only_old_recorded_uploads(self):
        with tempfile.TemporaryDirectory() as folder:
            state = {"deliveries": [], "uploads": [f"MY_{n}" for n in range(12)]}
            with patch.object(pipeline, 'STATE_FILE', Path(folder) / 'state.json'), \
                 patch.object(pipeline, 'frame_enabled', return_value=True), \
                 patch.object(pipeline, '_run_samsungtv', return_value='OK') as command:
                pipeline.retry_deliveries(state)
            self.assertEqual(state['uploads'], [f"MY_{n}" for n in range(2, 12)])
            self.assertEqual([c.args for c in command.call_args_list],
                             [('art-delete', 'MY_0'), ('art-delete', 'MY_1')])

    def test_calendar_boundaries_are_local_and_predictable(self):
        now = datetime(2026, 9, 23, 10, tzinfo=TZ)
        self.assertEqual(generation_settings.scheduled_boundary(now, 'daily').day, 23)
        self.assertEqual(generation_settings.scheduled_boundary(now, 'twice_weekly').day, 21)
        self.assertEqual(generation_settings.next_boundary(now, 'twice_weekly').day, 24)
        self.assertEqual(generation_settings.next_boundary(now, 'weekly').day, 28)
        before = datetime(2026, 10, 25, 3, tzinfo=TZ)
        self.assertEqual(generation_settings.next_boundary(before, 'daily').hour, 4)

    def test_birdnet_pagination_exact_window_confidence_and_unique_species(self):
        start = datetime(2026, 9, 21, 4, tzinfo=TZ)
        end = datetime(2026, 9, 24, 4, tzinfo=TZ)
        rows_by_day = {
            '2026-09-21': [
                {'timestamp': '2026-09-21T03:59:59+01:00', 'commonName': 'Robin', 'confidence': .9},
                {'timestamp': '2026-09-21T04:00:00+01:00', 'commonName': 'Robin', 'confidence': .9},
            ],
            '2026-09-22': [],
            '2026-09-23': [
                {'timestamp': '2026-09-23T11:00:00+01:00', 'commonName': 'Robin', 'confidence': .9},
                {'timestamp': '2026-09-23T12:00:00+01:00', 'commonName': 'Blue Tit', 'confidence': .2},
            ],
            '2026-09-24': [
                {'timestamp': '2026-09-24T04:00:00+01:00', 'commonName': 'Blackbird', 'confidence': .9},
            ],
        }
        requested_days = []

        def fetch(_, params):
            # BirdNET-Go has shown incomplete results for multi-day date ranges,
            # so BirdCanvas must query one station-local calendar day at a time.
            self.assertEqual(params['start_date'], params['end_date'])
            requested_days.append(params['start_date'])
            rows = rows_by_day[params['start_date']]
            offset = params['offset']
            limit = params['limit']
            return {'data': rows[offset:offset+limit], 'total': len(rows)}

        with patch.object(birdnet_go, '_get', side_effect=fetch), patch.dict('os.environ', {'BIRDCANVAS_MIN_CONFIDENCE': '0.5'}):
            result = birdnet_go.detections(start, end)

        self.assertEqual(result['species'], ['Robin'])
        self.assertEqual(result['detections_total'], 2)
        self.assertEqual(result['last_accepted_bird']['name'], 'Robin')
        self.assertEqual(result['latest_birdnet_detection']['name'], 'Blue Tit')
        self.assertEqual(result['latest_birdnet_detection']['filter_reason'], 'low_confidence')
        self.assertEqual(result['latest_birdnet_detection']['confidence'], 0.2)
        self.assertEqual(result['minimum_confidence'], 0.5)
        self.assertEqual(
            requested_days,
            ['2026-09-21', '2026-09-22', '2026-09-23', '2026-09-24'],
        )

    def test_live_activity_reports_rejected_and_empty_detections(self):
        start = datetime(2026, 10, 13, 4, tzinfo=TZ)
        end = datetime(2026, 10, 13, 15, tzinfo=TZ)
        rows = [
            {'timestamp': '2026-10-13T08:21:01+01:00',
             'commonName': 'Common Magpie', 'confidence': .62},
            {'timestamp': '2026-10-13T11:34:35+01:00',
             'commonName': 'European Goldfinch', 'confidence': .25},
            {'timestamp': '2026-10-13T11:36:00+01:00',
             'commonName': 'European Robin', 'confidence': .91,
             'verified': 'false_positive'},
        ]
        with patch.object(birdnet_go, '_daily_rows', return_value=rows):
            result = birdnet_go.detections(start, end)
        self.assertEqual(result['detections_total'], 1)
        self.assertEqual(result['last_accepted_bird']['name'], 'Common Magpie')
        self.assertEqual(result['latest_birdnet_detection']['name'], 'European Robin')
        self.assertEqual(result['latest_birdnet_detection']['filter_reason'], 'rejected')
        self.assertFalse(result['latest_birdnet_detection']['accepted'])
        with patch.object(birdnet_go, '_daily_rows', return_value=[]):
            empty = birdnet_go.detections(start, end)
        self.assertIsNone(empty['last_accepted_bird'])
        self.assertIsNone(empty['latest_birdnet_detection'])

    def test_live_activity_when_latest_detection_is_accepted(self):
        start = datetime(2026, 10, 13, 4, tzinfo=TZ)
        end = datetime(2026, 10, 13, 15, tzinfo=TZ)
        row = {'timestamp': '2026-10-13T11:34:35+01:00',
               'commonName': 'European Goldfinch', 'confidence': .88}
        with patch.object(birdnet_go, '_daily_rows', return_value=[row]):
            result = birdnet_go.detections(start, end)
        self.assertEqual(result['last_accepted_bird']['name'], 'European Goldfinch')
        self.assertTrue(result['latest_birdnet_detection']['accepted'])
        self.assertIsNone(result['latest_birdnet_detection']['filter_reason'])

    def test_send_gallery_artwork_uploads_once_then_reuses_frame_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = root / 'archived-artwork.png'
            image.write_bytes(b'image')
            upload_calls = []

            def upload(source, content_id=None, on_uploaded=None):
                upload_calls.append((Path(source), content_id))
                selected = content_id or 'MY_GALLERY_1'
                if content_id is None and on_uploaded:
                    on_uploaded(selected)
                return {'content_id': selected}

            with patch.object(pipeline, 'STATE_FILE', root / 'state.json'), \
                 patch.object(pipeline, 'LOCK_FILE', root / 'lock'), \
                 patch.object(pipeline, 'DATA_DIR', root), \
                 patch.object(pipeline, 'frame_enabled', return_value=True), \
                 patch.object(pipeline, 'artwork_image_path', return_value=image), \
                 patch.object(pipeline, 'upload_to_frame', side_effect=upload):
                first = pipeline.send_artwork_to_frame('older-artwork')
                second = pipeline.send_artwork_to_frame('older-artwork')
                state = pipeline.load_state()

            self.assertFalse(first['reused'])
            self.assertTrue(second['reused'])
            self.assertEqual(first['content_id'], 'MY_GALLERY_1')
            self.assertEqual(second['content_id'], 'MY_GALLERY_1')
            self.assertEqual(upload_calls, [(image, None), (image, 'MY_GALLERY_1')])
            self.assertEqual(state['uploads'], ['MY_GALLERY_1'])
            self.assertEqual(state['frame_content']['older-artwork'], 'MY_GALLERY_1')
            self.assertEqual(state['last_manual_delivery']['artwork_id'], 'older-artwork')

    def test_send_gallery_artwork_requires_frame_integration(self):
        with patch.object(pipeline, 'frame_enabled', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'currently disabled'):
                pipeline.send_artwork_to_frame('older-artwork')

    def test_style_test_reuses_real_observations_without_advancing_daily_cursor(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            current = root / "current"
            current.mkdir()
            (current / "manifest.json").write_text(__import__("json").dumps({
                "collection": "birdcanvas",
                "observation_date": "2026-10-14",
                "observation_window": "previous daily collection",
                "species_detected": ["Robin", "Blue Tit", "Woodpigeon"],
                "detections_total": 5,
            }))
            state_path = root / "state.json"
            old_end = "2026-10-15T04:00:00+01:00"
            state_path.write_text(__import__("json").dumps({
                "last_end": old_end, "deliveries": [], "uploads": [],
            }))
            image = root / "art.png"
            image.write_bytes(b"test image")
            now = datetime(2026, 10, 15, 7, 50, tzinfo=TZ)
            with patch.object(pipeline, "CURRENT_DIR", current), \
                 patch.object(pipeline, "STATE_FILE", state_path), \
                 patch.object(pipeline, "LOCK_FILE", root / "lock"), \
                 patch.object(pipeline, "DATA_DIR", root), \
                 patch.object(pipeline, "load_settings", return_value={
                     "frequency": "daily", "excluded_birds": ["pigeon"],
                 }), \
                 patch.object(pipeline, "compose", return_value={
                     "output": str(image), "birds": ["Robin"], "brief": {
                         "art_style": "Pop art",
                     }, "generation": {},
                 }) as composer, \
                 patch.object(pipeline, "publish_artwork", return_value={
                     "id": "birdcanvas-test-pop-art",
                 }) as publisher, \
                 patch.object(pipeline, "build_display_page"), \
                 patch.object(pipeline, "retry_deliveries"):
                result = pipeline.run_style_test("Pop art", now=now)
            self.assertEqual(result["art_style"], "Pop art")
            self.assertTrue(result["next_collection_unchanged"])
            self.assertEqual(
                __import__("json").loads(state_path.read_text())["last_end"],
                old_end,
            )
            self.assertEqual(
                __import__("json").loads(state_path.read_text())["deliveries"],
                [{"id": "birdcanvas-test-pop-art"}],
            )
            self.assertEqual(composer.call_args.kwargs["style_override"], "Pop art")
            self.assertEqual(composer.call_args.kwargs["birds"], ["Robin", "Blue Tit"])
            self.assertEqual(publisher.call_args.kwargs["species_detected"],
                             ["Robin", "Blue Tit", "Woodpigeon"])
            self.assertEqual(publisher.call_args.kwargs["species_eligible"],
                             ["Robin", "Blue Tit"])

    def test_manual_only_birds_drive_the_next_artwork_without_fake_detections(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = root / "art.png"
            image.write_bytes(b"test")
            now = datetime(2026, 10, 24, 4, tzinfo=TZ)
            sightings = [{"id": "test", "name": "Kingfisher",
                          "seen_at": "2026-10-23T15:00:00+01:00"}]
            with patch.object(pipeline, "STATE_FILE", root / "state.json"),                  patch.object(pipeline, "LOCK_FILE", root / "lock"),                  patch.object(pipeline, "DATA_DIR", root),                  patch.object(pipeline, "ARCHIVE_DIR", root / "archive"),                  patch.object(pipeline, "load_settings", return_value={"frequency": "daily", "excluded_birds": ["gull"]}),                  patch.object(pipeline, "detections", return_value={"species": [], "detections_total": 0}),                  patch.object(pipeline, "sightings_between", return_value=sightings),                  patch.object(pipeline, "compose", return_value={"output": str(image), "birds": ["Kingfisher"], "brief": {}}) as composer,                  patch.object(pipeline, "publish_artwork", return_value={"id": "test"}) as publisher,                  patch.object(pipeline, "build_display_page"),                  patch.object(pipeline, "retry_deliveries"):
                result = pipeline.run(now=now)
            self.assertEqual(result["status"], "published")
            self.assertEqual(composer.call_args.kwargs["birds"], ["Kingfisher"])
            self.assertEqual(composer.call_args.kwargs["priority_birds"], ["Kingfisher"])
            self.assertEqual(publisher.call_args.kwargs["species_detected"], [])
            self.assertEqual(publisher.call_args.kwargs["species_sighted"], ["Kingfisher"])
            self.assertEqual(publisher.call_args.kwargs["detections_total"], 0)
            self.assertEqual(publisher.call_args.kwargs["sightings_total"], 1)

    def test_style_test_preserves_visual_and_acoustic_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            current = root / "current"
            current.mkdir()
            (current / "manifest.json").write_text(__import__("json").dumps({
                "collection": "birdcanvas",
                "species_detected": ["Robin"],
                "species_sighted": ["Kingfisher"],
                "species_observed": ["Robin", "Kingfisher"],
                "sightings_total": 1, "detections_total": 3,
            }))
            image = root / "generated.png"
            image.write_bytes(b"test")
            with patch.object(pipeline, "CURRENT_DIR", current),                  patch.object(pipeline, "STATE_FILE", root / "state.json"),                  patch.object(pipeline, "LOCK_FILE", root / "lock"),                  patch.object(pipeline, "DATA_DIR", root),                  patch.object(pipeline, "load_settings", return_value={"frequency": "daily", "excluded_birds": []}),                  patch.object(pipeline, "compose", return_value={"output": str(image), "birds": ["Kingfisher"], "brief": {}}) as composer,                  patch.object(pipeline, "publish_artwork", return_value={"id": "test"}) as publisher,                  patch.object(pipeline, "build_display_page"),                  patch.object(pipeline, "retry_deliveries"):
                pipeline.run_style_test("Pop art", now=datetime(2026, 10, 24, 11, tzinfo=TZ))
            self.assertEqual(composer.call_args.kwargs["birds"], ["Robin", "Kingfisher"])
            self.assertEqual(composer.call_args.kwargs["priority_birds"], ["Kingfisher"])
            self.assertEqual(publisher.call_args.kwargs["species_detected"], ["Robin"])
            self.assertEqual(publisher.call_args.kwargs["species_sighted"], ["Kingfisher"])


    def test_daily_empty_collection_reuses_real_birds_without_falsifying_today(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "archive"
            previous = archive / "previous"
            previous.mkdir(parents=True)
            (previous / "manifest.json").write_text(json.dumps({
                "id": "previous",
                "collection": "birdcanvas",
                "generation_frequency": "daily",
                "observation_date": "2026-10-24",
                "observation_ended_at": "2026-10-24T04:00:00+01:00",
                "species_detected": ["Robin", "Woodpigeon"],
                "species_sighted": ["Kingfisher"],
            }))
            image = root / "art.png"
            image.write_bytes(b"image")
            with patch.object(pipeline, "DATA_DIR", root), \
                 patch.object(pipeline, "ARCHIVE_DIR", archive), \
                 patch.object(pipeline, "CURRENT_DIR", root / "current"), \
                 patch.object(pipeline, "STATE_FILE", root / "state.json"), \
                 patch.object(pipeline, "LOCK_FILE", root / "lock"), \
                 patch.object(pipeline, "load_settings", return_value={
                     "frequency": "daily", "excluded_birds": ["pigeon"]}), \
                 patch.object(pipeline, "detections", return_value={
                     "species": [], "detections_total": 0}), \
                 patch.object(pipeline, "sightings_between", return_value=[]), \
                 patch.object(pipeline, "compose", return_value={
                     "output": str(image), "birds": ["Robin"], "brief": {}}) as composer, \
                 patch.object(pipeline, "publish_artwork", return_value={"id": "fresh"}) as publisher, \
                 patch.object(pipeline, "build_display_page"), \
                 patch.object(pipeline, "retry_deliveries"):
                now = datetime(2026, 10, 25, 4, tzinfo=TZ)
                result = pipeline.run(now=now)
                self.assertEqual(result["status"], "published")
                self.assertEqual(pipeline.load_state()["last_end"], now.isoformat(timespec="seconds"))
            self.assertEqual(composer.call_args.kwargs["birds"], ["Robin", "Kingfisher"])
            self.assertEqual(composer.call_args.kwargs["priority_birds"], ["Kingfisher"])
            self.assertEqual(publisher.call_args.kwargs["detections_total"], 0)
            self.assertEqual(publisher.call_args.kwargs["species_detected"], [])
            self.assertEqual(publisher.call_args.kwargs["species_sighted"], [])
            self.assertEqual(publisher.call_args.kwargs["species_observed"], [])
            self.assertEqual(publisher.call_args.kwargs["species_eligible"], ["Robin", "Kingfisher"])
            self.assertEqual(publisher.call_args.kwargs["observation_fallback"]["source_artwork_id"], "previous")
            self.assertIn("previous observations", publisher.call_args.kwargs["title"])

    def test_fallback_does_not_recycle_previous_fallback_or_old_observations(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder)
            yesterday = archive / "yesterday"
            yesterday.mkdir()
            (yesterday / "manifest.json").write_text(json.dumps({
                "id": "yesterday",
                "collection": "birdcanvas",
                "observation_date": "2026-10-24",
                "observation_ended_at": "2026-10-24T04:00:00+01:00",
                "species_detected": [],
                "species_sighted": [],
                "observation_fallback": {"source_artwork_id": "very-old"},
                "species_eligible": ["Robin"],
            }))
            older = archive / "older"
            older.mkdir()
            (older / "manifest.json").write_text(json.dumps({
                "id": "older",
                "collection": "birdcanvas",
                "observation_date": "2026-10-22",
                "observation_ended_at": "2026-10-22T04:00:00+01:00",
                "species_detected": ["Blue Tit"],
                "species_sighted": [],
            }))
            with patch.object(pipeline, "ARCHIVE_DIR", archive), \
                 patch.object(pipeline, "CURRENT_DIR", archive / "current"):
                result = pipeline._previous_observations(
                    datetime(2026, 10, 25, 4, tzinfo=TZ), [])
                self.assertEqual(result["species"], ["Blue Tit"])
                self.assertEqual(result["source_artwork_id"], "older")
                stale = pipeline._previous_observations(
                    datetime(2026, 11, 15, 4, tzinfo=TZ), [])
                self.assertIsNone(stale)

    def test_non_daily_collection_with_no_birds_does_not_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(pipeline, "DATA_DIR", root), \
                 patch.object(pipeline, "ARCHIVE_DIR", root / "archive"), \
                 patch.object(pipeline, "CURRENT_DIR", root / "current"), \
                 patch.object(pipeline, "STATE_FILE", root / "state.json"), \
                 patch.object(pipeline, "LOCK_FILE", root / "lock"), \
                 patch.object(pipeline, "load_settings", return_value={
                     "frequency": "weekly", "excluded_birds": []}), \
                 patch.object(pipeline, "detections", return_value={
                     "species": [], "detections_total": 0}), \
                 patch.object(pipeline, "sightings_between", return_value=[]), \
                 patch.object(pipeline, "compose") as composer, \
                 patch.object(pipeline, "retry_deliveries"):
                result = pipeline.run(
                    now=datetime(2026, 10, 26, 4, tzinfo=TZ))
                self.assertEqual(result["status"], "no_birds")
                self.assertIsNone(pipeline.load_state().get("last_end"))
                composer.assert_not_called()

    def test_combining_heard_and_sighted_deduplicates_matching_species(self):
        observed, seen = pipeline._observed_species(
            ["Robin", "Blue Tit"], [{"name": "robin"}, {"name": "Kingfisher"}])
        self.assertEqual(observed, ["Robin", "Blue Tit", "Kingfisher"])
        self.assertEqual(seen, ["Robin", "Kingfisher"])

    def test_one_publication_and_retry_same_artwork_after_frame_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state_file = root / 'state.json'
            lock_file = root / 'lock'
            archive = root / 'archive'
            image = root / 'generated.png'
            image.write_bytes(b'image')
            now = datetime(2026, 9, 24, 4, tzinfo=TZ)
            observations = {'species': ['Robin', 'Blue Tit', 'Woodpigeon'], 'detections_total': 4}
            def publish(**kwargs):
                self.assertEqual(kwargs['birds'], ['Robin'])
                self.assertEqual(kwargs['species_detected'], ['Robin', 'Blue Tit', 'Woodpigeon'])
                self.assertEqual(kwargs['species_eligible'], ['Robin', 'Blue Tit'])
                self.assertEqual(kwargs['species_used'], ['Robin'])
                self.assertEqual(kwargs['species_not_featured'], ['Blue Tit'])
                self.assertEqual(kwargs['species_excluded'], ['Woodpigeon'])
                manifest = {'id': 'birdcanvas-2026-09-24-twice-weekly-20260924-040000'}
                folder = archive / manifest['id']
                folder.mkdir(parents=True)
                (folder / 'manifest.json').write_text(__import__('json').dumps(manifest))
                (folder / 'artwork.png').write_bytes(b'image')
                return manifest
            patches = [
                patch.object(pipeline, 'STATE_FILE', state_file),
                patch.object(pipeline, 'LOCK_FILE', lock_file),
                patch.object(pipeline, 'DATA_DIR', root),
                patch.object(pipeline, 'ARCHIVE_DIR', archive),
                patch.object(pipeline, 'load_settings', return_value={'frequency': 'twice_weekly', 'excluded_birds': ['pigeon']}),
                patch.object(pipeline, 'detections', return_value=observations),
                patch.object(pipeline, 'sightings_between', return_value=[]),
                patch('compose.excluded_birds', return_value=['pigeon']),
                patch.object(pipeline, 'compose', return_value={'output': str(image), 'birds': ['Robin'], 'brief': {}, 'generation': {'eligible_birds': ['Robin', 'Blue Tit'], 'featured_birds': ['Robin'], 'attempts_used': 1}}),
                patch.object(pipeline, 'publish_artwork', side_effect=publish),
                patch.object(pipeline, 'build_display_page'),
                patch.object(pipeline, 'frame_enabled', return_value=True),
                patch.object(pipeline, 'upload_to_frame', side_effect=[RuntimeError('TV offline'), {'content_id': 'MY_123'}]),
            ]
            for p in patches: p.start()
            try:
                first = pipeline.run(now=now)
                self.assertEqual(first['status'], 'published')
                self.assertEqual(first['pending_delivery'], 1)
                self.assertEqual(
                    first['artwork_id'],
                    'birdcanvas-2026-09-24-twice-weekly-20260924-040000',
                )
                self.assertEqual(
                    pipeline.load_state()['deliveries'][0]['id'],
                    'birdcanvas-2026-09-24-twice-weekly-20260924-040000',
                )
                self.assertEqual(pipeline.run(now=now)['status'], 'not_due')
                self.assertEqual(pipeline.load_state()['last_end'], now.isoformat(timespec='seconds'))
                self.assertEqual(pipeline.load_state()['deliveries'][0]['content_id'], 'MY_123')
                self.assertTrue(pipeline.load_state()['deliveries'][0]['delivered_at'])
                pipeline.compose.assert_called_once()
                pipeline.publish_artwork.assert_called_once()
            finally:
                for p in reversed(patches): p.stop()


if __name__ == '__main__':
    unittest.main()
