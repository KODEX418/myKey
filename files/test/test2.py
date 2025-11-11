from PyQt6.QtWidgets import QApplication, QMainWindow, QSpinBox, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import QSize, Qt
import sys

def create_plus_minus_images():
    """Создание изображений для + и -"""
    # Создаем изображение для +
    plus_pixmap = QPixmap(16, 16)
    plus_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(plus_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.GlobalColor.white)
    painter.setBrush(Qt.GlobalColor.white)

    # Рисуем плюс
    painter.drawRect(7, 3, 2, 10)  # Вертикальная линия
    painter.drawRect(3, 7, 10, 2)  # Горизонтальная линия
    painter.end()

    # Сохраняем изображение
    plus_image_path = "plus_icon.png"
    plus_pixmap.save(plus_image_path)

    # Создаем изображение для -
    minus_pixmap = QPixmap(16, 16)
    minus_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(minus_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.GlobalColor.white)
    painter.setBrush(Qt.GlobalColor.white)

    # Рисуем минус
    painter.drawRect(3, 7, 10, 2)  # Горизонтальная линия
    painter.end()

    # Сохраняем изображение
    minus_image_path = "minus_icon.png"
    minus_pixmap.save(minus_image_path)
create_plus_minus_images()

