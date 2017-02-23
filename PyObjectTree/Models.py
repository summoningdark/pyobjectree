from pyqtgraph import QtCore, QtGui
from .Data import Node, ObjectNode


class ObjectTreeModel(QtCore.QAbstractItemModel):
    sortRole = QtCore.Qt.UserRole
    filterRole = QtCore.Qt.UserRole + 1

    """INPUTS: Node, QObject"""

    def __init__(self, root=None, parent=None):
        super(ObjectTreeModel, self).__init__(parent)
        if root is not None:
            self._rootNode = root
        else:
            self._rootNode = Node("root", columns=2)

    """INPUTS: QModelIndex"""
    """OUTPUT: int"""

    def rowCount(self, parent):
        if parent.isValid():
            parentNode = parent.internalPointer()
        else:
            parentNode = self._rootNode

        return parentNode.childCount()

    """INPUTS: QModelIndex"""
    """OUTPUT: int"""

    def columnCount(self, parent):
        if parent.isValid():
            parentNode = parent.internalPointer()
        else:
            parentNode = self._rootNode

        return parentNode.columnCount()

    """INPUTS: QModelIndex, int"""
    """OUTPUT: QVariant, strings are cast to QString which is a QVariant"""

    def data(self, index, role):

        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.data(index.column())

        if role == QtCore.Qt.DecorationRole:
            if index.column() == 0:
                resource = node.resource()
                return QtGui.QIcon(QtGui.QPixmap(resource))

    """INPUTS: QModelIndex, QVariant, int (flag)"""

    def setData(self, index, value, role=QtCore.Qt.EditRole):

        if index.isValid():

            node = index.internalPointer()

            if role == QtCore.Qt.EditRole:
                node.setData(index.column(), value)
                self.dataChanged.emit(index, index)
                return True
        return False

    """INPUTS: int, Qt::Orientation, int"""
    """OUTPUT: QVariant, strings are cast to QString which is a QVariant"""

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Object"
            elif section == 1:
                return "Value"


    """INPUTS: QModelIndex"""
    """OUTPUT: int (flag)"""

    def flags(self, index):
        if index.isValid():
            node = index.internalPointer()
        else:
            node = self._rootNode
        return node.flags(index.column())

    """INPUTS: QModelIndex"""
    """OUTPUT: QModelIndex"""
    """Should return the parent of the node with the given QModelIndex"""

    def parent(self, index):

        node = self.getNode(index)
        parentNode = node.parent()

        if parentNode == self._rootNode:
            return QtCore.QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    """INPUTS: int, int, QModelIndex"""
    """OUTPUT: QModelIndex"""
    """Should return a QModelIndex that corresponds to the given row, column and parent node"""

    def index(self, row, column, parent):

        parentNode = self.getNode(parent)

        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    """CUSTOM"""
    """INPUTS: QModelIndex"""

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node

        return self._rootNode

    """INPUTS: int, int, QModelIndex"""

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):

        parentNode = self.getNode(parent)

        self.beginInsertRows(parent, position, position + rows - 1)

        for row in range(rows):
            childCount = parentNode.childCount()
            childNode = Node("untitled" + str(childCount))
            success = parentNode.insertChild(position, childNode)

        self.endInsertRows()

        return success

    """INPUTS: int, int, QModelIndex"""

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):

        parentNode = self.getNode(parent)
        self.beginRemoveRows(parent, position, position + rows - 1)

        for row in range(rows):
            success = parentNode.removeChild(position)

        self.endRemoveRows()

        return success

    def addObject(self, position, obj):

        parentNode = self._rootNode
        parent = self.createIndex(0, 0, self._rootNode)

        self.beginInsertRows(parent, position, position)

        childNode = ObjectNode(obj)
        success = parentNode.insertChild(position, childNode)

        self.endInsertRows()

        return success

    def removeObject(self, index):
        if index.isValid():
            parent = index.parent()
            parentNode = self.getNode(parent)
            if parentNode is self._rootNode:                  # can only delete items with root as parent
                self.removeRows(index.row(), 1, parent)
