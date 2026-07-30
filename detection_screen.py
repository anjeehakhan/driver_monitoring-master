# driver_monitoring-master/screens/detection_screen.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
import threading
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import log_violation
from app_bridge import current_driver_state


class DetectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver_id   = None
        self.driver_name = ''
        self.checkpoint  = ''
        self._detection_thread = None
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            Color(0.1, 0.1, 0.18, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)

        layout.add_widget(Label(
            text='📹 Live Detection',
            font_size='22sp', bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None, height=55
        ))

        self.driver_label = Label(
            text='Driver: —',
            font_size='14sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None, height=30
        )
        layout.add_widget(self.driver_label)

        # Status
        self.status_label = Label(
            text='🟡  Detection shuru nahi hui',
            font_size='15sp',
            color=(0.96, 0.65, 0.14, 1),
            size_hint_y=None, height=45
        )
        layout.add_widget(self.status_label)

        # Alert label
        self.alert_label = Label(
            text='',
            font_size='18sp', bold=True,
            color=(0.91, 0.27, 0.37, 1),
            size_hint_y=None, height=50
        )
        layout.add_widget(self.alert_label)

        # Counts
        self.counts_label = Label(
            text='Drowsy: 0  |  Phone: 0  |  Yawn: 0',
            font_size='14sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=35
        )
        layout.add_widget(self.counts_label)

        layout.add_widget(Label(
            text='(Camera OpenCV window mein dikhegi)',
            font_size='12sp',
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=None, height=30
        ))

        layout.add_widget(Label(size_hint_y=None, height=20))

        # Start button
        self.start_btn = Button(
            text='▶  Start Detection',
            font_size='16sp', bold=True,
            background_color=(0.91, 0.27, 0.37, 1),
            size_hint_y=None, height=55
        )
        self.start_btn.bind(on_press=self._start_detection)
        layout.add_widget(self.start_btn)

        # Alerts history button
        alerts_btn = Button(
            text='🔔  View Alerts',
            font_size='14sp',
            background_color=(0.29, 0.56, 0.89, 1),
            size_hint_y=None, height=45
        )
        alerts_btn.bind(on_press=lambda x: self._go_to('alerts'))
        layout.add_widget(alerts_btn)

        # Back button
        back_btn = Button(
            text='← Back to Profile',
            font_size='13sp',
            background_color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None, height=40
        )
        back_btn.bind(on_press=lambda x: self._go_to('profile'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def set_driver(self, driver_id, name, checkpoint):
        self.driver_id   = driver_id
        self.driver_name = name
        self.checkpoint  = checkpoint
        self.driver_label.text = f'Driver: {name}'

    def _start_detection(self, instance):
        if not self.checkpoint:
            self.status_label.text = '⚠ Pehle login karo!'
            return

        self.start_btn.disabled = True
        self.status_label.text  = '🟢  Detection chal rahi hai — q dabao band karne ke liye'

        # Counts reset
        self._sleepy = 0
        self._phone  = 0
        self._yawn   = 0

        # Detection alag thread mein
        self._detection_thread = threading.Thread(
            target=self._run_detection, daemon=True
        )
        self._detection_thread.start()

        # UI update timer
        Clock.schedule_interval(self._update_ui, 1.0)

    def _run_detection(self):
        from dms import run_detection

        def on_violation(driver_id, v_type):
            log_violation(driver_id, v_type)
            current_driver_state['state'] = v_type  # Flask ko update karo
            if v_type == 'drowsiness': self._sleepy += 1
            if v_type == 'phone':      self._phone  += 1
            if v_type == 'yawn':       self._yawn   += 1

        run_detection(
            checkpoint   = self.checkpoint,
            driver_id    = self.driver_id,
            on_violation = on_violation
        )

        # Detection khatam
        Clock.unschedule(self._update_ui)
        current_driver_state['state'] = 'Focused'

        # Dashboard update karo
        def finish(*args):
            self.start_btn.disabled = False
            self.status_label.text  = '⏹  Detection band ho gayi'
            self.alert_label.text   = ''
            # Alerts refresh karo
            self.manager.get_screen('alerts')._load_data()
            self.manager.current = 'alerts'

        Clock.schedule_once(finish, 0)

    def _update_ui(self, dt):
        """Har second counts update karo"""
        self.counts_label.text = (
            f'😴 Drowsy: {self._sleepy}  '
            f'|  📱 Phone: {self._phone}  '
            f'|  🥱 Yawn: {self._yawn}'
        )
        state = current_driver_state.get('state', 'Focused')
        if state == 'Focused':
            self.alert_label.text = ''
        else:
            self.alert_label.text = f'⚠ ALERT: {state.upper()}!'

    def _go_to(self, screen_name):
        self.manager.current = screen_name

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos  = self.pos