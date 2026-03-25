#!/bin/bash
# HotBunk demo recording script
# Record with: asciinema rec demo.cast -c "bash drafts/demo-script.sh"
# Convert to GIF: agg demo.cast demo.gif --theme monokai

# Simulate typing with delay
type_cmd() {
    echo ""
    echo -n "$ "
    echo "$1" | pv -qL 30
    sleep 0.5
    eval "$1"
    sleep 1.5
}

cd ~/projects/hotbunk
source .venv/bin/activate

clear
echo "# HotBunk - Cooperative Compute Orchestrator for Claude Code"
echo ""
sleep 2

type_cmd "hotbunk accounts"
type_cmd "hotbunk status"
type_cmd "hotbunk which"
type_cmd "hotbunk switch drew-personal"
type_cmd "hotbunk which"
type_cmd "hotbunk switch drew-work"
type_cmd "hotbunk submit militia -c 'echo running agent task' --dry-run"
type_cmd "hotbunk policy -a drew-work"

echo ""
echo "# Pool is live. Two Max accounts, four machines, zero wasted capacity."
sleep 3
