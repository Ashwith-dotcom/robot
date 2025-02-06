#!/bin/bash

# Start the animation handler in the background
python3 animation_handler.py &
ANIMATION_PID=$!

# Wait a moment for the animation handler to initialize
sleep 2

# Start the speech handler
python3 speech_handler.py

# When speech handler exits, kill the animation handler
kill $ANIMATION_PID