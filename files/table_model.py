from PyQt6.QtCore import Qt, QAbstractTableModel, QVariant, QModelIndex
from PyQt6.QtGui import QFont


class TableModel(QAbstractTableModel):
    """Базовый класс абстрактной модели таблицы"""

    def __init__(self, headers=None, rows=None, parent=None):
        super().__init__(parent)
        self._headers = headers or []
        self._rows = rows or []
        self.password_col = 2

    # Базовая «двумерность»
    def rowCount(self, parent=None):
        return len(self._rows)

    def columnCount(self, parent=None):
        return len(self._headers)

    # Данные на экран
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if index.column() == self.password_col:
                if role == Qt.ItemDataRole.DisplayRole:
                    return "••••••••"
                elif role == Qt.ItemDataRole.EditRole:
                    return self._rows[index.row()][index.column()]  # Реальный пароль для редактирования
            else:
                return self._rows[index.row()][index.column()]

        # Показывать реальный пароль в подсказке
        elif role == Qt.ItemDataRole.ToolTipRole and index.column() == self.password_col:
            return f"Password: {self._rows[index.row()][index.column()]}"
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setPointSize(12)
            font.setFamily("Bahnschrift Light")
            return font
        return QVariant()

    # Заголовки
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self._headers):
                return self._headers[section]
            return section + 1
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setFamily("Bahnschrift Light")
            font.setPointSize(10)
            return font
        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole and index.isValid():
            self._rows[index.row()][index.column()] = str(value)
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    # Вставка/удаление строк (на будущее)
    def insertRows(self, row, count, parent=None):
        self.beginInsertRows(parent or QModelIndex(), row, row + count - 1)
        for _ in range(count):
            self._rows.insert(row, [""] * len(self._headers))
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None):
        self.beginRemoveRows(parent or QModelIndex(), row, row + count - 1)
        for _ in range(count):
            self._rows.pop(row)
        self.endRemoveRows()
        return True
