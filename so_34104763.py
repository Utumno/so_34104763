# Imports
# -----------------------------------------------------------------------------
import sys
import uuid
import json
from random import randint
from PySide import QtGui

NODES = []
HIERARCHY = {}
INSTANCED_NODES = []
FONTS = None

# Fonts
# -----------------------------------------------------------------------------
class Fonts(object):
    def __init__(self):
        self._fonts = {}

    def add_font(self, name="", bold=False, italic=False):
        font = QtGui.QFont()
        font.setBold(bold)
        font.setItalic(italic)
        self._fonts.update({name: font})

    def get_font(self, name):
        return self._fonts.get(name)

# Class Object
# -----------------------------------------------------------------------------
class Person(object):
    def __init__(self, name="", age=0):
        self.name = name
        self.uid = str(uuid.uuid4())
        self.age = (randint(0, 20))
        NODES.append(self)

# Custom QTreeWidgetItem
# -----------------------------------------------------------------------------
class CustomTreeNode(QtGui.QTreeWidgetItem):
    def __init__(self, parent, name):
        super(CustomTreeNode, self).__init__(parent)
        self.setText(0, name)
        self.person = None

    def update(self):
        if self.person:
            self.setText(0, self.person.name)

# UI
# -----------------------------------------------------------------------------
class ExampleWidget(QtGui.QWidget):
    def __init__(self):
        super(ExampleWidget, self).__init__()
        self.init_fonts()
        self.initUI()

    @staticmethod
    def init_fonts():
        global FONTS
        FONTS = Fonts()
        FONTS.add_font(name="accent", bold=True, italic=True)
        FONTS.add_font(name="regular", bold=False, italic=False)

    def initUI(self):
        # widgets
        self.treeWidget = QtGui.QTreeWidget()
        self.treeWidget.setSelectionMode(
            QtGui.QAbstractItemView.ExtendedSelection)
        self.treeWidget.setAnimated(True)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setDragEnabled(True)
        self.treeWidget.setDropIndicatorShown(True)
        self.treeWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.btn_add_tree_nodes = QtGui.QPushButton("Add")
        self.btn_instance_tree_nodes = QtGui.QPushButton("Instance")
        self.btn_delete_tree_nodes = QtGui.QPushButton("Delete")
        # layout
        self.mainLayout = QtGui.QGridLayout(self)
        self.mainLayout.addWidget(self.btn_add_tree_nodes, 0, 0)
        self.mainLayout.addWidget(self.btn_instance_tree_nodes, 0, 1)
        self.mainLayout.addWidget(self.btn_delete_tree_nodes, 0, 2)
        self.mainLayout.addWidget(self.treeWidget, 1, 0, 1, 3)
        # signals
        self.btn_add_tree_nodes.clicked.connect(self.add_tree_nodes_clicked)
        self.btn_delete_tree_nodes.clicked.connect(
            self.delete_tree_nodes_clicked)
        self.btn_instance_tree_nodes.clicked.connect(
            self.instance_tree_nodes_clicked)
        self.treeWidget.itemSelectionChanged.connect(
            self.item_selection_changed)
        self.treeWidget.itemDoubleClicked.connect(self.item_doubleclicked)
        # Set TreeWidget Headers
        self.treeWidget.setColumnCount(1)
        self.treeWidget.setHeaderLabels(["Items"])
        # Set Columns Width to match content:
        for column in range(self.treeWidget.columnCount()):
            self.treeWidget.resizeColumnToContents(column)
        # display
        self.resize(200, 400)
        self.show()
        self.center_window(self, True)

    # Functions
    # -------------------------------------------------------------------------
    def closeEvent(self, event):
        print "saving"
        self.save_nodes()

    def showEvent(self, event):
        print "loading"

    @staticmethod
    def serialize_node(node):
        data = {}
        if node:
            # base attributes
            data["class_name"] = node.__class__.__name__
            data["name"] = node.name
            data["age"] = node.age
            data["uid"] = node.uid
        return data

    def save_nodes(self):
        print "Saving serialized nodes..."
        data = {}
        items = [self.serialize_node(x) for x in NODES]
        data.update({"nodes": items})
        data.update({"hierarchy": HIERARCHY})
        json.dump(data, open("test.json", 'w'), indent=4)

    def delete_tree_nodes_clicked(self):
        self.delete_treewidet_items(self.treeWidget)

    def update_nodes(self, root=None):
        for i in range(root.childCount()):
            item = root.child(i)
            item.update()
            self.update_nodes(root=item)

    def item_doubleclicked(self):
        item = self.treeWidget.selectedItems()[0]
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog',
                                              'Enter your name:')
        if ok:
            item.person.name = text
            item.setText(0, text)

            # update all nodes to reflect name change
            self.update_nodes(root=self.treeWidget.invisibleRootItem())

    def get_used_uids(self, root=None):
        results = []
        for i in range(root.childCount()):
            item = root.child(i)
            results.append(item.person.uid)
            results.extend(self.get_used_uids(root=item))
        return results

    def get_nodes_hierarchy(self, root=None):
        results = []
        for i in range(root.childCount()):
            item = root.child(i)
            data = {"uid": item.person.uid,
                    # recursive serialize children:
                    "children": [self.get_nodes_hierarchy(root=item)]}
            results.append(data)
        return results

    def get_hierarchy(self):
        print "nope"
        global HIERARCHY
        HIERARCHY = self.get_nodes_hierarchy(
            root=self.treeWidget.invisibleRootItem())

    def item_selection_changed(self):
        self.highlight_instances()
        self.get_hierarchy()

    def get_instanced_nodes(self, root=None, uids=()):
        uids = uids or []
        results = []
        for i in range(root.childCount()):
            item = root.child(i)
            if item.person.uid in uids:
                results.append(item)
            results.extend(self.get_instanced_nodes(root=item, uids=uids))
        return results

    def highlight_instances(self):
        global INSTANCED_NODES
        # reset previously instanced nodes
        for node in INSTANCED_NODES:
            if node:
                node.setFont(0, FONTS.get_font("regular"))
        # collect uid's from selected
        uids = [getattr(x.person, "uid") for x in
                self.treeWidget.selectedItems() if
                hasattr(x.person, "uid")]
        INSTANCED_NODES = []
        for uid in uids:
            _instances = self.get_instanced_nodes(
                root=self.treeWidget.invisibleRootItem(), uids=[uid])
            if len(_instances) > 1:
                INSTANCED_NODES += _instances
        for node in INSTANCED_NODES:
            node.setFont(0, FONTS.get_font("accent"))

    def add_tree_nodes_clicked(self):
        print "adding nodes"
        roots = [
            self.treeWidget] if self.treeWidget.selectedItems() == [] else \
            self.treeWidget.selectedItems()
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog',
                                              'Enter your name:')
        if ok:
            for root in roots:
                node = CustomTreeNode(root, text)
                node.person = Person(text)
                node.setExpanded(True)
                self.treeWidget.itemSelectionChanged.emit()

    def instance_tree_nodes_clicked(self):
        print "instancing nodes"
        roots = self.treeWidget.selectedItems()
        for root in roots:
            parent = self.treeWidget if not root.parent() else root.parent()
            node = CustomTreeNode(parent, root.person.name)
            node.person = root.person
            node.setExpanded(True)
            self.treeWidget.itemSelectionChanged.emit()

    def delete_treewidet_items(self, ctrl):
        global NODES
        root = self.treeWidget.invisibleRootItem()
        # delete treewidget items from gui
        for item in self.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
        # collect all uids used in GUI
        uids_used = self.get_used_uids(
            root=self.treeWidget.invisibleRootItem())
        for n in reversed(NODES):
            if n.uid not in uids_used:
                NODES.remove(n)
        self.get_hierarchy()

    def center_window(self, window, cursor=False):
        qr = window.frameGeometry()
        cp = QtGui.QCursor.pos() if cursor else QtGui.QDesktopWidget(
            ).availableGeometry().center()
        qr.moveCenter(cp)
        window.move(qr.topLeft())

# __name__
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = ExampleWidget()
    sys.exit(app.exec_())
