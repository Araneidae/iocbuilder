#!/bin/env dls-python2.7

from PyQt4.QtGui import \
    QMainWindow, QMessageBox, QApplication, QTableView, \
    QGridLayout, QListWidget, QDockWidget, QAbstractItemView, QUndoView, \
    QMenu, QFileDialog, QInputDialog, QLineEdit, QListWidgetItem, \
    QClipboard, QDialog, QScrollArea, QTextEdit, QFont, QPushButton, QLabel, \
    QToolTip, QIcon
from PyQt4.QtCore import Qt, SIGNAL, SLOT, QSize, QVariant, QString, QEvent, QPoint
from delegates import ComboBoxDelegate
import sys, signal, os, re, traceback
from optparse import OptionParser

class TooltipMenu(QMenu):
    def event(self, e):
        if e.type() == QEvent.ToolTip:
            # show action tooltip instead of widget tooltip
            act = self.actionAt(e.pos());
            if act and act.toolTip() != "None":
                QToolTip.showText(e.globalPos(), act.toolTip(), self)
                return True
        return QMenu.event(self, e)

## /todo A toggle button for showing and hiding optional values
class TableView(QTableView):

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            # override delete to delete the cell contents
            self.menuClear()
        else:
            return QTableView.keyPressEvent(self, event)

    def mousePressEvent(self, event):
        # override middle button paste
        if event.button() == Qt.MidButton:
            cb = app.clipboard()
            item = self.indexAt(event.pos())
            if item:
                item.model().setData(
                    item,QVariant(cb.text(QClipboard.Selection)))
        else:
            QTableView.mousePressEvent(self, event)

    def copy(self):
        selRange  = self.selectedIndexes()
        if not selRange:
            return
        rows = [ x.row() for x in selRange ]
        cols = [ x.column() for x in selRange ]
        minrows = min(rows)
        mincols = min(cols)
        nrows = max(rows) - minrows + 1
        ncols = max(cols) - mincols + 1
        data = []
        for _ in range(nrows):
            data.append(['\x00'] * ncols)
        for cell in selRange:
            data[cell.row() - minrows][cell.column() - mincols] = \
                str(cell.data(Qt.EditRole).toString())
        # insert escapes
        for row in data:
            for i, val in enumerate(row):
                row[i] = val.replace("\n", "\\n").replace("\t", "\\t")                
        rows = ['\t'.join(row) for row in data]
        cb = app.clipboard()
        cb.setText(QString('\n'.join(rows)))

    def pythonCode(self):
        self.codeBox.parent = self
        self.codeBox.show()

    def fillCellsInc(self):
        return self.fillCells(inc=True)

    def subText(self, srcText, number):
        """Increment the last number (with no - signs) in srcText by number"""
        # find the last positive int in the string
        match = re.search("[^\d]*(\d+)[^\d]*$", srcText)        
        # if we found a number
        if match:
            text  = srcText[:match.start(1)]
            fstr = '%%0%dd' % (match.end(1) - match.start(1))
            text += fstr % (int(srcText[match.start(1):match.end(1)]) + number)
            text += srcText[match.end(1):]
        else:
            text = srcText        
        return text

    def fillCells(self, inc=False):
        selRange = self.selectedIndexes()
        if not selRange:
            return
        rows = [ x.row() for x in selRange ]
        cols = [ x.column() for x in selRange ]
        minrows = min(rows)
        mincols = min(cols)
        nrows = max(rows) - minrows + 1
        ncols = max(cols) - mincols + 1
        if inc:
            self.model().stack.beginMacro('Increment Cells')
        else:
            self.model().stack.beginMacro('Fill Cells')
        if nrows == 1:
            for x in selRange:
                if x.column() == mincols and x.row() == minrows:
                     source = x
                     break
            cells = [x for x in selRange if x != source]
            srcText = str(source.data().toString())
            # Fill cells across
            for cell in cells:                
                if inc:
                    text = self.subText(srcText, cell.column() - mincols)
                else:
                    text = srcText
                self.__setCell(self.model(), cell.row(), cell.column(), text)
        else:
            # Treat as a group of columns
            for col in set(cols):
                cells = [ x for x in selRange if x.column() == col ]
                minrows = min([x.row() for x in cells])
                source = [ x for x in cells if x.row() == minrows ][0]
                cells = [ x for x in cells if x != source ]
                srcText = str(source.data().toString())
                # Fill cells down
                for cell in cells:
                    if inc:
                        text = self.subText(srcText, cell.row() - minrows)
                    else:
                        text = srcText
                    self.__setCell(self.model(), cell.row(), cell.column(), text)
        self.model().stack.endMacro()

    def cut(self):
        self.copy()
        self.menuClear()

    def menuClear(self):
        items = self.selectedIndexes()
        if items:
            items[0].model().clearIndexes(self.selectedIndexes())
            self.clearSelection()

    def __setCell(self, model, row, col, val):
        if val != '\x00':
            index = model.index(row, col)
            model.setData(index, QVariant(val), Qt.EditRole)

    def paste(self):
        cb = app.clipboard()
        clipText = str(cb.text()).rstrip('\n')
        selRange = self.selectedIndexes()
        if not selRange:
            return
        rows = [ x.row() for x in selRange ]
        cols = [ x.column() for x in selRange ]
        minrows = min(rows)
        mincols = min(cols)
        if '\t' in clipText or '\n' in clipText:
            # many cells in clipboard
            data = [row.split('\t') for row in clipText.split('\n')]
            nrows = len(data)
            ncols = max([len(x) for x in data])
        else:
            # single cell in clipboard
            nrows = max(rows) - minrows + 1
            ncols = max(cols) - mincols + 1
            data = [ [clipText] * ncols ] * nrows
        # replace escapes
        for row in data:
            for i, val in enumerate(row):
                row[i] = val.replace("\\n", "\n").replace("\\t", "\t")
        selRange[0].model().stack.beginMacro('Paste from clipboard')
        if len(selRange) == 1:
            # single cell selected, so write the size of the clipboard
            model = selRange[0].model()
            for row in range(minrows, minrows + nrows):
                for col in range(mincols, mincols + ncols):
                    val = data[row - minrows][col - mincols]
                    if model.index(row, col).data() != val:
                        self.__setCell(model, row, col, val)
        else:
            # many cells selected
            for cell in selRange:
                try:
                    val = data[(cell.row() - minrows) % nrows][(cell.column() - mincols) % ncols]
                except IndexError:
                    pass
                else:
                    if cell.data() != val:
                        self.__setCell(cell.model(), cell.row(), cell.column(), val)
        selRange[0].model().stack.endMacro()

    def insertRowUnder(self):
        self.insertRow(True)

    def insertRow(self, under = False):
        selRange = self.selectedIndexes()
        if selRange:
            rows = [ x.row() for x in selRange ]
            minrows = min(rows)
            nrows = max(rows) - minrows + 1
            if under:
                minrows += nrows
        else:
            if under:
                minrows = self.model().rowCount()
            else:
                minrows = 0
            nrows = 1
        self.model().insertRows(minrows, nrows)

    def removeRow(self):
        selRange = self.selectedIndexes()
        if not selRange:
            return
        rows = [ x.row() for x in selRange ]
        for row in reversed(sorted(set(rows))):
            selRange[0].model().removeRows(row, 1)

    def contextMenuEvent(self,event):
        # make a popup menu
        menu = self.parent().menuEdit
        menu.exec_(event.globalPos())

