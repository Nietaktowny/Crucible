# Playground examples

These small, synthetic CSV files and workflows ship with the repository.
They require no downloads, accounts or external services. All sample data
was written for Crucible and is covered by the repository's Apache-2.0
license. The café data uses a familiar dirty-sales shape; it is not copied
from Kaggle. The café cleanup is adapted from the workflow prepared in
Crucible, with portable input/output paths.

## Try them in Docker

From the repository root:

```bash
docker compose up --build -d
docker compose exec backend python /examples/load.py
```

Open [http://localhost:8080](http://localhost:8080) and refresh the workflow
list. Select an `example_` workflow, inspect successive steps in the data
table, edit filters or transformations, and run it to export results.

| Workflow | Input files | What to explore | Expected result |
| --- | --- | --- | --- |
| `example_cafe_cleanup` | `dirty_cafe_sales.csv` (20 rows) | Drop missing values, filter `ERROR`/`UNKNOWN` and allowed values, convert numbers and dates | 10 rows, total sales 43.50 |
| `example_cafe_summary` | Saved café cleanup + `cafe_menu.csv` (8 rows) | Reuse a workflow, join categories, group and sum | Drinks: 10 units / 21.50; Food: 8 units / 22.00 |
| `example_stock_cleanup` | `dirty_stock.csv` (8 rows) | Trim text, deduplicate, replace invalid values, drop/fill nulls, calculate stock value | 4 rows, total stock value 161.50 |

The café workflow deliberately keeps only complete rows matching its
configured allowed values. It does not repair every possible data error or
check that quantity times price matches the reported total. These are useful
exercises to try next. The stock workflow treats missing quantity/cost as
unusable and missing supplier as `Unspecified`.

The summary reads the latest **saved** café cleanup; save your edits there
before inspecting their effect in the summary. You do not need to run the
cleanup first, and reading it from the summary skips its export step.

Compose mounts this directory read-only at `/examples` in the backend.
`load.py` creates editable workflow copies in `/data/workflows`, resolves
input paths to `/examples/data`, and directs exports to
`/data/example-output`. Re-running it skips existing names so your edits
survive; delete an example workflow in the GUI and reload to reset it.
Loading does not run the workflows or overwrite existing exports.

After running the examples, copy exports to the host:

```bash
docker compose cp backend:/data/example-output ./example-output
```

Workspace copies and exports survive container recreation in the named
volume. `docker compose down -v` deletes them. The repository samples stay
unchanged. Arbitrary files on your computer still require their own mount
or transfer; see the [deployment guide](../docs/deployment.md#using-local-files-in-the-docker-test-deployment).

## Try them without Docker

With Crucible installed in your active Python environment, run from the
repository root:

```bash
python examples/load.py
```

This uses your normal Crucible workspace (or `CRUCIBLE_WORKSPACE_DIR` if
set), prints the export directory, and resolves sample inputs to absolute
paths in this checkout. Start the backend/GUI using the same workspace to
open the examples. YAML files under `workflows/` are templates for the loader;
load them before running the workspace copies through the GUI or CLI.
