#!/bin/bash
# Updates TaktTimer to most recent version from github

test -e ~/timer_update.sh && echo "timer_update.sh exists already" || cp ~/TaktTimer/timer_update.sh ~/timer_update.sh
test -e ~/Desktop/Update.desktop && echo "Update.desktop exists already" || cp ~/TaktTimer/Update.desktop ~/Desktop/Update.desktop
test -e ~/Desktop/Timer.desktop && echo "Timer.desktop exists already" || cp ~/TaktTimer/Timer.desktop ~/Desktop/Timer.desktop
chmod -x ~/timer_update.sh