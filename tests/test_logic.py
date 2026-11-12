"""Unit tests for the logic and data layers (no GUI needed). Run: python -m unittest -v"""
import json, tempfile, unittest
from pathlib import Path

from srm.models import Student, ValidationError, grade_for, validate
from srm.storage import StudentRepository


def make(**kw):
    base = dict(student_id="02230001", name="Tashi Dorji", gender="Male", programme="BSc IT",
                year=2, email="tashi@example.edu.bt", dob="2004-05-01",
                marks={"Programming": 80, "Mathematics": 70, "Databases": 60, "English": 50})
    base.update(kw)
    return Student(**base)


class TestModels(unittest.TestCase):
    def test_average_and_grade(self):
        s = make()
        self.assertEqual(s.average, 65.0)
        self.assertEqual(s.grade, "C")

    def test_grade_boundaries(self):
        self.assertEqual(grade_for(80), "A")
        self.assertEqual(grade_for(39.9), "F")

    def test_bad_id_rejected(self):
        with self.assertRaises(ValidationError):
            validate(make(student_id="12ab"))

    def test_bad_name_and_email_both_reported(self):
        with self.assertRaises(ValidationError) as ctx:
            validate(make(name="", email="not-an-email"))
        fields = {f for f, _ in ctx.exception.errors}
        self.assertEqual(fields, {"name", "email"})


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "students.json"
        self.repo = StudentRepository(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_persists_across_reload(self):
        self.repo.add(make())
        again = StudentRepository(self.path); again.load()
        self.assertEqual(again.get("02230001").name, "Tashi Dorji")

    def test_duplicate_id_rejected(self):
        self.repo.add(make())
        with self.assertRaises(ValidationError):
            self.repo.add(make(name="Someone Else"))

    def test_update_and_delete(self):
        self.repo.add(make())
        self.repo.update("02230001", make(name="Tashi D"))
        self.assertEqual(self.repo.get("02230001").name, "Tashi D")
        self.repo.delete("02230001")
        self.assertIsNone(self.repo.get("02230001"))

    def test_search_filters(self):
        self.repo.add(make())
        self.repo.add(make(student_id="02230002", name="Pema Choden", programme="BBA"))
        self.assertEqual(len(self.repo.search("pema")), 1)
        self.assertEqual(len(self.repo.search(programme="BSc IT")), 1)
        self.assertEqual(len(self.repo.search(min_avg=90)), 0)

    def test_corrupt_file_does_not_crash(self):
        self.path.write_text("{ this is not json", encoding="utf-8")
        self.repo.load()
        self.assertEqual(self.repo.all(), [])
        self.assertIsNotNone(self.repo.load_warning)


if __name__ == "__main__":
    unittest.main()
