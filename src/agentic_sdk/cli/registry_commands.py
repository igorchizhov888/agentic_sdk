"""CLI commands for tool registry management"""
import click
from agentic_sdk.registry import ToolRegistry


@click.group()
def registry():
    """Manage tool registry"""
    pass


@registry.command()
@click.option('--path', default='examples/tools', help='Path to scan for tools')
def discover(path):
    """Auto-discover tools in a directory"""
    reg = ToolRegistry()
    
    click.echo(f"\nScanning {path} for tools...")
    discovered = reg.auto_discover(path)
    
    click.echo(f"\nDiscovered {len(discovered)} tools:")
    for tool_name in discovered:
        click.echo(f"  - {tool_name}")
    
    click.echo()


@registry.command()
@click.option('--category', help='Filter by category')
def list(category):
    """List registered tools"""
    reg = ToolRegistry()
    tools = reg.list_tools(category=category)
    
    if not tools:
        click.echo("\nNo tools registered")
        return
    
    click.echo(f"\nRegistered Tools{f' (category: {category})' if category else ''}:")
    click.echo("-" * 60)
    
    for tool in tools:
        click.echo(f"\n{tool.name} (v{tool.version})")
        click.echo(f"  Category: {tool.category}")
        click.echo(f"  Description: {tool.description}")
        click.echo(f"  Tags: {', '.join(tool.tags)}")
    
    click.echo()


@registry.command()
@click.argument('tool_name')
def info(tool_name):
    """Show detailed tool information"""
    reg = ToolRegistry()
    metadata = reg.storage.get_tool(tool_name)
    
    if not metadata:
        click.echo(f"Tool '{tool_name}' not found", err=True)
        return
    
    click.echo(f"\nTool: {metadata.name}")
    click.echo("=" * 60)
    click.echo(f"Version: {metadata.version}")
    click.echo(f"Category: {metadata.category}")
    click.echo(f"Description: {metadata.description}")
    click.echo(f"Module: {metadata.module_path}")
    click.echo(f"Class: {metadata.class_name}")
    click.echo(f"Tags: {', '.join(metadata.tags)}")
    click.echo(f"Enabled: {metadata.enabled}")
    click.echo()


@registry.command()
@click.argument('agent_id')
@click.argument('tool_name')
def grant(agent_id, tool_name):
    """Grant agent access to a tool"""
    reg = ToolRegistry()
    
    # Check tool exists
    if not reg.storage.get_tool(tool_name):
        click.echo(f"Tool '{tool_name}' not found", err=True)
        return
    
    reg.storage.grant_tool_access(agent_id, tool_name)
    click.echo(f"Granted '{agent_id}' access to '{tool_name}'")


@registry.command()
@click.argument('agent_id')
@click.argument('tool_name')
def revoke(agent_id, tool_name):
    """Revoke agent access to a tool"""
    reg = ToolRegistry()
    reg.storage.revoke_tool_access(agent_id, tool_name)
    click.echo(f"Revoked '{agent_id}' access to '{tool_name}'")


@registry.command()
@click.argument('agent_id')
def show_permissions(agent_id):
    """Show tools available to an agent"""
    reg = ToolRegistry()
    tools = reg.get_tools_for_agent(agent_id)
    
    click.echo(f"\nTools available to '{agent_id}':")
    click.echo("-" * 60)
    
    if not tools:
        click.echo("(none)")
    else:
        for tool_name in tools:
            click.echo(f"  - {tool_name}")
    
    click.echo()
