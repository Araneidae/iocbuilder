from PyQt4.QtGui import \
    QItemDelegate, QComboBox, QPushButton, QCompleter, QLineEdit, \
    QBrush, QStyle, QColor, QPalette
from PyQt4.QtCore import Qt, QVariant, SIGNAL, SLOT

class ComboBoxDelegate(QItemDelegate):

    def createEditor(self, parent, option, index):
        values = index.data(Qt.UserRole)
        if values.isNull():
            editor = QItemDelegate.createEditor(self, parent, option, index)
            editor.connect(editor, SIGNAL('returnPressed()'), editor, SLOT("close()"))
            editor.connect(editor, SIGNAL('editingFinished()'), editor, SLOT("close()"))
            return editor
        elif index.column() == 0:
            editor = BoolButton('#', '', parent)
            editor.connect(editor, SIGNAL('toggled(bool)'), editor, SLOT("close()"))     
            return editor           
        else:
            editor = QComboBox(parent)
            editor.setEditable(True)
            editor.addItems(values.toStringList())
            editor.connect(editor, SIGNAL('activated(int)'), editor, SLOT("close()"))
            return editor

    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            i = editor.findText(index.data(Qt.EditRole).toString())
            if i > -1:
                editor.setCurrentIndex(i)
            else:                
                editor.setEditText(index.data(Qt.EditRole).toString())        
            editor.lineEdit().selectAll()     
        elif isinstance(editor, BoolButton):
            editor.setChecked(index.data(Qt.EditRole).toBool())
        else:
            return QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, QVariant(editor.currentText()), Qt.EditRole)
        elif isinstance(editor, BoolButton):
            model.setData(index, QVariant(editor.isChecked()), Qt.EditRole)
        else:
            return QItemDelegate.setModelData(self, editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        if isinstance(editor, BoolButton):            
            return editor.setGeometry(option.rect)    
        option.rect.setSize(editor.minimumSizeHint().expandedTo(option.rect.size()))        
        if isinstance(editor, QComboBox):
            editor.setGeometry(option.rect)
        else:
            return QItemDelegate.updateEditorGeometry(
                self, editor, option, index)

    def paint(self, painter, option, index):
        option.palette.setColor(
            QPalette.Highlight,QColor(
                index.data(Qt.BackgroundRole)).darker(107))
        option.palette.setColor(
            QPalette.HighlightedText,QColor(
                index.data(Qt.ForegroundRole)).darker(115))
        QItemDelegate.paint(self, painter, option, index)
        if option.showDecorationSelected and \
                (option.state & QStyle.State_Selected):
            painter.drawRect(option.rect)


class BoolButton(QPushButton):

    def __init__(self, onstr, offstr, parent):
        QPushButton.__init__(self, parent)
        self.connect(self, SIGNAL('toggled(bool)'), self.relabel)
        self.onstr = onstr
        self.offstr = offstr
        self.setCheckable(True)
        self.setMinimumSize(10,10)

    def relabel(self, on):
        if on:
            self.setText(self.onstr)
        else:
            self.setText(self.offstr)
