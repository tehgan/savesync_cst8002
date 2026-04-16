import QtCore

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: root

    minimumWidth: 320
    minimumHeight: 240

    title: qsTr("Preferences")

    GridLayout {
        anchors.margins: 4
        anchors.fill: parent
        rows: 3
        columns: 2

        Text {
            id: label
            Layout.row: 0
            Layout.columnSpan: 2
            text: qsTr("Local save file directory:")
            Layout.preferredHeight: label.contentHeight
        }

        TextField {
            id: pathField
            Layout.row: 1
            Layout.fillWidth: true
            // Strips 'file:///' prefix from URL
            // TODO: Error on quit, seems it's called after UrlHelper is destroyed, but this doesn't affect application function. Just clogs up the terminal.
            text: UrlHelper.to_local_file(settings.localDirectory)
            placeholderText: qsTr("Path to directory")
        }

        Button {
            text: qsTr("Select Folder")
            onClicked: folderDialog.open()
        }

        // Spacer; ensures other rows fit their content (in terms of height) without unnecessary padding
        Item {
            Layout.fillHeight: true
        }
    }

    // TODO: Folder view is very basic, might be a quirk w/ my setup. Test on Windows to see if it has a sidebar as it should.
    FolderDialog {
        id: folderDialog

        /* TODO: I need to check out how to properly check if settings have been loaded...
         *  Both ternary length-check conditionals (get_parent_dir() first and localDirectory first) return 0, meaning get_parent_dir is never run properly, but this works???
         *  But of course it won't work properly if the user has never set their local save directory, so it must be fixed for correctness. */
        currentFolder: UrlHelper.get_parent_dir(settings.localDirectory)

        selectedFolder: settings.localDirectory
        onAccepted: settings.localDirectory = selectedFolder
    }

    // QSettings offers a cross-platform interface for storing and retrieving key/value pairs, persisting them on the user's hard drive according to their OS specification
    Settings {
        id: settings
        property url localDirectory
        onLocalDirectoryChanged: SaveFileModel.repopulate(localDirectory)
    }

}
