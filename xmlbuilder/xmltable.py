from PyQt4.QtGui import QUndoStack, QUndoCommand, QColor
from PyQt4.QtCore import QStringList, Qt, QAbstractTableModel, QMimeData, \
    QVariant, SIGNAL, QString, QModelIndex
import re, time
from commands import ChangeValueCommand, RowCommand

class Table(QAbstractTableModel):

    def __init__(self, ob, parent):
        QAbstractTableModel.__init__(self)
        # store things
        self.ob = ob
        self.stack = QUndoStack()
        self._parent = parent
        # Make sure we have Name information first
        # _header contains the row headers
        self._header = [
            QVariant('--'), QVariant('#'), QVariant(getattr(self.ob, 'UniqueName', 'name'))]
        # _tooltips contains the tooltips
        self._tooltips = [
            QVariant('An -- indicates row is disabled %s'%bool),
            QVariant('Comment for row'),
            QVariant('Object name %s'%str)]
        # _required is a list of required columns
        self._required = []
        # _defaults is a dict of column -> default values
        self._defaults = {0: QVariant(False), 1: QVariant("")}
        # _optional is a list of optional columns
        self._optional = [2]
        # _cItems is a dict of column -> QVariant QStringList items, returned
        # to combo box
        self._cItems = {}
        # _cValues is a dict of column -> list of QVariant values, stored when
        # corresponding label stored by combobox
        self._cValues = {}
        # _idents is a list of identifier lookup fields
        self._idents = []
        # _types is a list of types for validation
        self._types = [bool, str, str]
        # rows is a list of rows. each row is a list of QVariants
        self.rows = []
        # work out the header and descriptions from the ArgInfo object
        a = ob.ArgInfo
        # for required names just process the ArgType object
        for name in a.required_names:
            self.__processArgType(name, a.descriptions[name])
        # for defaulted names give it a default too
        for name, default in zip(a.default_names, a.default_values):
            self.__processArgType(name, a.descriptions[name], default = default)
        # for optional names flag it as optional
        for name in a.optional_names:
            self.__processArgType(name, a.descriptions[name], optional = True)
        # maps (filt, without, upto) -> (timestamp, stringList)
        self._cachedNameList = {}

    def __processArgType(self, name, ob, **args):
        # this is the column index
        col = len(self._header)
        # If it's a name then be careful not to add it twice
        if name == getattr(self.ob, 'UniqueName', 'name'):
            assert ob.typ == str, 'Object name must be a string'
            self._tooltips[2] = QVariant(ob.desc)
        else:
            # add the header, type and tooltip
            self._header.append(QVariant(name))
            self._types.append(ob.typ)
            self._tooltips.append(QVariant(ob.desc))
        # if we have a default value, set it
        if 'default' in args:
            if args['default'] is None:
                self._defaults[col] = QVariant('None')
            else:
                self._defaults[col] = QVariant(args['default'])
        # if this is optional
        elif 'optional' in args:
            self._optional.append(col)
        # it must be required
        else:
            self._required.append(col)
        # if we have combo box items
        if hasattr(ob, 'labels'):
            self._cItems[col] = QVariant(
                QStringList([QString(str(x)) for x in ob.labels]))
        # if we have combo box values
        if hasattr(ob, 'values'):
            self._cValues[col] = [QVariant(x) for x in ob.values]
        # if it's an ident
        if hasattr(ob, 'ident'):
            self._idents.append(col)

    def __convert(self, variant, typ):
        # convert to the requested type
        val = variant.toString()
        if typ == bool:
            if val.toLower() == QString("true"):
                return (True, True)
            elif val.toLower() == QString("false"):
                return (False, True)
            elif "$(" in val:
                return (val, True)
            return (val, False)
        elif typ == int:
            if "$(" in val:
                return (val, True)
            return variant.toInt()
        elif typ == float:
            if "$(" in val:
                return (val, True)
            _, ret = variant.toDouble()
            return (val, ret)
        elif typ == str:
            return (variant.toString(), True)
        else:
            return (variant, False)

    def createElements(self, doc, name):
        # create xml elements from this table
        header = [ str(x.toString()) for x in self._header ]
        for row in self.rows:
            el = doc.createElement(name)
            # lookup and add attributes
            for i in range(2, len(row)):
                if not row[i].isNull():
                    val = str(row[i].toString())
                    # We want True and False to be capitalised in the xml file
                    if self._types[i] == bool and val in ["true", "false"]:
                        val = val.title()
                    el.setAttribute(header[i], val)
            if len(row[1].toString()) > 0:
                doc.documentElement.appendChild(doc.createComment(str(row[1].toString())))
            if row[0].toBool() == True:
                el = doc.createComment(el.toxml())
            doc.documentElement.appendChild(el)

    def addNode(self, node, commented = False, commentText = ""):
        # add xml nodes as rows in the table
        w = []
        row = [ QVariant() ] * len(self._header)
        self.rows.append(row)
        if commented:
            row[0] = QVariant(True)
        else:
            row[0] = QVariant(False)
        for attr, value in node.attributes.items():
            attr = str(attr)
            value = str(value)
            index = -1
            for i, item in enumerate(self._header):
                if str(item.toString()) == attr:
                    index = i
                    break
            if index == -1:
                w.append('%s doesn\'t have attr %s' % (node.nodeName, attr))
                continue
            typ = self._types[index]
            row[index] = QVariant(self.__convert(QVariant(value), typ)[0])
            invalid = self._isInvalid(row[index], len(self.rows)-1, index)
            if invalid:
                w.append('%s.%s: %s' %(node.nodeName, attr, invalid))
        # add the row to the table
        if commentText:
            row[1] = QVariant(commentText)
        return w

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def rowCount(self, parent = None):
        return len(self.rows)

    def columnCount(self, parent = None):
        return len(self._header)

    def headerData(self, section, orientation, role = Qt.DisplayRole ):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header[section]
            elif self.rows and self.rows[section] and \
                    not self.rows[section][2].isNull():
                return self.rows[section][2]
            else:
                return QVariant('[row %s]' % (section+1))
        elif role == Qt.ToolTipRole and orientation == Qt.Horizontal:
            return self._tooltips[section]
        else:
            return QVariant()


    # put the change request on the undo stack
    def setData(self, index, val, role=Qt.EditRole):
        if role == Qt.EditRole and \
                val != self.rows[index.row()][index.column()]:
            col = index.column()
            if col in self._cValues:
                # lookup the display in the list of _cItems
                for i, v in enumerate(self._cItems[col].toStringList()):
                    if v.toLower() == val.toString().toLower():
                        val = self._cValues[col][i]
            self.stack.push(
                ChangeValueCommand(index.row(), index.column(), val, self))
            return True
        else:
            return False

    def insertRows(self, row, count, parent = QModelIndex()):
        if count > 1:
            self.stack.beginMacro('Insert rows %d..%d'%(row+1, row+count))
        for row in range(row, row+count):
            self.stack.push(RowCommand(row, self, parent))
        if count > 1:
            self.stack.endMacro()

    def removeRows(self, row, count, parent = QModelIndex()):
        if count > 1:
            self.stack.beginMacro('Remove rows %d..%d'%(row+1, row+count))
        for row in reversed(range(row, row+count)):
            self.stack.push(RowCommand(row, self, parent, False))
        if count > 1:
            self.stack.endMacro()


    def _isCommented(self, row):
        return self.rows[row][0].toBool()

    def _nameList(self, filt = None, without = None, upto = None):
        # need to search all tables for a string list of object names
        # filt is a ModuleBase subclass to filter by
        # without is a row number to exclude from the current table
        # upto means only look at objects up to "upto" row in the current table
        if (filt, without, upto) in self._cachedNameList:
            timestamp, sl = self._cachedNameList[(filt, without, upto)]
            if self._parent.lastModified() < timestamp:
                return sl
        sl = QStringList()
        for name in self._parent.getTableNames():
            table = self._parent._tables[name]
            # if we have a filter, then make sure this table is a subclass of it
            if filt is not None and not issubclass(table.ob, filt):
                # if we are only going up to a certain table and this is it
                if table == self and upto is not None:
                    return sl
                continue
            for i,trow in enumerate(table.rows):
                if table == self:
                    # if the current table is self, make sure we are excluding
                    # the without row
                    if without is not None and without == i:
                        continue
                    # make sure we only go up to upto
                    if upto is not None and upto == i:
                        return sl
                # add a non-null name, which is not commented out to the list
                if not trow[2].isNull() and not \
                        (not trow[0].isNull() and trow[0].toBool() == True):
                    sl.append(trow[2].toString())
        # store the cached value
        self._cachedNameList[(filt, without, upto)] = (time.time(), sl)
        return sl

    def _isInvalid(self, value, row, col):
        # check that required rows are filled in
        if value.isNull():
            if col in self._required:
                return 'Required argument not filled in'
            else:
                return False
        # check that names are unique
        elif col == 2:
            name = value.toString()
            index = self._nameList(without = row).indexOf(name)
            if index != -1:
                return 'Object with name "%s" already exists' % name
        # check that idents are valid
        elif col in self._idents:
            name = value.toString()
            ob = self._types[col]
            index = self._nameList(filt = ob, upto = row).indexOf(name)
            if index == -1:
                return 'Can\'t perform identifier lookup on "%s"' % name
        # check that enums are valid
        elif col in self._cValues:
            if not max([value == x for x in self._cValues[col]]):
                return '"%s" is not a supported enum' % value.toString()
        # check that choices are valid
        elif col in self._cItems:
            if not max(
                [value == QVariant(x)
                 for x in self._cItems[col].toStringList()]):
                return '"%s" is not a supported choice' % value.toString()
        # check the type of basetypes
        else:
            typ = self._types[col]
            v, ret = self.__convert(value, typ)
            if ret != True:
                return 'Cannot convert "%s" to %s' % (value.toString(), typ)
        return False

    def _isDefault(self, value, col):
        return value.isNull() and col in self._defaults

    def data(self, index, role):
        col = index.column()
        row = index.row()
        value = self.rows[row][col]
        # default view
        if role == Qt.DisplayRole:
            # comment row
            if col == 1:
                if len(value.toString()) > 0:
                    return QVariant("#..")
                else:
                    return QVariant()
            # if the cell is defaulted, display the default value
            elif self._isDefault(value, col):
                value = self._defaults[col]
            # if we've got a combo box lookup the appropriate value for the enum
            if col in self._cValues:
                # lookup the display in the list of _cItems
                for i, v in enumerate(self._cValues[col]):
                    if v.toString() == value.toString():
                        return QVariant(self._cItems[col].toStringList()[i])
            # display commented out rows as --
            elif col == 0:
                if value.toBool():
                    return QVariant(QString('--'))
                else:
                    return QVariant(QString(''))
            # empty string rows should be ""
            elif not value.isNull() and self._types[col] == str and \
                    str(value.toString()) == '' and col != 1:
                value = QVariant(QString('""'))
            return value
        # text editor
        elif role == Qt.EditRole:
            # if the cell is defaulted, display the default value
            if self._isDefault(value, col):
                value = self._defaults[col]
            # if we've got a combo box lookup the appropriate value for the enum
            if col in self._cValues:
                # lookup the display in the list of _cItems
                for i, v in enumerate(self._cValues[col]):
                    if v.toString() == value.toString():
                        return QVariant(self._cItems[col].toStringList()[i])
            # empty string rows should be ""
            elif not value.isNull() and self._types[col] == str and \
                    str(value.toString()) == '' and col != 1:
                value = QVariant(QString('""'))
            return value
        elif role == Qt.ToolTipRole:
            # tooltip
            error = self._isInvalid(value, row, col)
            text = str(self._tooltips[col].toString())
            if error:
                text = '***Error: %s\n%s'%(error, text)
            if col in self._idents:
                lines = ['\nPossible Values: ']
                for name in self._nameList(filt = self._types[col], upto = row):
                    if len(lines[-1]) > 80:
                        lines.append('')
                    lines[-1] += str(name) + ', '
                text += '\n'.join(lines).rstrip(' ,')
            if col == 1 and len(value.toString()) > 0:
                text += ":\n\n" + value.toString()
            return QVariant(text)
        elif role == Qt.ForegroundRole:
            # cell foreground
            if self._isCommented(row):
                # comment
                return QVariant(QColor(120,140,180))
            if self._isDefault(value, col):
                # is default arg (always valid)
                return QVariant(QColor(160,160,160))
            elif self._isInvalid(value, row, col):
                # invalid
                return QVariant(QColor(255,0,0))
            else:
                # valid
                return QVariant(QColor(0,0,0))
        elif role == Qt.BackgroundRole:
            # cell background
            if self._isCommented(row):
                # commented
                return QVariant(QColor(160,180,220))
            elif self._isInvalid(value, row, col):
                # invalid
                return QVariant(QColor(255,200,200))
            elif col in self._defaults:
                # has default
                return QVariant(QColor(255,255,240))
            elif col in self._optional:
                #is optional
                return QVariant(QColor(180,180,180))
            else:
                # valid
                return QVariant(QColor(250,250,250))
        elif role == Qt.UserRole:
            # combo box asking for list of items
            if col in self._idents:
                return QVariant(
                    self._nameList(filt = self._types[col], upto = row))
            elif col in self._cItems:
                return self._cItems[col]
            else:
                return QVariant()
        else:
            return QVariant()

    def clearIndexes(self, indexes):
        # clear cells from a list of QModelIndex's
        begun = False
        for item in indexes:
            if not self.rows[item.row()][item.column()].isNull():
                if not begun:
                    begun = True
                    celltexts = [ '(%s, %d)' %
                        (self._header[c.column()].toString(), c.row() + 1) \
                        for c in indexes ]
                    self.stack.beginMacro('Cleared Cells: '+' '.join(celltexts))
                self.setData(item, QVariant(), Qt.EditRole)
        if begun:
            self.stack.endMacro()
