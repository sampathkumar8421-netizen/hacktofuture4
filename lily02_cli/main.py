import click
import requests
import json
import time
import os
import sys
from datetime import datetime
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
import subprocess

# Initialize Console
console = Console()

# ASCII Art
LILY_LOGO = r"""
  _      _ _             ___ ___  
 | |    (_) |           / _ \__ \ 
 | |     _| |_   _ ___ | | | | ) |
 | |    | | | | | / _ \| | | |/ / 
 | |____| | | |_| | (_) | |_| / /_ 
 |______|_|_|\__, |\___/ \___/____|
              __/ |                
             |___/                 
"""

class LilyAdvancedCLI:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url
        self.messages = []
        self.model_status = "STABLE"
        self.active_model = os.getenv("LOCAL_AGENT_MODEL", "gpt-oss-120b")

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=10),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="main", ratio=3),
            Layout(name="side", ratio=1)
        )
        return layout

    def generate_header(self) -> Panel:
        logo = Text(LILY_LOGO, style="bold cyan")
        info = Text(f"S.O.W v2.1 | Local Reasoning Core: {self.active_model} | {datetime.now().strftime('%H:%M:%S')}", style="dim")
        return Panel(Group(Align.center(logo), Align.center(info)), border_style="cyan")

    def generate_side(self) -> Panel:
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]Status[/]", f"[green]{self.model_status}[/]")
        table.add_row("[cyan]Region[/]", "LOCAL/DOCK")
        table.add_row("[cyan]Forensics[/]", "[yellow]ACTIVE[/]")
        table.add_row("[cyan]Vectors[/]", "[green]SYNCED[/]")
        return Panel(table, title="Telemetry", border_style="dim")

    def generate_footer(self) -> Panel:
        return Panel("[dim]Commands: /clear, /exit, /help | Lily02 Agentic Intelligence[/]", border_style="dim")

    def render_chat(self) -> Group:
        renderables = []
        for msg in self.messages[-6:]: # Show last 6 messages
            role = "[bold cyan]Lily02[/]" if msg["role"] == "bot" else "[bold magenta]You[/]"
            renderables.append(Panel(Markdown(msg["text"]), title=role, border_style="cyan" if msg["role"] == "bot" else "magenta"))
        return Group(*renderables)

    def interactive_session(self):
        layout = self.make_layout()
        
        # Initial health check
        try:
            requests.get(f"{self.api_url}/api/health", timeout=2)
        except:
            console.print("[red]Error: Lily02 Backend is not running on localhost:8080.[/red]")
            console.print("[yellow]Ensure 'python recovery.py' is active with Port 8080 binding.[/yellow]")
            return

        while True:
            # Refresh Layout
            layout["header"].update(self.generate_header())
            layout["side"].update(self.generate_side())
            layout["footer"].update(self.generate_footer())
            layout["main"].update(self.render_chat())
            
            console.clear()
            console.print(layout)
            
            user_input = Prompt.ask("\n[bold cyan]>[/bold cyan]")
            
            if user_input.lower() == "/exit":
                break
            if user_input.lower() == "/clear":
                self.messages = []
                continue
                
            self.messages.append({"role": "user", "text": user_input})
            
            # Bot Processing
            with Live(Spinner("dots", text="Orchestrating Hyperpipeline...", style="cyan"), refresh_per_second=10) as live:
                try:
                    response = requests.post(f"{self.api_url}/api/orchestrate", json={
                        "query": user_input,
                        "enable_automl": True # Default to true for premium CLI
                    }, timeout=120)
                    data = response.json()
                    bot_text = data.get("lily_response", "No response received.")
                except Exception as e:
                    bot_text = f"**System Error**: {str(e)}"
            
            self.messages.append({"role": "bot", "text": bot_text})

@click.group()
def main():
    """Lily02 Premium Terminal Framework"""
    pass

@main.command()
def chat():
    """Launch the interactive scientific chat framework."""
    cli = LilyAdvancedCLI()
    cli.interactive_session()

@main.command()
@click.argument('query')
def ask(query):
    """Execution a quick mission query."""
    try:
        r = requests.post("http://localhost:8080/api/orchestrate", json={"query": query, "enable_automl": True})
        console.print(Panel(Markdown(r.json()["lily_response"]), title="Lily02 Intelligence"))
    except Exception as e:
        console.print(f"[red]Error:[/] {str(e)}")

@main.command()
def hub():
    """Start the Web Hub (Workstation + Public Tunnel)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recovery_script = os.path.join(root, "recovery.py")
    
    if not os.path.exists(recovery_script):
        console.print(f"[red]Error:[/] Could not find recovery.py at {recovery_script}")
        return

    console.print("[cyan]🌊 Launching Lily02 Scientific Hub...[/]")
    console.print(f"[dim]Project Root: {root}[/]")
    
    # Launch recovery.py in a new process
    try:
        # On Windows, we use 'start' to launch it in a new window so the user can see log output
        subprocess.Popen(["python", recovery_script], cwd=root, creationflags=subprocess.CREATE_NEW_CONSOLE)
        console.print("[green]SUCCESS: Web Hub launched in a new terminal window.[/]")
        console.print("[yellow]Wait ~30 seconds for the Ngrok tunnel to stabilize.[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to launch hub:[/] {str(e)}")

if __name__ == "__main__":
    main()
