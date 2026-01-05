"""
LedgerMind - Agentic AI CFO Platform
Main entry point with customer isolation
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestration.workflow import AgentWorkflow
from llm.client import LLMClient
from core.customer import (
    CustomerManager,
    CustomerContext,
    set_active_customer,
    get_active_customer,
)


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


def show_customer_list(manager: CustomerManager) -> None:
    """Display list of customers in a table."""
    customers = manager.list_customers()
    
    if not customers:
        console.print("\n📭 No customers found.", style="yellow")
        console.print("   Create a new customer to get started.\n", style="dim")
        return
    
    table = Table(title="📊 Your Companies", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Company Name", style="bold")
    table.add_column("Customer ID", style="dim")
    table.add_column("GSTIN", style="green")
    table.add_column("Last Accessed", style="dim")
    
    for i, customer in enumerate(customers, 1):
        table.add_row(
            str(i),
            customer["company_name"],
            customer["customer_id"],
            customer.get("gstin") or "-",
            customer.get("last_accessed", "-")[:10] if customer.get("last_accessed") else "-"
        )
    
    console.print()
    console.print(table)
    console.print()


def select_customer(manager: CustomerManager) -> CustomerContext:
    """Interactive customer selection."""
    
    while True:
        customers = manager.list_customers()
        show_customer_list(manager)
        
        console.print(Panel(
            "[bold cyan]Options:[/bold cyan]\n"
            "  • Enter a [bold]number[/bold] to select a company\n"
            "  • Type [bold]new[/bold] to create a new company\n"
            "  • Type [bold]demo[/bold] to use sample data",
            title="🔐 Select Company",
            border_style="cyan"
        ))
        
        choice = Prompt.ask("[bold cyan]Your choice[/bold cyan]").strip().lower()
        
        # Demo mode
        if choice == "demo":
            console.print("\n🎮 Using demo mode with sample company...\n", style="green")
            customer = manager.get_customer("sample_company")
            # Don't require profile for sample_company (legacy)
            customer.root_dir.mkdir(parents=True, exist_ok=True)
            customer.data_dir.mkdir(exist_ok=True)
            return customer
        
        # Create new customer
        if choice == "new":
            return create_new_customer(manager)
        
        # Select by number
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(customers):
                customer_id = customers[idx]["customer_id"]
                customer = manager.get_customer(customer_id)
                customer.update_profile()  # Update last_accessed
                console.print(f"\n✅ Selected: [bold]{customers[idx]['company_name']}[/bold]\n", style="green")
                return customer
        
        console.print("\n❌ Invalid choice. Please try again.\n", style="red")


def create_new_customer(manager: CustomerManager) -> CustomerContext:
    """Create a new customer interactively."""
    
    console.print("\n[bold cyan]📝 Create New Company[/bold cyan]\n")
    
    # Get company name
    company_name = Prompt.ask("Company Name", default="My Company")
    
    # Generate customer ID from name
    customer_id = company_name.lower().replace(" ", "_").replace("-", "_")
    customer_id = "".join(c for c in customer_id if c.isalnum() or c == "_")
    
    # Check if exists
    if manager.customer_exists(customer_id):
        console.print(f"\n⚠️  Company '{customer_id}' already exists.", style="yellow")
        customer_id = Prompt.ask("Enter a unique ID", default=f"{customer_id}_2")
    
    # Optional: GSTIN
    gstin = Prompt.ask("GSTIN (optional, press Enter to skip)", default="")
    if gstin and len(gstin) != 15:
        console.print("⚠️  GSTIN should be 15 characters. Skipping.", style="yellow")
        gstin = None
    
    # Optional: Business type
    console.print("\n[dim]Business Type:[/dim]")
    console.print("  1. Trading")
    console.print("  2. Services")
    console.print("  3. Manufacturing")
    btype_choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
    business_types = {"1": "trading", "2": "services", "3": "manufacturing"}
    business_type = business_types[btype_choice]
    
    # Optional: Turnover category
    console.print("\n[dim]Business Size:[/dim]")
    console.print("  1. Micro (Turnover ≤ ₹5 Cr)")
    console.print("  2. Small (Turnover ≤ ₹50 Cr)")
    console.print("  3. Medium (Turnover ≤ ₹250 Cr)")
    size_choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
    turnover_categories = {"1": "micro", "2": "small", "3": "medium"}
    turnover_category = turnover_categories[size_choice]
    
    # Create customer
    try:
        customer = manager.create_customer(
            customer_id=customer_id,
            company_name=company_name,
            gstin=gstin or None,
            business_type=business_type,
            turnover_category=turnover_category
        )
        
        console.print(f"\n✅ Created: [bold]{company_name}[/bold]", style="green")
        console.print(f"   Workspace: [dim]{customer.root_dir}[/dim]")
        console.print(f"   Data folder: [dim]{customer.data_dir}[/dim]")
        console.print("\n💡 Place your Excel/CSV files in the [bold]data[/bold] folder.\n", style="cyan")
        
        return customer
        
    except ValueError as e:
        console.print(f"\n❌ Error: {e}\n", style="red")
        return create_new_customer(manager)  # Retry


def show_customer_info(customer: CustomerContext) -> None:
    """Show current customer info."""
    profile = customer.profile
    files = customer.list_data_files()
    
    console.print(Panel(
        f"[bold]{profile.company_name}[/bold]\n"
        f"[dim]ID: {profile.customer_id}[/dim]\n"
        f"GSTIN: {profile.gstin or 'Not set'}\n"
        f"Type: {profile.business_type.title()} | Size: {profile.turnover_category.title()}\n"
        f"Data files: {len(files)}",
        title="🏢 Current Company",
        border_style="green"
    ))


def main():
    """Main entry point."""
    
    print_banner()
    
    # Check Ollama
    console.print("\n🔍 Checking system...\n")
    ollama_ready = check_ollama()
    
    if not ollama_ready:
        console.print("\n⚠️  Some features may not work without Ollama.\n", style="yellow")
    
    # Customer selection
    console.print("\n" + "="*60 + "\n")
    console.print("[bold]🔐 CUSTOMER DATA ISOLATION[/bold]", style="cyan")
    console.print("[dim]Each company's data is stored separately and securely.[/dim]\n")
    
    manager = CustomerManager()
    
    # Check for command line argument (single command mode with customer)
    if len(sys.argv) > 2 and sys.argv[1] == "--customer":
        customer_id = sys.argv[2]
        customer = manager.get_customer(customer_id)
        if not customer.exists():
            console.print(f"❌ Customer not found: {customer_id}", style="red")
            return
        set_active_customer(customer)
        
        # Process remaining args as command
        if len(sys.argv) > 3:
            user_input = " ".join(sys.argv[3:])
            with customer:
                workflow = AgentWorkflow(customer=customer)
                response = workflow.run(user_input)
                console.print(Markdown(response))
            return
    
    # Interactive customer selection
    customer = select_customer(manager)
    set_active_customer(customer)
    
    # Initialize workflow with customer context
    console.print("\n🚀 Initializing LedgerMind...\n")
    
    try:
        with customer:
            workflow = AgentWorkflow(customer=customer)
            console.print("✅ System ready!\n", style="green")
            
            # Show customer info
            show_customer_info(customer)
            
            # Interactive mode
            console.print(Panel(
                "Type [bold cyan]help[/bold cyan] for commands\n"
                "[dim]• analyze data[/dim] — Analyze your Excel/CSV files\n"
                "[dim]• compliance check[/dim] — Check for GST issues\n"
                "[dim]• switch company[/dim] — Change to different company\n"
                "[dim]• exit[/dim] — Quit",
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
                    
                    # Switch company command
                    if user_input.lower() in ["switch company", "switch", "change company"]:
                        customer.close()
                        customer = select_customer(manager)
                        set_active_customer(customer)
                        customer.ensure_exists()
                        workflow = AgentWorkflow(customer=customer)
                        show_customer_info(customer)
                        continue
                    
                    # Show current company
                    if user_input.lower() in ["company", "who", "current"]:
                        show_customer_info(customer)
                        continue
                    
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
                    
    except Exception as e:
        console.print(f"❌ Initialization failed: {e}", style="red")
        return


if __name__ == "__main__":
    main()
