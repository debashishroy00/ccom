"""MCP Memory Commands for CCOM CLI - Phase 1 Implementation

New CLI commands that use MCP Direct Integration to replace legacy Node.js system.
These commands bridge CCOM with MCP Memory Keeper via Claude.
"""

import click
from .mcp_integration import MCPDirectIntegration


@click.group(name='memory')
def memory_group():
    """Memory management commands (Phase 1: MCP Direct Integration)"""
    pass


@memory_group.command()
@click.argument('feature_name')
@click.argument('description')
@click.option('--status', default='active', help='Feature status (active, completed, archived)')
@click.option('--force', is_flag=True, help='Save even if duplicates exist')
def remember(feature_name, description, status, force):
    """Save feature to MCP Memory Keeper (replaces Node.js version)"""

    mcp = MCPDirectIntegration()

    if not force:
        # Check for duplicates
        print(f"\n🔍 Checking for existing '{feature_name}' features...")
        existing = mcp.check_feature_exists(feature_name)

        # Note: existing will be empty list in Phase 1, real check happens in Claude
        # This command will trigger Claude to perform the actual MCP search

        if len(existing) > 0:  # This won't trigger in Phase 1, but kept for future phases
            click.echo(f"⚠️ Warning: Found {len(existing)} similar features.")
            click.echo("Use --force to save anyway, or check existing features first.")
            return

    # Save to MCP via Claude
    click.echo(f"\n💾 Saving feature to MCP Memory Keeper...")
    success = mcp.save_feature(feature_name, description, status)

    if success:
        click.echo(f"✅ Requested MCP save for: {feature_name}")
        click.echo("🔄 Claude should execute the MCP operation above.")
    else:
        click.echo(f"❌ Failed to request MCP save for: {feature_name}")


@memory_group.command()
@click.option('--status', help='Filter by status (active, completed, archived)')
def list(status):
    """List all features from MCP Memory Keeper"""

    mcp = MCPDirectIntegration()

    click.echo(f"\n📋 Retrieving features from MCP Memory Keeper...")
    features = mcp.list_all_features(status)

    click.echo("🔄 Claude should display the feature list above.")


@memory_group.command()
@click.argument('feature_name')
def show(feature_name):
    """Show detailed feature context from MCP Memory Keeper"""

    mcp = MCPDirectIntegration()

    click.echo(f"\n📖 Getting context for: {feature_name}")
    context = mcp.get_feature_context(feature_name)

    click.echo("🔄 Claude should display the feature context above.")


@memory_group.command()
@click.argument('feature_name')
@click.argument('note')
@click.option('--type', 'note_type', default='note',
              type=click.Choice(['note', 'decision', 'issue', 'progress', 'next_step']),
              help='Type of context note')
def note(feature_name, note, note_type):
    """Add a contextual note to a feature"""

    mcp = MCPDirectIntegration()

    click.echo(f"\n📝 Adding {note_type} for {feature_name}...")
    success = mcp.save_context_note(feature_name, note, note_type)

    if success:
        click.echo(f"✅ Requested MCP save for {note_type}: {note}")
        click.echo("🔄 Claude should execute the MCP operation above.")
    else:
        click.echo(f"❌ Failed to save {note_type}")


@memory_group.command()
@click.argument('query')
@click.option('--limit', default=5, help='Maximum number of results')
def search(query, limit):
    """Search all context in MCP Memory Keeper"""

    mcp = MCPDirectIntegration()

    click.echo(f"\n🔍 Searching MCP Memory Keeper for: '{query}'")
    results = mcp.search_context(query, limit)

    click.echo("🔄 Claude should display the search results above.")


@memory_group.command()
@click.option('--name', help='Custom checkpoint name')
@click.option('--description', help='Checkpoint description')
def checkpoint(name, description):
    """Create a checkpoint of current project state"""

    mcp = MCPDirectIntegration()

    click.echo(f"\n💾 Creating MCP Memory Keeper checkpoint...")
    checkpoint_name = mcp.create_checkpoint(name, description)

    if checkpoint_name:
        click.echo(f"✅ Requested checkpoint creation: {checkpoint_name}")
        click.echo("🔄 Claude should execute the MCP operation above.")
    else:
        click.echo("❌ Failed to request checkpoint creation")


@memory_group.command()
def summary():
    """Show intelligent project summary from MCP Memory Keeper"""

    mcp = MCPDirectIntegration()

    click.echo(f"\n📊 Getting project summary from MCP Memory Keeper...")
    summary = mcp.get_project_summary()

    click.echo("🔄 Claude should display the project summary above.")


@memory_group.command()
def migrate():
    """Migrate legacy memory.json to MCP Memory Keeper (Future Phase)"""

    click.echo("🔄 Migration command will be implemented in Phase 2")
    click.echo("📋 Current Phase 1 focuses on direct MCP integration")
    click.echo("💡 Legacy data migration coming in Phase 2")


@memory_group.command()
def validate():
    """Validate MCP Memory Keeper integration"""

    click.echo("🔍 Validating MCP Memory Keeper integration...")

    mcp = MCPDirectIntegration()

    # Test basic functionality
    click.echo(f"✅ Project name: {mcp.project_name}")
    click.echo("✅ MCP Direct Integration initialized")

    # Test a simple operation
    click.echo("\n🧪 Testing MCP save operation...")
    test_success = mcp.save_feature("test_validation", "Test feature for MCP validation", "test")

    if test_success:
        click.echo("✅ MCP Direct Integration working correctly")
        click.echo("🔄 Check above for Claude's MCP operation execution")
    else:
        click.echo("❌ MCP Direct Integration test failed")


# Export for CLI integration
def add_memory_commands(cli):
    """Add MCP memory commands to existing CLI"""
    cli.add_command(memory_group)