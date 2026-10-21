import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('doctor', Path(__file__).resolve().parents[1] / 'tools' / 'codex_doctor.py')
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.state = self.home / '.codex-global-state.json'

    def write_state(self, data):
        self.state.write_text(json.dumps(data), encoding='utf-8')

    def database(self, nested=False):
        folder = self.home / 'sqlite' if nested else self.home
        folder.mkdir(exist_ok=True)
        path = folder / 'state_5.sqlite'
        with sqlite3.connect(path) as db:
            db.executescript("CREATE TABLE projects(id TEXT, name TEXT); INSERT INTO projects VALUES ('private-project-id','Private Project Name'); CREATE TABLE threads(id TEXT, cwd TEXT, title TEXT, project_id TEXT); INSERT INTO threads VALUES ('private-thread-id','/home/private-user/secret-repo','Private Conversation',NULL);")
        return path

    def codes(self, report):
        return {item['code'] for item in report['findings']}

    def test_nul_state_and_intact_definitions(self):
        self.state.write_bytes(b'\0\0')
        self.database()
        result = doctor.diagnose(self.home)
        self.assertEqual(result['state']['nul_characters'], 2)
        self.assertIn('STATE_PARSE_FAILED', self.codes(result))
        self.assertIn('PROJECT_DEFINITIONS_WITHOUT_CACHE', self.codes(result))

    def test_valid_empty_state_can_still_lack_cache(self):
        self.write_state({})
        self.database()
        result = doctor.diagnose(self.home)
        self.assertEqual(result['state']['status'], 'valid')
        self.assertIn('PROJECT_DEFINITIONS_WITHOUT_CACHE', self.codes(result))

    def test_missing_directory_not_created(self):
        missing = self.home / 'missing'
        result = doctor.diagnose(missing)
        self.assertFalse(missing.exists())
        self.assertIn('STATE_MISSING', self.codes(result))

    def test_unknown_schema_and_corrupt_db(self):
        self.write_state({'local-projects': []})
        (self.home / 'state_9.sqlite').write_bytes(b'not a database')
        result = doctor.diagnose(self.home)
        self.assertEqual(result['state']['status'], 'schema_not_supported')
        self.assertEqual(result['databases'][0]['status'], 'unavailable')

    def test_legacy_threads_without_project_id(self):
        self.write_state({})
        with sqlite3.connect(self.home / 'state_1.sqlite') as db:
            db.execute('CREATE TABLE threads(id TEXT)')
        result = doctor.diagnose(self.home)
        self.assertEqual(result['databases'][0]['threads_records'], 0)
        self.assertNotIn('threads_with_project_id', result['databases'][0])

    def test_multiple_candidates_not_selected(self):
        self.write_state({})
        self.database()
        self.database(nested=True)
        result = doctor.diagnose(self.home)
        self.assertIn('MULTIPLE_DATABASE_CANDIDATES', self.codes(result))
        self.assertNotIn('active_database', result)

    def test_no_sensitive_metadata_or_mutation(self):
        self.write_state({'local-projects': {'private-project-id': {'name':'Private Project Name','rootPaths':['/home/private-user/secret-repo']}},'thread-project-assignments': {'private-thread-id': {'projectKind':'local','projectId':'private-project-id'}}})
        self.database()
        (self.home / 'auth.json').write_text('{"token":"DO_NOT_READ_OR_PRINT"}')
        before = {path.name:path.read_bytes() for path in self.home.iterdir()}
        result = doctor.diagnose(self.home)
        after = {path.name:path.read_bytes() for path in self.home.iterdir()}
        self.assertEqual(before, after)
        text = json.dumps(result)
        for secret in ('private-project-id','private-thread-id','Private Project Name','Private Conversation','private-user','secret-repo','DO_NOT_READ_OR_PRINT',str(self.home)):
            self.assertNotIn(secret, text)

    def test_report_never_overwrites(self):
        self.write_state({})
        output = self.home / 'report.json'
        output.write_text('keep')
        with self.assertRaises(SystemExit) as caught:
            doctor.main(['--codex-home',str(self.home),'--output',str(output)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(output.read_text(), 'keep')

    def test_explicit_home_wins_over_environment(self):
        with patch.dict(os.environ, {'CODEX_HOME':str(self.home / 'env')}):
            self.assertEqual(doctor.choose_home(str(self.home)), self.home.resolve())

    def test_invalid_root_and_unhashable_assignment(self):
        self.write_state([])
        self.assertEqual(doctor.diagnose(self.home)['state']['status'], 'invalid_root_type')
        self.write_state({'thread-project-assignments':{'synthetic':{'projectKind':'local','projectId':[]}}})
        self.assertEqual(doctor.diagnose(self.home)['state']['local_assignments_without_cached_project'], 1)


if __name__ == '__main__':
    unittest.main()
