"""CLI commands for nanobot."""

import asyncio
import os
import signal
from pathlib import Path
import select
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout

from nanobot import __version__, __logo__

app = typer.Typer(
    name="nanobot",
    help=f"{__logo__} nanobot - Personal AI Assistant",
    no_args_is_help=True,
)

console = Console()
EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q"}

# ---------------------------------------------------------------------------
# CLI input: prompt_toolkit for editing, paste, history, and display
# ---------------------------------------------------------------------------

_PROMPT_SESSION: PromptSession | None = None
_SAVED_TERM_ATTRS = None  # original termios settings, restored on exit


def _flush_pending_tty_input() -> None:
    """Drop unread keypresses typed while the model was generating output."""
    try:
        fd = sys.stdin.fileno()
        if not os.isatty(fd):
            return
    except Exception:
        return

    try:
        import termios
        termios.tcflush(fd, termios.TCIFLUSH)
        return
    except Exception:
        pass

    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0)
            if not ready:
                break
            if not os.read(fd, 4096):
                break
    except Exception:
        return


def _restore_terminal() -> None:
    """Restore terminal to its original state (echo, line buffering, etc.)."""
    if _SAVED_TERM_ATTRS is None:
        return
    try:
        import termios
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _SAVED_TERM_ATTRS)
    except Exception:
        pass


def _init_prompt_session() -> None:
    """Create the prompt_toolkit session with persistent file history."""
    global _PROMPT_SESSION, _SAVED_TERM_ATTRS

    # Save terminal state so we can restore it on exit
    try:
        import termios
        _SAVED_TERM_ATTRS = termios.tcgetattr(sys.stdin.fileno())
    except Exception:
        pass

    history_file = Path.home() / ".nanobot" / "history" / "cli_history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    _PROMPT_SESSION = PromptSession(
        history=FileHistory(str(history_file)),
        enable_open_in_editor=False,
        multiline=False,   # Enter submits (single line mode)
    )


def _print_agent_response(response: str, render_markdown: bool) -> None:
    """Render assistant response with consistent terminal styling."""
    content = response or ""
    body = Markdown(content) if render_markdown else Text(content)
    console.print()
    console.print(f"[cyan]{__logo__} nanobot[/cyan]")
    console.print(body)
    console.print()


def _is_exit_command(command: str) -> bool:
    """Return True when input should end interactive chat."""
    return command.lower() in EXIT_COMMANDS


async def _read_interactive_input_async() -> str:
    """Read user input using prompt_toolkit (handles paste, history, display).

    prompt_toolkit natively handles:
    - Multiline paste (bracketed paste mode)
    - History navigation (up/down arrows)
    - Clean display (no ghost characters or artifacts)
    """
    if _PROMPT_SESSION is None:
        raise RuntimeError("Call _init_prompt_session() first")
    try:
        with patch_stdout():
            return await _PROMPT_SESSION.prompt_async(
                HTML("<b fg='ansiblue'>You:</b> "),
            )
    except EOFError as exc:
        raise KeyboardInterrupt from exc



def version_callback(value: bool):
    if value:
        console.print(f"{__logo__} nanobot v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
):
    """nanobot - Personal AI Assistant."""
    pass


# ============================================================================
# Onboard / Setup
# ============================================================================


@app.command()
def onboard():
    """Initialize nanobot configuration and workspace."""
    from nanobot.config.loader import get_config_path, save_config
    from nanobot.config.schema import Config
    from nanobot.utils.helpers import get_workspace_path
    
    config_path = get_config_path()
    
    if config_path.exists():
        console.print(f"[yellow]Config already exists at {config_path}[/yellow]")
        if not typer.confirm("Overwrite?"):
            raise typer.Exit()
    
    # Create default config
    config = Config()
    save_config(config)
    console.print(f"[green]✓[/green] Created config at {config_path}")
    
    # Create workspace
    workspace = get_workspace_path()
    console.print(f"[green]✓[/green] Created workspace at {workspace}")
    
    # Create default bootstrap files
    _create_workspace_templates(workspace)
    
    console.print(f"\n{__logo__} nanobot is ready!")
    console.print("\nNext steps:")
    console.print("  1. Add your API key to [cyan]~/.nanobot/config.json[/cyan]")
    console.print("     Get one at: https://openrouter.ai/keys")
    console.print("  2. Chat: [cyan]nanobot agent -m \"Hello!\"[/cyan]")
    console.print("\n[dim]Want Telegram/WhatsApp? See: https://github.com/HKUDS/nanobot#-chat-apps[/dim]")




