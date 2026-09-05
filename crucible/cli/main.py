from argparse import ArgumentParser, Namespace
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
    """Command-line entry point for running workflows and inspecting steps.

    Instantiated and invoked by `crucible/__main__.py` (`python -m crucible`)
    and by `crucible_server`'s console script; not used by the FastAPI
    server or GUI at runtime.
    """

    def parse_args(self) -> Namespace:
        """Parse `sys.argv` into a namespace with a `command` and its options.

        Supports two subcommands: `run` (execute a workflow file, with
        `--workflow`/`-w` required and `--inspect`/`-i` optional) and
        `available-steps` (list registered step keys).

        Returns:
            Namespace: Parsed arguments, as returned by `ArgumentParser.parse_args`.
        """
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
        """Configure logging and dispatch to the requested subcommand.

        Raises:
            ValueError: If no recognized subcommand was provided.
        """
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
        """Run a workflow file and, if `inspect` is set, print its result.

        Args:
            workflow_path (Path): Path to the workflow YAML file to run.
            inspect (bool, optional): If true, also pretty-print the compiled
                execution plan and, once run, the result's statistics and
                output preview. Defaults to False.
        """
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
        """Print the JSON Schema of every step registered in `StepsRegistry`."""
        registry = StepsRegistry()
        console = Console()

        for step in registry.list_step_keys():
            console.print(JSON.from_data(step))

    def _print_preview(self, result: WorkflowRunResult):
        """Render a run result's preview rows as a Rich table.

        Args:
            result (WorkflowRunResult): Run result whose `preview` (a list of
                row dicts) should be printed. If `None`, prints a hint to
                re-run with `--inspect` instead.
        """
        if result.preview is None:
            logger.info("No preview available. Run with --inspect.")
            return

        console = Console()

        table = Table(title="Workflow Result Preview")

        columns = list(result.preview[0].keys()) if result.preview else []

        for column in columns:
            table.add_column(str(column))

        for row in result.preview:
            table.add_row(*[str(row.get(column, "")) for column in columns])

        console.print(table)

        if result.row_count is not None:
            console.print(f"[bold]Row count:[/bold] {result.row_count}")

    def _print_statistics(self, result: WorkflowRunResult):
        """Render a run result's runtime statistics as a Rich table.

        Args:
            result (WorkflowRunResult): Run result to summarize.
        """
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
            table.add_row("Error", f"{result.error.step_name}: {result.error.error}")

        console.print(table)
