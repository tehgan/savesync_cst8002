import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    minimumWidth: 640
    minimumHeight: 480
    visible: true
    title: qsTr("SaveSync (CST8002)")

    // Unfinished and unused
    function compare_timestamps() {
        const TIME_SAME = 0
        const TIME_OLDER = 1
        const TIME_NEWER = 2
        const NOT_YET_TRANSFERRED = 3

        const listA = SaveFileModelA.get_last_modified()
        const listB = SaveFileModelB.get_last_modified()

        const lbUnique = {};


        // TODO:
        //  Get unique elements from either list, separate and turn 'NOT_YET_TRANSFERRED' (green?)
        //  Get matching elements from either list
        //  If X's key[value] > Y's key[value], set X to 'TIME_NEWER' (yellow?) and Y to 'TIME_OLDER' (red?)

        // [UNFINISHED]
        /*
        for (const [key, value] of Object.entries(listA)) {
            console.log(`${key}: ${value}`);
            if (listB.hasOwnProperty(key)) {
                if (listA[key] > listB[key]) {

                } else if (listA[key] < listB[key]) {

                }
            }
        }
        */
    }

    // Application menu bar (usually shows 'File', 'Edit', 'Help', et cetera)
    menuBar: MenuBar {
        Menu {
            title: qsTr("&Edit")
            Action {
                // TODO: If Preferences expands, I may need to reword this in the future
                text: qsTr("&Configure save directories")
                onTriggered: {
                    preferences.show()
                }
            }
        }
    }

    // Import the preferences window. Rest of code is declared in Preferences.qml
    // TODO: Double-check that this is indeed the proper way to pop a new window (e.g. does it always allocate resources like this?)
    Preferences {
        id: preferences
        visible: false
    }

    GridLayout {
        anchors.margins: 4
        anchors.fill: parent
        columns: 3
        rows: 2

        Component {
            id: saveGameDelegate
            Item {
                id: saveGameItem

                property color backgroundColour: "whitesmoke"
                required property url fileUrl
                // Qt expects model->view properties to be 'required', see below
                /* https://doc.qt.io/qt-6/qtquick-modelviewsdata-modelview.html#models
                    https://doc.qt.io/qt-6/qml-codingconventions.html#required-properties */
                required property url iconUrl
                required property string title
                required property string description
                required property string lastModified

                // TODO: Check height vs. implicitHeight
                height: 64
                // Ensures the item (and therefore its coloured highlight) matches the width of its parent pane
                width: ListView.view.width

                Rectangle {
                    anchors.fill: parent
                    color: backgroundColour

                    GridLayout {
                        columns: 2
                        rows: 3

                        // Icon (32x32, may be animated)
                        Image {
                            Layout.column: 0
                            Layout.rowSpan: 3

                            width: 32
                            height: 32
                            smooth: false
                            mipmap: false

                        /*
                            TODO: Does this need optimization?
                            I believe I read that Qt re-creates delegates while scrolling,
                            which'd mean this is continuously called in runtime, but I'm having trouble finding that again in the docs.
                        */
                        // Check if icon url was provided and is not empty. If it seems valid, load from it, or if not, load the placeholder image.
                            source: (iconUrl && iconUrl.toString().length > 0) ? iconUrl : "../../res/placeholder_32.png"
                        }

                        Text {
                            text: title
                        }

                        Text {
                            text: description
                        }

                        Text {
                            text: lastModified
                            font.italic: true
                            color: "grey"
                        }
                    }
                }
            }
        }

        Pane {
            /* TODO: Minimum width feels hacky; it was implemented to work around initial pane being too thin.
             *  Panes were 50/50 when using a ColumnLayout, but with a ListView they bug out. Not sure why. */
            // minimumWidth == 640/2 - 4 (left padding) - 2 (half of right padding)
            Layout.minimumWidth: 314
            Layout.fillWidth: true
            Layout.fillHeight: true

            // TODO: Temporary. Differentiates pane from rest of window.
            background: Rectangle {}

            // TODO: Lists should be scrollable both vertically and horizontally, if needed.
            // TODO: Current behaviour has flickability (pulling), feels like a mobile interface. Don't want that.
            ListView {
                id: listViewA
                anchors.fill: parent
                model: SaveFileModelA
                delegate: saveGameDelegate

                // Clips (cuts off) text if its length exceeds the parent width
                clip: true

                //onCountChanged: compare_timestamps()
            }
        }

        // See previous Pane for 'todo' notes; most code is duplicated
        Pane {
            // minimumWidth == 640/2 - 4 (right padding) - 2 (half of left padding)
            Layout.minimumWidth: 314
            Layout.fillWidth: true
            Layout.fillHeight: true

            background: Rectangle {}

            ListView {
                id: listViewB
                anchors.fill: parent
                model: SaveFileModelB
                delegate: saveGameDelegate
                clip: true

                //onCountChanged: compare_timestamps()
            }
        }

        Button {
            Layout.row: 1;
            Layout.column: 1;
            Layout.alignment: Qt.AlignRight
            text: "Synchronise"
        }
    }

}
