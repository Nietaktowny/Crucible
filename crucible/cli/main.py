from argparse import ArgumentParser
from pathlib import Path
import logging

from rich.traceback import install
from rich.logging import RichHandler

from crucible.workflow import WorkflowExecutor
from crucible.workflow.loader import WorkflowLoader
from crucible.workflow.preprocessor import WorkflowPreprocessor
from crucible.workflow.optimizer import WorkflowOptimizer
from crucible.workflow.compiler import WorkflowCompiler
from crucible.workflow.registry import StepsRegistry

logger = logging.getLogger(__name__)

install(show_locals=True)


class CrucibleCli:
    def parse_args(self):
        parser = ArgumentParser(description="Crucible CLI")
        subparsers = parser.add_subparsers(dest="command")

        run_parser = subparsers.add_parser("run", help="Run workflow")
        run_parser.add_argument("--workflow", "-w", required=True, type=Path)

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
            self.run_workflow(args.workflow)
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

    def run_workflow(self, workflow_path: Path):
        workflow_loader = WorkflowLoader()
        workflow = workflow_loader.load(workflow_path)

        preprocessor = WorkflowPreprocessor()
        workflow = preprocessor.preprocess(workflow)

        optimizer = WorkflowOptimizer()
        workflow = optimizer.optimize(workflow)

        compiler = WorkflowCompiler()
        workflow_execution_plan = compiler.compile(workflow)
        compiler.print_execution_plan(workflow_execution_plan)

        executor = WorkflowExecutor()
        executor.run(workflow_execution_plan)

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