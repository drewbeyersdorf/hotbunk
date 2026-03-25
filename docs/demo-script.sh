#!/usr/bin/env bash
# Demo script for hotbunk - runs commands with small delays for clean recording
set -e

source /home/drew/projects/hotbunk/.venv/bin/activate

type_and_run() {
    local cmd="$1"
    # Print prompt + command
    printf '\033[1;32m$\033[0m %s\n' "$cmd"
    sleep 0.3
    eval "$cmd"
    echo
    sleep 0.8
}

echo
printf '\033[1;36m  hotbunk — cooperative compute orchestrator for Claude Code\033[0m\n'
echo
sleep 1

type_and_run "hotbunk accounts"
type_and_run "hotbunk status"
type_and_run "hotbunk which"
type_and_run "hotbunk switch drew-personal"
type_and_run "hotbunk which"
type_and_run "hotbunk switch drew-work"
type_and_run "hotbunk submit militia -c \"claude -p 'run nightly audit'\" --dry-run"
type_and_run "hotbunk policy -a drew-work"

printf '\033[1;36m  Done. Two accounts, one machine, zero wasted capacity.\033[0m\n'
echo
sleep 1
