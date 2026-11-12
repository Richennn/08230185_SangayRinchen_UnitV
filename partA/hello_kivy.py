"""Hello-world in Kivy: a label and a button that changes it."""
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

Window.size = (320, 140)


class HelloApp(App):                         # 1. subclass App, build() returns the root widget
    title = "Hello Kivy - Sangay Rinchen (08230185)"

    def build(self):
        self.clicks = 0
        root = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.label = Label(text="Hello, Kivy!")
        button = Button(text="Click me")
        button.bind(on_press=self.on_click)  # 2. bind an event to a callback
        root.add_widget(self.label)
        root.add_widget(button)
        return root

    def on_click(self, instance):
        self.clicks += 1
        self.label.text = f"Button clicked {self.clicks} time(s)"


if __name__ == "__main__":
    HelloApp().run()                         # 3. run() starts the event loop
