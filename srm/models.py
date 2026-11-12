"""Logic layer: the Student record, validation and grade calculations.

Nothing in this file imports PyQt, so it can be unit-tested without a GUI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import date

from srm.config import SUBJECTS, PROGRAMMES, PASS_MARK

STUDENT_ID_RE = re.compile(r"^\d{8}$")                 # e.g. 02230045
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,59}$")   # letters, spaces, . ' -
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


class ValidationError(ValueError):
    """Raised with a list of (field, message) pairs the UI can show to the user."""

    def __init__(self, errors: list[tuple[str, str]]):
        self.errors = errors
        super().__init__("; ".join(msg for _, msg in errors))


@dataclass
class Student:
    student_id: str
    name: str
    gender: str                      # "Male" | "Female" | "Other"
    programme: str
    year: int                        # 1-4
    email: str
    dob: str                         # ISO date "YYYY-MM-DD"
    active: bool = True
    marks: dict[str, int] = field(default_factory=lambda: {s: 0 for s in SUBJECTS})

    # ---- derived values -------------------------------------------------
    @property
    def average(self) -> float:
        return round(sum(self.marks.values()) / len(self.marks), 1) if self.marks else 0.0

    @property
    def grade(self) -> str:
        return grade_for(self.average)

    @property
    def passed(self) -> bool:
        return all(m >= PASS_MARK for m in self.marks.values())

    # ---- (de)serialisation ---------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Student":
        marks = {s: int(d.get("marks", {}).get(s, 0)) for s in SUBJECTS}
        return cls(
            student_id=str(d["student_id"]), name=str(d["name"]),
            gender=str(d.get("gender", "Other")), programme=str(d.get("programme", PROGRAMMES[0])),
            year=int(d.get("year", 1)), email=str(d.get("email", "")),
            dob=str(d.get("dob", "2005-01-01")), active=bool(d.get("active", True)), marks=marks,
        )


def grade_for(avg: float) -> str:
    """Map an average mark to a letter grade."""
    for cutoff, letter in ((80, "A"), (70, "B"), (60, "C"), (50, "D"), (PASS_MARK, "E")):
        if avg >= cutoff:
            return letter
    return "F"


def validate(student: Student) -> None:
    """Check every field; raise ValidationError listing *all* problems at once."""
    errors: list[tuple[str, str]] = []
    if not STUDENT_ID_RE.match(student.student_id):
        errors.append(("student_id", "Student ID must be exactly 8 digits, e.g. 02230045."))
    if not NAME_RE.match(student.name.strip()):
        errors.append(("name", "Name must be 2-60 letters (spaces, . ' - allowed)."))
    if student.email and not EMAIL_RE.match(student.email):
        errors.append(("email", "Email is not valid, e.g. name@rub.edu.bt."))
    if student.programme not in PROGRAMMES:
        errors.append(("programme", "Choose a programme from the list."))
    if not 1 <= student.year <= 4:
        errors.append(("year", "Year must be between 1 and 4."))
    try:
        born = date.fromisoformat(student.dob)
        age = (date.today() - born).days // 365
        if not 15 <= age <= 80:
            errors.append(("dob", "Date of birth gives an age outside 15-80 years."))
    except ValueError:
        errors.append(("dob", "Date of birth is not a valid date."))
    for subject, mark in student.marks.items():
        if not 0 <= mark <= 100:
            errors.append(("marks", f"{subject} mark must be between 0 and 100."))
    if errors:
        raise ValidationError(errors)
