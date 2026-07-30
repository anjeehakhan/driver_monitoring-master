# driver_monitoring-master/screens/login_screen.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import add_driver, create_db


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        # Dark background
        with self.canvas.before:
            Color(0.1, 0.1, 0.18, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)

        # Title
        layout.add_widget(Label(
            text='🚗 Driver Monitoring System',
            font_size='22sp', bold=True,
            color=(1, 1, 1, 1), size_hint_y=None, height=60
        ))
        layout.add_widget(Label(
            text='FYP Project — BSCS',
            font_size='13sp',
            color=(0.6, 0.6, 0.6, 1), size_hint_y=None, height=30
        ))

        # Name field
        layout.add_widget(Label(
            text='Driver Name',
            font_size='14sp', color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=30, halign='left'
        ))
        self.name_input = TextInput(
            hint_text='Apna naam likhو',
            multiline=False, font_size='16sp',
            background_color=(0.086, 0.13, 0.24, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            size_hint_y=None, height=45
        )
        layout.add_widget(self.name_input)

        # License field
        layout.add_widget(Label(
            text='License Number',
            font_size='14sp', color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=30
        ))
        self.license_input = TextInput(
            hint_text='License number likhو',
            multiline=False, font_size='16sp',
            background_color=(0.086, 0.13, 0.24, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            size_hint_y=None, height=45
        )
        layout.add_widget(self.license_input)

        # Checkpoint field
        layout.add_widget(Label(
            text='Model Path',
            font_size='14sp', color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=30
        ))
        self.checkpoint_input = TextInput(
            text='models/model_split.h5',
            multiline=False, font_size='14sp',
            background_color=(0.086, 0.13, 0.24, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            size_hint_y=None, height=45
        )
        layout.add_widget(self.checkpoint_input)

        # Status label
        self.status_label = Label(
            text='', font_size='13sp',
            color=(0.91, 0.27, 0.37, 1),
            size_hint_y=None, height=30
        )
        layout.add_widget(self.status_label)

        # Start button
        start_btn = Button(
            text='▶  Start Monitoring',
            font_size='16sp', bold=True,
            background_color=(0.91, 0.27, 0.37, 1),
            size_hint_y=None, height=55
        )
        start_btn.bind(on_press=self._on_start)
        layout.add_widget(start_btn)

        # View Alerts button
        alerts_btn = Button(
            text='🔔  View Alerts History',
            font_size='14sp',
            background_color=(0.29, 0.56, 0.89, 1),
            size_hint_y=None, height=45
        )
        alerts_btn.bind(on_press=lambda x: self._go_to('alerts'))
        layout.add_widget(alerts_btn)

        self.add_widget(layout)

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos  = self.pos

    def _on_start(self, instance):
        name       = self.name_input.text.strip()
        license_no = self.license_input.text.strip()
        checkpoint = self.checkpoint_input.text.strip()

        if not name:
            self.status_label.text = '⚠ Driver name daalo!'
            return
        if not license_no:
            self.status_label.text = '⚠ License number daalo!'
            return
        if not os.path.exists(checkpoint):
            self.status_label.text = '⚠ Model file nahi mili!'
            return

        # DB mein save karo
        create_db()
        driver_id = add_driver(name, license_no)

        # Driver info agle screens ko pass karo
        app = self.manager
        app.get_screen('profile').set_driver(driver_id, name, license_no, checkpoint)
        app.get_screen('detection').set_driver(driver_id, name, checkpoint)
        app.get_screen('alerts').set_driver(driver_id, name)

        # Profile screen par jao
        self.manager.current = 'profile'

    def _go_to(self, screen_name):
        self.manager.current = screen_name