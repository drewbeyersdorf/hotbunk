"""HotBunk CLI -- cooperative compute orchestrator for Claude Code."""

import json
import os
import subprocess
import sys
import time
import uuid

import click
from rich.console import Console
from rich.table import Table

from .accounts import AccountManager, ACCOUNTS_DIR
from .detector import SessionDetector
from .pool import PoolManager, AccountState

console = Console()


def get_pool() -> PoolManager:
    am = AccountManager()
    sd = SessionDetector()
    return PoolManager(am, sd)


@click.group()
@click.version_option(version="0.1.0")
def main():
    """HotBunk -- cooperative compute orchestrator for Claude Code."""
    pass


@main.command()
def status():
    """Show all accounts and their current state."""
    pool = get_pool()
    statuses = pool.get_pool_status()

    if not statuses:
        console.print("[yellow]No accounts registered. Run 'hotbunk register' first.[/yellow]")
        return

    table = Table(title="HotBunk Pool Status")
    table.add_column("Account", style="cyan")
    table.add_column("Email", style="dim")
    table.add_column("State", justify="center")
    table.add_column("Tier", style="dim")
    table.add_column("Sessions", justify="center")
    table.add_column("Auto Jobs", justify="center")
    table.add_column("Headroom", justify="center")

    state_styles = {
        AccountState.INTERACTIVE: "[bold blue]INTERACTIVE[/bold blue]",
        AccountState.IDLE: "[green]IDLE[/green]",
        AccountState.SLEEPING: "[magenta]SLEEPING[/magenta]",
        AccountState.THROTTLED: "[bold red]THROTTLED[/bold red]",
        AccountState.COOLDOWN: "[yellow]COOLDOWN[/yellow]",
    }

    for s in statuses:
        headroom_bar = _headroom_bar(s.headroom_estimate)
        table.add_row(
            s.account.name,
            s.account.email,
            state_styles.get(s.state, str(s.state)),
            s.account.rate_limit_tier,
            str(s.active_sessions),
            str(s.automated_jobs),
            headroom_bar,
        )

    console.print(table)


@main.command()
@click.argument("name")
@click.option("--email", prompt="Account email", help="Email for this Claude account")
def register(name: str, email: str):
    """Register the currently logged-in Claude account.

    Saves the current ~/.claude/.credentials.json under NAME.
    Log in to each account first with 'claude auth login --email EMAIL',
    then run 'hotbunk register NAME --email EMAIL' to save it.
    """
    am = AccountManager()

    existing = am.get_account(name)
    if existing:
        if not click.confirm(f"Account '{name}' already exists. Overwrite?"):
            return

    try:
        info = am.register_current(name, email)
        console.print(f"[green]Registered account '{name}'[/green]")
        console.print(f"  Email: {email}")
        console.print(f"  Type: {info.subscription_type}")
        console.print(f"  Tier: {info.rate_limit_tier}")
        console.print()
        console.print("[dim]Policy saved with defaults. Edit with 'hotbunk policy --edit'.[/dim]")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("name")
def switch(name: str):
    """Switch to a different account for interactive use."""
    am = AccountManager()
    account = am.get_account(name)

    if not account:
        console.print(f"[red]Account '{name}' not found.[/red]")
        console.print("Available accounts:")
        for a in am.list_accounts():
            console.print(f"  - {a.name} ({a.email})")
        sys.exit(1)

    current = am._identify_current_account()
    if current == name:
        console.print(f"[yellow]Already on account '{name}'.[/yellow]")
        return

    if am.activate(name):
        console.print(f"[green]Switched to '{name}' ({account.email})[/green]")
        if current:
            console.print(f"[dim]Previous account '{current}' credentials saved.[/dim]")
        console.print("[dim]New Claude Code sessions will use this account.[/dim]")
    else:
        console.print(f"[red]Failed to switch to '{name}'.[/red]")
        sys.exit(1)


@main.command()
def which():
    """Show which account is currently active."""
    am = AccountManager()
    current = am._identify_current_account()

    if current:
        account = am.get_account(current)
        console.print(f"[cyan]{current}[/cyan] ({account.email if account else 'unknown'})")
    else:
        console.print("[yellow]Current account not recognized by hotbunk.[/yellow]")
        console.print("Register it with 'hotbunk register <name> --email <email>'")


