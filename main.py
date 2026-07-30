# driver_monitoring-master/main.py

import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window

from app_bridge import run_flask
from database import create_db

# Window size set karo
Window.size = (480, 650)

# ── Screen Manager ──
class DMS_App(App):
    def build(self):
        # DB ready karo
        create_db()

        # Flask server alag thread mein shuru karo
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # Screen Manager
        sm = ScreenManager(transition=FadeTransition())

        # Screens add karo
        from screens.login_screen    import LoginScreen
        from screens.driver_profile  import DriverProfileScreen
        from screens.alerts_history  import AlertsHistoryScreen
        from screens.detection_screen import DetectionScreen

        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DriverProfileScreen(name='profile'))
        sm.add_widget(DetectionScreen(name='detection'))
        sm.add_widget(AlertsHistoryScreen(name='alerts'))

        # Pehli screen
        sm.current = 'login'

        return sm

if __name__ == '__main__':
    DMS_App().run()