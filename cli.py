import os
import sys
import click
import uvicorn
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Ensure UTF-8 output encoding across Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from yc_launch_monitor.config import settings
from yc_launch_monitor.database import db
from yc_launch_monitor.engine import monitor_engine
from yc_launch_monitor.slack.notifier import slack_notifier
from yc_launch_monitor.slack.block_kit import SlackBlockBuilder
from yc_launch_monitor.models import LaunchStatus, ProgramType, LaunchSource, LaunchItem, FounderInfo
from yc_launch_monitor.scheduler import scheduler

console = Console(force_terminal=True, legacy_windows=False)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

@click.group()
def cli():
    """🚀 YC & Speedrun Launch Monitor - Real-Time GTM Founder Radar & Slack Bot"""
    pass

@cli.command()
@click.option("--sources", "-s", help="Comma-separated list of sources (yc_directory,speedrun_directory,x_twitter,linkedin)")
@click.option("--dry-run", is_flag=True, help="Simulate scan without sending live Slack messages (renders terminal previews)")
@click.option("--no-slack", is_flag=True, help="Disable Slack alerting during scan")
def scan(sources, dry_run, no_slack):
    """Run an immediate incremental scan across all 4 monitoring sources."""
    src_list = [s.strip() for s in sources.split(",")] if sources else None
    send_slack = not no_slack

    console.print(Panel(Text("🚀 Executing YC & Speedrun Launch Scan", style="bold cyan"), subtitle="Rho GTM Pipeline Radar"))
    
    summary = monitor_engine.run_scan(
        specific_sources=src_list,
        send_slack=send_slack,
        dry_run=dry_run
    )

    table = Table(title="Scan Execution Summary", show_header=True, header_style="bold magenta")
    table.add_column("Source", style="cyan")
    table.add_column("Total Found", justify="right")
    table.add_column("New Items", justify="right", style="bold green")
    table.add_column("Duration (s)", justify="right")
    table.add_column("Status", style="bold")

    for src_key, res in summary.results_by_source.items():
        status_str = "[red]Error[/red]" if res.error else "[green]Success[/green]"
        table.add_row(
            src_key,
            str(res.total_found),
            str(res.new_items_count),
            f"{res.duration_seconds}s",
            status_str
        )

    console.print(table)
    console.print(f"\n[bold green]Total New Detections:[/bold green] {summary.total_new_items} "
                  f"([yellow]🔥 Early Signals: {summary.total_early_signals}[/yellow], "
                  f"[green]✅ Confirmed: {summary.total_confirmed}[/green])")
    console.print(f"[bold cyan]Slack Alerts Delivered:[/bold cyan] {summary.slack_delivered_count}\n")

@cli.command()
@click.option("--dry-run", is_flag=True, help="Render alert in terminal only")
def test_slack(dry_run):
    """Send test alert cards (Early Founder Signal & Confirmed Launch) to Slack."""
    console.print(Panel(Text("🔔 Sending Test Slack Alert Cards", style="bold yellow")))
    
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)

    # Test Item 1: Early Founder Signal
    early_test = LaunchItem(
        id="test_early_signal_01",
        company_name="Acme AI",
        slug="acme-ai",
        website="https://acme.ai",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.X_TWITTER,
        status=LaunchStatus.EARLY_SIGNAL,
        founders=[
            FounderInfo(
                name="Jane Doe",
                handle="@janedoe",
                profile_url="https://x.com/janedoe",
                title="Co-Founder & CEO"
            )
        ],
        description="Autonomous AI infrastructure optimization agents for hyperscale clusters.",
        post_text="We got into YC S26! Excited to move to SF and start building.",
        post_url="https://x.com/janedoe/status/2061493360150601738",
        detected_at=now
    )

    # Test Item 2: Confirmed YC Directory Launch
    confirmed_test = LaunchItem(
        id="test_confirmed_02",
        company_name="Example Labs",
        slug="example-labs",
        website="https://examplelabs.io",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.YC_DIRECTORY,
        status=LaunchStatus.CONFIRMED,
        description="AI agents for logistics companies and cross-border freight forwarding.",
        post_url="https://www.ycombinator.com/companies/example-labs",
        detected_at=now,
        confirmed_at=now
    )

    console.print("\n[bold yellow]1. Dispatching Early Founder Detection Alert...[/bold yellow]")
    s1, ts1 = slack_notifier.send_launch_alert(early_test, dry_run=dry_run)
    console.print(f"Result: {'[green]SUCCESS[/green]' if s1 else '[red]FAILED[/red]'} (ID: {ts1})")

    console.print("\n[bold green]2. Dispatching Confirmed Directory Launch Alert...[/bold green]")
    s2, ts2 = slack_notifier.send_launch_alert(confirmed_test, dry_run=dry_run)
    console.print(f"Result: {'[green]SUCCESS[/green]' if s2 else '[red]FAILED[/red]'} (ID: {ts2})\n")