@main.command()
@click.argument("job_type", type=click.Choice(["militia", "training", "ci", "general"]))
@click.option("--command", "-c", required=True, help="Command to run")
@click.option("--dry-run", is_flag=True, help="Show what would happen without running")
def submit(job_type: str, command: str, dry_run: bool):
    """Submit an automated job to the pool.

    The pool picks the best available account and runs the command
    with CLAUDE_CONFIG_DIR set to that account's credentials.
    """
    pool = get_pool()
    account_name = pool.pick_account(job_type)

    if not account_name:
        console.print("[red]No accounts available for this job type.[/red]")
        console.print()
        console.print("Possible reasons:")
        console.print("  - All accounts are in INTERACTIVE or THROTTLED state")
        console.print("  - No account policies allow this job type")
        console.print("  - All accounts at max concurrent automated jobs")
        console.print()
        console.print("Run 'hotbunk status' to see pool state.")
        sys.exit(1)

    am = AccountManager()
    creds_dir = am.get_credentials_dir(account_name)

    if dry_run:
        console.print(f"[yellow]DRY RUN[/yellow]")
        console.print(f"Would assign to: [cyan]{account_name}[/cyan]")
        console.print(f"CLAUDE_CONFIG_DIR: {creds_dir}")
        console.print(f"Command: {command}")
        return

    console.print(f"Submitting [bold]{job_type}[/bold] job to [cyan]{account_name}[/cyan]")

    # Launch the command with the correct credentials
    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = str(creds_dir)
    env["HOTBUNK_ACCOUNT"] = account_name
    env["HOTBUNK_JOB_TYPE"] = job_type

    pool.record_job_start(account_name)

    try:
        result = subprocess.run(
            command,
            shell=True,
            env=env,
        )
        if result.returncode == 0:
            console.print(f"[green]Job completed successfully on {account_name}[/green]")
        else:
            console.print(f"[red]Job failed with exit code {result.returncode}[/red]")
    except KeyboardInterrupt:
        console.print("[yellow]Job interrupted[/yellow]")
    finally:
        pool.record_job_end(account_name)


@main.command()
@click.option("--edit", is_flag=True, help="Open policy in editor")
@click.option("--account", "-a", help="Account name (default: current)")
def policy(edit: bool, account: str):
    """View or edit an account's automation policy."""
    am = AccountManager()

    if not account:
        account = am._identify_current_account()
        if not account:
            console.print("[red]Can't determine current account. Use --account NAME.[/red]")
            sys.exit(1)

    info = am.get_account(account)
    if not info:
        console.print(f"[red]Account '{account}' not found.[/red]")
        sys.exit(1)

    policy_path = ACCOUNTS_DIR / account / "policy.yaml"

    if edit:
        editor = os.environ.get("EDITOR", "nvim")
        subprocess.run([editor, str(policy_path)])
        console.print(f"[green]Policy updated for '{account}'.[/green]")
    else:
        if info.policy:
            console.print(f"[cyan]Policy for '{account}':[/cyan]")
            console.print(info.policy.to_yaml())
        else:
            console.print(f"[yellow]No policy found for '{account}'.[/yellow]")


def _headroom_bar(value: float) -> str:
    """Render a headroom bar like [||||      ] 40%."""
    filled = int(value * 10)
    bar = "|" * filled + " " * (10 - filled)
    pct = int(value * 100)

    if value >= 0.7:
        color = "green"
    elif value >= 0.3:
        color = "yellow"
    else:
        color = "red"

    return f"[{color}][{bar}] {pct}%[/{color}]"


@main.command()
@click.option("--refresh", "-r", default=2.0, type=float, help="Refresh interval in seconds")
def monitor(refresh: float):
    """Live terminal dashboard showing pool status, jobs, and events."""
    from .monitor import run_monitor

    run_monitor(refresh_rate=refresh)


@main.command(name="accounts")
def list_accounts():
    """List all registered accounts."""
    am = AccountManager()
    accounts = am.list_accounts()

    if not accounts:
        console.print("[yellow]No accounts registered.[/yellow]")
        console.print()
        console.print("To register your first account:")
        console.print("  1. claude auth login --email you@example.com")
        console.print("  2. hotbunk register my-account --email you@example.com")
        return

    current = am._identify_current_account()

    for a in accounts:
        marker = " [green]*[/green]" if a.name == current else ""
        console.print(f"  [cyan]{a.name}[/cyan]{marker} - {a.email} ({a.subscription_type}, {a.rate_limit_tier})")

    if current:
        console.print(f"\n[dim]* = currently active[/dim]")
