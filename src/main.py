# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider

from helpers.url_helper import UrlHelper
from model import SaveFileModel


# https://doc.qt.io/qtforpython-6/PySide6/QtQuick/QQuickImageProvider.html
class IconImageProvider(QQuickImageProvider):
    def requestPixmap(self, id, size, requestedSize, /):
        width = 32
        height = 32
        if size:
            size = QSize(width, height)
        pixmap = QPixmap(requestedSize.width() > 0 if requestedSize.width() else width,
                         requestedSize.height() > 0 if requestedSize.height() else height)
        # TODO: Get ID, fill w/ rgba or smth


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    # Both organization and app names must be set in order to use QSettings
    QGuiApplication.setOrganizationName("tehgan")
    QGuiApplication.setApplicationName("savesync")

    engine = QQmlApplicationEngine()

    # Allow access to UrlHelper functions from within Qml
    url_helper = UrlHelper()
    engine.rootContext().setContextProperty("UrlHelper", url_helper)

    # Allow access to SaveFileModel from within Qml (data-getting from main.qml, repopulation call from Preferences.qml)
    save_file_model = SaveFileModel()
    engine.rootContext().setContextProperty("SaveFileModel", save_file_model)

    qml_file = Path(__file__).resolve().parent / "ui" / "main.qml"

    engine.load(qml_file)
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
