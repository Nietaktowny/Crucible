from argparse import ArgumentParser
from pathlib import Path
import logging

from rich.traceback import install
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table
from rich.json import JSON

from crucible.workflow.loader import WorkflowLoader
from crucible.runner import run_workflow, WorkflowRunResult
from crucible.workflow.registry import StepsRegistry

logger = logging.getLogger(__name__)

install(show_locals=True)


class CrucibleCli:
    def parse_args(self):
        parser = ArgumentParser(description="Crucible CLI")
        subparsers = parser.add_subparsers(dest="command")

        run_parser = subparsers.add_parser("run", help="Run workflow")
        run_parser.add_argument("--workflow", "-w", required=True, type=Path)
        run_parser.add_argument("--inspect", "-i", default=False, action='store_true')

        available_parser = subparsers.add_parser(
            "available-steps",
            help="List available registered step keys",
        )

        return parser.parse_args()

    def run(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
            handlers=[
                RichHandler(
                    rich_tracebacks=True,
                    show_path=False,
                )
            ],
        )

        args = self.parse_args()
        logger.info("Running Crucible CLI")

        if args.command == "run":
            self.run_workflow(args.workflow, inspect=args.inspect)
            return

        if args.command == "available-steps":
            self.list_available_steps()
            return

        raise ValueError("No command provided. Use: run, add-step, remove-step, list-steps.")

    def run_workflow(self, workflow_path: Path, inspect: bool = False):
        result = run_workflow(
            workflow_path=workflow_path,
            print_plan=inspect,
            inspect=inspect,
            preview_limit=100
        )
        
        if inspect and result.preview is not None:
            self._print_statistics(result)
            
            self._print_preview(result)

    def list_available_steps(self):
        registry = StepsRegistry()
        console = Console()

        for step in registry.list_step_keys():
            console.print(JSON.from_data(step))
                
    def _print_preview(self, result: WorkflowRunResult):
        if result.preview is None:
            logger.info("No preview available. Run with --inspect.")
            return

        console = Console()

        table = Table(title="Workflow Result Preview")

        for column in result.preview.columns:
            table.add_column(str(column))

        for row in result.preview.iter_rows():
            table.add_row(*[str(value) for value in row])

        console.print(table)

        if result.row_count is not None:
            console.print(f"[bold]Row count:[/bold] {result.row_count}")
            
    def _print_statistics(self, result: WorkflowRunResult):
        console = Console()

        stats = result.statistics

        table = Table(title="Workflow Runtime Statistics")

        table.add_column("Metric", style="bold")
        table.add_column("Value")

        table.add_row("Run ID", result.run_id)
        table.add_row("Status", result.status.value)
        table.add_row("Success", str(result.success))
        table.add_row("Total steps", str(stats.total_steps))
        table.add_row("System steps", str(stats.system_steps))

        table.add_row(
            "Started at",
            stats.started_at.isoformat(sep=" ", timespec="seconds")
            if stats.started_at
            else "-"
        )

        table.add_row(
            "Ended at",
            stats.ended_at.isoformat(sep=" ", timespec="seconds")
            if stats.ended_at
            else "-"
        )

        table.add_row("Total time", f"{stats.total_time:.4f} s")

        if result.row_count is not None:
            table.add_row("Row count", str(result.row_count))

        if result.error is not None:
            table.add_row("Error", str(result.error))

        console.print(table)