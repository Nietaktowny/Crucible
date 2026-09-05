# Getting Started

Crucible needs **Python 3.13+** to run the engine/server, and **Node.js
18+** if you also want to run the GUI from source. If you'd rather skip
local installs entirely, see [Deployment](deployment.md) for the Docker
setup.

## 1. Install

```bash
git clone https://github.com/Nietaktowny/Crucible.git
cd Crucible

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

The `dev` extra pulls in `pytest` and the MkDocs toolchain used to build
this site; drop it for a runtime-only install.

## 2. Write a workflow

Workflows are plain YAML files. Save this as `first_workflow.yaml`:

```yaml
name: first_workflow
steps:
  - key: read_csv
    parameters:
      path: sales.csv
  - key: select_columns
    parameters:
      columns: [order_id, country, amount]
```

See [Writing workflows](workflows.md) for the full step catalog and the
YAML file's shape.

## 3. Run it

### From the CLI

```bash
python -m crucible run --workflow first_workflow.yaml --inspect
```

`--inspect` prints the compiled execution plan plus a preview and row count
of the result once it finishes.

### From the API + GUI

Start the backend:

```bash
uvicorn crucible_server.app:create_app --factory --reload
```

...or via the console entry point:

```bash
python -m crucible_server.main
```

The API is now live at `http://127.0.0.1:8000` (interactive docs at
`/docs`). Point requests at it with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{"name": "first_workflow", "content": "name: first_workflow\nsteps:\n  - key: read_csv\n    parameters:\n      path: sales.csv\n"}'

curl -X POST http://127.0.0.1:8000/api/v1/runs/workflows/first_workflow \
  -H "Content-Type: application/json" -d '{}'
```

To use the visual editor instead, run the frontend in a second terminal:

```bash
cd crucible_gui
npm install
npm run dev
```

Open `http://localhost:5173` — it talks to the backend above automatically.
(`npm run dev:full` from `crucible_gui/` starts both the backend and
frontend together, if your backend is installed under a local `.venv`.)

## Next steps

- [Writing workflows](workflows.md) — the full step catalog and YAML format.
- [Deployment](deployment.md) — run everything with Docker instead.
- [Development](development.md) — run the backend and frontend test suites.
