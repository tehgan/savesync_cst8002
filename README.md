# SaveSync (CST8002 prototype)
A project written for Algonquin College's "Programming Language Research Project" course (CST8002)

I was to write a program in a language that I hadn't used before, and have it completed by the end of the semester; 3 months. The language and topic were up to the student, so I selected Python as my language and a basic save file transfer tool as my topic.

<img width="1048" height="517" alt="A screenshot of SaveSync's UI" src="https://github.com/user-attachments/assets/14626038-c5a7-48cf-9997-a2b7e23e9bd5" />

The application takes two directories, parses them for valid .gci files (Nintendo GameCube saved games), and displays a list of saved game metadata.

gci parsing is a solved problem, but since this was an academic project I wanted to rely on external code as little as possible. This ended up costing me quite a bit of time, and as such I wasn't able to implement some final features, nor tidy up what's there.

### What's here:
* gci parser (hex/binary to usable variables; save name, description, timestamp, icon of varying size and address)
* Conversion of static CI8 icons (4-bit, paletted and tiled) into QImage objects (8-bit, upper-left to bottom-right continuous) with accurate value conversion
* Qt Quick GUI (Qt 6, PySide6)
* ListView with a custom QAbstractListModel implementation, allowing for display of gci metadata
* Basic QQuickImageProvider implementation for feeding internally generated QImages to QML
* Local directory path is persisted via QSettings

### What isn't:
* Timestamp-based synchronisation (and visual cues)
* Parsing and display of animated CI8 icons
* Parsing and display of static and animated RGB5A3 icons
* A proper build system
* Testing in environments other than Linux/SwayWM
* Cleanup (architecture, general correctness)
