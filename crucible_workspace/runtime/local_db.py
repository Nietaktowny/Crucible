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
    def __init__(self) -> None:
        self._db_path = get_runtime_data_dir() / "crucible.sqlite"
        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

        RuntimeModelBase.metadata.create_all(self._engine)

    @event.listens_for(Engine, "connect")
    def configure_sqlite(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    def _pydantic_to_orm(self, model: ModelResult) -> OrmResult:
        error = model.error

        return OrmResult(
            run_id=model.run_id,
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
            status=ModelStatus(orm.status),
            preview=None,
            row_count=orm.row_count,
            error=error,
            statistics=statistics,
        )

    def add_result(self, result: ModelResult) -> str:
        with Session(self._engine) as session:
            orm = self._pydantic_to_orm(result)
            session.add(orm)
            session.commit()
            return orm.run_id

    def get_result(self, run_id: str) -> ModelResult | None:
        with Session(self._engine) as session:
            orm = session.get(OrmResult, run_id)

            if orm is None:
                return None

            return self._orm_to_pydantic(orm)

    def get_all_results(self) -> list[ModelResult]:
        with Session(self._engine) as session:
            statement = select(OrmResult).order_by(OrmResult.started_at.desc())
            rows = session.scalars(statement).all()

            return [self._orm_to_pydantic(row) for row in rows]

    def update_result(self, result: ModelResult) -> bool:
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
        with Session(self._engine) as session:
            orm = session.get(OrmResult, run_id)

            if orm is None:
                return False

            session.delete(orm)
            session.commit()
            return True

    def delete_all_results(self) -> int:
        with Session(self._engine) as session:
            rows = session.scalars(select(OrmResult)).all()
            count = len(rows)

            for row in rows:
                session.delete(row)

            session.commit()
            return count