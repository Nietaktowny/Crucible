from pathlib import Path
import json
import yaml
import logging

from rich.pretty import Pretty

from crucible.models import Workflow

logger = logging.getLogger(__name__)
class WorkflowLoader:
    def load(self, path: str | Path) -> Workflow:
        """Load and parse Workflow configuration from file.

        Args:
            path (str | Path): Path to workflow configuration file.

        Raises:
            FileNotFoundError: If workflow file is not found on specified path.

        Returns:
            Workflow: Parsed Workflow model.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Workflow file does not exist: {path}")

        raw_data = self._read_file(path)
        workflow = Workflow.model_validate(raw_data)
        logger.info(f"Loaded workflow: {workflow.name}")

        logger.debug(
            "Loaded workflow details:\n%s",
            json.dumps(
                workflow.model_dump(),
                indent=2,
                default=str,
            )
        )
        return workflow

    def load_raw(self, path: str | Path) -> dict:
        """Load workflow configuration file as raw dictionary.

        Args:
            path (str | Path): Path to workflow configuration file.

        Raises:
            FileNotFoundError: If workflow file is not found on specified path.

        Returns:
            dict: Workflow configuration as dictionary.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Workflow file does not exist: {path}")

        return self._read_file(path)

    def save_raw(self, raw_data: dict, path: str | Path):
        """Save raw Workflow data in dictionary format to YAML or JSON file.

        Supported suffixes:
        
        - .yaml, .yml
        - .json

        Args:
            raw_data (dict): Raw data to save.
            path (str | Path): Path of output file.

        Raises:
            ValueError: If suffix indicates unsupported workflow file format.
        """
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            path.write_text(
                yaml.safe_dump(
                    raw_data,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            return

        if suffix == ".json":
            path.write_text(
                json.dumps(
                    raw_data,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            return

        raise ValueError(
            f"Unsupported workflow file format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )

    def _read_file(self, path: Path) -> dict:
        """Read text workflow configuration file into dict.

        Supported formats:

        - .yaml, .yml
        - .json
        
        Args:
            path (Path): Path to file.

        Raises:
            ValueError: If file suffix indicates unsupported workflow configuration file format.

        Returns:
            dict: Parsed text data as dictionary.
        """
        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(path.read_text(encoding="utf-8"))

        if suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))

        raise ValueError(
            f"Unsupported workflow file format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )
        
    def save(self, workflow: Workflow, path: str | Path):
        """Save Workflow configuration to text file.
        
        Supported formats:
        
        - .yaml, .yml
        - .json

        Args:
            workflow (Workflow): Workflow configuration to save.
            path (str | Path): Output file path.

        Raises:
            ValueError: If file suffix indicates unsupported workflow configuration file format.
        """
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            path.write_text(yaml.safe_dump(workflow.model_dump()), encoding="utf-8")
            return

        if suffix == ".json":
            path.write_text(json.dumps(workflow.model_dump(), indent=2), encoding="utf-8")
            return

        raise ValueError(
            f"Unsupported workflow file format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )