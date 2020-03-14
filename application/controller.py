"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub

from application.grid import Grid
from application.main_window import MainWindow
from application.component_library import ComponentLibrary


class Controller(object):

    def __init__(self):

        self.grid = Grid(75, 40)  # the ASCII grid

        self.gui = MainWindow()
        self.components = ComponentLibrary()

        all_components = [key for key in self.components.get_dict()]
        pub.sendMessage('ALL_COMPONENTS', list=all_components)

        pub.subscribe(self.on_component_changed, 'COMPONENT_CHANGED')

    def show_all(self):
        self.gui.show_all()

    def on_component_changed(self, label):
        grid = self.components.get_grid(label)
        pub.sendMessage('SYMBOL_SELECTED', grid=grid)
