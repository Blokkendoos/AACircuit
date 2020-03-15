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

        # setup MVC

        self.grid = Grid(75, 40)  # the ASCII grid

        self.gui = MainWindow()

        self.components = ComponentLibrary()
        all_components = [key for key in self.components.get_dict()]
        print("{0} libraries loaded, total number of components: {1}".format(self.components.nr_libraries(),
                                                                             self.components.nr_components()))
        # messages

        pub.sendMessage('ALL_COMPONENTS', list=all_components)
        pub.sendMessage('GRID', grid=self.grid)

        # subscriptions

        pub.subscribe(self.on_component_changed, 'COMPONENT_CHANGED')
        pub.subscribe(self.on_rotate_symbol, 'ROTATE_SYMBOL')
        pub.subscribe(self.on_paste_symbol, 'PASTE_SYMBOL')

    def show_all(self):
        self.gui.show_all()

    def on_component_changed(self, label):
        grid = self.components.get_grid(label)
        pub.sendMessage('SYMBOL_SELECTED', grid=grid)

    def on_rotate_symbol(self):
        grid = self.components.get_grid_next()
        pub.sendMessage('SYMBOL_SELECTED', grid=grid)

    def on_paste_symbol(self, pos):
        symbol_grid = self.components.get_grid_current()
        self.grid.fill_rect(pos, symbol_grid)

