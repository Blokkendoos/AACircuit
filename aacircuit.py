"""
AACircuit.py
2020-03-02 JvO

usage: python3.7 aacircuit.py
For debugging the Gtk (style) UI: export GTK_DEBUG=interactive; python3.7 aacircuit.py

"""

from application.controller import Controller

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

if __name__ == "__main__":
    app = Controller()
    app.show_all()
    Gtk.main()
