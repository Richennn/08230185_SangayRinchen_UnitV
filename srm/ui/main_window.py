"""UI layer: the main window. It only talks to the data layer through StudentRepository."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QSplitter, QGroupBox, QFrame,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDateEdit, QCheckBox,
    QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem, QHeaderView,
    QSlider, QProgressBar, QMessageBox, QFileDialog, QAbstractItemView, QScrollArea,
)

from srm import config
from srm.models import Student, ValidationError
from srm.storage import StudentRepository, StorageError
from srm.ui.chart import BarChart

TABLE_COLUMNS = ["ID", "Name", "Programme", "Year", "Average", "Grade", "Active"]


class MainWindow(QMainWindow):
    def __init__(self, repo: StudentRepository):
        super().__init__()
        self.repo = repo
        self.editing_id: str | None = None        # ID of the row being edited, if any

        self.setWindowTitle(config.WINDOW_TITLE)
        self.resize(1180, 720)
        self.setMinimumSize(900, 560)

        self._build_menu()
        tabs = QTabWidget()
        tabs.addTab(self._build_records_tab(), "Records")
        tabs.addTab(self._build_summary_tab(), "Summary")
        tabs.currentChanged.connect(self.refresh_summary)
        self.setCentralWidget(tabs)
        self.statusBar().showMessage(f"Loaded {len(repo.all())} records from {config.DATA_FILE.name}")
        if config.IS_FROZEN:
            # Running from the PyInstaller build: show which file and how big it is.
            exe = config.EXE_PATH
            size_mb = exe.stat().st_size / 1_000_000
            self.statusBar().addPermanentWidget(QLabel(f"Packaged build: {exe.name} ({size_mb:.0f} MB)  |"))
        # name + roll number visible in every screenshot (assignment rule)
        self.statusBar().addPermanentWidget(QLabel(f"{config.STUDENT_NAME}  |  {config.ROLL_NO}  "))

        self.refresh_table()
        self.refresh_summary()

    # ================================================================ build
    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        export = QAction("&Export to CSV...", self, shortcut=QKeySequence("Ctrl+E"))
        export.triggered.connect(self.on_export_csv)
        quit_ = QAction("E&xit", self, shortcut=QKeySequence("Ctrl+Q"))
        quit_.triggered.connect(self.close)
        file_menu.addActions([export, quit_])

        rec_menu = self.menuBar().addMenu("&Records")
        new = QAction("&New student", self, shortcut=QKeySequence("Ctrl+N"))
        new.triggered.connect(self.clear_form)
        rec_menu.addAction(new)

        help_menu = self.menuBar().addMenu("&Help")
        about = QAction("&About", self)
        about.triggered.connect(self.on_about)
        help_menu.addAction(about)

    def _build_records_tab(self) -> QWidget:
        # The form sits in a scroll area, so a small window shows a scroll bar
        # instead of squashing the fields on top of each other.
        form_scroll = QScrollArea()
        form_scroll.setWidget(self._build_form())
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_scroll.setMinimumWidth(380)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(form_scroll)
        splitter.addWidget(self._build_table_panel())
        splitter.setStretchFactor(0, 0)            # form keeps its width
        splitter.setStretchFactor(1, 1)            # table takes the extra space
        splitter.setSizes([400, 780])
        return splitter

    def _build_form(self) -> QWidget:
        page = QWidget(objectName="page")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(16, 16, 8, 16)
        outer.setSpacing(8)

        details = QGroupBox("Student details")
        grid = QGridLayout(details)                # label column + field column
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        self.id_edit = QLineEdit(placeholderText="8 digits, e.g. 02230045", maxLength=8)
        self.name_edit = QLineEdit(placeholderText="Full name")
        self.gender_group = QButtonGroup(self)
        gender_row = QHBoxLayout()
        for i, g in enumerate(("Male", "Female", "Other")):
            rb = QRadioButton(g)
            self.gender_group.addButton(rb, i)
            gender_row.addWidget(rb)
        self.gender_group.button(0).setChecked(True)
        self.programme_combo = QComboBox()
        self.programme_combo.addItems(config.PROGRAMMES)
        self.year_spin = QSpinBox(minimum=1, maximum=4)
        self.email_edit = QLineEdit(placeholderText="name@rub.edu.bt")
        self.dob_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.dob_edit.setDate(QDate(2005, 1, 1))
        self.active_check = QCheckBox("Currently enrolled")
        self.active_check.setChecked(True)

        rows = [("Student ID", self.id_edit), ("Name", self.name_edit), ("Gender", gender_row),
                ("Programme", self.programme_combo), ("Year", self.year_spin),
                ("Email", self.email_edit), ("Date of birth", self.dob_edit), ("", self.active_check)]
        for r, (label, w) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            if isinstance(w, QHBoxLayout):
                grid.addLayout(w, r, 1)
            else:
                grid.addWidget(w, r, 1)
        grid.setColumnStretch(1, 1)

        marks_box = QGroupBox("Marks (0-100)")
        marks_form = QFormLayout(marks_box)
        self.mark_spins: dict[str, QSpinBox] = {}
        for subject in config.SUBJECTS:
            spin = QSpinBox(minimum=0, maximum=100)
            self.mark_spins[subject] = spin
            marks_form.addRow(subject, spin)

        self.error_label = QLabel(objectName="error", wordWrap=True)
        self.error_label.hide()

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("Add", objectName="primary")
        self.update_btn = QPushButton("Update")
        self.delete_btn = QPushButton("Delete", objectName="danger")
        self.clear_btn = QPushButton("Clear")
        for b in (self.add_btn, self.update_btn, self.delete_btn, self.clear_btn):
            buttons.addWidget(b)
        # --- signals -> slots ---
        self.add_btn.clicked.connect(self.on_add)
        self.update_btn.clicked.connect(self.on_update)
        self.delete_btn.clicked.connect(self.on_delete)
        self.clear_btn.clicked.connect(self.clear_form)

        outer.addWidget(details)
        outer.addWidget(marks_box)
        outer.addWidget(self.error_label)
        outer.addLayout(buttons)
        outer.addStretch(1)
        self._set_editing(None)
        return page

    def _build_table_panel(self) -> QWidget:
        page = QWidget(objectName="page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 16, 16)

        filters = QHBoxLayout()
        self.search_edit = QLineEdit(placeholderText="Search by name or ID...", clearButtonEnabled=True)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", *config.PROGRAMMES])
        self.min_slider = QSlider(Qt.Orientation.Horizontal, minimum=0, maximum=100, singleStep=5)
        self.min_slider.setFixedWidth(140)
        self.min_label = QLabel("Min avg: 0", objectName="muted")
        self.min_label.setFixedWidth(80)
        filters.addWidget(self.search_edit, 1)
        filters.addWidget(self.filter_combo)
        filters.addWidget(self.min_label)
        filters.addWidget(self.min_slider)
        self.search_edit.textChanged.connect(self.refresh_table)
        self.filter_combo.currentIndexChanged.connect(self.refresh_table)
        self.min_slider.valueChanged.connect(self.on_min_changed)

        self.table = QTableWidget(0, len(TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.on_row_selected)

        self.count_label = QLabel(objectName="muted")
        layout.addLayout(filters)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.count_label)
        return page

    def _build_summary_tab(self) -> QWidget:
        page = QWidget(objectName="page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        cards = QHBoxLayout()
        self.stat_labels: dict[str, QLabel] = {}
        for key, caption in (("count", "Students"), ("class_average", "Class average"),
                             ("pass_rate", "Pass rate (all subjects >= 40)")):
            card = QFrame(objectName="statCard")
            v = QVBoxLayout(card)
            value = QLabel("0", objectName="statValue")
            v.addWidget(value)
            v.addWidget(QLabel(caption, objectName="statCaption"))
            self.stat_labels[key] = value
            cards.addWidget(card)

        self.pass_bar = QProgressBar(maximum=100, format="Pass rate %p%")
        chart_box = QGroupBox("Average mark per subject")
        QVBoxLayout(chart_box).addWidget(chart := BarChart())
        self.chart = chart

        layout.addLayout(cards)
        layout.addWidget(self.pass_bar)
        layout.addWidget(chart_box, 1)
        return page

    # ============================================================ helpers
    def _form_to_student(self) -> Student:
        return Student(
            student_id=self.id_edit.text().strip(),
            name=" ".join(self.name_edit.text().split()),
            gender=self.gender_group.checkedButton().text(),
            programme=self.programme_combo.currentText(),
            year=self.year_spin.value(),
            email=self.email_edit.text().strip(),
            dob=self.dob_edit.date().toString("yyyy-MM-dd"),
            active=self.active_check.isChecked(),
            marks={s: spin.value() for s, spin in self.mark_spins.items()},
        )

    def _student_to_form(self, s: Student) -> None:
        self.id_edit.setText(s.student_id)
        self.name_edit.setText(s.name)
        for b in self.gender_group.buttons():
            b.setChecked(b.text() == s.gender)
        self.programme_combo.setCurrentText(s.programme)
        self.year_spin.setValue(s.year)
        self.email_edit.setText(s.email)
        self.dob_edit.setDate(QDate.fromString(s.dob, "yyyy-MM-dd"))
        self.active_check.setChecked(s.active)
        for subject, spin in self.mark_spins.items():
            spin.setValue(s.marks.get(subject, 0))

    def _set_editing(self, student_id: str | None) -> None:
        self.editing_id = student_id
        self.update_btn.setEnabled(student_id is not None)
        self.delete_btn.setEnabled(student_id is not None)

    def _show_errors(self, err: ValidationError) -> None:
        """Highlight the bad fields and list every message under the form."""
        field_widgets = {"student_id": self.id_edit, "name": self.name_edit, "email": self.email_edit,
                         "dob": self.dob_edit, "programme": self.programme_combo}
        self._clear_errors()
        for field, _ in err.errors:
            if w := field_widgets.get(field):
                w.setProperty("invalid", True)
                w.style().unpolish(w); w.style().polish(w)    # re-apply stylesheet
        self.error_label.setText("\n".join(f"- {m}" for _, m in err.errors))
        self.error_label.show()
        QMessageBox.warning(self, "Please check the form", "\n".join(m for _, m in err.errors))

    def _clear_errors(self) -> None:
        for w in (self.id_edit, self.name_edit, self.email_edit, self.dob_edit, self.programme_combo):
            w.setProperty("invalid", False)
            w.style().unpolish(w); w.style().polish(w)
        self.error_label.hide()

    # ============================================================== slots
    def on_add(self) -> None:
        try:
            student = self._form_to_student()
            self.repo.add(student)
        except ValidationError as err:
            self._show_errors(err)
            return
        except StorageError as err:
            QMessageBox.critical(self, "Save failed", str(err))
            return
        self.statusBar().showMessage(f"Added {student.name} ({student.student_id})", 5000)
        self.clear_form()
        self.refresh_table()

    def on_update(self) -> None:
        if self.editing_id is None:
            return
        try:
            student = self._form_to_student()
            self.repo.update(self.editing_id, student)
        except ValidationError as err:
            self._show_errors(err)
            return
        except StorageError as err:
            QMessageBox.critical(self, "Save failed", str(err))
            return
        self.statusBar().showMessage(f"Updated {student.name}", 5000)
        self.clear_form()
        self.refresh_table()

    def on_delete(self) -> None:
        s = self.repo.get(self.editing_id) if self.editing_id else None
        if s is None:
            return
        answer = QMessageBox.question(
            self, "Delete student", f"Delete {s.name} ({s.student_id})?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.repo.delete(s.student_id)
        except StorageError as err:
            QMessageBox.critical(self, "Save failed", str(err))
            return
        self.statusBar().showMessage(f"Deleted {s.name}", 5000)
        self.clear_form()
        self.refresh_table()

    def clear_form(self) -> None:
        self.table.clearSelection()
        for w in (self.id_edit, self.name_edit, self.email_edit):
            w.clear()
        self.gender_group.button(0).setChecked(True)
        self.programme_combo.setCurrentIndex(0)
        self.year_spin.setValue(1)
        self.dob_edit.setDate(QDate(2005, 1, 1))
        self.active_check.setChecked(True)
        for spin in self.mark_spins.values():
            spin.setValue(0)
        self._clear_errors()
        self._set_editing(None)
        self.id_edit.setFocus()

    def on_row_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        student_id = self.table.item(rows[0].row(), 0).text()
        if s := self.repo.get(student_id):
            self._clear_errors()
            self._student_to_form(s)
            self._set_editing(student_id)

    def on_min_changed(self, value: int) -> None:
        self.min_label.setText(f"Min avg: {value}")
        self.refresh_table()

    def refresh_table(self) -> None:
        students = self.repo.search(self.search_edit.text(), self.filter_combo.currentText(),
                                    self.min_slider.value())
        self.table.setRowCount(len(students))
        for r, s in enumerate(students):
            values = [s.student_id, s.name, s.programme, str(s.year), f"{s.average:.1f}",
                      s.grade, "Yes" if s.active else "No"]
            for c, v in enumerate(values):
                item = QTableWidgetItem(v)
                if c in (3, 4, 5):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.count_label.setText(f"Showing {len(students)} of {len(self.repo.all())} students")

    def refresh_summary(self, *_):
        info = self.repo.summary()
        self.stat_labels["count"].setText(str(info["count"]))
        self.stat_labels["class_average"].setText(f"{info['class_average']:.1f}")
        self.stat_labels["pass_rate"].setText(f"{info['pass_rate']}%")
        self.pass_bar.setValue(info["pass_rate"])
        self.chart.set_data(info["subject_average"])

    def on_export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export students", "students.csv", "CSV files (*.csv)")
        if not path:
            return
        try:
            n = self.repo.export_csv(path)
        except StorageError as err:
            QMessageBox.critical(self, "Export failed", str(err))
            return
        self.statusBar().showMessage(f"Exported {n} records to {path}", 5000)

    def on_about(self) -> None:
        QMessageBox.about(self, "About", f"<b>{config.APP_NAME}</b><br>Unit V assignment - PyQt6<br><br>"
                                         f"Name: {config.STUDENT_NAME}<br>Roll no: {config.ROLL_NO}")

    def closeEvent(self, event):                     # Qt calls this when the window closes
        try:
            self.repo.save()
        except StorageError as err:
            QMessageBox.critical(self, "Save failed", str(err))
        event.accept()
