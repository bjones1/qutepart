"""Autocompletion widget and logic
"""

import re

from PyQt4.QtCore import QAbstractItemModel, QModelIndex, QObject, QSize, Qt
from PyQt4.QtGui import QListView, QStyle

from qutepart.htmldelegate import HTMLDelegate


class _CompletionModel(QAbstractItemModel):
    """QAbstractItemModel implementation for a list of completion variants
    """
    def __init__(self, wordBeforeCursor, words):
        QAbstractItemModel.__init__(self)
        
        self._typedText = wordBeforeCursor
        self._words = words

        self._canCompleteText = ''

    def plainText(self, rowIndex):
        """Get plain text of specified item
        """
        return self._words[rowIndex]

    def data(self, index, role = Qt.DisplayRole):
        """QAbstractItemModel method implementation
        """
        if role == Qt.DisplayRole:
            text = self.plainText(index.row())
            typed = text[:len(self._typedText)]
            canComplete = text[len(self._typedText):len(self._typedText) + len(self._canCompleteText)]
            rest = text[len(self._typedText) + len(self._canCompleteText):]
            return '<html>' \
                           '%s' \
                        '<b>%s</b>' \
                           '%s' \
                    '</html>' % (typed, canComplete, rest)
        else:
            return None
    
    def rowCount(self, index):
        """QAbstractItemModel method implementation
        """
        return len(self._words)
    
    def typedText(self):
        """Get current typed text
        """
        return self._typedText
    
    """Trivial QAbstractItemModel methods implementation
    """
    def flags(self, index):                                 return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    def headerData(self, index):                            return None
    def columnCount(self, index):                           return 1
    def index(self, row, column, parent = QModelIndex()):   return self.createIndex(row, column)
    def parent(self, index):                                return QModelIndex()


class _ListView(QListView):
    """Completion list widget
    """
    def __init__(self, qpart, model):
        QListView.__init__(self, qpart.viewport())
        self.setItemDelegate(HTMLDelegate(self))
        self.setFont(qpart.font())
        
        qpart.setFocus()
        
        self._qpart = qpart
        self.setModel(model)
        
        self.move(self._qpart.cursorRect().right() - self._horizontalShift(),
                  self._qpart.cursorRect().bottom())
        
        self.show()
    
    def __del__(self):
        """Without this empty destructor Qt prints strange trace
            QObject::startTimer: QTimer can only be used with threads started with QThread
        when exiting
        """
        pass
    
    def del_(self):
        """Explicitly called destructor.
        Removes widget from the qpart
        """
        self.hide()
        self.setParent(None)
        # Now gc could collect me
    
    def sizeHint(self):
        """QWidget.sizeHint implementation
        Automatically resizes the widget according to rows count
        """
        width = max([self.fontMetrics().width(self.model().plainText(i)) \
                        for i in range(self.model().rowCount(QModelIndex()))])
        
        width += 4  # margin
        
        # drawn with scrollbar without +2. I don't know why
        height = self.sizeHintForRow(0) * self.model().rowCount(QModelIndex()) + 2
        
        return QSize(width, height)

    def _horizontalShift(self):
        """List should be plased such way, that typed text in the list is under
        typed text in the editor
        """
        strangeAdjustment = 2  # I don't know why. Probably, won't work on other systems and versions
        return self.fontMetrics().width(self.model().typedText()) + strangeAdjustment


class Completer(QObject):
    """Object listens Qutepart widget events, computes and shows autocompletion lists
    """
    _wordPattern = "\w\w+"
    _wordRegExp = re.compile(_wordPattern)
    _wordAtEndRegExp = re.compile(_wordPattern + '$')
    
    def __init__(self, qpart):
        self._qpart = qpart
        self._widget = None
    
    def __del__(self):
        """Close completion widget, if exists
        """
        self.closeCompletion()
    
    def invokeCompletionIfAvailable(self):
        """Invoke completion, if available. Called after text has been typed in qpart
        """
        self.closeCompletion()
        
        wordBeforeCursor = self._wordBeforeCursor()
        if wordBeforeCursor is None:
            print 'no word'
            return
        
        words = self._makeListOfCompletions(wordBeforeCursor)
        if not words:
            return
        
        model = _CompletionModel(wordBeforeCursor, words)
        
        self._widget = _ListView(self._qpart, model)

    def closeCompletion(self):
        """Close completion, if visible.
        Delete widget
        """
        if self._widget is not None:
            self._widget.del_()
            self._widget = None
    
    def isActive(self):
        """Check if completion list is visible
        """
        return self._widget is not None
    
    def _wordBeforeCursor(self):
        """Get word, which is located before cursor
        """
        cursor = self._qpart.textCursor()
        textBeforeCursor = cursor.block().text()[:cursor.position() - cursor.block().position()]
        match = self._wordAtEndRegExp.search(textBeforeCursor)
        if match:
            return match.group(0)
        else:
            return None
    
    def _makeWordSet(self):
        """Make a set of words, which shall be completed, from text
        """
        return set(self._wordRegExp.findall(self._qpart.toPlainText()))

    def _makeListOfCompletions(self, wordBeforeCursor):
        """Make list of completions, which shall be shown
        """
        allWords = self._makeWordSet()
        onlySuitable = [word for word in allWords \
                                if word.startswith(wordBeforeCursor) and \
                                   word != wordBeforeCursor]
        
        return sorted(onlySuitable)