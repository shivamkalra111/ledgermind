"""
LedgerMind - Agentic AI CFO Platform
Main entry point
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestration.workflow import AgentWorkflow
from llm.client import LLMClient


console = Console()


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██╗     ███████╗██████╗  ██████╗ ███████╗██████╗               ║
║   ██║     ██╔════╝██╔══██╗██╔════╝ ██╔════╝██╔══██╗              ║
║   ██║     █████╗  ██║  ██║██║  ███╗█████╗  ██████╔╝              ║
║   ██║     ██╔══╝  ██║  ██║██║   ██║██╔══╝  ██╔══██╗              ║
║   ███████╗███████╗██████╔╝╚██████╔╝███████╗██║  ██║              ║
║   ╚══════╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝              ║
║                                                                   ║
║           🤖 AI CFO for MSMEs | GST 2026 Ready                   ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")


def check_ollama():
    """Check if Ollama is running."""
    try:
        llm = LLMClient()
        if llm.is_available():
            console.print("✅ Ollama connected", style="green")
            return True
        else:
            console.print("⚠️  Ollama running but model not found", style="yellow")
            console.print("   Run: ollama pull qwen2.5:7b-instruct", style="dim")
            return False
    except Exception as e:
        console.print("❌ Ollama not running", style="red")
        console.print("   Run: ollama serve", style="dim")
        return False


def main():
    """Main entry point."""
    
    print_banner()
    
    # Check Ollama
    console.print("\n🔍 Checking system...\n")
    ollama_ready = check_ollama()
    
    if not ollama_ready:
        console.print("\n⚠️  Some features may not work without Ollama.\n", style="yellow")
    
    # Initialize workflow
    console.print("\n🚀 Initializing LedgerMind...\n")
    
    try:
        workflow = AgentWorkflow()
        console.print("✅ System ready!\n", style="green")
    except Exception as e:
        console.print(f"❌ Initialization failed: {e}", style="red")
        return
    
    # Check for command line argument (single command mode)
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        console.print(f"[bold]> {user_input}[/bold]\n")
        response = workflow.run(user_input)
        console.print(Markdown(response))
        return
    
    # Interactive mode
    console.print(Panel(
        "Type [bold cyan]help[/bold cyan] for commands, or start by analyzing a folder:\n"
        "[dim]analyze folder /path/to/your/excels/[/dim]",
        title="💡 Quick Start",
        border_style="cyan"
    ))
    
    while True:
        try:
            console.print()
            user_input = console.input("[bold cyan]You>[/bold cyan] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("\n👋 Goodbye!\n", style="bold cyan")
                break
            
            # Process input
            console.print()
            with console.status("[bold green]Thinking...[/bold green]"):
                response = workflow.run(user_input)
            
            # Display response
            console.print(Markdown(response))
            
        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!\n", style="bold cyan")
            break
        except Exception as e:
            console.print(f"\n❌ Error: {e}\n", style="red")


if __name__ == "__main__":
    main()