@cli.command()
def stats():
    """Display persistent database metrics, early detection count, and last scan."""
    st = db.get_stats()
    table = Table(title="YC Launch Monitor - Persistent Database Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right", style="yellow")

    table.add_row("Total Tracked Companies", str(st.total_tracked_companies))
    table.add_row("🔥 Early Founder Signals", str(st.early_signal_count))
    table.add_row("✅ Confirmed Official Launches", str(st.confirmed_count))
    table.add_row("🚀 Speedrun Cohort Companies", str(st.speedrun_count))
    table.add_row("📙 Y Combinator Companies", str(st.yc_count))
    table.add_row("Last Scan Completed", str(st.last_scan_time or "Never"))
    table.add_row("Slack Status", "Configured" if slack_notifier.is_configured else "Dry Run Preview")

    console.print(table)

@cli.command()
@click.option("--limit", "-l", default=20, help="Number of items to show")
@click.option("--early-only", is_flag=True, help="Show only early founder signals")
@click.option("--query", "-q", help="Search keyword or batch")
def list_launches(limit, early_only, query):
    """List monitored launches from SQLite database."""
    status_filter = LaunchStatus.EARLY_SIGNAL if early_only else None
    items = db.list_launches(limit=limit, status=status_filter, query=query)

    if not items:
        console.print("[yellow]No launches found in database matching criteria.[/yellow]")
        return

    table = Table(title=f"Monitored Launches ({len(items)} items)", show_header=True, header_style="bold cyan")
    table.add_column("Company", style="bold white")
    table.add_column("Batch", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Source", style="cyan")
    table.add_column("Founder", style="yellow")
    table.add_column("Website / Link", style="blue")

    for itm in items:
        status_str = "[yellow]🔥 Early[/yellow]" if itm.status == LaunchStatus.EARLY_SIGNAL else "[green]✅ Confirmed[/green]"
        table.add_row(
            itm.company_name,
            itm.batch or "YC",
            status_str,
            itm.source.value,
            itm.display_founder,
            itm.primary_link
        )

    console.print(table)

@cli.command()
@click.option("--port", "-p", default=8000, help="Server port (default: 8000)")
@click.option("--host", "-h", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
@click.option("--with-scheduler", is_flag=True, default=True, help="Start background 8-hour continuous scheduler daemon")
def serve(port, host, with_scheduler):
    """Start Pond Protocol V1 API Server + Background 8-hour Scheduler."""
    console.print(Panel(
        Text(f"🤖 Starting Pond Protocol V1 Agent Server on http://{host}:{port}\n"
             f"Endpoints:\n"
             f"  - GET  /manifest   (Pond Protocol Discovery)\n"
             f"  - POST /runs       (Pond Run Execution)\n"
             f"  - GET  /health     (Infrastructure Health Check)\n\n"
             f"Cadence: Continuous 8-hour background scans ({'Enabled' if with_scheduler else 'Disabled'})",
             style="bold green"),
        title="Pond Agent Infrastructure"
    ))

    if with_scheduler:
        scheduler.start(run_immediately=False)

    uvicorn.run("yc_launch_monitor.pond.server:app", host=host, port=port, log_level="info")

if __name__ == "__main__":
    cli()
