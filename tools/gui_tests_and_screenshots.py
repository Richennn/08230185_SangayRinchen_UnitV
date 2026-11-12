"""Drive the real MainWindow, record test results and save screenshots for the report.

Run from the project folder:  python tools/gui_tests_and_screenshots.py
It works on a COPY of data/students.sample.json, so your real data file is not touched.
Results -> report/test_results.json, screenshots -> report/img/
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import QDate, QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

from srm import config
from srm.storage import StudentRepository
from srm.ui.main_window import MainWindow
from srm.ui.screenshot import grab_with_frame
from srm.ui.theme import load_stylesheet

IMG = ROOT / "report" / "img"
IMG.mkdir(parents=True, exist_ok=True)

app = QApplication(sys.argv)
app.setStyleSheet(load_stylesheet())

tmp = Path(tempfile.mkdtemp())
data = tmp / "students.json"
shutil.copy(ROOT / "data" / "students.sample.json", data)
repo = StudentRepository(data); repo.load()
win = MainWindow(repo)
win.show()
app.processEvents()

# Record message boxes instead of blocking on them.
popups: list[tuple[str, str]] = []
answer = {"value": QMessageBox.StandardButton.Yes}
QMessageBox.warning = lambda parent, title, text, *a, **k: popups.append((title, text))
QMessageBox.critical = lambda parent, title, text, *a, **k: popups.append((title, text))
QMessageBox.question = lambda parent, title, text, *a, **k: (popups.append((title, text)), answer["value"])[1]

results = []


def record(num, action, inp, expected, ok_fn, actual_fn):
    app.processEvents()
    actual = actual_fn()
    results.append({"#": num, "action": action, "input": inp, "expected": expected,
                     "actual": actual, "result": "Pass" if ok_fn() else "Fail"})


def shot(name, widget=None):
    """Save a screenshot of the window (or dialog) with its title bar."""
    loop = QEventLoop()
    QTimer.singleShot(400, loop.quit)       # let the window manager draw the frame first
    loop.exec()
    grab_with_frame(widget or win).save(str(IMG / f"{name}.png"))


def fill(sid="02230099", name="Dawa Lhamo", email="dawa.lhamo@example.edu.bt", marks=(78, 66, 81, 72)):
    win.clear_form()
    win.id_edit.setText(sid); win.name_edit.setText(name); win.email_edit.setText(email)
    win.gender_group.button(1).setChecked(True)
    win.programme_combo.setCurrentText("BSc IT"); win.year_spin.setValue(2)
    win.dob_edit.setDate(QDate(2004, 6, 15))
    for spin, m in zip(win.mark_spins.values(), marks):
        spin.setValue(m)


start = len(repo.all())
shot("01_records_main")

# 1 add valid
fill(); win.add_btn.click()
record(1, "Add a new student", "02230099, Dawa Lhamo, valid email, marks 78/66/81/72",
       "Row added; status bar confirms; count +1",
       lambda: repo.get("02230099") is not None and len(repo.all()) == start + 1,
       lambda: f"Added; {len(repo.all())} records; status: '{win.statusBar().currentMessage()}'")

# 2 persistence
reloaded = StudentRepository(data); reloaded.load()
record(2, "Close and reopen data file", "-", "Dawa Lhamo still present after reload",
       lambda: reloaded.get("02230099") is not None,
       lambda: "Found after reload" if reloaded.get("02230099") else "Missing")

# 3 invalid id
popups.clear(); fill(sid="12ab"); win.add_btn.click()
shot("06_validation_error")
record(3, "Add with invalid Student ID", "ID '12ab'", "Error dialog; ID field highlighted red; nothing saved",
       lambda: bool(popups) and win.id_edit.property("invalid") and repo.get("12ab") is None,
       lambda: f"Dialog '{popups[-1][0]}': {popups[-1][1]}" if popups else "No dialog")

# 4 empty name
popups.clear(); fill(sid="02230100", name=""); win.add_btn.click()
record(4, "Add with empty name", "Name ''", "Error 'Name must be 2-60 letters'",
       lambda: any("Name must" in t for _, t in popups),
       lambda: popups[-1][1] if popups else "No dialog")

# 5 bad email
popups.clear(); fill(sid="02230101", email="dawa@"); win.add_btn.click()
record(5, "Add with invalid email", "Email 'dawa@'", "Error 'Email is not valid'",
       lambda: any("Email" in t for _, t in popups),
       lambda: popups[-1][1] if popups else "No dialog")

# 6 duplicate id
popups.clear(); fill(sid="02230001"); win.add_btn.click()
record(6, "Add with an ID that already exists", "ID 02230001", "Error 'already exists'; original record unchanged",
       lambda: any("already exists" in t for _, t in popups) and repo.get("02230001").name == "Tashi Dorji",
       lambda: popups[-1][1] if popups else "No dialog")

# 7 dob out of range
popups.clear(); fill(sid="02230102"); win.dob_edit.setDate(QDate(2024, 1, 1)); win.add_btn.click()
record(7, "Add with date of birth giving age < 15", "DOB 2024-01-01", "Error about age range",
       lambda: any("age" in t for _, t in popups),
       lambda: popups[-1][1] if popups else "No dialog")

# 8 mark above 100 (spin box clamps)
fill(sid="02230103"); win.mark_spins["English"].setValue(150)
record(8, "Type 150 into a mark spin box", "English = 150", "Value clamped to 100 by QSpinBox",
       lambda: win.mark_spins["English"].value() == 100,
       lambda: f"Spin box value = {win.mark_spins['English'].value()}")
win.clear_form()

# 9 select row -> form filled
win.table.selectRow(0)
shot("02_record_selected")
record(9, "Click first table row", "Row 0", "Form shows that student; Update/Delete enabled",
       lambda: win.id_edit.text() == win.table.item(0, 0).text() and win.update_btn.isEnabled(),
       lambda: f"Form ID={win.id_edit.text()}, Update enabled={win.update_btn.isEnabled()}")

# 10 update
sel = win.id_edit.text()
win.mark_spins["Programming"].setValue(99); win.update_btn.click()
record(10, "Edit a mark and click Update", f"{sel}: Programming -> 99", "Saved; table average updated",
       lambda: repo.get(sel).marks["Programming"] == 99,
       lambda: f"Programming = {repo.get(sel).marks['Programming']}, avg {repo.get(sel).average}")

# 11 delete -> No
popups.clear(); answer["value"] = QMessageBox.StandardButton.No
win.table.selectRow(0); sel = win.id_edit.text(); win.delete_btn.click()
record(11, "Delete, then answer No", sel, "Confirmation shown; record kept",
       lambda: bool(popups) and repo.get(sel) is not None,
       lambda: f"Asked '{popups[-1][1].splitlines()[0]}'; record kept={repo.get(sel) is not None}")

# 12 delete -> Yes
answer["value"] = QMessageBox.StandardButton.Yes
win.table.selectRow(0); sel = win.id_edit.text(); win.delete_btn.click()
record(12, "Delete, then answer Yes", sel, "Record removed; count -1",
       lambda: repo.get(sel) is None,
       lambda: f"Removed={repo.get(sel) is None}; {len(repo.all())} records")

# 13 search
win.search_edit.setText("pema")
shot("03_search_filter")
record(13, "Type in search box", "'pema'", "Only matching names listed",
       lambda: win.table.rowCount() == 1 and "Pema" in win.table.item(0, 1).text(),
       lambda: f"{win.table.rowCount()} row(s): {win.table.item(0, 1).text() if win.table.rowCount() else '-'}")
win.search_edit.clear()

# 14 slider
win.min_slider.setValue(70)
expected_rows = len(repo.search(min_avg=70))
record(14, "Drag min-average slider", "70", "Only students with average >= 70 shown",
       lambda: win.table.rowCount() == expected_rows and all(float(win.table.item(r, 4).text()) >= 70
                                                             for r in range(win.table.rowCount())),
       lambda: f"{win.table.rowCount()} row(s), lowest avg "
               f"{min((float(win.table.item(r, 4).text()) for r in range(win.table.rowCount())), default='-')}")
win.min_slider.setValue(0)

# 15 corrupt file
bad = tmp / "bad.json"; bad.write_text("{ broken", encoding="utf-8")
bad_repo = StudentRepository(bad); bad_repo.load()
record(15, "Start with a corrupt data file", "'{ broken'", "Warning shown, backup kept, app starts empty (no crash)",
       lambda: bad_repo.load_warning is not None and (tmp / "bad.corrupt.json").exists(),
       lambda: bad_repo.load_warning or "No warning")

# Summary tab + dialogs
win.centralWidget().setCurrentIndex(1)
shot("04_summary")
win.centralWidget().setCurrentIndex(0)

about = QMessageBox(QMessageBox.Icon.Information, "About",
                    f"<b>{config.APP_NAME}</b><br>Unit V assignment - PyQt6<br><br>"
                    f"Name: {config.STUDENT_NAME}<br>Roll no: {config.ROLL_NO}", parent=win)
about.show(); shot("05_about", about); about.close()
s = repo.all()[0]
confirm = QMessageBox(QMessageBox.Icon.Question, "Delete student",
                      f"Delete {s.name} ({s.student_id})?\nThis cannot be undone.",
                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, win)
confirm.show(); shot("07_delete_confirm", confirm); confirm.close()

win.resize(920, 580); shot("08_resized_small")

(ROOT / "report" / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
passed = sum(r["result"] == "Pass" for r in results)
print(f"{passed}/{len(results)} GUI test cases passed")
for r in results:
    print(r["#"], r["result"], "-", r["actual"])
QTimer.singleShot(0, app.quit)
app.exec()
