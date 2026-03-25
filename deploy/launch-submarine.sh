#!/bin/bash
# Launch the HotBunk daemon in a tmux session
# Usage: bash deploy/launch-submarine.sh
# Or remotely: ssh gpu-rig 'bash -s' < deploy/launch-submarine.sh

SESSION="submarine"

# Kill existing session if running
tmux kill-session -t "$SESSION" 2>/dev/null

# Create new session with daemon
tmux new-session -d -s "$SESSION" \
    "source ~/.hotbunk/.venv/bin/activate && hotbunk daemon --log-level INFO 2>&1 | tee ~/.hotbunk/daemon.log"

# Split pane for monitor
tmux split-window -t "$SESSION" -v \
    "source ~/.hotbunk/.venv/bin/activate && hotbunk monitor"

echo "Submarine launched. Attach with: tmux attach -t $SESSION"
