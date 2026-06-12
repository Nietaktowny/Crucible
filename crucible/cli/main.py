from argparse import ArgumentParser
from pathlib import Path
import logging

from rich.traceback import install
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table

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

        add_parser = subparsers.add_parser("add-step", help="Add step template to workflow")
        add_parser.add_argument("--workflow", "-w", required=True, type=Path)
        add_parser.add_argument("step_key", help="Step key, for example: filter_rows")
        add_parser.add_argument(
            "--index",
            "-i",
            type=int,
            default=None,
            help="Insert step at index. If omitted, step is appended.",
        )

        remove_parser = subparsers.add_parser("remove-step", help="Remove step from workflow")
        remove_parser.add_argument("--workflow", "-w", required=True, type=Path)
        remove_parser.add_argument("index", type=int, help="Step index to remove")

        list_parser = subparsers.add_parser("list-steps", help="List workflow steps")
        list_parser.add_argument("--workflow", "-w", required=True, type=Path)

        available_parser = subparsers.add_parser(
            "available-steps",
            help="List available registered step keys",
        )

        shell_parser = subparsers.add_parser("shell", help="Open workflow editing shell")
        shell_parser.add_argument("--workflow", "-w", required=True, type=Path)

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

        if args.command == "add-step":
            self.add_step(args.workflow, args.step_key, args.index)
            return

        if args.command == "remove-step":
            self.remove_step(args.workflow, args.index)
            return

        if args.command == "list-steps":
            self.list_steps(args.workflow)
            return

        if args.command == "available-steps":
            self.list_available_steps()
            return
        
        if args.command == "shell":
            self.shell(args.workflow)
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

    def add_step(self, workflow_path: Path, step_key: str, index: int | None = None):
        loader = WorkflowLoader()
        registry = StepsRegistry()

        raw_workflow = loader.load_raw(workflow_path)
        raw_workflow.setdefault("steps", [])

        step_template = registry.get_step_template(step_key)

        if index is None:
            raw_workflow["steps"].append(step_template)
            logger.info("Added step '%s' at the end.", step_key)
        else:
            if index < 0 or index > len(raw_workflow["steps"]):
                raise IndexError(f"Step index out of range: {index}")

            raw_workflow["steps"].insert(index, step_template)
            logger.info("Added step '%s' at index %s.", step_key, index)

        loader.save_raw(raw_workflow, workflow_path)

    def remove_step(self, workflow_path: Path, index: int):
        loader = WorkflowLoader()
        raw_workflow = loader.load_raw(workflow_path)

        steps = raw_workflow.get("steps", [])

        if index < 0 or index >= len(steps):
            raise IndexError(f"Step index out of range: {index}")

        removed_step = steps.pop(index)
        loader.save_raw(raw_workflow, workflow_path)

        logger.info(
            "Removed step at index %s: %s",
            index,
            removed_step.get("key", "<unknown>"),
        )

    def list_steps(self, workflow_path: Path):
        loader = WorkflowLoader()
        raw_workflow = loader.load_raw(workflow_path)

        steps = raw_workflow.get("steps", [])

        if not steps:
            logger.info("Workflow has no steps.")
            return

        for index, step in enumerate(steps):
            logger.info("%s: %s", index, step.get("key", "<unknown>"))

    def list_available_steps(self):
        registry = StepsRegistry()

        for step_key in registry.list_step_keys():
            logger.info(step_key)
            
    def shell(self, workflow_path: Path):
        loader = WorkflowLoader()
        registry = StepsRegistry()

        raw_workflow = loader.load_raw(workflow_path)

        logger.info("Opened workflow shell for: %s", workflow_path)
        logger.info("Commands: list, available, add <step_key> [index], remove <index>, save, run, exit")

        dirty = False

        while True:
            try:
                command = input("crucible> ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if not command:
                continue

            parts = command.split()
            action = parts[0]

            try:
                if action in {"exit", "quit", "q"}:
                    if dirty:
                        answer = input("Unsaved changes. Save before exit? [y/N] ").strip().lower()
                        if answer == "y":
                            loader.save_raw(raw_workflow, workflow_path)
                            logger.info("Saved workflow.")
                    break

                elif action in {"help", "h"}:
                    print(
                        "Commands:\n"
                        "  list\n"
                        "  available\n"
                        "  add <step_key> [index]\n"
                        "  remove <index>\n"
                        "  save\n"
                        "  run\n"
                        "  exit"
                    )

                elif action == "list":
                    steps = raw_workflow.get("steps", [])

                    if not steps:
                        logger.info("Workflow has no steps.")
                        continue

                    for index, step in enumerate(steps):
                        logger.info("%s: %s", index, step.get("key", "<unknown>"))

                elif action == "available":
                    for step_key in registry.list_step_keys():
                        logger.info(step_key)

                elif action == "add":
                    if len(parts) < 2:
                        logger.error("Usage: add <step_key> [index]")
                        continue

                    step_key = parts[1]
                    index = int(parts[2]) if len(parts) >= 3 else None

                    raw_workflow.setdefault("steps", [])
                    step_template = registry.get_step_template(step_key)

                    if index is None:
                        raw_workflow["steps"].append(step_template)
                        logger.info("Added step '%s' at the end.", step_key)
                    else:
                        if index < 0 or index > len(raw_workflow["steps"]):
                            raise IndexError(f"Step index out of range: {index}")

                        raw_workflow["steps"].insert(index, step_template)
                        logger.info("Added step '%s' at index %s.", step_key, index)

                    dirty = True

                elif action == "remove":
                    if len(parts) != 2:
                        logger.error("Usage: remove <index>")
                        continue

                    index = int(parts[1])
                    steps = raw_workflow.get("steps", [])

                    if index < 0 or index >= len(steps):
                        raise IndexError(f"Step index out of range: {index}")

                    removed_step = steps.pop(index)
                    logger.info("Removed step %s: %s", index, removed_step.get("key", "<unknown>"))
                    dirty = True

                elif action == "save":
                    loader.save_raw(raw_workflow, workflow_path)
                    dirty = False
                    logger.info("Saved workflow.")

                elif action == "run":
                    loader.save_raw(raw_workflow, workflow_path)
                    dirty = False
                    logger.info("Saved workflow before run.")
                    self.run_workflow(workflow_path)

                else:
                    logger.error("Unknown command: %s", action)

            except Exception as exc:
                logger.error("%s", exc)
                
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