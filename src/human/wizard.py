"""
InteractiveWizard - Terminal wizard for collecting user inputs.

This module provides an interactive command-line interface for collecting
all required inputs for the tailoring orchestration workflow, including:
- Job posting URLs
- Input file paths (resumes, guidelines, company culture)
- Configuration parameters
- Output directory preferences

The wizard provides a guided experience with validation, defaults, and
confirmation before proceeding with orchestration.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class InteractiveWizard:
    """
    Interactive terminal wizard for collecting user inputs.

    This wizard guides users through the input collection process with:
    - Rich terminal formatting and colors
    - Input validation with helpful error messages
    - Sensible defaults for all configuration parameters
    - Summary confirmation before proceeding

    Example:
        ```python
        wizard = InteractiveWizard()
        inputs = await wizard.run()

        # Access collected inputs
        job_urls = inputs['job_urls']
        file_paths = inputs['input_file_paths']
        config_params = inputs['config_params']
        output_dir = inputs['output_dir']
        ```
    """

    def __init__(self):
        """Initialize the InteractiveWizard with console and logger."""
        self.console = Console()
        self.logger = logging.getLogger(__name__)

    async def run(self) -> Dict[str, Any]:
        """
        Run the interactive wizard to collect all inputs.

        Steps:
        1. Display welcome banner
        2. Collect job posting URLs
        3. Collect file paths for inputs
        4. Collect configuration parameters
        5. Display summary and request confirmation
        6. Return collected data

        Returns:
            Dict[str, Any]: Collected inputs containing:
                - job_urls: List[str] - Job posting URLs
                - input_file_paths: Dict[str, str] - Paths to input files
                    - master_resume: Path to master resume
                    - resume_guidelines: Path to resume best practices
                    - cover_letter_guidelines: Path to cover letter best practices
                    - company_culture: Path to company culture report
                - config_params: Dict[str, Any] - Configuration parameters
                    - max_iterations: Max refinement iterations
                    - quality_threshold: Quality acceptance threshold
                    - agent_pool_size: Max concurrent agents
                    - ai_detection_threshold: AI detection threshold
                - output_dir: Path - Base output directory

        Raises:
            KeyboardInterrupt: If user cancels the wizard
        """
        try:
            # Step 1: Welcome
            self._display_welcome()

            # Step 2: Collect job URLs
            job_urls = self._collect_job_urls()

            # Step 3: Collect file paths
            input_file_paths = self._collect_file_paths()

            # Step 4: Collect configuration
            config_params = self._collect_config()

            # Step 5: Output directory
            output_dir = self._collect_output_dir()

            # Assemble all inputs
            inputs = {
                "job_urls": job_urls,
                "input_file_paths": input_file_paths,
                "config_params": config_params,
                "output_dir": output_dir
            }

            # Step 6: Summary and confirmation
            self._display_summary(inputs)

            if not self._confirm():
                self.console.print("\n[yellow]Wizard cancelled by user.[/yellow]")
                raise KeyboardInterrupt("User cancelled wizard")

            self.console.print("\n[bold green]✓ Configuration complete![/bold green]\n")
            return inputs

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Wizard interrupted. Exiting...[/yellow]")
            raise

    def _display_welcome(self):
        """Display welcome banner with ASCII art and instructions."""
        welcome_text = Text()
        welcome_text.append("Resume & Cover Letter Tailoring System\n", style="bold cyan")
        welcome_text.append("━" * 50 + "\n", style="cyan")
        welcome_text.append("\nThis wizard will guide you through setting up a tailoring run.\n")
        welcome_text.append("You'll need to provide:\n")
        welcome_text.append("  • Job posting URLs\n", style="dim")
        welcome_text.append("  • Input file paths (resume, guidelines, company culture)\n", style="dim")
        welcome_text.append("  • Configuration parameters\n", style="dim")
        welcome_text.append("\nPress Ctrl+C at any time to cancel.\n", style="italic dim")

        self.console.print(Panel(welcome_text, border_style="cyan", padding=(1, 2)))
        self.console.print()

    def _collect_job_urls(self) -> List[str]:
        """
        Collect job posting URLs from the user.

        Returns:
            List[str]: List of job posting URLs (at least one)
        """
        self.console.print("[bold]Step 1/4: Job Posting URLs[/bold]")
        self.console.print("Enter the URLs of job postings you want to apply to.")
        self.console.print("(Enter each URL, then press Enter. Type 'done' when finished)\n")

        urls = []
        while True:
            if urls:
                prompt_text = f"Job URL #{len(urls) + 1} (or 'done')"
            else:
                prompt_text = "Job URL #1"

            url = Prompt.ask(prompt_text, default="done" if urls else None)

            if url.lower() == "done":
                if not urls:
                    self.console.print("[red]Error: You must provide at least one job URL.[/red]")
                    continue
                break

            # Basic URL validation
            if not url.startswith(("http://", "https://")):
                self.console.print(
                    "[yellow]Warning: URL should start with http:// or https://[/yellow]"
                )
                if not Confirm.ask("Add this URL anyway?", default=False):
                    continue

            urls.append(url)
            self.console.print(f"[green]✓[/green] Added: {url}")

        self.console.print(f"\n[green]Collected {len(urls)} job URL(s)[/green]\n")
        return urls

    def _collect_file_paths(self) -> Dict[str, str]:
        """
        Collect paths to input files with validation.

        Returns:
            Dict[str, str]: Dictionary of file paths for:
                - master_resume
                - resume_guidelines
                - cover_letter_guidelines
                - company_culture
        """
        self.console.print("[bold]Step 2/4: Input File Paths[/bold]")
        self.console.print("Provide paths to your input files.\n")

        file_paths = {}

        # Master Resume
        file_paths["master_resume"] = self._collect_file_path(
            "Master Resume",
            "Path to your master resume file (LaTeX or Markdown)",
            default="data/inputs/resume.md"
        )

        # Resume Guidelines
        file_paths["resume_guidelines"] = self._collect_file_path(
            "Resume Guidelines",
            "Path to resume best practices guidelines",
            default="data/inputs/resume_best_practices.md"
        )

        # Cover Letter Guidelines
        file_paths["cover_letter_guidelines"] = self._collect_file_path(
            "Cover Letter Guidelines",
            "Path to cover letter best practices guidelines",
            default="data/inputs/cover_letter_best_practices.md"
        )

        # Company Culture Report
        file_paths["company_culture"] = self._collect_file_path(
            "Company Culture Report",
            "Path to company culture research (optional)",
            default="data/inputs/company_culture.md",
            required=False
        )

        self.console.print("\n[green]All file paths collected[/green]\n")
        return file_paths

    def _collect_file_path(
        self,
        name: str,
        description: str,
        default: str,
        required: bool = True
    ) -> str:
        """
        Collect and validate a single file path.

        Args:
            name: Display name of the file
            description: Description for the user
            default: Default file path
            required: Whether the file must exist

        Returns:
            str: Validated file path (or empty string if optional and skipped)
        """
        while True:
            self.console.print(f"[cyan]{name}[/cyan]: {description}")
            path_str = Prompt.ask("  Path", default=default)

            if not path_str and not required:
                self.console.print("[dim]  Skipped (optional)[/dim]")
                return ""

            try:
                path = self._validate_file_path(path_str)
                self.console.print(f"[green]  ✓ Found: {path}[/green]")
                return str(path)
            except FileNotFoundError as e:
                self.console.print(f"[red]  ✗ {e}[/red]")
                if not required and not Confirm.ask("  Try again?", default=True):
                    return ""

    def _validate_file_path(self, path_str: str) -> Path:
        """
        Validate that a file exists and is accessible.

        Args:
            path_str: Path string to validate

        Returns:
            Path: Validated Path object

        Raises:
            FileNotFoundError: If file doesn't exist or isn't accessible
        """
        path = Path(path_str)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise FileNotFoundError(f"Path is not a file: {path}")

        return path.resolve()

    def _collect_config(self) -> Dict[str, Any]:
        """
        Collect configuration parameters with defaults.

        Returns:
            Dict[str, Any]: Configuration parameters:
                - max_iterations: int
                - quality_threshold: float
                - agent_pool_size: int or None
                - ai_detection_threshold: float
        """
        self.console.print("[bold]Step 3/4: Configuration Parameters[/bold]")
        self.console.print("Configure orchestration behavior (press Enter for defaults).\n")

        config = {}

        # Max iterations
        config["max_iterations"] = IntPrompt.ask(
            "[cyan]Max Iterations[/cyan] (refinement cycles per document)",
            default=10
        )

        # Quality threshold
        config["quality_threshold"] = FloatPrompt.ask(
            "[cyan]Quality Threshold[/cyan] (0.0-1.0, acceptance threshold)",
            default=0.8
        )

        # Agent pool size
        self.console.print(
            "[cyan]Agent Pool Size[/cyan] (max concurrent agents, or 0 for unlimited)"
        )
        pool_size = IntPrompt.ask("  Pool size", default=5)
        config["agent_pool_size"] = pool_size if pool_size > 0 else None

        # AI detection threshold
        config["ai_detection_threshold"] = FloatPrompt.ask(
            "[cyan]AI Detection Threshold[/cyan] (0.0-1.0, for cover letters)",
            default=0.999
        )

        self.console.print("\n[green]Configuration collected[/green]\n")
        return config

    def _collect_output_dir(self) -> Path:
        """
        Collect output directory path.

        Returns:
            Path: Base output directory
        """
        self.console.print("[bold]Step 4/4: Output Directory[/bold]")
        self.console.print("Where should outputs be saved?\n")

        output_str = Prompt.ask(
            "[cyan]Output directory[/cyan]",
            default="data"
        )

        output_dir = Path(output_str)
        self.console.print(f"[green]✓ Output directory: {output_dir.resolve()}[/green]\n")

        return output_dir

    def _display_summary(self, inputs: Dict[str, Any]):
        """
        Display summary of collected inputs and request confirmation.

        Args:
            inputs: All collected wizard inputs
        """
        self.console.print("\n" + "=" * 80)
        self.console.print("[bold cyan]Configuration Summary[/bold cyan]")
        self.console.print("=" * 80 + "\n")

        # Job URLs
        self.console.print("[bold]Job Posting URLs:[/bold]")
        for i, url in enumerate(inputs["job_urls"], 1):
            self.console.print(f"  {i}. {url}")
        self.console.print()

        # Input Files
        self.console.print("[bold]Input Files:[/bold]")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="dim")

        for key, path in inputs["input_file_paths"].items():
            name = key.replace("_", " ").title()
            display_path = path if path else "[italic]Not provided[/italic]"
            table.add_row(name, display_path)

        self.console.print(table)
        self.console.print()

        # Configuration
        self.console.print("[bold]Configuration:[/bold]")
        config_table = Table(show_header=False, box=None, padding=(0, 2))
        config_table.add_column("Parameter", style="cyan")
        config_table.add_column("Value", style="green")

        for key, value in inputs["config_params"].items():
            param_name = key.replace("_", " ").title()
            display_value = str(value) if value is not None else "Unlimited"
            config_table.add_row(param_name, display_value)

        self.console.print(config_table)
        self.console.print()

        # Output Directory
        self.console.print(f"[bold]Output Directory:[/bold] {inputs['output_dir']}")
        self.console.print("\n" + "=" * 80 + "\n")

    def _confirm(self) -> bool:
        """
        Request yes/no confirmation from user.

        Returns:
            bool: True if user confirms, False otherwise
        """
        return Confirm.ask(
            "[bold yellow]Proceed with this configuration?[/bold yellow]",
            default=True
        )
