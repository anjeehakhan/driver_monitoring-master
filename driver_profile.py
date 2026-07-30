# driver_monitoring-master/screens/driver_profile.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle


class DriverProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver_id   = None
        self.driver_name = ''
        self.license_no  = ''
        self.checkpoint  = ''
        self._build_ui()

    def _build_ui(self):
        # Dark background
        with self.canvas.before:
            Color(0.1, 0.1, 0.18, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.layout = BoxLayout(orientation='vertical', padding=40, spacing=20)

        # Header
        self.layout.add_widget(Label(
            text='👤 Driver Profile',
            font_size='22sp', bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None, height=60
        ))

        # ── Info Cards ──
        self.name_label = Label(
            text='Name: —',
            font_size='16sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=40
        )
        self.layout.add_widget(self.name_label)

        self.license_label = Label(
            text='License: —',
            font_size='16sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=40
        )
        self.layout.add_widget(self.license_label)

        self.id_label = Label(
            text='Driver ID: —',
            font_size='16sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=40
        )
        self.layout.add_widget(self.id_label)

        self.checkpoint_label = Label(
            text='Model: —',
            font_size='13sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None, height=35
        )
        self.layout.add_widget(self.checkpoint_label)

        # Spacer
        self.layout.add_widget(Label(size_hint_y=None, height=20))

        # Status card
        self.status_card = Label(
            text='🟢  Status: Ready',
            font_size='15sp',
            color=(0.49, 0.83, 0.13, 1),
            size_hint_y=None, height=45
        )
        self.layout.add_widget(self.status_card)

        # ── Buttons ──
        start_btn = Button(
            text='📹  Start Detection',
            font_size='16sp', bold=True,
            background_color=(0.91, 0.27, 0.37, 1),
            size_hint_y=None, height=55
        )
        start_btn.bind(on_press=self._go_detection)
        self.layout.add_widget(start_btn)

        alerts_btn = Button(
            text='🔔  View Alerts History',
            font_size='14sp',
            background_color=(0.29, 0.56, 0.89, 1),
            size_hint_y=None, height=45
        )
        alerts_btn.bind(on_press=lambda x: self._go_to('alerts'))
        self.layout.add_widget(alerts_btn)

        back_btn = Button(
            text='← Back to Login',
            font_size='13sp',
            background_color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None, height=40
        )
        back_btn.bind(on_press=lambda x: self._go_to('login'))
        self.layout.add_widget(back_btn)

        self.add_widget(self.layout)

    def set_driver(self, driver_id, name, license_no, checkpoint):
        """Login screen se driver info receive karo"""
        self.driver_id   = driver_id
        self.driver_name = name
        self.license_no  = license_no
        self.checkpoint  = checkpoint

        # Labels update karo
        self.name_label.text       = f'👤  Name:      {name}'
        self.license_label.text    = f'🪪  License:   {license_no}'
        self.id_label.text         = f'🔢  Driver ID: {driver_id}'
        self.checkpoint_label.text = f'🤖  Model:     {checkpoint}'
        self.status_card.text      = '🟢  Status: Ready to Monitor'

    def _go_detection(self, instance):
        self.manager.current = 'detection'

    def _go_to(self, screen_name):
        self.manager.current = screen_name

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos  = self.pos