class ListView(QListWidget):

    def dropEvent(self,event):
        text = self.currentItem().text()
        ret = QListWidget.dropEvent(self,event)
        self.writeNames()
        items = self.findItems(text, Qt.MatchExactly)
        if items:
            self.setCurrentItem(items[0])
        self.parent().parent().populate(name = str(items[0].text()))
        return ret

    def contextMenuEvent(self,event):
        # make a popup menu
        menu = self.parent().parent().menuComponents
        menu.exec_(event.globalPos())

    def removeTable(self):
        sel = self.selectedItems()
        texts = [self.item(i).text()
            for i in range(self.count())
            if self.item(i) not in sel ]
        self.clear()
        for text in texts:
            self.addItem(text)
        self.writeNames()
        self.parent().parent().populate()

    def writeNames(self):
        store = self.parent().parent().store
        items = [str(self.item(i).text()) for i in range(self.count())]
        store.setTableNames(items)
        self.parent().parent()._setClean()


class GUI(QMainWindow):

    def __init__(self, debug=False):
        QMainWindow.__init__(self)
        # initialise filename
        self.filename = None        
        # make the data store
        from xmlstore import Store
        self.store = Store(debug = debug)
        # view the current table
        self.tableView = TableView(self)
        #self.tableView.setDragEnabled(True);
        #self.tableView.setDragDropMode(QAbstractItemView.InternalMove)
        #self.tableView.setAcceptDrops(True);
        #self.tableView.setDropIndicatorShown(True);        
        self.tableView.verticalHeader().sectionMoved.connect(self.sectionMoved)
        self.tableView.verticalHeader().setMovable(True)
        
        self.setCentralWidget(self.tableView)
        # add a custom delegate to it
        self.delegate = ComboBoxDelegate()
        self.tableView.setItemDelegate(self.delegate)
        # dock the table selection on the left
        self.dock1 = QDockWidget(self)
        self.listView = ListView(self)
        self.listView.setDragEnabled(True);
        self.listView.setDragDropMode(QAbstractItemView.InternalMove)
        self.listView.setDropIndicatorShown(True);
        self.dock1.setWidget(self.listView)
        self.dock1.setFeatures(
            QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock1)
        # connect it to the populate method
        self.connect(self.listView, SIGNAL('activated ( const QModelIndex & )'),
                     self.populate)
        self.connect(self.listView, SIGNAL('clicked ( const QModelIndex & )'),
                     self.populate)
        # dock the undoView on the left
        self.dock2 = QDockWidget(self)
        self.undoView = QUndoView(self.store.stack)
        self.dock2.setWidget(self.undoView)
        self.dock2.setFeatures(
            QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.dock2.setWindowTitle('Undo Stack')
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock2)
        # create a menubar
        self.menu = self.menuBar()
        # create file menu headings
        self.menuFile = self.menu.addMenu('File')
        self.menuFile.addAction('New', self.New).setShortcut('CTRL+N')
        self.menuFile.addAction('Open...', self.Open).setShortcut('CTRL+O')
        self.menuFile.addAction('Reload', self.Reload)
        self.menuFile.addAction('Save', self.Save).setShortcut('CTRL+S')
        self.menuFile.addAction('Save As...', self.SaveAs)
        self.menuFile.addSeparator()
        self.menuFile.addAction('Set Architecture...', self.setArch)
        self.menuFile.addSeparator()
        self.menuFile.addAction('Quit', self.closeEvent).setShortcuts(['CTRL+Q', 'ALT+F4'])
        # create edit menu headings
        self.menuEdit = self.menu.addMenu('Edit')
        self.menuEdit.addAction('Insert Row',
            self.tableView.insertRow).setShortcut('CTRL+I')
        self.menuEdit.addAction('Insert Row Under',
            self.tableView.insertRowUnder).setShortcut('CTRL+U')
        self.menuEdit.addAction('Remove Row', self.tableView.removeRow)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction('Cut',
            self.tableView.cut).setShortcut('CTRL+X')
        self.menuEdit.addAction('Copy',
            self.tableView.copy).setShortcuts(['CTRL+C', 'CTRL+INS'])
        self.menuEdit.addAction('Paste',
            self.tableView.paste).setShortcuts(['CTRL+V', 'SHIFT+INS'])
        self.menuEdit.addAction('Clear',
            self.tableView.menuClear).setShortcut('CTRL+D')
        self.menuEdit.addSeparator()
        self.menuEdit.addAction('Fill Cells',
            self.tableView.fillCells).setShortcut('CTRL+L')
        self.menuEdit.addAction('Fill Cells and Increment',
            self.tableView.fillCellsInc).setShortcut('CTRL+R')
        self.menuEdit.addAction('Python Code...',
            self.tableView.pythonCode).setShortcut('CTRL+P')
        self.tableView.codeBox = pythonCode()
        self.menuEdit.addSeparator()
        self.menuEdit.addAction('Undo',
            self.store.stack, SLOT('undo()')).setShortcut('CTRL+Z')
        self.menuEdit.addAction('Redo',
            self.store.stack, SLOT('redo()')).setShortcut('CTRL+SHIFT+Z')
        # create component menu
        self.menuComponents = self.menu.addMenu('Components')
        self.resize(QSize(1000,500))

    def Save(self):
        # save menu command
        self.SaveAs(self.filename)

    def setArch(self):
        arch = self.store.getArch()
        arch, ok = QInputDialog.getText(self, 'Architecture Dialog',
             'Enter Architecture', QLineEdit.Normal, arch)
        arch = str(arch)
        if ok:
            self.store.setArch(arch)

    def SaveAs(self, filename = ''):
        # save as menu command
        if filename == '':
            filename = str(QFileDialog.getSaveFileName())
        if filename != '':
            self.filename = filename
            self.store.Save(filename)
            self._setClean()

    def Reload(self):
        if self.filename is not None:
            self.Open(self.filename, name = self.tablename)

    def Open(self, filename = '', name = None):
        # make sure the user is sure if there are unsaved changes
        if self.__prompt_unsaved() == QMessageBox.Cancel:
            return
        # ask for a filename
        if filename == '':
            filename = str(QFileDialog.getOpenFileName())
        if filename == '':
            return
        # store the filename
        self.filename = filename
        # tell the store to open a new set of tables
        try:
            problems, warnings = self.store.Open(filename)
            if problems:
                errorstr = 'Can\'t load all object types: '+', '.join(problems)
                QMessageBox.warning(self,'Open Error',errorstr)
            if warnings:
                errorstr = \
                    'The following warnings were generated:\n' + \
                    '\n'.join(warnings)
                QMessageBox.warning(self,'Open Warnings',errorstr)
        except Exception, e:
            x = formLog('An error ocurred. Make sure all the modules listed '
                'in RELEASE files are built. Check the text below for '
                'details:\n\n' + traceback.format_exc(), self)
            x.show()
            return
        # populate
        self.setWindowTitle('XEB - %s[*]'%filename)
        self.listView.clear()
        for t in self.store.getTableNames():
            self.__insertListViewItem(t)
        self.__populateMenu()
        self.populate(name = name)
        self._setClean()

    def __insertListViewItem(self, name, row = None):
        ob = self.store._tables[name].ob
        item = QListWidgetItem(QString(name))
        doc = str(ob.__doc__)
        search = re.search(r'\n[ \t]*', doc)
        if search:
            doc = re.sub(search.group(), '\n', doc)
        item.setToolTip(QString(str(doc)))
        if row is None:
            self.listView.addItem(item)
        else:
            self.listView.insertItem(row, item)

    def New(self, filename = ''):
        print "**", filename
        # make sure the user is sure if there are unsaved changes
        if self.__prompt_unsaved() == QMessageBox.Cancel:
            return
        # tell the store to create a new set of tables
        try:
            self.store.New(filename)
        except Exception, e:
            x = formLog('An error ocurred. Make sure all the modules listed '
                'in RELEASE files are built. Check the text below for '
                'details:\n\n' + traceback.format_exc(), self)
            x.show()
            return
        self.filename = filename
        self.setWindowTitle('XEB - %s[*]' % (filename or "<untitled>"))
        self.listView.clear()
        self.__populateMenu()
        self.populate()
        self.store.setStored()
        self._setClean()


    def closeEvent(self, event=None):
        # override closeEvent so we can check things have been saved
        if self.__prompt_unsaved() == QMessageBox.Cancel:
            if event:
                event.ignore()
        else:        
            if event:
                event.accept()
            else:
                app.quit()

    def __prompt_unsaved(self):
        ret = QMessageBox.Discard
        if self.isWindowModified():
            ret = QMessageBox.question(self, 'Unsaved Changes',
                'The current file has unsaved changes, what would you like to do?',
                (QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel))
            if ret == QMessageBox.Save:
                self.Save()
        return ret

    def __populateMenu(self):
        # populate the component menu with menus
        self.menuComponents.clear()
        self.menuComponents.addAction('Remove Table', self.listView.removeTable)
        self.menuComponents.addSeparator()
        modules = {}
        self.functions = []
        autos = []
        normals = []
        for name in self.store.allTableNames():
            ob = self.store._tables[name].ob
            if ob.ModuleName not in modules:
                modules[ob.ModuleName] = TooltipMenu(ob.ModuleName, self.menuComponents)
                self.menuComponents.addMenu(modules[ob.ModuleName])
            def f(name = name):
                self.populate(name = name)
            self.functions.append(f)
            if ob.__name__.startswith("auto_"):
                autos.append((ob, f))
            else:
                normals.append((ob, f))
        for ob, f in normals:
            a = modules[ob.ModuleName].addAction(ob.__name__, f)
            a.setToolTip(str(ob.__doc__))
        sep_done = []
        for ob, f in autos:
            if ob.ModuleName not in sep_done:
                sep_done.append(ob.ModuleName)
                modules[ob.ModuleName].addSeparator()
            a = modules[ob.ModuleName].addAction(ob.__name__, f)
            a.setToolTip("None")

    def populate(self, index = None, name = None):
        # first store the state of the current view
        if getattr(self, "tablename", None) in self.store.getTableNames():
            topLeftIndex = self.tableView.indexAt(QPoint(0,0)) 
            self.store.getTable(self.tablename).topLeftIndex = topLeftIndex
        if index is not None:
            name = str(index.data().toString())
        if name is None:
            names = self.store.getTableNames()
            if names:
                name = names[0]
            else:
                name = sorted(self.store._tables.keys())[0]
        table = self.store.getTable(name)
        # make sure the listView is up to date
        items = self.listView.findItems(QString(name), Qt.MatchExactly)
        if items:
            self.listView.setCurrentItem(items[0])
        else:
            row = self.listView.currentRow() + 1
            if row == 0:
                row = self.listView.count() + 1
            self.__insertListViewItem(name, row)
            self.listView.setCurrentRow(row)
            self.listView.writeNames()
        self.tablename = name
        self.dock1.setWindowTitle('Table: '+name)
        self.tableView.setModel(table)
        self.tableView.resizeColumnsToContents()
        self.connect(table.stack, SIGNAL('cleanChanged(bool)'),
                     self._setClean)
        # scroll to the stored point of the table
        if table.topLeftIndex:
            self.tableView.scrollTo(table.index(table.rowCount() - 1, table.columnCount() - 1))
            self.tableView.scrollTo(table.topLeftIndex)
        elif table.rowCount():
            self.tableView.scrollTo(table.index(0, 0))

    def sectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.store.getTable(self.tablename).sectionMoved(logicalIndex, oldVisualIndex, newVisualIndex)
        self.tableView.selectRow(newVisualIndex)

    def _isClean(self):
        for s in self.store.stack.stacks():
            if not s.isClean():
                return False
        return self.store.isClean()

    def _setClean(self, clean=None):
        self.setWindowModified(not self._isClean())

