from pyqtgraph import QtCore


class Node(object):
    def __init__(self, name, parent=None):

        super(Node, self).__init__()

        nameflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        # self._data is a nested list of column data. first index is the data, second is the flags
        self._data = [[name, nameflags], ]
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
        return self._children[row]

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

    def data(self, column):
        return self._data[column][0]

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


class ObjectNode(Node):
    def __init__(self, obj, parent=None):

        self._object = obj
        self._object_hasname = False
        self._object_writename = False
        name = 'None'

        # check if the object has a name property
        name_attribute = getattr(type(obj), 'name', None)
        if name_attribute is not None:
            if isinstance(name_attribute, property):
                self._object_hasname = True
                if name_attribute.fset is not None:
                    self._object_writename = True
        else:
            # object has no inherent name
            name = str(obj)
        Node.__init__(self, name, parent=parent)

        if not self._object_writename:
            self._data[0][1] = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        # loop through all the properties and add nodes for them
        for p in dir(obj):
            if p != 'name':
                flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
                attribute = getattr(type(obj), p, None)
                if isinstance(attribute, property):
                    if attribute.fset is not None:
                        flags |= QtCore.Qt.ItemIsEditable
                    self.addChild(PropertyNode(p, flags))

    def columnCount(self):
        return 2

    def data(self, column):
        """
        override base method to allow using the referenced object's name property
        :param column:
        :return:
        """
        if not self._object_hasname:
            return Node.data(self, column)
        else:
            if column == 0:
                return self._object.name

    def setData(self, column, value):
        """
        override setData to allow using the referenced object's name property
        :param column:
        :param value:
        :return:
        """
        if not self._object_hasname:
            return Node.setData(self, column, value)

        if column == 0:
            if self._object_writename:
                if isinstance(value, QtCore.QVariant):
                    self._object.name = value.toPyObject()
                else:
                    self._object.name = value


class PropertyNode(Node):
    def __init__(self, name, flags, parent=None):
        Node.__init__(self, name, parent=parent)
        self._data[0][1] = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable     # property names are not editable
        self._data.append([None, flags])                                            # property may be editable

    def data(self, column):
        if column == 1:                     # second column is for the object property's value
            return str(getattr(self._parent._object, self.name))
        else:
            return Node.data(self, column)

    def setData(self, column, value):
        if column == 1:
            if self._data[1][1] & QtCore.Qt.ItemIsEditable:
                if isinstance(value, QtCore.QVariant):
                    setattr(self._parent._object, self.name, value.toPyObject())
                else:
                    setattr(self._parent._object, self.name, value)
