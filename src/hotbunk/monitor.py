"""Live terminal dashboard for HotBunk pool monitoring."""

import time
from collections import deque
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .accounts import AccountManager
from .detector import SessionDetector
from .pool import AccountState, PoolManager


# Max events to keep in the scrollback log
MAX_EVENTS = 50

# Cost comparison: Claude Max subscription vs API pricing
# Max is ~$100/mo per account. API Opus is ~$15/M input + $75/M output tokens.
# Conservative estimate: 1M tokens/hr of automated work ~ $45/hr API cost.
API_COST_PER_HOUR = 45.0
MAX_COST_PER_ACCOUNT_PER_MONTH = 100.0


class EventLog:
    """Ring buffer of recent events with timestamps."""

    def __init__(self, maxlen: int = MAX_EVENTS):
        self._events: deque[tuple[datetime, str, str]] = deque(maxlen=maxlen)

    def add(self, message: str, style: str = "dim"):
        self._events.append((datetime.now(), message, style))

    def get_recent(self, n: int = 15) -> list[tuple[datetime, str, str]]:
        return list(self._events)[-n:]


class MonitorDashboard:
    """Builds and refreshes the live dashboard layout."""

    def __init__(self):
        self.account_manager = AccountManager()
        self.detector = SessionDetector()
        self.pool = PoolManager(self.account_manager, self.detector)
        self.events = EventLog()
        self._previous_states: dict[str, AccountState] = {}
        self._start_time = time.time()
        self._tick_count = 0

        self.events.add("Monitor started", "green")

    def build_layout(self) -> Layout:
        """Create the full dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="status", ratio=3),
            Layout(name="middle", ratio=2),
            Layout(name="events", ratio=2),
        )
        return layout

    def refresh(self, layout: Layout) -> None:
        """Update all panels with fresh data."""
        self._tick_count += 1

        # Fetch live data
        statuses = self.pool.get_pool_status()
        sessions = self.detector.get_active_sessions()

        # Detect state changes and log events
        self._detect_changes(statuses)

        # Build each panel
        layout["header"].update(self._build_header(statuses))
        layout["status"].update(self._build_pool_table(statuses))
        layout["middle"].update(self._build_jobs_and_savings(statuses, sessions))
        layout["events"].update(self._build_event_log())

    def _build_header(self, statuses: list) -> Panel:
        """Top bar with summary counts."""
        total = len(statuses)
        idle = sum(1 for s in statuses if s.state == AccountState.IDLE)
        sleeping = sum(1 for s in statuses if s.state == AccountState.SLEEPING)
        interactive = sum(1 for s in statuses if s.state == AccountState.INTERACTIVE)
        throttled = sum(1 for s in statuses if s.state == AccountState.THROTTLED)
        cooldown = sum(1 for s in statuses if s.state == AccountState.COOLDOWN)
        available = idle + sleeping

        uptime = time.time() - self._start_time
        uptime_str = _format_duration(uptime)

        summary = Text()
        summary.append(f"  {total} accounts", style="bold")
        summary.append("  |  ")
        summary.append(f"{available} available", style="bold green")
        summary.append("  |  ")
        if interactive:
            summary.append(f"{interactive} interactive", style="bold blue")
            summary.append("  |  ")
        if throttled:
            summary.append(f"{throttled} throttled", style="bold red")
            summary.append("  |  ")
        if cooldown:
            summary.append(f"{cooldown} cooldown", style="bold yellow")
            summary.append("  |  ")
        summary.append(f"uptime {uptime_str}", style="dim")

        return Panel(summary, title="[bold cyan]HotBunk Monitor[/bold cyan]", border_style="cyan")

    def _build_pool_table(self, statuses: list) -> Panel:
        """Pool status table showing all accounts."""
        table = Table(expand=True, show_edge=False, pad_edge=False)
        table.add_column("Account", style="cyan", ratio=2)
        table.add_column("Email", style="dim", ratio=3)
        table.add_column("State", justify="center", ratio=2)
        table.add_column("Tier", style="dim", justify="center", ratio=1)
        table.add_column("Sessions", justify="center", ratio=1)
        table.add_column("Auto Jobs", justify="center", ratio=1)
        table.add_column("Headroom", justify="center", ratio=2)

        state_styles = {
            AccountState.INTERACTIVE: "[bold blue]INTERACTIVE[/bold blue]",
            AccountState.IDLE: "[bold green]IDLE[/bold green]",
            AccountState.SLEEPING: "[bold magenta]SLEEPING[/bold magenta]",
            AccountState.THROTTLED: "[bold red]THROTTLED[/bold red]",
            AccountState.COOLDOWN: "[bold yellow]COOLDOWN[/bold yellow]",
        }

        if not statuses:
            table.add_row(
                "[dim]No accounts registered[/dim]",
                "", "", "", "", "", "",
            )
        else:
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

        return Panel(table, title="[bold]Pool Status[/bold]", border_style="green")

    def _build_jobs_and_savings(self, statuses: list, sessions: list) -> Panel:
        """Middle panel: active jobs + estimated savings."""
        layout = Layout()
        layout.split_row(
            Layout(name="jobs", ratio=3),
            Layout(name="savings", ratio=2),
        )

        # Active jobs / sessions table
        jobs_table = Table(expand=True, show_edge=False, pad_edge=False)
        jobs_table.add_column("PID", style="dim", justify="right")
        jobs_table.add_column("Account", style="cyan")
        jobs_table.add_column("Directory", style="dim")
        jobs_table.add_column("Running", justify="center")

        if sessions:
            for sess in sessions:
                duration = _format_duration(time.time() - sess.started_at)
                acct = sess.account or "unknown"
                # Truncate cwd to last 2 path components
                cwd_parts = sess.cwd.split("/")
                short_cwd = "/".join(cwd_parts[-2:]) if len(cwd_parts) > 2 else sess.cwd
                jobs_table.add_row(
                    str(sess.pid),
                    acct,
                    short_cwd,
                    duration,
                )
        else:
            jobs_table.add_row("[dim]No active sessions[/dim]", "", "", "")

        layout["jobs"].update(
            Panel(jobs_table, title="[bold]Active Sessions[/bold]", border_style="blue")
        )

        # Savings estimate
        layout["savings"].update(self._build_savings_panel(statuses))

        return Panel(layout, title="", border_style="dim", padding=0)

    def _build_savings_panel(self, statuses: list) -> Panel:
        """Estimated savings vs API costs."""
        total_accounts = len(statuses)
        automated_jobs = sum(s.automated_jobs for s in statuses)
        uptime_hours = (time.time() - self._start_time) / 3600

        # What this would cost on API if each automated job burns ~$45/hr
        api_cost_estimate = automated_jobs * API_COST_PER_HOUR * uptime_hours
        max_subscription_cost = total_accounts * MAX_COST_PER_ACCOUNT_PER_MONTH

        savings = Text()
        savings.append("Subscription cost\n", style="dim")
        savings.append(f"  ${max_subscription_cost:.0f}/mo", style="bold")
        savings.append(f" ({total_accounts} x ${MAX_COST_PER_ACCOUNT_PER_MONTH:.0f})\n")
        savings.append("\n")
        savings.append("Equivalent API cost\n", style="dim")
        if api_cost_estimate > 0:
            savings.append(f"  ~${api_cost_estimate:,.0f}", style="bold green")
            savings.append(" this session\n")
        else:
            savings.append("  $0 ", style="bold")
            savings.append("(no automated jobs yet)\n")
        savings.append("\n")

        if total_accounts > 0:
            # The real value: you get unlimited usage for a flat fee
            savings.append("Value proposition\n", style="dim")
            savings.append(f"  {total_accounts} accounts pooled\n", style="bold cyan")
            savings.append("  Flat rate, unlimited compute\n", style="green")
            savings.append("  vs $15/$75 per M tokens (API)\n", style="dim")

        return Panel(savings, title="[bold]Savings vs API[/bold]", border_style="yellow")

    def _build_event_log(self) -> Panel:
        """Recent events panel."""
        events = self.events.get_recent(12)
        text = Text()

        if not events:
            text.append("  Waiting for events...", style="dim")
        else:
            for ts, message, style in events:
                timestamp = ts.strftime("%H:%M:%S")
                text.append(f"  {timestamp}  ", style="dim")
                text.append(f"{message}\n", style=style)

        return Panel(text, title="[bold]Event Log[/bold]", border_style="magenta")

    def _detect_changes(self, statuses: list) -> None:
        """Compare current states to previous and log transitions."""
        for s in statuses:
            name = s.account.name
            prev = self._previous_states.get(name)
            curr = s.state

            if prev is not None and prev != curr:
                transition = f"{name}: {prev.value} -> {curr.value}"
                style = _state_event_style(curr)
                self.events.add(transition, style)

            self._previous_states[name] = curr


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


def _format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def _state_event_style(state: AccountState) -> str:
    """Pick a Rich style for a state-change event."""
    return {
        AccountState.INTERACTIVE: "blue",
        AccountState.IDLE: "green",
        AccountState.SLEEPING: "magenta",
        AccountState.THROTTLED: "bold red",
        AccountState.COOLDOWN: "yellow",
    }.get(state, "dim")


def run_monitor(refresh_rate: float = 2.0) -> None:
    """Main entry point: launch the live dashboard."""
    console = Console()
    dashboard = MonitorDashboard()
    layout = dashboard.build_layout()

    # Initial render
    dashboard.refresh(layout)

    try:
        with Live(
            layout,
            console=console,
            refresh_per_second=1 / refresh_rate if refresh_rate >= 1 else 4,
            screen=True,
        ) as live:
            while True:
                dashboard.refresh(layout)
                live.update(layout)
                time.sleep(refresh_rate)
    except KeyboardInterrupt:
        console.print("\n[dim]Monitor stopped.[/dim]")
