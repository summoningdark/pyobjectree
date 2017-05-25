import numbers
import collections
from pyqtgraph import QtCore, QtGui
import ast


class Node(object):
    def __init__(self, name, parent=None, columns=1):

        super(Node, self).__init__()

        nameflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        # self._data is a nested list of column data. first index is the data, second is the flags
        self._data = []
        for i in range(columns):
            self._data.append([None, QtCore.Qt.NoItemFlags])
        self._data[0] = [name, nameflags]

        self._children = []
        self._parent = parent

        if parent is not None:
            parent.addChild(self)

    @property
    def name(self):
        return self._data[0][0]

    @name.setter
    def name(self, value):
        self._data[0][0] = value

    def addChild(self, child):
        self._children.append(child)
        child._parent = self

    def insertChild(self, position, child):

        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):

        if position < 0 or position > len(self._children):
            return False

        child = self._children.pop(position)
        child._parent = None

        return True

    def child(self, row):
        if 0 <= row < len(self._children):
            return self._children[row]
        return None

    def childCount(self):
        return len(self._children)

    def columnCount(self):
        return len(self._data)

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)

    def log(self, tabLevel=-1):

        output = ""
        tabLevel += 1

        for i in range(tabLevel):
            output += "\t"

        output += "|------" + self.name + "\n"

        for child in self._children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += "\n"

        return output

    def __repr__(self):
        return self.log()

    def data(self, column, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self._data[column][0]

        if role == QtCore.Qt.DecorationRole:
            if column == 0:
                return QtGui.QIcon(QtGui.QPixmap(self.resource()))

    def setData(self, column, value):
        if column < len(self._data):
            if isinstance(value, QtCore.QVariant):
                self._data[column][0] = value.toPyObject()
            else:
                self._data[column][0] = value

    def flags(self, column):
        if column < len(self._data):
            return self._data[column][1]
        return QtCore.Qt.NoItemFlags

    def resource(self):
        """
        returns the resource to use for the icon
        :return:
        """
        return None


class PropertyNode(Node):
    def __init__(self, name, flags, object_parent, parent=None):
        Node.__init__(self, name, parent=parent)
        self._object_parent = object_parent
        self._data[0][1] = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable     # property names are not editable
        self._data.append([None, flags])                                            # property may be editable

    @property
    def object_parent(self):
        return self._object_parent

    def data(self, column, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if column == 1:                     # second column is for the object property's value
                return str(getattr(self._object_parent.object, self.name))
            else:
                return Node.data(self, column, role)
        return Node.data(self, column, role)

    def setData(self, column, value):
        if column == 1:
            if self._data[1][1] & QtCore.Qt.ItemIsEditable:
                str_val = str(value)
                try:
                    new_val = ast.literal_eval(str_val)             # try evaluating the string as a constant
                except ValueError:
                    new_val = str_val                               # if that fails, just use the string
                setattr(self._object_parent.object, self.name, new_val)


class ObjectNode(Node):
    def __init__(self, obj, name = None, parent=None, pNode = PropertyNode, showValue=False):
        """
        node to represent a python object in the tree
        :param obj: the python object instance to represent
        :param parent: parent Node
        :param pNode: otpional PropertyNode class to use
        """

        self._object = obj
        self._object_hasname = False
        self._object_writename = False
        self._showValue = showValue

        if name is None:
            # check if the object has a name property
            name = 'None'
            name_attribute = getattr(type(obj), 'name', None)
            if name_attribute is not None:
                if isinstance(name_attribute, property):
                    self._object_hasname = True
                    if name_attribute.fset is not None:
                        self._object_writename = True
            else:
                # object has no inherent name
                name = str(obj)

        Node.__init__(self, name, columns=2, parent=parent)
        self._data[1][1] = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        if not self._object_writename:
            self._data[0][1] = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        # do special handling for some basic types
        if isinstance(self._object, numbers.Number):
            self._initNumber()
        elif isinstance(self._object, collections.Sequence) and not isinstance(self._object, str):
            self._initSequence()
        elif isinstance(self._object, collections.Set):
            pass
        elif isinstance(self._object, collections.Mapping):
            pass
        else:
            self._initGeneric(pNode=pNode)

    def _initNumber(self):
        pass

    def _initSequence(self):
        # loop through all the elements and add nodes for them
        for o in reversed(self._object):        # add in reversed order so element 0 is first
            self.addChild(ObjectNode(o))

    def _initGeneric(self, pNode=None):
        # loop through all the properties and add nodes for them
        for p in dir(self._object):
            if p != 'name' and p[0] != '_':
                flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
                attribute = getattr(type(self._object), p, None)
                if isinstance(attribute, property):
                    if attribute.fset is not None:
                        flags |= QtCore.Qt.ItemIsEditable
                    self.addChild(pNode(p, flags, self))
                elif not hasattr(attribute, '__call__'):                        # get non-callable attributes
                    self.addChild(ObjectNode(getattr(self._object, p, None), name=p))

    @property
    def object(self):
        return self._object

    def columnCount(self):
        return 2

    def data(self, column, role):
        """
        override base method to allow using the referenced object's name property
        :param column:
        :return:
        """
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if column == 0:
                if self._object_hasname:
                    return self._object.name
                else:
                    return Node.data(self, column, role)
            elif column == 1:
                if self._showValue:
                    return str(self._object)
                return None

        return Node.data(self, column, role)

    def setData(self, column, value):
        """
        override setData to allow using the referenced object's name property
        :param column:
        :param value:
        :return:
        """
        if column == 0:
            if not self._object_hasname:
                return Node.setData(self, column, value)
            if self._object_writename:
                self._object.name = value
