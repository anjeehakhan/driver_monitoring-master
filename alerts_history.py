# driver_monitoring-master/screens/alerts_history.py

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
import sys, os, csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_violations, get_violation_counts


class AlertsHistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver_id   = None
        self.driver_name = ''
        self._build_ui()

    def _build_ui(self):
        # Dark background
        with self.canvas.before:
            Color(0.1, 0.1, 0.18, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Header
        self.main_layout.add_widget(Label(
            text='🔔 Alerts History',
            font_size='22sp', bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None, height=55
        ))

        # Driver name
        self.driver_label = Label(
            text='Driver: —',
            font_size='14sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None, height=30
        )
        self.main_layout.add_widget(self.driver_label)

        # ── Stats Row ──
        self.stats_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=70,
            spacing=10
        )
        self.main_layout.add_widget(self.stats_layout)

        # ── Table Header ──
        header = GridLayout(
            cols=2, size_hint_y=None,
            height=35, spacing=2
        )
        header.add_widget(Label(
            text='Violation Type', bold=True,
            font_size='13sp', color=(1, 1, 1, 1)
        ))
        header.add_widget(Label(
            text='Time', bold=True,
            font_size='13sp', color=(1, 1, 1, 1)
        ))
        self.main_layout.add_widget(header)

        # ── Scrollable Table ──
        scroll = ScrollView(size_hint=(1, 1))
        self.table_layout = GridLayout(
            cols=2, spacing=4,
            size_hint_y=None
        )
        self.table_layout.bind(
            minimum_height=self.table_layout.setter('height')
        )
        scroll.add_widget(self.table_layout)
        self.main_layout.add_widget(scroll)

        # ── Buttons ──
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=50,
            spacing=10
        )

        export_btn = Button(
            text='📥 Export CSV',
            font_size='13sp',
            background_color=(0.29, 0.56, 0.89, 1)
        )
        export_btn.bind(on_press=self._export_csv)
        btn_row.add_widget(export_btn)

        refresh_btn = Button(
            text='🔄 Refresh',
            font_size='13sp',
            background_color=(0.49, 0.83, 0.13, 1)
        )
        refresh_btn.bind(on_press=lambda x: self._load_data())
        btn_row.add_widget(refresh_btn)

        back_btn = Button(
            text='← Back',
            font_size='13sp',
            background_color=(0.3, 0.3, 0.3, 1)
        )
        back_btn.bind(on_press=lambda x: self._go_back())
        btn_row.add_widget(back_btn)

        self.main_layout.add_widget(btn_row)
        self.add_widget(self.main_layout)

    def set_driver(self, driver_id, name):
        """Login se driver info receive karo"""
        self.driver_id   = driver_id
        self.driver_name = name
        self.driver_label.text = f'Driver: {name}'
        self._load_data()

    def _load_data(self):
        """DB se violations load karo"""
        if not self.driver_id:
            return

        # ── Stats Cards ──
        self.stats_layout.clear_widgets()
        counts = get_violation_counts(self.driver_id)

        stats = [
            ('😴 Drowsy',  counts.get('drowsiness', 0), (0.91, 0.27, 0.37, 1)),
            ('📱 Phone',   counts.get('phone',       0), (0.96, 0.65, 0.14, 1)),
            ('🥱 Yawn',    counts.get('yawn',        0), (0.49, 0.83, 0.13, 1)),
        ]

        for label, count, color in stats:
            card = BoxLayout(orientation='vertical', padding=5)
            with card.canvas.before:
                Color(*color)
                card.rect = Rectangle(size=card.size, pos=card.pos)
            card.bind(
                size=lambda w, v: setattr(w.rect, 'size', v),
                pos =lambda w, v: setattr(w.rect, 'pos',  v)
            )
            card.add_widget(Label(
                text=str(count),
                font_size='22sp', bold=True,
                color=(1, 1, 1, 1)
            ))
            card.add_widget(Label(
                text=label,
                font_size='11sp',
                color=(1, 1, 1, 1)
            ))
            self.stats_layout.add_widget(card)

        # ── Table Rows ──
        self.table_layout.clear_widgets()
        violations = get_violations(self.driver_id)

        if not violations:
            self.table_layout.add_widget(Label(
                text='Koi violation nahi mili',
                font_size='14sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None, height=40
            ))
            return

        colors = {
            'drowsiness': (0.91, 0.27, 0.37, 1),
            'phone':      (0.96, 0.65, 0.14, 1),
            'yawn':       (0.49, 0.83, 0.13, 1),
        }

        for v_type, timestamp, _ in violations:
            color = colors.get(v_type, (0.7, 0.7, 0.7, 1))
            self.table_layout.add_widget(Label(
                text=v_type.upper(),
                font_size='13sp',
                color=color,
                size_hint_y=None, height=35
            ))
            self.table_layout.add_widget(Label(
                text=timestamp,
                font_size='12sp',
                color=(0.8, 0.8, 0.8, 1),
                size_hint_y=None, height=35
            ))

    def _export_csv(self, instance):
        if not self.driver_id:
            return
        rows     = get_violations(self.driver_id)
        filename = f'report_{self.driver_name}_{self.driver_id}.csv'
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Violation Type', 'Timestamp', 'Screenshot'])
            writer.writerows(rows)
        print(f"✅ CSV exported: {filename}")

    def _go_back(self):
        if self.manager.has_screen('profile'):
            self.manager.current = 'profile'
        else:
            self.manager.current = 'login'

    def _update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos  = self.pos