def _create_workspace_templates(workspace: Path):
    """Create default workspace template files."""
    templates = {
        "AGENTS.md": """# Agent Instructions

You are a helpful AI assistant. Be concise, accurate, and friendly.

## Guidelines

- Always explain what you're doing before taking actions
- Ask for clarification when the request is ambiguous
- Use tools to help accomplish tasks
- Remember important information in your memory files
""",
        "SOUL.md": """# Soul

I am nanobot, a lightweight AI assistant.

## Personality

- Helpful and friendly
- Concise and to the point
- Curious and eager to learn

## Values

- Accuracy over speed
- User privacy and safety
- Transparency in actions
""",
        "USER.md": """# User

Information about the user goes here.

## Preferences

- Communication style: (casual/formal)
- Timezone: (your timezone)
- Language: (your preferred language)
""",
    }
    
    for filename, content in templates.items():
        file_path = workspace / filename
        if not file_path.exists():
            file_path.write_text(content)
            console.print(f"  [dim]Created {filename}[/dim]")
    
    # Create memory directory and MEMORY.md
    memory_dir = workspace / "memory"
    memory_dir.mkdir(exist_ok=True)
    memory_file = memory_dir / "MEMORY.md"
    if not memory_file.exists():
        memory_file.write_text("""# Long-term Memory

This file stores important information that should persist across sessions.

## User Information

(Important facts about the user)

## Preferences

(User preferences learned over time)

## Important Notes

(Things to remember)
""")
        console.print("  [dim]Created memory/MEMORY.md[/dim]")

    # Create skills directory for custom user skills
    skills_dir = workspace / "skills"
    skills_dir.mkdir(exist_ok=True)


def _make_provider(config):
    """Create LiteLLMProvider from config. Exits if no API key found."""
    from nanobot.providers.litellm_provider import LiteLLMProvider
    model = config.agents.defaults.model
    p = config.get_provider(model or None)
    if not (p and p.api_key) and not model.startswith("bedrock/"):
        console.print("[red]Error: No API key configured.[/red]")
        console.print("Set one in ~/.nanobot/config.json under providers section")
        raise typer.Exit(1)
    return LiteLLMProvider(
        api_key=p.api_key if p else None,
        api_base=config.get_api_base(model or None),
        default_model=model or "auto",
        extra_headers=p.extra_headers if p else None,
        provider_name=config.get_provider_name(model or None),
    )


# ============================================================================
# Heartbeat callback helper (shared by gateway + CLI trigger)
# ============================================================================


def _strip_think_tags(text: str) -> str:
    """Strip <think>...</think> blocks from model output."""
    import re
    return re.sub(r"<think>[\s\S]*?</think>\s*", "", text).strip()


def _make_heartbeat_callback(config, agent, task_store, session_manager, event_bus):
    """Build the task-wrapped heartbeat callback. Shared by gateway() and heartbeat trigger."""
    async def on_heartbeat(prompt: str) -> str:
        from nanobot.bus.event_bus import AgentEvent
        hb = config.heartbeat
        channel = hb.channel or "cli"
        chat_id = hb.chat_id or "direct"
        # Each heartbeat run gets its own session for isolated context
        task = task_store.add("heartbeat", "Heartbeat check", "")
        session_key = f"heartbeat:{task.id}"
        task.session_key = session_key
        task_store._save()
        await event_bus.publish(AgentEvent("task", "started", {
            "task_id": task.id, "type": "heartbeat", "label": task.label,
        }))

        # Inject system message into chat session
        chat_session = session_manager.get_or_create("api:default")
        chat_session.add_message("assistant", "[System] Heartbeat task started")
        session_manager.save(chat_session)
        await event_bus.publish(AgentEvent("system_message", "injected", {
            "task_id": task.id, "content": "[System] Heartbeat task started",
        }))

        try:
            response = await agent.process_direct(
                prompt,
                session_key=session_key,
                channel=channel,
                chat_id=chat_id,
                metadata={"task_id": task.id},
            )
            summary = _strip_think_tags(response or "")[:120]
            task_store.update(task.id, status="completed", summary=summary)
            await event_bus.publish(AgentEvent("task", "completed", {
                "task_id": task.id, "summary": summary,
            }))
            chat_session = session_manager.get_or_create("api:default")
            chat_session.add_message("assistant", f"[System] Heartbeat completed: {summary}")
            session_manager.save(chat_session)
            await event_bus.publish(AgentEvent("system_message", "injected", {
                "task_id": task.id, "content": f"[System] Heartbeat completed: {summary}",
            }))
            return response
        except Exception as e:
            task_store.update(task.id, status="failed", error=str(e))
            await event_bus.publish(AgentEvent("task", "failed", {
                "task_id": task.id, "error": str(e),
            }))
            chat_session = session_manager.get_or_create("api:default")
            chat_session.add_message("assistant", f"[System] Heartbeat failed: {e}")
            session_manager.save(chat_session)
            await event_bus.publish(AgentEvent("system_message", "injected", {
                "task_id": task.id, "content": f"[System] Heartbeat failed: {e}",
            }))
            return ""
    return on_heartbeat


