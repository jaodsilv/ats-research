"""Standalone Best Practices Merger Application.

This module provides a CLI tool for merging theoretical best practices (R1) with
real-world analysis (R2) to generate comprehensive, actionable guidelines for
resumes or cover letters.

The tool uses an iterative merge process with quality validation:
1. Initial comprehensive merge via Claude API
2. Validation across 4 quality dimensions
3. Iterative refinement until quality threshold met
4. Final output with metadata and validation report

Usage:
    python -m src.merger_main \\
        --r1 path/to/theoretical.md \\
        --r2 path/to/real_world.md \\
        --document-type resume \\
        --region "North America" \\
        --role "Software Engineer" \\
        --level "Senior" \\
        --max-iterations 3 \\
        --quality-threshold 0.85
"""

import argparse
import sys
import asyncio
from pathlib import Path
from typing import Optional
import logging
import json

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from src.merger.merger_engine import MergerEngine

# Setup console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_markdown_file(file_path: Path) -> str:
    """Load markdown content from a file.

    Args:
        file_path: Path to the markdown file

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise IOError(f"Path is not a file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            raise ValueError(f"File is empty: {file_path}")

        return content

    except Exception as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


def save_merged_guidelines(content: str, output_path: Path) -> None:
    """Save merged guidelines to a file.

    Args:
        content: Merged guidelines content
        output_path: Path where to save the file

    Raises:
        IOError: If file can't be written
    """
    try:
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[green]✓[/green] Merged guidelines saved to: {output_path}")

    except Exception as e:
        raise IOError(f"Failed to write output file {output_path}: {e}")


def save_validation_report(
    validation_results: dict,
    metadata: dict,
    output_path: Path
) -> None:
    """Save validation report as JSON.

    Args:
        validation_results: Validation results from merge
        metadata: Additional metadata
        output_path: Path where to save the report

    Raises:
        IOError: If file can't be written
    """
    try:
        # Convert ValidationResult objects to dicts
        report = {
            "validation_results": {
                name: {
                    "passed": result.passed,
                    "score": result.score,
                    "coverage": result.coverage,
                    "details": result.details,
                    "issues": result.issues,
                }
                for name, result in validation_results.items()
            },
            "metadata": metadata
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        console.print(f"[green]✓[/green] Validation report saved to: {output_path}")

    except Exception as e:
        logger.warning(f"Failed to save validation report: {e}")


def display_results_summary(
    confidence_score: float,
    iterations: int,
    validation_results: dict,
    key_takeaways: list
) -> None:
    """Display summary of merge results.

    Args:
        confidence_score: Overall confidence score
        iterations: Number of iterations performed
        validation_results: Validation results dict
        key_takeaways: List of key takeaways
    """
    # Overall summary
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]Merge Complete![/bold cyan]")
    console.print("=" * 80 + "\n")

    console.print(f"[bold]Confidence Score:[/bold] {confidence_score:.1%}")
    console.print(f"[bold]Iterations:[/bold] {iterations}")
    console.print()

    # Validation results table
    table = Table(title="Validation Results")
    table.add_column("Validator", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Details", style="dim")

    for name, result in validation_results.items():
        status = "✓ PASS" if result.passed else "✗ FAIL"
        status_style = "green" if result.passed else "red"
        table.add_row(
            name.replace("_", " ").title(),
            f"{result.score:.1%}",
            f"[{status_style}]{status}[/{status_style}]",
            result.details
        )

    console.print(table)
    console.print()

    # Key takeaways
    if key_takeaways:
        console.print("[bold]Key Takeaways:[/bold]")
        for i, takeaway in enumerate(key_takeaways[:5], 1):
            console.print(f"  {i}. {takeaway}")
        if len(key_takeaways) > 5:
            console.print(f"  ... and {len(key_takeaways) - 5} more in the full document")
        console.print()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Merge theoretical best practices with real-world analysis using iterative refinement.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with defaults
  python -m src.merger_main \\
      --r1 data/research/resume_theoretical.md \\
      --r2 data/research/resume_real_world.md \\
      --document-type resume

  # Advanced usage with custom parameters
  python -m src.merger_main \\
      --r1 data/research/cover_letter_theoretical.md \\
      --r2 data/research/cover_letter_real_world.md \\
      --document-type cover_letter \\
      --region "North America" \\
      --role "Software Engineer" \\
      --level "Senior" \\
      --max-iterations 5 \\
      --quality-threshold 0.90 \\
      --verbose

Output Files:
  - {document_type}-merged.md: Final merged guidelines with metadata
  - {document_type}-validation-report.json: Detailed validation results
        """
    )

    # Required arguments
    parser.add_argument(
        '--r1', '--theoretical',
        dest='r1_path',
        type=Path,
        required=True,
        help='Path to R1 theoretical best practices markdown file'
    )

    parser.add_argument(
        '--r2', '--real-world',
        dest='r2_path',
        type=Path,
        required=True,
        help='Path to R2 real-world analysis markdown file'
    )

    parser.add_argument(
        '--document-type',
        dest='document_type',
        type=str,
        required=True,
        choices=['resume', 'cover_letter'],
        help='Type of document: resume or cover_letter'
    )

    # Optional arguments - Context
    parser.add_argument(
        '--region',
        type=str,
        default='Global',
        help='Geographic region (default: Global)'
    )

    parser.add_argument(
        '--role',
        type=str,
        default='General',
        help='Job role (default: General)'
    )

    parser.add_argument(
        '--level',
        type=str,
        default='All Levels',
        help='Seniority level (default: All Levels)'
    )

    # Optional arguments - Quality control
    parser.add_argument(
        '--max-iterations',
        dest='max_iterations',
        type=int,
        default=3,
        help='Maximum refinement iterations (default: 3)'
    )

    parser.add_argument(
        '--quality-threshold',
        dest='quality_threshold',
        type=float,
        default=0.85,
        help='Minimum confidence score to accept (0-1, default: 0.85)'
    )

    # Optional arguments - Output
    parser.add_argument(
        '--output',
        type=Path,
        help='Optional: Custom output file path (default: {document_type}-merged.md in R1 directory)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


async def main() -> int:
    """Main entry point for the merger tool.

    Returns:
        Exit code: 0 for success, 1 for error
    """
    try:
        # Parse arguments
        args = parse_arguments()

        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Display banner
        console.print(Panel(
            "[bold cyan]Best Practices Merger[/bold cyan]\n"
            "Iterative merge with quality validation",
            border_style="cyan"
        ))
        console.print()

        # Load input files
        console.print("[bold]Loading input files...[/bold]")
        r1_content = load_markdown_file(args.r1_path)
        console.print(f"[green]✓[/green] R1 loaded: {len(r1_content):,} characters")

        r2_content = load_markdown_file(args.r2_path)
        console.print(f"[green]✓[/green] R2 loaded: {len(r2_content):,} characters")
        console.print()

        # Determine output paths
        if args.output:
            output_path = args.output
        else:
            output_dir = args.r1_path.parent
            output_filename = f"{args.document_type}-merged.md"
            output_path = output_dir / output_filename

        report_path = output_path.with_suffix('.validation-report.json')

        # Display configuration
        console.print("[bold]Configuration:[/bold]")
        console.print(f"  Document Type: {args.document_type}")
        console.print(f"  Region: {args.region}")
        console.print(f"  Role: {args.role}")
        console.print(f"  Level: {args.level}")
        console.print(f"  Max Iterations: {args.max_iterations}")
        console.print(f"  Quality Threshold: {args.quality_threshold:.1%}")
        console.print(f"  Output: {output_path}")
        console.print()

        # Create merger engine
        console.print("[bold]Initializing merger engine...[/bold]")
        engine = MergerEngine(
            max_iterations=args.max_iterations,
            quality_threshold=args.quality_threshold
        )
        console.print("[green]✓[/green] Engine initialized")
        console.print()

        # Execute merge with progress indicator
        console.print("[bold]Executing iterative merge...[/bold]")
        console.print("[dim]This may take several minutes depending on iterations needed[/dim]\n")

        result = await engine.merge(
            r1_content=r1_content,
            r2_content=r2_content,
            document_type=args.document_type,
            region=args.region,
            role=args.role,
            level=args.level,
            verbose=args.verbose
        )

        # Save outputs
        console.print("\n[bold]Saving outputs...[/bold]")
        save_merged_guidelines(result.merged_guidelines, output_path)
        save_validation_report(
            result.validation_results,
            result.metadata,
            report_path
        )

        # Display summary
        display_results_summary(
            result.confidence_score,
            result.iterations_performed,
            result.validation_results,
            result.key_takeaways
        )

        console.print("=" * 80 + "\n")

        return 0

    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found:[/red] {e}", style="bold")
        return 1

    except ValueError as e:
        console.print(f"[red]✗ Invalid input:[/red] {e}", style="bold")
        return 1

    except IOError as e:
        console.print(f"[red]✗ IO error:[/red] {e}", style="bold")
        return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        return 1

    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}", style="bold")
        logger.exception("Detailed error:")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
