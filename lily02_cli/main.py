import click
import requests
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.table import Table

console = Console()

class LilyCLI:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url

    def query(self, text, automl=False):
        try:
            # Check if backend is alive
            try:
                requests.get(f"{self.api_url}/api/health", timeout=2)
            except:
                console.print("[red]Error: Lily02 Backend is not running on localhost:8000.[/red]")
                console.print("[yellow]Please run 'python recovery.py' first.[/yellow]")
                return

            console.print(Panel(f"Dive Initialization: [cyan]{text}[/cyan]", title="Lily02 Mission", border_style="cyan"))
            
            with Live(Spinner("dots", text="Orchestrating Hyperpipeline...", style="cyan"), refresh_per_second=10) as live:
                start_time = time.time()
                response = requests.post(f"{self.api_url}/api/orchestrate", json={
                    "query": text,
                    "enable_automl": automl
                }, timeout=120)
                elapsed = time.time() - start_time
                live.update(f"Mission Complete ({elapsed:.1f}s)")
            
            data = response.json()
            
            # Print Plan
            if "plan_steps" in data:
                table = Table(title="Mission Execution Plan", show_header=True, header_style="bold magenta")
                table.add_column("Step", style="dim", width=6)
                table.add_column("Action")
                for i, step in enumerate(data["plan_steps"]):
                    table.add_row(str(i+1), step)
                console.print(table)

            # Print Response
            console.print(Panel(Markdown(data["lily_response"]), title="Lily02 Intelligence Response", border_style="green"))
            
        except Exception as e:
            console.print(f"[red]Critical Failure:[/red] {str(e)}")

@click.group()
def main():
    """Lily02 Agentic Ocean Intelligence CLI"""
    pass

@main.command()
@click.argument('text', required=False)
@click.option('--automl', is_flag=True, help="Enable Deep Auto-ML Forensics")
def ask(text, automl):
    """Ask Lily02 a scientific query."""
    if not text:
        text = click.prompt("How can I assist your research today?")
    
    cli = LilyCLI()
    cli.query(text, automl)

@main.command()
def status():
    """Check Lily02 backend and model status."""
    try:
        r = requests.get("http://localhost:8000/api/health", timeout=3)
        data = r.json()
        console.print(Panel(
            f"Status: [green]ONLINE[/green]\n"
            f"Engine: {data.get('engine')}\n"
            f"Uptime: Active",
            title="System Diagnostics"
        ))
    except:
        console.print("[red]Status: OFFLINE[/red]")

if __name__ == "__main__":
    main()
