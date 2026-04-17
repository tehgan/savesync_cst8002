# This Python file uses the following encoding: utf-8
from PySide6.QtQuick import QQuickImageProvider

from icon_provider import IconProvider


# Generates(?) URLs for QImages, so that I can use icons as an Image source.
class IconImageProvider(QQuickImageProvider):
    def __init__(self, icon_provider: IconProvider):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._icon_provider = icon_provider

    def requestImage(self, game_id, size, requested_size, /):
        return self._icon_provider.get_icon(game_id)
