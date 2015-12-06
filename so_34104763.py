# Imports
# -----------------------------------------------------------------------------
import collections
import sys
import uuid
import json
from random import randint
from PySide import QtGui

persons_count = collections.defaultdict(int)
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

    def __eq__(self, other):
        return isinstance(other, Person) and self.uid == other.uid
    def __ne__(self, other): return self != other # you need this
    def __hash__(self):
        return hash(self.uid)

# Custom QTreeWidgetItem
# -----------------------------------------------------------------------------
class CustomTreeNode(QtGui.QTreeWidgetItem):
    def __init__(self, parent, person):
        super(CustomTreeNode, self).__init__(parent)
        self.setText(0, person.name)
        self.person = person
        persons_count[person] += 1

# UI
# -----------------------------------------------------------------------------
class ExampleWidget(QtGui.QWidget):
    def __init__(self):
        super(ExampleWidget, self).__init__()
        # Initialize fonts
        global FONTS
        FONTS = Fonts()
        FONTS.add_font(name="accent", bold=True, italic=True)
        FONTS.add_font(name="regular", bold=False, italic=False)
        # Initialize the UI
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
            self.highlight_instances)
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
        # highlighted nodes
        self.highlighted = set()

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
        items = [self.serialize_node(x) for x in iter(persons_count.keys())]
        data.update({"nodes": items})
        data.update({"hierarchy": self.get_nodes_hierarchy(
            root=self.treeWidget.invisibleRootItem())})
        json.dump(data, open("test.json", 'w'), indent=4)

    def item_doubleclicked(self):
        item = self.treeWidget.selectedItems()[0]
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog',
                                              'Enter your name:')
        if ok:
            item.person.name = text
            item.setText(0, text)
            # update all nodes to reflect name change
            def _rename(node):
                if item.person == node.person: # avoid reseting the text
                    node.setText(0, text)
            self._process_nodes(self.treeWidget.invisibleRootItem(), _rename)

    def get_nodes_hierarchy(self, root):
        results = []
        for i in range(root.childCount()):
            item = root.child(i)
            data = {"uid": item.person.uid,
                    # recursive serialize children:
                    "children": [self.get_nodes_hierarchy(root=item)]}
            results.append(data)
        return results

    def _process_nodes(self, root, func):
        for i in range(root.childCount()):
            item = root.child(i)
            func(item)
            self._process_nodes(root=item, func=func)

    def highlight_instances(self):
        # reset previously highlighted nodes
        for node in self.highlighted:
            node.setFont(0, FONTS.get_font("regular"))
        self.highlighted.clear()
        selected = set(x.person for x in self.treeWidget.selectedItems())
        def _same_person(item):
            if item.person in selected and persons_count[item.person] > 1:
                self.highlighted.add(item)
                item.setFont(0, FONTS.get_font("accent"))
        self._process_nodes(self.treeWidget.invisibleRootItem(), _same_person)

    def add_tree_nodes_clicked(self):
        print "adding nodes"
        selected = self.treeWidget.selectedItems()
        roots = [self.treeWidget] if not selected else selected
        text, ok = QtGui.QInputDialog.getText(self, 'Input Dialog',
                                              'Enter your name:')
        if not ok: return
        for root in roots:
            node = CustomTreeNode(root, Person(text))
            node.setExpanded(True)
            self.highlight_instances()

    def instance_tree_nodes_clicked(self):
        print "instancing nodes"
        roots = self.treeWidget.selectedItems()
        for root in roots:
            parent = self.treeWidget if not root.parent() else root.parent()
            node = CustomTreeNode(parent, root.person)
            node.setExpanded(True)
            self.highlight_instances()

    def delete_tree_nodes_clicked(self):
        root = self.treeWidget.invisibleRootItem()
        # delete treewidget items from gui
        for item in self.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
            self.highlighted.discard(item)
            persons_count[item.person] -= 1
            if not persons_count[item.person]: del persons_count[item.person]

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
