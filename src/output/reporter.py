"""Report generation for video processing results."""
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from loguru import logger


def create_success_report(results: Dict[str, Any], output_dir: Path) -> None:
    """
    Create SUCCESS.md or FAILURE.md based on actual results.
    
    Args:
        results: Processing results dictionary
        output_dir: Directory to save report
    """
    total = results['total']
    success = results['success']
    failed = total - success
    
    if success == total:
        # Complete success
        report = f"""# Video Generation Report - SUCCESS

## Summary
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Total Videos**: {total}
- **Successful**: {success}
- **Failed**: {failed}
- **Total Cost**: ${results['cost']:.2f}

## Output Location
{output_dir}

## Cost Breakdown
- Videos generated: {success}
- Average cost per video: ${results['cost'] / success:.2f}
- Total cost: ${results['cost']:.2f}

## Status
✅ All videos generated successfully!
"""
        report_path = output_dir / "SUCCESS.md"
        report_path.write_text(report)
        logger.info(f"Success report saved: {report_path}")
        
    else:
        # Partial or complete failure
        status_emoji = "⚠️" if success > 0 else "❌"
        status_msg = f"{status_emoji} {failed}/{total} videos failed"
        
        report = f"""# Video Generation Report - FAILURE

## Summary
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Total Videos**: {total}
- **Successful**: {success}
- **Failed**: {failed}
- **Total Cost**: ${results['cost']:.2f}

## Output Location
{output_dir}

## Cost Breakdown
- Videos generated: {success}
- Average cost per video: ${results['cost'] / max(success, 1):.2f}
- Total cost: ${results['cost']:.2f}

## Status
{status_msg}

## Next Steps
1. Check the run log for error details
2. Verify profile configuration
3. Confirm API access and quotas
4. Re-run after fixing issues
"""
        report_path = output_dir / "FAILURE.md"
        report_path.write_text(report)
        logger.error(f"Failure report saved: {report_path}")


def create_cost_report(results: Dict[str, Any], output_dir: Path) -> None:
    """
    Create cost_report.md with detailed cost breakdown.
    
    Args:
        results: Processing results dictionary
        output_dir: Directory to save report
    """
    report = f"""# Cost Report

## Video Generation Costs

| Metric | Value |
|--------|-------|
| Videos Generated | {results['success']} |
| Average Cost per Video | ${results['cost'] / max(results['success'], 1):.2f} |
| **Total Cost** | **${results['cost']:.2f}** |

## Generation Time
- Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Notes
- Pricing is determined by profile configuration
- Failed attempts are not charged
- Costs are in USD
"""
    
    report_path = output_dir / "cost_report.md"
    report_path.write_text(report)
    logger.info(f"Cost report saved: {report_path}")