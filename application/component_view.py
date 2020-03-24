"""
AACircuit
2020-03-02 JvO
"""

from pubsub import pub
import gettext
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

_ = gettext.gettext


class ComponentView():

    columns = [_('Description')]

    def __init__(self, builder):

        scrolled_window = builder.get_object('component_window')
        # scrolled_window.set_size_request(200, 100)
        scrolled_window.set_border_width(2)
        # scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.listmodel = builder.get_object('liststore1')

        view = builder.get_object('treeview1')

        # when a row is selected
        view.get_selection().connect('changed', self.on_changed)

        # the label we use to show the selection
        # self.component_label = Gtk.Label()
        # self.component_label.set_text("")

        for i, column in enumerate(self.columns):
            # cellrenderer to render the text
            cell = Gtk.CellRendererText()
            # the column is created
            col = Gtk.TreeViewColumn(column, cell, text=i)
            # and it is appended to the treeview
            view.append_column(col)

        # subscriptions

        pub.subscribe(self.set_components, 'ALL_COMPONENTS')

    def set_components(self, list):
        for label in list:
            self.listmodel.append((label,))

    def on_changed(self, selection):
        # get the model and the iterator that points at the data in the model
        (model, iter) = selection.get_selected()
        label = model[iter][0]

        # get the default grid for the symbol that represents this component
        pub.sendMessage('COMPONENT_CHANGED', label=label)

        return True
