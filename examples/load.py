"""Install editable example workflows into the current Crucible workspace."""

from pathlib import Path

import yaml

from crucible_workspace.exceptions import WorkflowAlreadyExistsError
from crucible_workspace.paths import get_workspace_dir
from crucible_workspace.store import WorkflowStore


def load_examples(examples_dir: Path | None = None) -> None:
    examples_dir = examples_dir or Path(__file__).resolve().parent
    output_dir = get_workspace_dir().resolve() / "example-output"
    output_dir.mkdir(parents=True, exist_ok=True)
    store = WorkflowStore()

    for source in sorted((examples_dir / "workflows").glob("*.yaml")):
        workflow = yaml.safe_load(source.read_text(encoding="utf-8"))
        for step in workflow["steps"]:
            if step["key"] == "read_csv":
                step["parameters"]["path"] = str(
                    examples_dir / step["parameters"]["path"]
                )
            elif step["key"] == "write_csv":
                step["parameters"]["path"] = str(
                    output_dir / Path(step["parameters"]["path"]).name
                )
        try:
            store.create_workflow(
                source.stem, yaml.safe_dump(workflow, sort_keys=False)
            )
        except WorkflowAlreadyExistsError:
            print(f"Skipped {source.stem}: already exists (edits preserved)")
        else:
            print(f"Loaded {source.stem}")

    print(f"Example exports: {output_dir}")


if __name__ == "__main__":
    load_examples()
