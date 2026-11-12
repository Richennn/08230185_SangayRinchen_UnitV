"""Hello-world in PyQt6: a label and a button that changes it."""
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton

app = QApplication(sys.argv)                 # 1. every Qt program needs one QApplication
window = QWidget()
window.setWindowTitle("Hello PyQt6 - Sangay Rinchen (08230185)")
window.resize(320, 140)

label = QLabel("Hello, PyQt6!")
button = QPushButton("Click me")
clicks = 0

def on_click():                              # slot
    global clicks
    clicks += 1
    label.setText(f"Button clicked {clicks} time(s)")

button.clicked.connect(on_click)             # 2. connect signal -> slot

layout = QVBoxLayout(window)                 # 3. layout manager positions widgets
layout.addWidget(label)
layout.addWidget(button)

window.show()
sys.exit(app.exec())                         # 4. start the event loop
