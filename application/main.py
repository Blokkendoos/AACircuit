from application.controller import Controller

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402


def main():
    app = Controller()
    app.show_all()
    Gtk.main()
