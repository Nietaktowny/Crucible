from sqlalchemy import Engine, create_engine, event, select
from sqlalchemy.orm import Session

from crucible_workspace.paths import get_runtime_data_dir
from crucible_workspace.runtime.models import (
    _WorkflowRunResult as OrmResult,
    RuntimeModelBase,
)
from crucible.models import (
    WorkflowRunResult as ModelResult,
    WorkflowRuntimeStatistics as ModelStatistics,
    WorkflowErrorContext as ModelError,
    WorkflowStatus as ModelStatus,
)


class RuntimeDataStorage:
    """SQLite-backed store of workflow run history.

    Persists `crucible.models.WorkflowRunResult` instances to a local
    SQLite database (`<runtime_data_dir>/crucible.sqlite`), translating
    between the Pydantic model used by the engine/API and the flattened
    ORM row defined in `crucible_workspace.runtime.models`. Note that a run's
    preview rows are never stored here (see `is_preview`); only `PreviewCache`
    persists preview data.
    """

    def __init__(self) -> None:
        runtime_data_dir = get_runtime_data_dir()
        runtime_data_dir.mkdir(parents=True, exist_ok=True)

        self._db_path = runtime_data_dir / "crucible.sqlite"
        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

        RuntimeModelBase.metadata.create_all(self._engine)

    @event.listens_for(Engine, "connect")
    def configure_sqlite(dbapi_connection, connection_record) -> None:
        """Apply per-connection SQLite pragmas (foreign keys, WAL, busy timeout).

        Registered as a SQLAlchemy connect event so every new DB-API
        connection gets these settings, not just the first one.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    def _pydantic_to_orm(self, model: ModelResult) -> OrmResult:
        """Flatten a `WorkflowRunResult` into its ORM row representation.

        Args:
            model (ModelResult): Run result to convert.

        Returns:
            OrmResult: Equivalent ORM row, not yet attached to a session.
        """
        error = model.error

        return OrmResult(
            run_id=model.run_id,
            name=model.name,
            status=model.status.value,
            is_preview=model.preview is not None,
            row_count=model.row_count,
            is_error=error is not None,

            total_steps=model.statistics.total_steps,
            system_steps=model.statistics.system_steps,
            started_at=model.statistics.started_at,
            ended_at=model.statistics.ended_at,
            total_time=model.statistics.total_time,

            error=str(error.error) if error else None,
            errored_step_id=error.step_id if error else None,
            errored_step_name=error.step_name if error else None,
            errored_frame_schema=error.frame_schema if error else None,
        )

    def _orm_to_pydantic(self, orm: OrmResult) -> ModelResult:
        """Rebuild a `WorkflowRunResult` from its stored ORM row.

        The preview is always `None` on the returned model, since it is
        never persisted to this database. When `orm.is_error` is set, a
        synthetic `RuntimeError` is reconstructed from the stored message
        text (the original exception instance/traceback is not preserved).

        Args:
            orm (OrmResult): Stored ORM row to convert.

        Returns:
            ModelResult: Equivalent `WorkflowRunResult`, with `preview=None`.
        """
        statistics = ModelStatistics(
            total_steps=orm.total_steps,
            system_steps=orm.system_steps,
            started_at=orm.started_at,
            ended_at=orm.ended_at,
            total_time=orm.total_time,
        )

        error = None
        if orm.is_error:
            error = ModelError(
                error=RuntimeError(orm.error or "Unknown workflow error"),
                step_id=orm.errored_step_id or "",
                step_name=orm.errored_step_name or "",
                frame_schema=orm.errored_frame_schema,
            )

        return ModelResult(
            run_id=orm.run_id,
            name=orm.name,
            status=ModelStatus(orm.status),
            preview=None,
            row_count=orm.row_count,
            error=error,
            statistics=statistics,
        )

    def add_result(self, result: ModelResult) -> str:
        """Insert a new run result.

        Args:
            result (ModelResult): Run result to store.

        Returns:
            str: The stored run's `run_id`.
        """
        with Session(self._engine) as session:
            orm = self._pydantic_to_orm(result)
            session.add(orm)
            session.commit()
            return orm.run_id

    def get_result(self, run_id: str) -> ModelResult | None:
        """Fetch one run result by id.

        Args:
            run_id (str): Run identifier to look up.

        Returns:
            ModelResult | None: The run result, or `None` if not found.
        """
        with Session(self._engine) as session:
            orm = session.get(OrmResult, run_id)

            if orm is None:
                return None

            return self._orm_to_pydantic(orm)

    def get_all_results(self) -> list[ModelResult]:
        """Fetch every stored run result, most recently started first.

        Returns:
            list[ModelResult]: All stored run results.
        """
        with Session(self._engine) as session:
            statement = select(OrmResult).order_by(OrmResult.started_at.desc())
            rows = session.scalars(statement).all()

            return [self._orm_to_pydantic(row) for row in rows]

    def update_result(self, result: ModelResult) -> bool:
        """Update an existing run result in place.

        Args:
            result (ModelResult): Run result with updated fields; matched by `run_id`.

        Returns:
            bool: `True` if a matching row was found and updated, `False` otherwise.
        """
        with Session(self._engine) as session:
            existing = session.get(OrmResult, result.run_id)

            if existing is None:
                return False

            updated = self._pydantic_to_orm(result)

            existing.status = updated.status
            existing.is_preview = updated.is_preview
            existing.row_count = updated.row_count
            existing.is_error = updated.is_error

            existing.total_steps = updated.total_steps
            existing.system_steps = updated.system_steps
            existing.started_at = updated.started_at
            existing.ended_at = updated.ended_at
            existing.total_time = updated.total_time

            existing.error = updated.error
            existing.errored_step_id = updated.errored_step_id
            existing.errored_step_name = updated.errored_step_name
            existing.errored_frame_schema = updated.errored_frame_schema

            session.commit()
            return True

    def upsert_result(self, result: ModelResult) -> str:
        """Insert a run result, or update it in place if it already exists.

        Args:
            result (ModelResult): Run result to store or update.

        Returns:
            str: The run's `run_id`.
        """
        with Session(self._engine) as session:
            existing = session.get(OrmResult, result.run_id)

            if existing is None:
                orm = self._pydantic_to_orm(result)
                session.add(orm)
                session.commit()
                return orm.run_id

            updated = self._pydantic_to_orm(result)

            existing.status = updated.status
            existing.is_preview = updated.is_preview
            existing.row_count = updated.row_count
            existing.is_error = updated.is_error

            existing.total_steps = updated.total_steps
            existing.system_steps = updated.system_steps
            existing.started_at = updated.started_at
            existing.ended_at = updated.ended_at
            existing.total_time = updated.total_time

            existing.error = updated.error
            existing.errored_step_id = updated.errored_step_id
            existing.errored_step_name = updated.errored_step_name
            existing.errored_frame_schema = updated.errored_frame_schema

            session.commit()
            return result.run_id

    def delete_result(self, run_id: str) -> bool:
        """Delete one run result by id.

        Args:
            run_id (str): Run identifier to delete.

        Returns:
            bool: `True` if a row was deleted, `False` if none existed.
        """
        with Session(self._engine) as session:
            orm = session.get(OrmResult, run_id)

            if orm is None:
                return False

            session.delete(orm)
            session.commit()
            return True

    def delete_all_results(self) -> int:
        """Delete every stored run result.

        Returns:
            int: Number of rows deleted.
        """
        with Session(self._engine) as session:
            rows = session.scalars(select(OrmResult)).all()
            count = len(rows)

            for row in rows:
                session.delete(row)

            session.commit()
            return count
