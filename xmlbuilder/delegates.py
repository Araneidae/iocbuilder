from PyQt4.QtGui import \
    QItemDelegate, QComboBox, QPushButton, QCompleter, QLineEdit, \
    QBrush, QStyle, QColor, QPalette, QKeyEvent, QAbstractItemDelegate, QTextEdit, QFont
from PyQt4.QtCore import Qt, QVariant, SIGNAL, SLOT, QEvent

class ComboBoxDelegate(QItemDelegate):

    def createEditor(self, parent, option, index):
        values = index.data(Qt.UserRole)
        self.lastcolumn = index.column() == index.model().columnCount()-1
        if index.column() == 0:
            index.model().setData(index, QVariant(not index.data(Qt.EditRole).toBool()), Qt.EditRole)
            return None
        elif index.column() == 1:
            editor = QTextEdit(parent)
            editor.setFont(QFont('monospace', 10))
            editor.setAcceptRichText(False)
            return editor
        elif values.isNull():
            editor = QLineEdit(parent)
            return editor
        else:
            editor = SpecialComboBox(parent)
            editor.delegate = self
            editor.setEditable(True)
            editor.addItems(values.toStringList())
            return editor

    def eventFilter(self, editor, event):
        # check some key presses
        if event.type() == QEvent.KeyPress:
            # if we pressed return and aren't at the last column send a tab
#            if event.key() == Qt.Key_Return and not self.lastcolumn:
#                event.accept()
#                event = QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier)
            # if we pressed tab and are in the last column send a return
            if event.key() == Qt.Key_Tab and self.lastcolumn:
                event.accept()
                event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
        # just pass the event up
        return QItemDelegate.eventFilter(self, editor, event)

    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            i = editor.findText(index.data(Qt.EditRole).toString())
            if i > -1:
                editor.setCurrentIndex(i)
            else:
                editor.setEditText(index.data(Qt.EditRole).toString())
            editor.lineEdit().selectAll()
        elif isinstance(editor, QTextEdit):
            editor.setText(index.data(Qt.EditRole).toString())
            editor.selectAll()
        else:
            return QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, QVariant(editor.currentText()), Qt.EditRole)
        elif isinstance(editor, QTextEdit):
            model.setData(index, QVariant(editor.toPlainText()), Qt.EditRole)
        else:
            return QItemDelegate.setModelData(self, editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        option.rect.setSize(editor.minimumSizeHint().expandedTo(option.rect.size()))
        if isinstance(editor, QComboBox):
            editor.setGeometry(option.rect)
        elif isinstance(editor, QTextEdit):
            editor.setMinimumWidth(480)
            editor.setMinimumHeight(160)
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

class SpecialComboBox(QComboBox):
    # Qt outputs an activated signal if you start typing then mouse click on the
    # down arrow. By delaying the activated event until after the mouse click
    # we avoid this problem
    def closeEvent(self, i):
        self.delegate.commitData.emit(self)
        self.delegate.closeEditor.emit(self, QAbstractItemDelegate.SubmitModelCache)

    def mousePressEvent(self, event):
        QComboBox.mousePressEvent(self, event)
        self.activated.connect(self.closeEvent)
