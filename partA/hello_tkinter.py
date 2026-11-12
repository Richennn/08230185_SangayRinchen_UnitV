"""Hello-world in Tkinter: a label and a button that changes it."""
import tkinter as tk

root = tk.Tk()                               # 1. the main window
root.title("Hello Tkinter - Sangay Rinchen (08230185)")
root.geometry("320x140")

clicks = 0
label = tk.Label(root, text="Hello, Tkinter!")

def on_click():
    global clicks
    clicks += 1
    label.config(text=f"Button clicked {clicks} time(s)")

button = tk.Button(root, text="Click me", command=on_click)   # 2. callback via command=
label.pack(pady=10)                          # 3. pack geometry manager
button.pack()

root.mainloop()                              # 4. start the event loop
