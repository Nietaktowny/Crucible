from argparse import ArgumentParser
from pathlib import Path
import logging

from rich.traceback import install
from rich.logging import RichHandler

from crucible.workflow import WorkflowExecutor
from crucible.workflow.loader import WorkflowLoader
from crucible.workflow.preprocessor import WorkflowPreprocessor
from crucible.workflow.optimizer import WorkflowOptimizer
from crucible.workflow.complier import WorkflowCompiler
from crucible.models import Workflow, IOConfig

logger = logging.getLogger(__name__)

install(show_locals=True)

class CrucibleCli:
    def __init__(self):
        pass
    
    def parse_args(self):
        parser = ArgumentParser(description="Crucible CLI")
        parser.add_argument("--input", "-i", help="Input file path", type=Path)
        parser.add_argument("--output", "-o", help="Output file path", type=Path)
        parser.add_argument("--workflow", "-w", help="Workflow file path", type=Path)
        return parser.parse_args()

    def run(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
            handlers=[
                RichHandler(
                    rich_tracebacks=True,
                    show_path=False
                )
            ]
        )
        
        args = self.parse_args()
        logger.info("Running Crucible CLI")
        
        workflow_loader = WorkflowLoader()
        workflow = workflow_loader.load(args.workflow)
        logger.info(f"Loaded workflow: '{workflow.name}'")
        logger.debug(f"Loaded workflow details: '{workflow.model_dump()}'")
        
        preprocessor = WorkflowPreprocessor()
        workflow = preprocessor.preprocess(workflow)
        
        optimizer = WorkflowOptimizer()
        workflow = optimizer.optimize(workflow)
        
        compiler = WorkflowCompiler()
        workflow_execution_plan = compiler.compile(workflow)

        executor = WorkflowExecutor()
        executor.run(workflow_execution_plan)