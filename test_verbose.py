#!/usr/bin/env python3
"""Test script for verbose output functionality."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.verbose_output import VerboseContext, log_stage_emoji, show_error_with_retry
from src.utils.enhanced_logging import setup_dual_logging
import time


def test_verbose_output():
    """Test verbose output components."""
    
    print("Testing verbose output module...")
    print("=" * 60)
    
    # Test 1: Basic logging with emojis
    setup_dual_logging(enable_verbose=True)
    
    log_stage_emoji("starting", "Test starting...")
    log_stage_emoji("preparing", "Preparing test data...")
    log_stage_emoji("processing", "Processing test...")
    log_stage_emoji("complete", "Test complete!")
    
    # Test 2: Progress display
    with VerboseContext() as ctx:
        progress = ctx.progress
        task = progress.add_task("Test task", total=10, status="Starting...")
        
        with progress:
            for i in range(10):
                time.sleep(0.2)
                progress.update(task, advance=1, status=f"Step {i+1}/10")
                log_stage_emoji("processing", f"Processing item {i+1}")
    
    # Test 3: Error with retry
    try:
        raise ValueError("Test error for retry display")
    except Exception as e:
        show_error_with_retry(e, attempt=1, max_attempts=3, wait_time=3)
    
    print("=" * 60)
    print("Verbose output test complete!")
    
    # Test 4: Test with redirected output
    print("\nTesting with redirected output (this should still work)...")
    log_stage_emoji("complete", "Redirection test successful")


def test_terminal_sizes():
    """Test with different terminal sizes."""
    from rich.console import Console
    
    print("\nTesting terminal size detection...")
    console = Console()
    print(f"Terminal size: {console.width} x {console.height}")
    
    # Create a progress bar that adapts to terminal width
    from src.utils.verbose_output import create_progress_display
    progress = create_progress_display()
    
    with progress:
        task = progress.add_task("Adaptive progress bar", total=100)
        for i in range(100):
            time.sleep(0.01)
            progress.advance(task)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", choices=["basic", "terminal"], default="basic")
    args = parser.parse_args()
    
    if args.test == "basic":
        test_verbose_output()
    else:
        test_terminal_sizes()