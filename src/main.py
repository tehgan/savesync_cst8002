# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from helpers.url_helper import UrlHelper
from model import SaveFileModel
from icon_provider import IconProvider
from icon_qquick_image_provider import IconImageProvider

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
    icon_provider = IconProvider()
    save_file_model_a = SaveFileModel(icon_provider)
    save_file_model_b = SaveFileModel(icon_provider)
    engine.rootContext().setContextProperty("SaveFileModelA", save_file_model_a)
    engine.rootContext().setContextProperty("SaveFileModelB", save_file_model_b)

    engine.addImageProvider("icons", IconImageProvider(icon_provider))

    qml_file = Path(__file__).resolve().parent / "ui" / "main.qml"

    engine.load(qml_file)
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
