"""
Agentic SDK Command Line Interface
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="agentic-sdk")
def cli():
    """
    Agentic SDK - Build enterprise AI agents with MCP control plane
    """
    pass


@cli.group()
def server():
    """Manage MCP server"""
    pass


@server.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, type=int, help="Server port")
@click.option("--max-concurrent", default=100, type=int, help="Max concurrent executions")
def start(host: str, port: int, max_concurrent: int):
    """Start MCP server"""
    
    async def _start():
        from agentic_sdk.mcp.server import MCPServer, MCPServerConfig
        
        console.print(f"\n[cyan]Starting MCP Server...[/cyan]")
        console.print(f"  Host: {host}")
        console.print(f"  Port: {port}")
        console.print(f"  Max concurrent: {max_concurrent}\n")
        
        config = MCPServerConfig(
            host=host,
            port=port,
            max_concurrent_executions=max_concurrent,
        )
        
        server = MCPServer(config=config)
        await server.start()
        
        console.print(f"[green]MCP Server started successfully[/green]")
        console.print(f"  Server ID: {server.config.server_id}\n")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            await server.stop()
            console.print("[green]Server stopped[/green]\n")
    
    try:
        asyncio.run(_start())
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)


@cli.group()
def tool():
    """Manage tools"""
    pass


@tool.command("list")
@click.option("--category", help="Filter by category")
def list_tools(category: Optional[str]):
    """List registered tools"""
    
    async def _list():
        from agentic_sdk.mcp.server import MCPServer
        
        # Start temporary server to list tools
        server = MCPServer()
        await server.start()
        
        # TODO: Load tools from config/directory
        # For now, register example tools
        from examples.tools.calculator_tool import CalculatorTool
        await server.register_tool(CalculatorTool())
        
        tools = await server.list_tools(category=category)
        
        if not tools:
            console.print("\n[yellow]No tools registered[/yellow]\n")
            await server.stop()
            return
        
        table = Table(title=f"\nRegistered Tools{f' (category: {category})' if category else ''}")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Version", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Description", style="white")
        
        for t in tools:
            table.add_row(
                t["name"],
                t["version"],
                t["category"],
                t["description"][:50] + "..." if len(t["description"]) > 50 else t["description"]
            )
        
        console.print(table)
        console.print()
        
        await server.stop()
    
    try:
        asyncio.run(_list())
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)


@cli.group()
def agent():
    """Manage and run agents"""
    pass


@agent.command()
@click.argument("task")
@click.option("--model", default="gpt-4", help="LLM model (future use)")
@click.option("--max-iterations", default=10, type=int, help="Max iterations")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def run(task: str, model: str, max_iterations: int, verbose: bool):
    """Run agent with a task"""
    
    async def _run():
        from agentic_sdk.mcp.server import MCPServer
        from agentic_sdk.runtime.basic_agent import BasicAgent
        from agentic_sdk.core.interfaces.agent import AgentConfig
        from examples.tools.calculator_tool import CalculatorTool
        
        console.print(f"\n[cyan]Running agent...[/cyan]")
        console.print(f"  Task: {task}")
        console.print(f"  Model: {model}")
        console.print(f"  Max iterations: {max_iterations}\n")
        
        # Start MCP server
        mcp = MCPServer()
        await mcp.start()
        
        # Register tools
        await mcp.register_tool(CalculatorTool())
        # TODO: Auto-discover and load tools
        
        if verbose:
            tools = await mcp.list_tools()
            console.print(f"[dim]Loaded {len(tools)} tools[/dim]\n")
        
        # Create agent
        config = AgentConfig(
            name="cli_agent",
            model=model,
            system_prompt="You are a helpful assistant",
            max_iterations=max_iterations,
        )
        
        agent = BasicAgent(config=config, mcp_server=mcp)
        
        # Execute task
        with console.status("[bold cyan]Agent working..."):
            result = await agent.execute(task)
        
        # Display results
        if result.success:
            console.print(f"\n[green]Success![/green]")
            console.print(f"\n[bold]Output:[/bold]")
            console.print(result.output)
        else:
            console.print(f"\n[red]Failed[/red]")
            console.print(f"Error: {result.error}")
        
        if verbose:
            console.print(f"\n[dim]Iterations: {result.iterations}[/dim]")
            console.print(f"[dim]Tools used: {', '.join(result.tools_invoked)}[/dim]")
            console.print(f"[dim]Duration: {result.duration_seconds:.3f}s[/dim]")
        
        console.print()
        
        await mcp.stop()
    
    try:
        asyncio.run(_run())
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    import agentic_sdk
    console.print(f"\n[cyan]Agentic SDK[/cyan] version [bold]{agentic_sdk.__version__}[/bold]")
    console.print(f"Author: {agentic_sdk.__author__}")
    console.print(f"License: {agentic_sdk.__license__}\n")


@cli.command()
def info():
    """Show system information"""
    import sys
    import platform
    
    table = Table(title="\nSystem Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("Platform", platform.platform())
    table.add_row("Architecture", platform.machine())
    
    console.print(table)
    console.print()


if __name__ == "__main__":
    cli()


# Import prompt commands
from agentic_sdk.cli.prompt_commands import prompts

# Register prompt commands group
cli.add_command(prompts)


# Import registry commands
from agentic_sdk.cli.registry_commands import registry

# Register registry commands group
cli.add_command(registry)
