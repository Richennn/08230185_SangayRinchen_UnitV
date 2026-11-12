"""Data layer: keeps students in memory and persists them to a JSON file."""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from srm.config import SUBJECTS
from srm.models import Student, validate, ValidationError


class StorageError(Exception):
    """A file could not be read or written; the message is safe to show the user."""


class StudentRepository:
    """CRUD + search over Student records, saved to `path` after every change."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._students: dict[str, Student] = {}
        self.load_warning: str | None = None   # set if the file was corrupt

    # ---- persistence ----------------------------------------------------
    def load(self) -> None:
        if not self.path.exists():
            self._students = {}
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._students = {d["student_id"]: Student.from_dict(d) for d in data["students"]}
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            # Never crash on a bad file: keep a backup and start empty.
            backup = self.path.with_suffix(".corrupt.json")
            shutil.copy(self.path, backup)
            self._students = {}
            self.load_warning = (f"The data file was damaged ({exc.__class__.__name__}). "
                                 f"A copy was kept as {backup.name}; starting with an empty list.")

    def save(self) -> None:
        payload = {"version": 1, "students": [s.to_dict() for s in self.all()]}
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self.path)          # atomic: no half-written file on crash
        except OSError as exc:
            raise StorageError(f"Could not save data: {exc.strerror}") from exc

    # ---- CRUD -----------------------------------------------------------
    def all(self) -> list[Student]:
        return sorted(self._students.values(), key=lambda s: s.student_id)

    def get(self, student_id: str) -> Student | None:
        return self._students.get(student_id)

    def add(self, student: Student) -> None:
        validate(student)
        if student.student_id in self._students:
            raise ValidationError([("student_id", f"Student ID {student.student_id} already exists.")])
        self._students[student.student_id] = student
        self.save()

    def update(self, original_id: str, student: Student) -> None:
        validate(student)
        if original_id not in self._students:
            raise ValidationError([("student_id", "That student no longer exists.")])
        if student.student_id != original_id and student.student_id in self._students:
            raise ValidationError([("student_id", f"Student ID {student.student_id} already exists.")])
        del self._students[original_id]
        self._students[student.student_id] = student
        self.save()

    def delete(self, student_id: str) -> None:
        self._students.pop(student_id, None)
        self.save()

    # ---- queries --------------------------------------------------------
    def search(self, text: str = "", programme: str = "All", min_avg: float = 0) -> list[Student]:
        text = text.strip().lower()
        return [s for s in self.all()
                if (not text or text in s.name.lower() or text in s.student_id)
                and (programme == "All" or s.programme == programme)
                and s.average >= min_avg]

    def summary(self) -> dict:
        students = self.all()
        n = len(students)
        subject_avg = {sub: round(sum(s.marks[sub] for s in students) / n, 1) if n else 0
                       for sub in SUBJECTS}
        return {
            "count": n,
            "class_average": round(sum(s.average for s in students) / n, 1) if n else 0.0,
            "pass_rate": round(100 * sum(s.passed for s in students) / n) if n else 0,
            "subject_average": subject_avg,
        }

    def export_csv(self, path: Path) -> int:
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["student_id", "name", "gender", "programme", "year", "email",
                            "dob", "active", *SUBJECTS, "average", "grade"])
                for s in self.all():
                    w.writerow([s.student_id, s.name, s.gender, s.programme, s.year, s.email,
                                s.dob, s.active, *(s.marks[x] for x in SUBJECTS), s.average, s.grade])
        except OSError as exc:
            raise StorageError(f"Could not write CSV: {exc.strerror}") from exc
        return len(self._students)
