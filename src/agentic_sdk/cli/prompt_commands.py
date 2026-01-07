"""CLI commands for prompt management"""
import click
from agentic_sdk.prompts import PromptManager, PromptStorage


@click.group()
def prompts():
    """Manage agent prompts"""
    pass


@prompts.command()
@click.argument('name')
def list_versions(name):
    """List all versions of a prompt"""
    storage = PromptStorage("prompts.db")
    manager = PromptManager(storage)
    
    versions = manager.list_versions(name)
    
    if not versions:
        click.echo(f"No versions found for prompt '{name}'")
        return
    
    click.echo(f"\nVersions of '{name}':")
    click.echo("-" * 60)
    
    for v in versions:
        active = "[ACTIVE]" if v['is_active'] else "        "
        click.echo(f"{active} v{v['version']} - {v['created_at']}")
        click.echo(f"         By: {v['created_by']}")
        if v['metadata'].get('description'):
            click.echo(f"         {v['metadata']['description']}")
        click.echo()


@prompts.command()
@click.argument('name')
@click.option('--version', type=int, help='Specific version (default: active)')
def show(name, version):
    """Show prompt content"""
    storage = PromptStorage("prompts.db")
    manager = PromptManager(storage)
    
    try:
        prompt = manager.get_prompt(name, version)
        click.echo(f"\nPrompt '{name}' version {version or 'active'}:")
        click.echo("=" * 60)
        click.echo(prompt)
        click.echo("=" * 60)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@prompts.command()
@click.argument('name')
@click.argument('version', type=int)
def activate(name, version):
    """Activate a specific prompt version"""
    storage = PromptStorage("prompts.db")
    manager = PromptManager(storage)
    
    try:
        manager.activate_version(name, version)
        click.echo(f"Activated '{name}' version {version}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@prompts.command()
@click.argument('name')
def rollback(name):
    """Rollback to previous version"""
    storage = PromptStorage("prompts.db")
    manager = PromptManager(storage)
    
    try:
        current = manager.storage.get_active_version(name)
        manager.rollback(name)
        new_version = manager.storage.get_active_version(name)
        click.echo(f"Rolled back '{name}' from v{current} to v{new_version}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@prompts.command()
@click.argument('name')
@click.argument('template')
@click.option('--created-by', default='system', help='Author name')
@click.option('--description', help='Version description')
def create(name, template, created_by, description):
    """Create a new prompt version"""
    storage = PromptStorage("prompts.db")
    manager = PromptManager(storage)
    
    # Simple variable extraction - find {variable_name} patterns
    import re
    variables = re.findall(r'\{(\w+)\}', template)
    
    metadata = {}
    if description:
        metadata['description'] = description
    
    version = manager.register_prompt(
        name=name,
        template=template,
        variables=variables,
        created_by=created_by,
        metadata=metadata
    )
    
    click.echo(f"Created '{name}' version {version}")
    if variables:
        click.echo(f"Variables: {', '.join(variables)}")
