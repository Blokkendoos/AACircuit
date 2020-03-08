"""
AACircuit.py
2020-03-02 JvO
"""
from application.main_window import MainWindow

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

if __name__ == "__main__":
    app = MainWindow()
    app.show_all()
    Gtk.main()