class formLog(QDialog):
    '''Error log form'''
    def __init__(self,text,*args):
        '''text = text to display in a readonly QTextEdit'''
        QDialog.__init__(self,*args)
        formLayout = QGridLayout(self)#,1,1,11,6,'formLayout')
        self.formLayout = formLayout
        self.scroll = QScrollArea(self)
        self.lab = QTextEdit()
        self.lab.setFont(QFont('monospace', 10))
        self.lab.setText(text)
        self.lab.setReadOnly(True)
        self.scroll.setWidget(self.lab)
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumWidth(700)
        self.scroll.setMinimumHeight(700)
        formLayout.addWidget(self.scroll,1,1,1,2)
        self.btnClose = QPushButton('Close', self)
        formLayout.addWidget(self.btnClose,3,2,1,1)
        self.connect(self.btnClose, SIGNAL('clicked ()'),self.close)

class pythonCode(formLog):
    def __init__(self,*args):
        formLog.__init__(self,"text = text.replace('.', '-')",*args)
        self.btnRun = QPushButton('Run', self)
        self.scroll.setMinimumHeight(100)
        self.connect(self.btnRun, SIGNAL('clicked ()'),self.runCode)
        self.formLayout.addWidget(self.btnRun,3,1,1,1)
        self.lab.setReadOnly(False)
        self.help = QLabel("Variables:\n\ttext: cell text\n\tcell: cell object\n")
        self.formLayout.addWidget(self.help,2,1,1,2)

    def runCode(self):
        code = str(self.lab.toPlainText())
        self.selRange = self.parent.selectedIndexes()
        model = self.selRange[0].model()
        model.stack.beginMacro('Run python code')
        for cell in self.selRange:
            text = str(cell.data().toString())
            env = dict(cell = cell, text = text)
            try:
                exec(code, env)
            except:
                print "Failed"
            else:
                if env["text"] != text:
                    index = model.index(cell.row(), cell.column())
                    model.setData(index, QVariant(env["text"]), Qt.EditRole)
        model.stack.endMacro()

def main():
    parser = OptionParser('usage: %prog [options] [<xml-file>]')
    parser.add_option(
        '-d', action='store_true', dest='debug',
        help='Print lots of debug information')
    (options, args) = parser.parse_args()
    if options.debug:
        debug = True
    else:
        debug = False
    global app
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.dirname(__file__) + '/xeb.png'))
    g = GUI(debug=debug)
    g.show()
    if len(args)>0:
        if os.path.isfile(args[0]):
            g.Open(args[0])
        else:
            QMessageBox.warning(g,'Open Error','No such file "%s". Starting new file'%args[0])
            g.New(args[0])
    else:
        g.New()
    # catch CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec_())

if __name__ == '__main__':
    root = os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..', '..'))
    sys.path.append(os.path.join(root, 'dls_environment'))
    sys.path.append(os.path.join(root, 'dls_dependency_tree'))
    sys.path.append(os.path.join(root, 'iocbuilder'))
    main()