# ============================================================================
# Gateway / Server
# ============================================================================


@app.command()
def gateway(
    port: int = typer.Option(18790, "--port", "-p", help="Gateway port"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Start the nanobot gateway."""
    from nanobot.config.loader import load_config, get_data_dir
    from nanobot.bus.queue import MessageBus
    from nanobot.bus.event_bus import EventBus
    from nanobot.agent.loop import AgentLoop
    from nanobot.channels.manager import ChannelManager
    from nanobot.session.manager import SessionManager
    from nanobot.cron.service import CronService
    from nanobot.cron.types import CronJob
    from nanobot.heartbeat.service import HeartbeatService
    from nanobot.task.store import TaskStore

    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    console.print(f"{__logo__} Starting nanobot gateway on port {port}...")
    
    config = load_config()
    bus = MessageBus()
    event_bus = EventBus()
    provider = _make_provider(config)
    session_manager = SessionManager(config.workspace_path)
    
    # Create task store for tracking autonomous work
    task_store = TaskStore(get_data_dir() / "tasks.json")

    # Create cron service first (callback set after agent creation)
    cron_store_path = get_data_dir() / "cron" / "jobs.json"
    cron = CronService(cron_store_path, event_bus=event_bus)
    
    # Create agent with cron service
    agent = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model or None,
        max_iterations=config.agents.defaults.max_tool_iterations,
        brave_api_key=config.tools.web.search.api_key or None,
        exec_config=config.tools.exec,
        cron_service=cron,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        session_manager=session_manager,
        event_bus=event_bus,
        max_tokens=config.agents.defaults.max_tokens,
        temperature=config.agents.defaults.temperature,
        context_window=config.agents.defaults.context_window,
    )
    
    # Set cron callback (needs agent)
    async def on_cron_job(job: CronJob) -> str | None:
        """Execute a cron job through the agent, wrapped in a task."""
        from nanobot.bus.event_bus import AgentEvent
        channel = job.payload.channel or "cli"
        chat_id = job.payload.to or "direct"

        # Each cron run gets its own session for isolated context
        task = task_store.add("cron", f"Cron: {job.name}", "")
        session_key = f"cron:{task.id}"
        task.session_key = session_key
        task_store._save()
        await event_bus.publish(AgentEvent("task", "started", {
            "task_id": task.id, "type": "cron", "label": task.label,
        }))

        # Inject system message into chat session
        chat_session = session_manager.get_or_create("api:default")
        chat_session.add_message("assistant", f"[System] Cron task started: {job.name}")
        session_manager.save(chat_session)
        await event_bus.publish(AgentEvent("system_message", "injected", {
            "task_id": task.id, "content": f"[System] Cron task started: {job.name}",
        }))

        try:
            response = await agent.process_direct(
                job.payload.message,
                session_key=session_key,
                channel=channel,
                chat_id=chat_id,
                metadata={"task_id": task.id},
            )
            summary = _strip_think_tags(response or "")[:120]
            task_store.update(task.id, status="completed", summary=summary)
            await event_bus.publish(AgentEvent("task", "completed", {
                "task_id": task.id, "summary": summary,
            }))
            # Inject completion system message
            chat_session = session_manager.get_or_create("api:default")
            chat_session.add_message("assistant", f"[System] Cron completed: {summary}")
            session_manager.save(chat_session)
            await event_bus.publish(AgentEvent("system_message", "injected", {
                "task_id": task.id, "content": f"[System] Cron completed: {summary}",
            }))
        except Exception as e:
            task_store.update(task.id, status="failed", error=str(e))
            await event_bus.publish(AgentEvent("task", "failed", {
                "task_id": task.id, "error": str(e),
            }))
            chat_session = session_manager.get_or_create("api:default")
            chat_session.add_message("assistant", f"[System] Cron failed: {e}")
            session_manager.save(chat_session)
            await event_bus.publish(AgentEvent("system_message", "injected", {
                "task_id": task.id, "content": f"[System] Cron failed: {e}",
            }))
            response = None

        if job.payload.deliver and job.payload.to:
            from nanobot.bus.events import OutboundMessage
            await bus.publish_outbound(OutboundMessage(
                channel=channel,
                chat_id=job.payload.to,
                content=response or ""
            ))
        return response
    cron.on_job = on_cron_job
    
    # Create heartbeat service
    on_heartbeat = _make_heartbeat_callback(config, agent, task_store, session_manager, event_bus)

    heartbeat = HeartbeatService(
        workspace=config.workspace_path,
        on_heartbeat=on_heartbeat,
        interval_s=config.heartbeat.interval_minutes * 60,
        enabled=config.heartbeat.enabled,
        event_bus=event_bus,
    )
    
    # Create channel manager
    channels = ChannelManager(config, bus, session_manager=session_manager, event_bus=event_bus,
                              task_store=task_store)
    
    if channels.enabled_channels:
        console.print(f"[green]✓[/green] Channels enabled: {', '.join(channels.enabled_channels)}")
    else:
        console.print("[yellow]Warning: No channels enabled[/yellow]")
    
    cron_status = cron.status()
    if cron_status["jobs"] > 0:
        console.print(f"[green]✓[/green] Cron: {cron_status['jobs']} scheduled jobs")
    
    if config.heartbeat.enabled:
        console.print(f"[green]✓[/green] Heartbeat: every {config.heartbeat.interval_minutes}m")
    else:
        console.print("[dim]Heartbeat: disabled[/dim]")
    
    async def run():
        try:
            await cron.start()
            await heartbeat.start()
            await asyncio.gather(
                agent.run(),
                channels.start_all(),
            )
        except KeyboardInterrupt:
            console.print("\nShutting down...")
            heartbeat.stop()
            cron.stop()
            agent.stop()
            await channels.stop_all()
    
    asyncio.run(run())




# ============================================================================
# Agent Commands
# ============================================================================


@app.command()
def agent(
    message: str = typer.Option(None, "--message", "-m", help="Message to send to the agent"),
    session_id: str = typer.Option("cli:default", "--session", "-s", help="Session ID"),
    markdown: bool = typer.Option(True, "--markdown/--no-markdown", help="Render assistant output as Markdown"),
    logs: bool = typer.Option(False, "--logs/--no-logs", help="Show nanobot runtime logs during chat"),
):
    """Interact with the agent directly."""
    from nanobot.config.loader import load_config
    from nanobot.bus.queue import MessageBus
    from nanobot.agent.loop import AgentLoop
    from loguru import logger
    
    config = load_config()
    
    bus = MessageBus()
    provider = _make_provider(config)

    if logs:
        logger.enable("nanobot")
    else:
        logger.disable("nanobot")
    
    agent_loop = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model or None,
        brave_api_key=config.tools.web.search.api_key or None,
        exec_config=config.tools.exec,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        max_tokens=config.agents.defaults.max_tokens,
        temperature=config.agents.defaults.temperature,
        context_window=config.agents.defaults.context_window,
    )
    
    # Show spinner when logs are off (no output to miss); skip when logs are on
    def _thinking_ctx():
        if logs:
            from contextlib import nullcontext
            return nullcontext()
        # Animated spinner is safe to use with prompt_toolkit input handling
        return console.status("[dim]nanobot is thinking...[/dim]", spinner="dots")

    if message:
        # Single message mode
        async def run_once():
            with _thinking_ctx():
                response = await agent_loop.process_direct(message, session_id)
            _print_agent_response(response, render_markdown=markdown)
        
        asyncio.run(run_once())
    else:
        # Interactive mode
        _init_prompt_session()
        console.print(f"{__logo__} Interactive mode (type [bold]exit[/bold] or [bold]Ctrl+C[/bold] to quit)\n")

        def _exit_on_sigint(signum, frame):
            _restore_terminal()
            console.print("\nGoodbye!")
            os._exit(0)

        signal.signal(signal.SIGINT, _exit_on_sigint)
        
        async def run_interactive():
            while True:
                try:
                    _flush_pending_tty_input()
                    user_input = await _read_interactive_input_async()
                    command = user_input.strip()
                    if not command:
                        continue

                    if _is_exit_command(command):
                        _restore_terminal()
                        console.print("\nGoodbye!")
                        break
                    
                    with _thinking_ctx():
                        response = await agent_loop.process_direct(user_input, session_id)
                    _print_agent_response(response, render_markdown=markdown)
                except KeyboardInterrupt:
                    _restore_terminal()
                    console.print("\nGoodbye!")
                    break
                except EOFError:
                    _restore_terminal()
                    console.print("\nGoodbye!")
                    break
        
        asyncio.run(run_interactive())


# ============================================================================
# Channel Commands
# ============================================================================


channels_app = typer.Typer(help="Manage channels")
app.add_typer(channels_app, name="channels")


@channels_app.command("status")
def channels_status():
    """Show channel status."""
    from nanobot.config.loader import load_config

    config = load_config()

    table = Table(title="Channel Status")
    table.add_column("Channel", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Configuration", style="yellow")

    # WhatsApp
    wa = config.channels.whatsapp
    table.add_row(
        "WhatsApp",
        "✓" if wa.enabled else "✗",
        wa.bridge_url
    )

    dc = config.channels.discord
    table.add_row(
        "Discord",
        "✓" if dc.enabled else "✗",
        dc.gateway_url
    )

    # Feishu
    fs = config.channels.feishu
    fs_config = f"app_id: {fs.app_id[:10]}..." if fs.app_id else "[dim]not configured[/dim]"
    table.add_row(
        "Feishu",
        "✓" if fs.enabled else "✗",
        fs_config
    )

    # Mochat
    mc = config.channels.mochat
    mc_base = mc.base_url or "[dim]not configured[/dim]"
    table.add_row(
        "Mochat",
        "✓" if mc.enabled else "✗",
        mc_base
    )
    
    # Telegram
    tg = config.channels.telegram
    tg_config = f"token: {tg.token[:10]}..." if tg.token else "[dim]not configured[/dim]"
    table.add_row(
        "Telegram",
        "✓" if tg.enabled else "✗",
        tg_config
    )

    # Slack
    slack = config.channels.slack
    slack_config = "socket" if slack.app_token and slack.bot_token else "[dim]not configured[/dim]"
    table.add_row(
        "Slack",
        "✓" if slack.enabled else "✗",
        slack_config
    )

    console.print(table)


def _get_bridge_dir() -> Path:
    """Get the bridge directory, setting it up if needed."""
    import shutil
    import subprocess
    
    # User's bridge location
    user_bridge = Path.home() / ".nanobot" / "bridge"
    
    # Check if already built
    if (user_bridge / "dist" / "index.js").exists():
        return user_bridge
    
    # Check for npm
    if not shutil.which("npm"):
        console.print("[red]npm not found. Please install Node.js >= 18.[/red]")
        raise typer.Exit(1)
    
    # Find source bridge: first check package data, then source dir
    pkg_bridge = Path(__file__).parent.parent / "bridge"  # nanobot/bridge (installed)
    src_bridge = Path(__file__).parent.parent.parent / "bridge"  # repo root/bridge (dev)
    
    source = None
    if (pkg_bridge / "package.json").exists():
        source = pkg_bridge
    elif (src_bridge / "package.json").exists():
        source = src_bridge
    
    if not source:
        console.print("[red]Bridge source not found.[/red]")
        console.print("Try reinstalling: pip install --force-reinstall nanobot")
        raise typer.Exit(1)
    
    console.print(f"{__logo__} Setting up bridge...")
    
    # Copy to user directory
    user_bridge.parent.mkdir(parents=True, exist_ok=True)
    if user_bridge.exists():
        shutil.rmtree(user_bridge)
    shutil.copytree(source, user_bridge, ignore=shutil.ignore_patterns("node_modules", "dist"))
    
    # Install and build
    try:
        console.print("  Installing dependencies...")
        subprocess.run(["npm", "install"], cwd=user_bridge, check=True, capture_output=True)
        
        console.print("  Building...")
        subprocess.run(["npm", "run", "build"], cwd=user_bridge, check=True, capture_output=True)
        
        console.print("[green]✓[/green] Bridge ready\n")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Build failed: {e}[/red]")
        if e.stderr:
            console.print(f"[dim]{e.stderr.decode()[:500]}[/dim]")
        raise typer.Exit(1)
    
    return user_bridge


@channels_app.command("login")
def channels_login():
    """Link device via QR code."""
    import subprocess
    
    bridge_dir = _get_bridge_dir()
    
    console.print(f"{__logo__} Starting bridge...")
    console.print("Scan the QR code to connect.\n")
    
    try:
        subprocess.run(["npm", "start"], cwd=bridge_dir, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Bridge failed: {e}[/red]")
    except FileNotFoundError:
        console.print("[red]npm not found. Please install Node.js.[/red]")


# ============================================================================
# Cron Commands
# ============================================================================

cron_app = typer.Typer(help="Manage scheduled tasks")
app.add_typer(cron_app, name="cron")


@cron_app.command("list")
def cron_list(
    all: bool = typer.Option(False, "--all", "-a", help="Include disabled jobs"),
):
    """List scheduled jobs."""
    from nanobot.config.loader import get_data_dir
    from nanobot.cron.service import CronService
    
    store_path = get_data_dir() / "cron" / "jobs.json"
    service = CronService(store_path)
    
    jobs = service.list_jobs(include_disabled=all)
    
    if not jobs:
        console.print("No scheduled jobs.")
        return
    
    table = Table(title="Scheduled Jobs")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Schedule")
    table.add_column("Status")
    table.add_column("Next Run")
    
    import time
    for job in jobs:
        # Format schedule
        if job.schedule.kind == "every":
            sched = f"every {(job.schedule.every_ms or 0) // 1000}s"
        elif job.schedule.kind == "cron":
            sched = job.schedule.expr or ""
        else:
            sched = "one-time"
        
        # Format next run
        next_run = ""
        if job.state.next_run_at_ms:
            next_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(job.state.next_run_at_ms / 1000))
            next_run = next_time
        
        status = "[green]enabled[/green]" if job.enabled else "[dim]disabled[/dim]"
        
        table.add_row(job.id, job.name, sched, status, next_run)
    
    console.print(table)


@cron_app.command("add")
def cron_add(
    name: str = typer.Option(..., "--name", "-n", help="Job name"),
    message: str = typer.Option(..., "--message", "-m", help="Message for agent"),
    every: int = typer.Option(None, "--every", "-e", help="Run every N seconds"),
    cron_expr: str = typer.Option(None, "--cron", "-c", help="Cron expression (e.g. '0 9 * * *')"),
    at: str = typer.Option(None, "--at", help="Run once at time (ISO format)"),
    deliver: bool = typer.Option(False, "--deliver", "-d", help="Deliver response to channel"),
    to: str = typer.Option(None, "--to", help="Recipient for delivery"),
    channel: str = typer.Option(None, "--channel", help="Channel for delivery (e.g. 'telegram', 'whatsapp')"),
):
    """Add a scheduled job."""
    from nanobot.config.loader import get_data_dir
    from nanobot.cron.service import CronService
    from nanobot.cron.types import CronSchedule
    
    # Determine schedule type
    if every:
        schedule = CronSchedule(kind="every", every_ms=every * 1000)
    elif cron_expr:
        schedule = CronSchedule(kind="cron", expr=cron_expr)
    elif at:
        import datetime
        dt = datetime.datetime.fromisoformat(at)
        schedule = CronSchedule(kind="at", at_ms=int(dt.timestamp() * 1000))
    else:
        console.print("[red]Error: Must specify --every, --cron, or --at[/red]")
        raise typer.Exit(1)
    
    store_path = get_data_dir() / "cron" / "jobs.json"
    service = CronService(store_path)
    
    job = service.add_job(
        name=name,
        schedule=schedule,
        message=message,
        deliver=deliver,
        to=to,
        channel=channel,
    )
    
    console.print(f"[green]✓[/green] Added job '{job.name}' ({job.id})")


@cron_app.command("remove")
def cron_remove(
    job_id: str = typer.Argument(..., help="Job ID to remove"),
):
    """Remove a scheduled job."""
    from nanobot.config.loader import get_data_dir
    from nanobot.cron.service import CronService
    
    store_path = get_data_dir() / "cron" / "jobs.json"
    service = CronService(store_path)
    
    if service.remove_job(job_id):
        console.print(f"[green]✓[/green] Removed job {job_id}")
    else:
        console.print(f"[red]Job {job_id} not found[/red]")


@cron_app.command("enable")
def cron_enable(
    job_id: str = typer.Argument(..., help="Job ID"),
    disable: bool = typer.Option(False, "--disable", help="Disable instead of enable"),
):
    """Enable or disable a job."""
    from nanobot.config.loader import get_data_dir
    from nanobot.cron.service import CronService
    
    store_path = get_data_dir() / "cron" / "jobs.json"
    service = CronService(store_path)
    
    job = service.enable_job(job_id, enabled=not disable)
    if job:
        status = "disabled" if disable else "enabled"
        console.print(f"[green]✓[/green] Job '{job.name}' {status}")
    else:
        console.print(f"[red]Job {job_id} not found[/red]")


@cron_app.command("run")
def cron_run(
    job_id: str = typer.Argument(..., help="Job ID to run"),
    force: bool = typer.Option(False, "--force", "-f", help="Run even if disabled"),
):
    """Manually run a job."""
    from nanobot.config.loader import get_data_dir
    from nanobot.cron.service import CronService
    
    store_path = get_data_dir() / "cron" / "jobs.json"
    service = CronService(store_path)
    
    async def run():
        return await service.run_job(job_id, force=force)
    
    if asyncio.run(run()):
        console.print(f"[green]✓[/green] Job executed")
    else:
        console.print(f"[red]Failed to run job {job_id}[/red]")


# ============================================================================
# Heartbeat Commands
# ============================================================================

heartbeat_app = typer.Typer(help="Manage heartbeat")
app.add_typer(heartbeat_app, name="heartbeat")


@heartbeat_app.command("trigger")
def heartbeat_trigger():
    """Manually trigger a heartbeat now."""
    from loguru import logger as _logger
    from nanobot.config.loader import load_config, get_data_dir
    from nanobot.bus.queue import MessageBus
    from nanobot.bus.event_bus import EventBus, AgentEvent
    from nanobot.agent.loop import AgentLoop
    from nanobot.session.manager import SessionManager
    from nanobot.heartbeat.service import HeartbeatService
    from nanobot.task.store import TaskStore

    # Silence loguru INFO — event bus output replaces it
    _logger.disable("nanobot")

    config = load_config()
    bus = MessageBus()
    event_bus = EventBus()
    provider = _make_provider(config)
    session_manager = SessionManager(config.workspace_path)
    task_store = TaskStore(get_data_dir() / "tasks.json")

    agent = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model or None,
        max_iterations=config.agents.defaults.max_tool_iterations,
        brave_api_key=config.tools.web.search.api_key or None,
        exec_config=config.tools.exec,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        session_manager=session_manager,
        event_bus=event_bus,
        max_tokens=config.agents.defaults.max_tokens,
        temperature=config.agents.defaults.temperature,
        context_window=config.agents.defaults.context_window,
    )

    on_heartbeat = _make_heartbeat_callback(config, agent, task_store, session_manager, event_bus)
    heartbeat_svc = HeartbeatService(
        workspace=config.workspace_path,
        on_heartbeat=on_heartbeat,
        interval_s=config.heartbeat.interval_minutes * 60,
        enabled=True,  # Always enabled for manual trigger
        event_bus=event_bus,
    )

    # Live progress via event bus
    async def on_event(event: AgentEvent):
        if event.category == "agent":
            if event.event == "thinking_started":
                n = event.data.get("iteration", "?")
                console.print(f"  [dim]thinking (iteration {n})...[/dim]")
            elif event.event == "tool_call":
                name = event.data.get("name", "?")
                args = event.data.get("args", {})
                preview = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
                console.print(f"  [cyan]> {name}[/cyan]({preview})")
            elif event.event == "tool_result":
                ms = event.data.get("duration_ms", 0)
                result = event.data.get("result_preview", "")[:80]
                if result:
                    console.print(f"  [dim]  {result} ({ms}ms)[/dim]")
            elif event.event == "thinking_finished":
                n = event.data.get("iterations", "?")
                console.print(f"  [green]done[/green] [dim]({n} iterations)[/dim]")

    event_bus.subscribe(on_event)
    console.print(f"{__logo__} Running heartbeat...\n")

    async def run():
        return await heartbeat_svc.trigger_now()

    response = asyncio.run(run())
    if response:
        console.print(f"\n{__logo__} Result:\n")
        console.print(Markdown(response))
    else:
        console.print("[yellow]No heartbeat response (HEARTBEAT.md may be empty)[/yellow]")


@heartbeat_app.command("status")
def heartbeat_status():
    """Show heartbeat configuration and last run."""
    from nanobot.config.loader import load_config, get_data_dir
    from nanobot.task.store import TaskStore

    config = load_config()
    hb = config.heartbeat

    console.print(f"{__logo__} Heartbeat Status\n")
    console.print(f"Enabled: {'[green]yes[/green]' if hb.enabled else '[red]no[/red]'}")
    console.print(f"Interval: {hb.interval_minutes} minutes")
    if hb.channel:
        console.print(f"Channel: {hb.channel}")
    if hb.chat_id:
        console.print(f"Chat ID: {hb.chat_id}")

    # Show HEARTBEAT.md status
    hb_file = config.workspace_path / "HEARTBEAT.md"
    if hb_file.exists():
        content = hb_file.read_text().strip()
        lines = len(content.splitlines()) if content else 0
        console.print(f"HEARTBEAT.md: [green]exists[/green] ({lines} lines)")
    else:
        console.print("HEARTBEAT.md: [dim]not found[/dim]")

    # Show last run from task store
    task_store = TaskStore(get_data_dir() / "tasks.json")
    recent = [t for t in task_store.list_recent(limit=10) if t.type == "heartbeat"]

    if recent:
        console.print(f"\n[bold]Recent runs:[/bold]")
        import time
        for task in recent[:5]:
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(task.created_at_ms / 1000))
            dot = {"completed": "[green]●[/green]", "failed": "[red]●[/red]", "running": "[yellow]●[/yellow]"}.get(task.status, "○")
            summary = f" — {task.summary}" if task.summary else ""
            if task.error:
                summary = f" — [red]{task.error}[/red]"
            console.print(f"  {dot} {ts}  {task.status}{summary}")
    else:
        console.print("\n[dim]No recent heartbeat runs.[/dim]")


# ============================================================================
# Status Commands
# ============================================================================


@app.command()
def status():
    """Show nanobot status."""
    from nanobot.config.loader import load_config, get_config_path

    config_path = get_config_path()
    config = load_config()
    workspace = config.workspace_path

    console.print(f"{__logo__} nanobot Status\n")

    console.print(f"Config: {config_path} {'[green]✓[/green]' if config_path.exists() else '[red]✗[/red]'}")
    console.print(f"Workspace: {workspace} {'[green]✓[/green]' if workspace.exists() else '[red]✗[/red]'}")

    if config_path.exists():
        from nanobot.providers.registry import PROVIDERS

        model_display = config.agents.defaults.model or "[dim]auto-discover[/dim]"
        console.print(f"Model: {model_display}")
        
        # Check API keys from registry
        for spec in PROVIDERS:
            p = getattr(config.providers, spec.name, None)
            if p is None:
                continue
            if spec.is_local:
                # Local deployments show api_base instead of api_key
                if p.api_base:
                    console.print(f"{spec.label}: [green]✓ {p.api_base}[/green]")
                else:
                    console.print(f"{spec.label}: [dim]not set[/dim]")
            else:
                has_key = bool(p.api_key)
                console.print(f"{spec.label}: {'[green]✓[/green]' if has_key else '[dim]not set[/dim]'}")


if __name__ == "__main__":
    app()
