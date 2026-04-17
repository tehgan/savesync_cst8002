# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QAbstractListModel, Qt, QUrl, QModelIndex, Slot

from parser import SaveFile, parse


# TODO: See https://doc.qt.io/qt-6/model-view-programming.html#model-subclassing-reference for what I need to implement
# Adapted from https://doc.qt.io/qtforpython-6/examples/example_qml_editingmodel.html
class SaveFileModel(QAbstractListModel):
    def __init__(self, icon_provider, parent=None):
        super().__init__(parent)

        # Keep reference to icon provider, for dict of game IDs/icons
        self._icon_provider = icon_provider

        # Strongly typed to allow access to member variables
        self._items: list[SaveFile] = []
        self.FILE_URL = Qt.ItemDataRole.UserRole.value
        self.ICON_URL = Qt.ItemDataRole.UserRole + 1
        self.TITLE = Qt.ItemDataRole.UserRole + 2
        self.DESCRIPTION = Qt.ItemDataRole.UserRole + 3
        self.LAST_MODIFIED = Qt.ItemDataRole.UserRole + 4
        self._role_names = {
            # Keys must be byte strings, as roleNames() expects QByteArray
            # Using standard strings raises the error 'expected dict, got dict'... Not fun to debug.
            self.FILE_URL: b'fileUrl',
            self.ICON_URL: b'iconUrl',
            self.TITLE: b'title',
            self.DESCRIPTION: b'description',
            self.LAST_MODIFIED: b'lastModified'
        }

    # TODO: Called twice after repopulate, not sure why, may just be a Qt quirk
    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._items)

    # Seems that this is only called automatically if a Qml property is marked as 'required'
    def data(self, index, /, role=...):
        if not index.isValid():
            return None
        elif role in self._role_names:
            match role:
                case self.FILE_URL:
                    url = QUrl(self._items[index.row()].file_path)
                    return url
                case self.ICON_URL:
                    # URL for use with IconImageProvider
                    raw_url = "image://icons/" + self._items[index.row()].file_info
                    url = QUrl(raw_url)
                    return url
                case self.TITLE:
                    return self._items[index.row()].title
                case self.DESCRIPTION:
                    return self._items[index.row()].description
                case self.LAST_MODIFIED:
                    return self._items[index.row()].localized_last_modified
        return None

    def roleNames(self):
        return self._role_names

    def flags(self, index, /):
        # No item flags for now, https://doc.qt.io/qt-6/qt.html#ItemFlag-enum
        print('flags called')
        return 0

    # TODO: Works, but for assignment 3 I'll be looking into optimizations, both for performance and correctness.
    @Slot(QUrl)
    def repopulate(self, directory_qurl: QUrl):
        print('Repopulating save file list...')
        old_row_count = len(self._items)
        directory_path = directory_qurl.toLocalFile()
        items = parse(directory_path, self._icon_provider)
        self.beginResetModel()
        self._items = items
        new_row_count = len(self._items)
        upper_index = max(old_row_count, new_row_count)
        # print('Calling on index 0 and ', end='')
        print(upper_index)
        self.endResetModel()
        """
        Keeping these functions in as a reminder on what I should be looking into (as resetting on each directory change MAY be too destructive/unoptimized)
        self.beginInsertRows(QModelIndex(), )
        self.dataChanged.emit(self.index(0), self.index(self.rowCount() - 1), [])
        self.dataChanged.emit(self.index(0,0), self.index(upper_index-1,0))
        self.beginInsertRows(QModelIndex(), 0, 2)
        self.endInsertRows()
        """

    # For comparing timestamps between differing models
    @Slot(result='QVariant')
    def get_last_modified(self):
        modified_dict = {}
        for item in self._items:
            modified_dict[item.file_info] = item.epoch_last_modified
        return modified_dict
