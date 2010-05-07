from PyQt4.QtGui import QItemDelegate, QComboBox, QPushButton, QCompleter, QLineEdit, QBrush, QStyle, QColor, QPalette
from PyQt4.QtCore import Qt, QVariant, SIGNAL        

class ComboBoxDelegate(QItemDelegate):

    def createEditor(self, parent, option, index):
        print "createEditor"    
        values = index.data(Qt.UserRole)        
        if values.isNull():
            return QItemDelegate.createEditor(self, parent, option, index)
        elif values.type() == QVariant.Bool:
            if index.column() == 0:                
                return BoolButton("#", "", parent)            
            else:
                return BoolButton("true", "false", parent)
        else:
            editor = ComboLineEdit(values.toStringList(), parent)
            return editor
            
    def setEditorData(self, editor, index):
        print "setEditorData"
        if isinstance(editor, BoolButton):
            editor.setChecked(index.data(Qt.EditRole).toBool())       
        elif isinstance(editor, ComboLineEdit):    
            editor.setText(index.data(Qt.EditRole).toString())
        else:
            return QItemDelegate.setEditorData(self, editor, index)
            
    def setModelData(self, editor, model, index):
        print "setModelData"    
        if isinstance(editor, ComboLineEdit):
            model.setData(index, QVariant(editor.text()), Qt.EditRole)           
        elif isinstance(editor, BoolButton):
            model.setData(index, QVariant(editor.isChecked()), Qt.EditRole)            
        else:
            return QItemDelegate.setModelData(self, editor, model, index)    
            
    def updateEditorGeometry(self, editor, option, index):
        print "updateEditorGeometry"
        if isinstance(editor, QComboBox):
            editor.setGeometry(option.rect)         
        elif isinstance(editor, ComboLineEdit):
            editor.setGeometry(option.rect)               
        else:
            return QItemDelegate.updateEditorGeometry(self, editor, option, index)
            
    def paint(self, painter, option, index):
        option.palette.setColor(QPalette.Highlight,QColor(index.data(Qt.BackgroundRole)).darker(107))
        option.palette.setColor(QPalette.HighlightedText,QColor(index.data(Qt.ForegroundRole)).darker(115))    
        QItemDelegate.paint(self, painter, option, index)
        if (option.showDecorationSelected and (option.state & QStyle.State_Selected)):
            painter.drawRect(option.rect)        
        

class ComboLineEdit(QLineEdit):
    def __init__(self, l, parent):
        QLineEdit.__init__(self, parent)
        self.c = QCompleter(l, parent)
        self.c.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.c.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.c)
        

class BoolButton(QPushButton):

    def __init__(self, onstr, offstr, parent):
        QPushButton.__init__(self, parent)
        self.connect(self, SIGNAL('toggled(bool)'), self.relabel)
        self.onstr = onstr
        self.offstr = offstr
        self.setCheckable(True)        
        
    def relabel(self, on):
        if on:
            self.setText(self.onstr)
        else:
            self.setText(self.offstr)
    
