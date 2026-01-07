"""CLI commands for trace observability"""
import click
import json
from agentic_sdk.observability import AgentTracer


@click.group()
def traces():
    """View and analyze execution traces"""
    pass


@traces.command()
@click.option('--agent-id', help='Filter by agent ID')
@click.option('--success/--failed', default=None, help='Filter by success status')
@click.option('--limit', default=10, type=int, help='Number of traces to show')
def list(agent_id, success, limit):
    """List recent traces"""
    tracer = AgentTracer()
    
    traces = tracer.query_traces(
        agent_id=agent_id,
        success=success,
        limit=limit
    )
    
    if not traces:
        click.echo("\nNo traces found")
        return
    
    click.echo(f"\nRecent Traces (showing {len(traces)}):")
    click.echo("-" * 80)
    
    for trace in traces:
        status = "SUCCESS" if trace['success'] else "FAILED"
        status_color = "green" if trace['success'] else "red"
        
        click.echo(f"\n{trace['trace_id']}")
        click.echo(f"  Agent: {trace['agent_id']}")
        click.echo(f"  Task: {trace['task']}")
        click.echo(f"  Duration: {trace['duration_seconds']:.3f}s")
        click.secho(f"  Status: {status}", fg=status_color)
        if trace['error']:
            click.secho(f"  Error: {trace['error']}", fg='red')
    
    click.echo()


@traces.command()
@click.argument('trace_id')
def show(trace_id):
    """Show detailed trace information"""
    tracer = AgentTracer()
    
    details = tracer.get_trace_details(trace_id)
    
    if not details:
        click.echo(f"Trace '{trace_id}' not found", err=True)
        return
    
    trace = details['trace']
    spans = details['spans']
    metrics = details['metrics']
    
    # Trace overview
    click.echo(f"\nTrace: {trace['trace_id']}")
    click.echo("=" * 80)
    click.echo(f"Agent: {trace['agent_id']}")
    click.echo(f"Session: {trace['session_id']}")
    click.echo(f"Task: {trace['task']}")
    click.echo(f"Duration: {trace['duration_seconds']:.3f}s")
    
    status = "SUCCESS" if trace['success'] else "FAILED"
    status_color = "green" if trace['success'] else "red"
    click.secho(f"Status: {status}", fg=status_color)
    
    if trace['error']:
        click.secho(f"Error: {trace['error']}", fg='red')
    
    # Metadata
    if trace['metadata']:
        metadata = json.loads(trace['metadata'])
        click.echo(f"\nMetadata:")
        for key, value in metadata.items():
            click.echo(f"  {key}: {value}")
    
    # Spans
    click.echo(f"\nSpans ({len(spans)}):")
    click.echo("-" * 80)
    
    for span in spans:
        attrs = json.loads(span['attributes'])
        click.echo(f"\n{span['name']}")
        click.echo(f"  Duration: {span['duration_seconds']:.3f}s")
        click.echo(f"  Started: {span['start_time']}")
        
        if attrs:
            click.echo(f"  Attributes:")
            for key, value in attrs.items():
                click.echo(f"    {key}: {value}")
    
    # Metrics
    if metrics:
        click.echo(f"\nMetrics ({len(metrics)}):")
        click.echo("-" * 80)
        
        for metric in metrics:
            tags = json.loads(metric['tags'])
            tag_str = ""
            if tags:
                tag_str = " (" + ", ".join(f"{k}={v}" for k, v in tags.items()) + ")"
            
            click.echo(f"  {metric['metric_name']}: {metric['metric_value']}{tag_str}")
    
    click.echo()


@traces.command()
@click.option('--agent-id', help='Filter by agent ID')
@click.option('--limit', default=100, type=int, help='Number of traces to analyze')
def stats(agent_id, limit):
    """Show trace statistics"""
    tracer = AgentTracer()
    
    traces = tracer.query_traces(agent_id=agent_id, limit=limit)
    
    if not traces:
        click.echo("\nNo traces found")
        return
    
    # Calculate stats
    total = len(traces)
    successful = sum(1 for t in traces if t['success'])
    failed = total - successful
    
    durations = [t['duration_seconds'] for t in traces if t['duration_seconds']]
    avg_duration = sum(durations) / len(durations) if durations else 0
    min_duration = min(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    
    click.echo(f"\nTrace Statistics (last {total} traces):")
    click.echo("=" * 80)
    
    if agent_id:
        click.echo(f"Agent: {agent_id}")
    
    click.echo(f"\nExecution Summary:")
    click.echo(f"  Total: {total}")
    click.secho(f"  Successful: {successful} ({successful/total*100:.1f}%)", fg='green')
    if failed > 0:
        click.secho(f"  Failed: {failed} ({failed/total*100:.1f}%)", fg='red')
    
    click.echo(f"\nDuration:")
    click.echo(f"  Average: {avg_duration:.3f}s")
    click.echo(f"  Min: {min_duration:.3f}s")
    click.echo(f"  Max: {max_duration:.3f}s")
    
    # Most common tasks
    task_counts = {}
    for trace in traces:
        task = trace['task']
        task_counts[task] = task_counts.get(task, 0) + 1
    
    if task_counts:
        click.echo(f"\nMost Common Tasks:")
        for task, count in sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            click.echo(f"  {count}x: {task}")
    
    click.echo()


@traces.command()
@click.confirmation_option(prompt='Are you sure you want to clear all traces?')
def clear():
    """Clear all traces (WARNING: irreversible)"""
    import os
    
    if os.path.exists("traces.db"):
        os.remove("traces.db")
        click.echo("All traces cleared")
    else:
        click.echo("No traces to clear")
