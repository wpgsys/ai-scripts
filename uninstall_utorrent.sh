#!/bin/bash
#uTorrent Uninstaller For MacOS
#To Run Enter The Commands Below
#chmod +x uninstall_utorrent.sh
#./uninstall_utorrent.sh

# Quit uTorrent if it's running
echo "Quitting uTorrent..."
osascript -e 'quit app "uTorrent"'

# Wait a few seconds to ensure the app quits
sleep 3

# Remove the uTorrent application
echo "Removing uTorrent application..."
rm -rf /Applications/uTorrent.app

# Remove uTorrent-related files in the Library folders
echo "Removing uTorrent support files..."
rm -rf ~/Library/Application\ Support/uTorrent
rm -rf ~/Library/Preferences/com.utorrent.uTorrent.plist
rm -rf ~/Library/Caches/com.utorrent.uTorrent

# Empty the Trash (Optional)
echo "Emptying the Trash..."
osascript -e 'tell application "Finder" to empty the trash'

# Done
echo "uTorrent has been successfully uninstalled."

