"""CLI commands for A/B testing"""
import click
from agentic_sdk.ab_testing import ABTester
from agentic_sdk.prompts import PromptManager, PromptStorage


@click.group()
def ab_test():
    """Manage A/B tests for prompts"""
    pass


@ab_test.command()
@click.argument('prompt_name')
@click.argument('version_a', type=int)
@click.argument('version_b', type=int)
@click.option('--split', default=50, type=int, help='% traffic to version A (0-100)')
@click.option('--min-samples', default=100, type=int, help='Minimum samples per version')
@click.option('--description', help='Test description')
def start(prompt_name, version_a, version_b, split, min_samples, description):
    """Start a new A/B test"""
    tester = ABTester()
    
    metadata = {}
    if description:
        metadata['description'] = description
    
    try:
        test_id = tester.start_test(
            prompt_name=prompt_name,
            version_a=version_a,
            version_b=version_b,
            split_percentage=split,
            min_samples=min_samples,
            metadata=metadata
        )
        
        click.echo(f"\nA/B Test Started")
        click.echo(f"  Test ID: {test_id}")
        click.echo(f"  Prompt: {prompt_name}")
        click.echo(f"  Version A: {version_a} ({split}% traffic)")
        click.echo(f"  Version B: {version_b} ({100-split}% traffic)")
        click.echo(f"  Min Samples: {min_samples} per version")
        click.echo()
        
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@ab_test.command()
@click.argument('test_id')
def results(test_id):
    """Show results for an A/B test"""
    tester = ABTester()
    
    try:
        results = tester.get_results(test_id)
        
        click.echo(f"\nA/B Test Results")
        click.echo("=" * 60)
        click.echo(f"Test ID: {test_id}")
        
        # Version A
        click.echo(f"\nVersion A:")
        v_a = results.version_a_stats
        if v_a:
            click.echo(f"  Requests: {v_a['total_requests']}")
            click.echo(f"  Success Rate: {v_a['success_rate']*100:.1f}%")
            click.echo(f"  Avg Duration: {v_a['avg_duration']:.3f}s")
            click.echo(f"  Total Cost: ${v_a['total_cost']:.4f}")
        else:
            click.echo("  No data yet")
        
        # Version B
        click.echo(f"\nVersion B:")
        v_b = results.version_b_stats
        if v_b:
            click.echo(f"  Requests: {v_b['total_requests']}")
            click.echo(f"  Success Rate: {v_b['success_rate']*100:.1f}%")
            click.echo(f"  Avg Duration: {v_b['avg_duration']:.3f}s")
            click.echo(f"  Total Cost: ${v_b['total_cost']:.4f}")
        else:
            click.echo("  No data yet")
        
        # Recommendation
        click.echo(f"\nRecommendation:")
        click.echo(f"  {results.recommendation}")
        click.echo(f"  Confidence: {results.confidence*100:.1f}%")
        click.echo()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@ab_test.command()
@click.option('--status', type=click.Choice(['running', 'completed', 'cancelled']), 
              help='Filter by status')
def list(status):
    """List all A/B tests"""
    tester = ABTester()
    
    tests = tester.list_tests(status=status)
    
    if not tests:
        click.echo("\nNo tests found")
        return
    
    status_filter = f" (status: {status})" if status else ""
    click.echo(f"\nA/B Tests{status_filter}:")
    click.echo("-" * 80)
    
    for test in tests:
        click.echo(f"\n{test['test_id']}")
        click.echo(f"  Prompt: {test['prompt_name']}")
        click.echo(f"  Versions: {test['version_a']} vs {test['version_b']}")
        click.echo(f"  Split: {test['split_percentage']}% / {100-test['split_percentage']}%")
        click.echo(f"  Status: {test['status']}")
        click.echo(f"  Started: {test['started_at']}")
        if test['ended_at']:
            click.echo(f"  Ended: {test['ended_at']}")
        if test['winner_version']:
            click.echo(f"  Winner: Version {test['winner_version']}")
    
    click.echo()


@ab_test.command()
@click.argument('test_id')
@click.option('--promote-winner/--no-promote', default=False,
              help='Automatically activate winning version')
def complete(test_id, promote_winner):
    """Complete an A/B test"""
    tester = ABTester()
    
    try:
        winner = tester.complete_test(test_id, promote_winner=promote_winner)
        
        click.echo(f"\nTest completed: {test_id}")
        
        if promote_winner and winner:
            click.echo(f"Winner (version {winner}) promoted to active")
            
            # Also update prompt manager
            prompt_storage = PromptStorage("prompts.db")
            prompt_manager = PromptManager(prompt_storage)
            
            # Get prompt name from test
            test_data = tester.storage.conn.execute(
                "SELECT prompt_name FROM ab_tests WHERE test_id = ?",
                (test_id,)
            ).fetchone()
            
            if test_data:
                prompt_name = test_data['prompt_name']
                prompt_manager.activate_version(prompt_name, winner)
                click.echo(f"Prompt '{prompt_name}' version {winner} is now active")
        else:
            click.echo("No winner promoted")
        
        click.echo()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@ab_test.command()
@click.argument('test_id')
def cancel(test_id):
    """Cancel a running A/B test"""
    tester = ABTester()
    
    try:
        tester.cancel_test(test_id)
        click.echo(f"Test cancelled: {test_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@ab_test.command()
@click.argument('test_id')
@click.argument('split', type=int)
def update_split(test_id, split):
    """Update traffic split for running test"""
    tester = ABTester()
    
    if split < 0 or split > 100:
        click.echo("Split must be between 0 and 100", err=True)
        return
    
    try:
        tester.storage.conn.execute("""
            UPDATE ab_tests 
            SET split_percentage = ?
            WHERE test_id = ? AND status = 'running'
        """, (split, test_id))
        tester.storage.conn.commit()
        
        click.echo(f"\nUpdated split for test {test_id}")
        click.echo(f"New split: {split}% / {100-split}%")
        click.echo()
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
