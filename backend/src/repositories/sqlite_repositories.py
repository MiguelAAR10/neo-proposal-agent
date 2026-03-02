from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import uuid
from typing import Any

from src.models.human_insight import CompanyProfileStored, HumanInsightStored, StructuredInsightItem
from src.repositories.base import CompanyProfileRepository, HumanInsightRepository

try:
    from sqlalchemy import JSON, DateTime, Index, String, Text, UniqueConstraint, create_engine, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
    from sqlalchemy.pool import StaticPool

    HAS_SQLALCHEMY = True
    SQLALCHEMY_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover
    HAS_SQLALCHEMY = False
    SQLALCHEMY_IMPORT_ERROR = exc


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _stable_hash(company_id: str, author: str, raw_text: str) -> str:
    norm = f"{company_id.strip().lower()}|{author.strip().lower()}|{raw_text.strip().lower()}"
    return sha256(norm.encode("utf-8")).hexdigest()


def _to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.astimezone(timezone.utc).isoformat()


def _build_sqlite_url(db_value: str) -> str:
    raw = (db_value or "").strip()
    if raw.startswith("sqlite://"):
        return raw
    path = Path(raw).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


if HAS_SQLALCHEMY:
    class Base(DeclarativeBase):
        pass


    class HumanInsightORM(Base):
        __tablename__ = "intel_human_insights"
        __table_args__ = (
            UniqueConstraint("insight_hash", name="uq_insight_hash"),
            Index("ix_human_insights_company_created", "company_id", "created_at"),
            Index("ix_human_insights_created", "created_at"),
            Index("ix_human_insights_department", "department"),
        )

        id: Mapped[str] = mapped_column(String(64), primary_key=True)
        company_id: Mapped[str] = mapped_column(String(120), index=True)
        author: Mapped[str] = mapped_column(String(120), index=True)
        department: Mapped[str] = mapped_column(String(80), index=True)
        sentiment: Mapped[str] = mapped_column(String(40), index=True)
        raw_text: Mapped[str] = mapped_column(Text)
        structured_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
        source: Mapped[str] = mapped_column(String(50))
        parser_version: Mapped[str] = mapped_column(String(20), default="v1")
        insight_hash: Mapped[str] = mapped_column(String(64), index=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


    class CompanyProfileORM(Base):
        __tablename__ = "intel_company_profiles"
        __table_args__ = (
            UniqueConstraint("company_id", "area", name="uq_company_area"),
            Index("ix_profiles_company_updated", "company_id", "updated_at"),
        )

        id: Mapped[str] = mapped_column(String(64), primary_key=True)
        company_id: Mapped[str] = mapped_column(String(120), index=True)
        area: Mapped[str] = mapped_column(String(120), index=True)
        profile_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class _SQLAlchemyStorage:
    def __init__(self, db_url_or_path: str) -> None:
        if not HAS_SQLALCHEMY:  # pragma: no cover
            raise RuntimeError("SQLAlchemy es obligatorio para SQLite repositories") from SQLALCHEMY_IMPORT_ERROR

        database_url = _build_sqlite_url(db_url_or_path)
        engine_kwargs: dict[str, Any] = {
            "future": True,
            "connect_args": {"check_same_thread": False},
        }
        if database_url.endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool

        self._engine = create_engine(database_url, **engine_kwargs)
        self._session_factory = sessionmaker(self._engine, expire_on_commit=False, class_=Session)
        Base.metadata.create_all(bind=self._engine)
        self._ensure_sqlite_schema_compat()

    def _ensure_sqlite_schema_compat(self) -> None:
        # Sin Alembic en MVP: compatibilidad mínima para tablas existentes.
        with self._engine.begin() as conn:
            rows = conn.exec_driver_sql("PRAGMA table_info('intel_human_insights')").fetchall()
            columns = {str(row[1]) for row in rows}
            if "author" not in columns:
                conn.exec_driver_sql("ALTER TABLE intel_human_insights ADD COLUMN author VARCHAR(120)")
                conn.exec_driver_sql("UPDATE intel_human_insights SET author = 'Unknown' WHERE author IS NULL")
            if "department" not in columns:
                conn.exec_driver_sql("ALTER TABLE intel_human_insights ADD COLUMN department VARCHAR(80)")
                conn.exec_driver_sql("UPDATE intel_human_insights SET department = 'General' WHERE department IS NULL")
            if "sentiment" not in columns:
                conn.exec_driver_sql("ALTER TABLE intel_human_insights ADD COLUMN sentiment VARCHAR(40)")
                conn.exec_driver_sql("UPDATE intel_human_insights SET sentiment = 'Neutral' WHERE sentiment IS NULL")

            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_human_insights_company_created ON intel_human_insights (company_id, created_at)"
            )
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_human_insights_created ON intel_human_insights (created_at)"
            )
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_human_insights_department ON intel_human_insights (department)"
            )

    def save_human_insight(
        self,
        *,
        company_id: str,
        author: str,
        department: str,
        sentiment: str,
        raw_text: str,
        structured_payload: list[StructuredInsightItem],
        source: str,
        parser_version: str,
    ) -> HumanInsightStored:
        insight_hash = _stable_hash(company_id, author, raw_text)
        payload = [item.model_dump() for item in structured_payload]

        with self._session_factory() as session:
            existing = session.execute(
                select(HumanInsightORM).where(HumanInsightORM.insight_hash == insight_hash)
            ).scalar_one_or_none()
            if existing:
                return HumanInsightStored(
                    id=existing.id,
                    company_id=existing.company_id,
                    author=existing.author,
                    department=existing.department,
                    sentiment=existing.sentiment,
                    raw_text=existing.raw_text,
                    structured_payload=[StructuredInsightItem.model_validate(row) for row in existing.structured_payload],
                    source=existing.source,
                    created_at=_to_iso(existing.created_at),
                    parser_version=existing.parser_version,
                )

            row = HumanInsightORM(
                id=str(uuid.uuid4()),
                company_id=company_id,
                author=author,
                department=department,
                sentiment=sentiment,
                raw_text=raw_text,
                structured_payload=payload,
                source=source,
                parser_version=parser_version,
                insight_hash=insight_hash,
                created_at=_utc_now(),
            )
            session.add(row)
            session.commit()

            return HumanInsightStored(
                id=row.id,
                company_id=row.company_id,
                author=row.author,
                department=row.department,
                sentiment=row.sentiment,
                raw_text=row.raw_text,
                structured_payload=[StructuredInsightItem.model_validate(item) for item in payload],
                source=row.source,
                created_at=_to_iso(row.created_at),
                parser_version=row.parser_version,
            )

    def list_recent_human_insights(self, *, company_id: str, limit: int) -> list[HumanInsightStored]:
        with self._session_factory() as session:
            rows = session.execute(
                select(HumanInsightORM)
                .where(HumanInsightORM.company_id == company_id)
                .order_by(HumanInsightORM.created_at.desc())
                .limit(max(1, int(limit)))
            ).scalars().all()

            return [
                HumanInsightStored(
                    id=row.id,
                    company_id=row.company_id,
                    author=row.author,
                    department=row.department,
                    sentiment=row.sentiment,
                    raw_text=row.raw_text,
                    structured_payload=[StructuredInsightItem.model_validate(item) for item in row.structured_payload],
                    source=row.source,
                    created_at=_to_iso(row.created_at),
                    parser_version=row.parser_version,
                )
                for row in rows
            ]

    def get_profile(self, *, company_id: str, area: str) -> CompanyProfileStored | None:
        with self._session_factory() as session:
            row = session.execute(
                select(CompanyProfileORM)
                .where(CompanyProfileORM.company_id == company_id, CompanyProfileORM.area == area)
                .limit(1)
            ).scalar_one_or_none()
            if row:
                return CompanyProfileStored(
                    company_id=row.company_id,
                    area=row.area,
                    profile_payload=dict(row.profile_payload or {}),
                    updated_at=_to_iso(row.updated_at),
                )

            fallback = session.execute(
                select(CompanyProfileORM)
                .where(CompanyProfileORM.company_id == company_id)
                .order_by(CompanyProfileORM.updated_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            if not fallback:
                return None

            payload = dict(fallback.profile_payload or {})
            payload.setdefault("notas", "Perfil parcial por empresa (area no mapeada)")
            return CompanyProfileStored(
                company_id=fallback.company_id,
                area=fallback.area,
                profile_payload=payload,
                updated_at=_to_iso(fallback.updated_at),
            )

    def upsert_profile(self, *, company_id: str, area: str, profile_payload: dict) -> CompanyProfileStored:
        with self._session_factory() as session:
            row = session.execute(
                select(CompanyProfileORM).where(
                    CompanyProfileORM.company_id == company_id,
                    CompanyProfileORM.area == area,
                )
            ).scalar_one_or_none()
            now = _utc_now()

            if row:
                row.profile_payload = profile_payload
                row.updated_at = now
            else:
                row = CompanyProfileORM(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    area=area,
                    profile_payload=profile_payload,
                    updated_at=now,
                )
                session.add(row)
            session.commit()

            return CompanyProfileStored(
                company_id=row.company_id,
                area=row.area,
                profile_payload=dict(row.profile_payload or {}),
                updated_at=_to_iso(row.updated_at),
            )


class SQLiteHumanInsightRepository(HumanInsightRepository):
    def __init__(self, db_url_or_path: str) -> None:
        self._storage = _SQLAlchemyStorage(db_url_or_path)

    def save(
        self,
        *,
        company_id: str,
        author: str,
        department: str,
        sentiment: str,
        raw_text: str,
        structured_payload: list[StructuredInsightItem],
        source: str,
        parser_version: str = "v1",
    ) -> HumanInsightStored:
        return self._storage.save_human_insight(
            company_id=company_id,
            author=author,
            department=department,
            sentiment=sentiment,
            raw_text=raw_text,
            structured_payload=structured_payload,
            source=source,
            parser_version=parser_version,
        )

    def list_recent(self, *, company_id: str, limit: int = 5) -> list[HumanInsightStored]:
        return self._storage.list_recent_human_insights(company_id=company_id, limit=limit)


class SQLiteCompanyProfileRepository(CompanyProfileRepository):
    def __init__(self, db_url_or_path: str) -> None:
        self._storage = _SQLAlchemyStorage(db_url_or_path)

    def get_profile(self, *, company_id: str, area: str) -> CompanyProfileStored | None:
        return self._storage.get_profile(company_id=company_id, area=area)

    def upsert_profile(self, *, company_id: str, area: str, profile_payload: dict) -> CompanyProfileStored:
        return self._storage.upsert_profile(company_id=company_id, area=area, profile_payload=profile_payload)
