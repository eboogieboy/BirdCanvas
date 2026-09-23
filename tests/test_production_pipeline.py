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
        rows = [
            {'timestamp': '2026-09-21T03:59:59+01:00', 'commonName': 'Robin', 'confidence': .9},
            {'timestamp': '2026-09-21T04:00:00+01:00', 'commonName': 'Robin', 'confidence': .9},
            {'timestamp': '2026-09-23T11:00:00+01:00', 'commonName': 'Robin', 'confidence': .9},
            {'timestamp': '2026-09-23T12:00:00+01:00', 'commonName': 'Blue Tit', 'confidence': .2},
            {'timestamp': '2026-09-24T04:00:00+01:00', 'commonName': 'Blackbird', 'confidence': .9},
        ]
        def fetch(_, params):
            offset = params['offset']
            return {'data': rows[offset:offset+2], 'total': len(rows)}
        with patch.object(birdnet_go, '_get', side_effect=fetch), patch.dict('os.environ', {'BIRDCANVAS_MIN_CONFIDENCE': '0.5'}):
            result = birdnet_go.detections(start, end)
        self.assertEqual(result['species'], ['Robin'])
        self.assertEqual(result['detections_total'], 2)

    def test_one_publication_and_retry_same_artwork_after_frame_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state_file = root / 'state.json'
            lock_file = root / 'lock'
            archive = root / 'archive'
            image = root / 'generated.png'
            image.write_bytes(b'image')
            now = datetime(2026, 9, 24, 4, tzinfo=TZ)
            observations = {'species': ['Robin', 'Woodpigeon'], 'detections_total': 3}
            def publish(**kwargs):
                self.assertEqual(kwargs['birds'], ['Robin'])
                self.assertEqual(kwargs['species_excluded'], ['Woodpigeon'])
                manifest = {'id': 'birdcanvas-2026-09-24-twice_weekly-20260924-040000'}
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
                patch('compose.excluded_birds', return_value=['pigeon']),
                patch.object(pipeline, 'compose', return_value={'output': str(image), 'birds': ['Robin'], 'brief': {}, 'generation': {'attempts_used': 1}}),
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
