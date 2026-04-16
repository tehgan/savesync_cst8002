# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QObject, Slot, QUrl, QDir

# TODO: Remove this comment if there's a spot for it in the report
"""
QML + QSettings seems to treat urls as strings, so to avoid adding JavaScript
 (which would muddy the codebase; core is Python, ui is Qml, JavaScript serves no separate purpose),
  I have to create a helper class which can be accessed from my Qml files.
"""
class UrlHelper(QObject):
    # Used to format URLs (which contains 'file://' prefix) into a more user-friendly path string (e.g. '/home/user/selected_folder')
    @Slot(str, result=str)
    def to_local_file(self, url_string):
        # Python allows for String truthiness (blank = false), checking can prevent unwanted function runs (e.g. on program launch and exit)
        if url_string:
            url = QUrl(url_string)
            if (url.isLocalFile()):
                # toLocalFile used rather than RegEx in case of edge cases; I found conflicting answers online regarding backslash count per operating system (file:// or file:///)
                return url.toLocalFile()
        else:
            # If the text property is set to blank, placeholderText takes its place.
            return ""

    # Given a file's url, returns its parent directory's url
    @Slot(str, result=str)
    def get_parent_dir(self, url_string):
        if url_string:
            # QDir doesn't initialize property with a raw URL, so it must be formatted first ('file://' prefix stripped)
            formatted_path = self.to_local_file(url_string)
            # QDir functions are used to best prevent against cross-platform edge cases
            dir = QDir(formatted_path)
            if (dir.exists()):
                if (dir.cdUp()):
                    qurl = QUrl.fromLocalFile(dir.absolutePath())
                    # QUrl Must be converted back to a String in order to return properly
                    return qurl.toString()
        else:
            return ""
