from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import uuid
from typing import Any

from src.models.human_insight import CompanyProfileStored, HumanInsightStored, StructuredInsightItem
from src.repositories.base import CompanyProfileRepository, HumanInsightRepository

try:
    from sqlalchemy import JSON, DateTime, String, Text, UniqueConstraint, create_engine, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

    HAS_SQLALCHEMY = True
except Exception:  # pragma: no cover - fallback for restricted runtime
    HAS_SQLALCHEMY = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _stable_hash(company_id: str, seller_id: str, raw_text: str) -> str:
    norm = f"{company_id.strip().lower()}|{seller_id.strip().lower()}|{raw_text.strip().lower()}"
    return sha256(norm.encode("utf-8")).hexdigest()


if HAS_SQLALCHEMY:
    class Base(DeclarativeBase):
        pass


    class HumanInsightORM(Base):
        __tablename__ = "intel_human_insights"
        __table_args__ = (UniqueConstraint("insight_hash", name="uq_insight_hash"),)

        id: Mapped[str] = mapped_column(String(64), primary_key=True)
        company_id: Mapped[str] = mapped_column(String(120), index=True)
        seller_id: Mapped[str] = mapped_column(String(120))
        raw_text: Mapped[str] = mapped_column(Text)
        structured_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
        source: Mapped[str] = mapped_column(String(50))
        parser_version: Mapped[str] = mapped_column(String(20), default="v1")
        insight_hash: Mapped[str] = mapped_column(String(64), index=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


    class CompanyProfileORM(Base):
        __tablename__ = "intel_company_profiles"
        __table_args__ = (UniqueConstraint("company_id", "area", name="uq_company_area"),)

        id: Mapped[str] = mapped_column(String(64), primary_key=True)
        company_id: Mapped[str] = mapped_column(String(120), index=True)
        area: Mapped[str] = mapped_column(String(120), index=True)
        profile_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class _SQLAlchemyStorage:
    def __init__(self, db_path: str) -> None:
        if not HAS_SQLALCHEMY:  # pragma: no cover
            raise RuntimeError("SQLAlchemy no disponible")
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            future=True,
            connect_args={"check_same_thread": False},
        )
        self._session_factory = sessionmaker(self._engine, expire_on_commit=False, class_=Session)
        Base.metadata.create_all(self._engine)

    def save_human_insight(
        self,
        *,
        company_id: str,
        seller_id: str,
        raw_text: str,
        structured_payload: list[StructuredInsightItem],
        source: str,
        parser_version: str,
    ) -> HumanInsightStored:
        insight_hash = _stable_hash(company_id, seller_id, raw_text)
        payload = [item.model_dump() for item in structured_payload]
        with self._session_factory() as session:
            existing = session.execute(
                select(HumanInsightORM).where(HumanInsightORM.insight_hash == insight_hash)
            ).scalar_one_or_none()
            if existing:
                return HumanInsightStored(
                    id=existing.id,
                    company_id=existing.company_id,
                    seller_id=existing.seller_id,
                    raw_text=existing.raw_text,
                    structured_payload=[StructuredInsightItem.model_validate(row) for row in existing.structured_payload],
                    source=existing.source,
                    created_at=existing.created_at.isoformat(),
                    parser_version=existing.parser_version,
                )

            row = HumanInsightORM(
                id=str(uuid.uuid4()),
                company_id=company_id,
                seller_id=seller_id,
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
                seller_id=row.seller_id,
                raw_text=row.raw_text,
                structured_payload=[StructuredInsightItem.model_validate(item) for item in payload],
                source=row.source,
                created_at=row.created_at.isoformat(),
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
                    seller_id=row.seller_id,
                    raw_text=row.raw_text,
                    structured_payload=[StructuredInsightItem.model_validate(item) for item in row.structured_payload],
                    source=row.source,
                    created_at=row.created_at.isoformat(),
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
                    updated_at=row.updated_at.isoformat(),
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
                updated_at=fallback.updated_at.isoformat(),
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
                updated_at=row.updated_at.isoformat(),
            )


class _SQLite3Storage:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intel_human_insights (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    seller_id TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    structured_payload TEXT NOT NULL,
                    source TEXT NOT NULL,
                    parser_version TEXT NOT NULL,
                    insight_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intel_company_profiles (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    area TEXT NOT NULL,
                    profile_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(company_id, area)
                )
                """
            )
            conn.commit()

    def save_human_insight(
        self,
        *,
        company_id: str,
        seller_id: str,
        raw_text: str,
        structured_payload: list[StructuredInsightItem],
        source: str,
        parser_version: str,
    ) -> HumanInsightStored:
        insight_hash = _stable_hash(company_id, seller_id, raw_text)
        created_at = _utc_now().isoformat()
        payload = [item.model_dump() for item in structured_payload]
        with self._connect() as conn:
            current = conn.execute(
                "SELECT * FROM intel_human_insights WHERE insight_hash = ? LIMIT 1",
                (insight_hash,),
            ).fetchone()
            if current:
                structured = [StructuredInsightItem.model_validate(row) for row in json.loads(current["structured_payload"])]
                return HumanInsightStored(
                    id=current["id"],
                    company_id=current["company_id"],
                    seller_id=current["seller_id"],
                    raw_text=current["raw_text"],
                    structured_payload=structured,
                    source=current["source"],
                    created_at=current["created_at"],
                    parser_version=current["parser_version"],
                )

            row_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO intel_human_insights (
                    id, company_id, seller_id, raw_text, structured_payload, source, parser_version, insight_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    company_id,
                    seller_id,
                    raw_text,
                    json.dumps(payload, ensure_ascii=False),
                    source,
                    parser_version,
                    insight_hash,
                    created_at,
                ),
            )
            conn.commit()
            return HumanInsightStored(
                id=row_id,
                company_id=company_id,
                seller_id=seller_id,
                raw_text=raw_text,
                structured_payload=[StructuredInsightItem.model_validate(item) for item in payload],
                source=source,
                created_at=created_at,
                parser_version=parser_version,
            )

    def list_recent_human_insights(self, *, company_id: str, limit: int) -> list[HumanInsightStored]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM intel_human_insights
                WHERE company_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (company_id, max(1, int(limit))),
            ).fetchall()
            result: list[HumanInsightStored] = []
            for row in rows:
                structured = [StructuredInsightItem.model_validate(item) for item in json.loads(row["structured_payload"])]
                result.append(
                    HumanInsightStored(
                        id=row["id"],
                        company_id=row["company_id"],
                        seller_id=row["seller_id"],
                        raw_text=row["raw_text"],
                        structured_payload=structured,
                        source=row["source"],
                        created_at=row["created_at"],
                        parser_version=row["parser_version"],
                    )
                )
            return result

    def get_profile(self, *, company_id: str, area: str) -> CompanyProfileStored | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM intel_company_profiles
                WHERE company_id = ? AND area = ?
                LIMIT 1
                """,
                (company_id, area),
            ).fetchone()
            if row:
                return CompanyProfileStored(
                    company_id=row["company_id"],
                    area=row["area"],
                    profile_payload=json.loads(row["profile_payload"]),
                    updated_at=row["updated_at"],
                )
            fallback = conn.execute(
                """
                SELECT *
                FROM intel_company_profiles
                WHERE company_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (company_id,),
            ).fetchone()
            if not fallback:
                return None
            payload = json.loads(fallback["profile_payload"])
            payload.setdefault("notas", "Perfil parcial por empresa (area no mapeada)")
            return CompanyProfileStored(
                company_id=fallback["company_id"],
                area=fallback["area"],
                profile_payload=payload,
                updated_at=fallback["updated_at"],
            )

    def upsert_profile(self, *, company_id: str, area: str, profile_payload: dict) -> CompanyProfileStored:
        now = _utc_now().isoformat()
        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT id
                FROM intel_company_profiles
                WHERE company_id = ? AND area = ?
                LIMIT 1
                """,
                (company_id, area),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE intel_company_profiles
                    SET profile_payload = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (json.dumps(profile_payload, ensure_ascii=False), now, existing["id"]),
                )
                row_id = existing["id"]
            else:
                row_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO intel_company_profiles (id, company_id, area, profile_payload, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (row_id, company_id, area, json.dumps(profile_payload, ensure_ascii=False), now),
                )
            conn.commit()
            return CompanyProfileStored(
                company_id=company_id,
                area=area,
                profile_payload=profile_payload,
                updated_at=now,
            )


class SQLiteHumanInsightRepository(HumanInsightRepository):
    def __init__(self, db_path: str) -> None:
        self._storage = _SQLAlchemyStorage(db_path) if HAS_SQLALCHEMY else _SQLite3Storage(db_path)

    def save(
        self,
        *,
        company_id: str,
        seller_id: str,
        raw_text: str,
        structured_payload: list[StructuredInsightItem],
        source: str,
        parser_version: str = "v1",
    ) -> HumanInsightStored:
        return self._storage.save_human_insight(
            company_id=company_id,
            seller_id=seller_id,
            raw_text=raw_text,
            structured_payload=structured_payload,
            source=source,
            parser_version=parser_version,
        )

    def list_recent(self, *, company_id: str, limit: int = 5) -> list[HumanInsightStored]:
        return self._storage.list_recent_human_insights(company_id=company_id, limit=limit)


class SQLiteCompanyProfileRepository(CompanyProfileRepository):
    def __init__(self, db_path: str) -> None:
        self._storage = _SQLAlchemyStorage(db_path) if HAS_SQLALCHEMY else _SQLite3Storage(db_path)

    def get_profile(self, *, company_id: str, area: str) -> CompanyProfileStored | None:
        return self._storage.get_profile(company_id=company_id, area=area)

    def upsert_profile(self, *, company_id: str, area: str, profile_payload: dict) -> CompanyProfileStored:
        return self._storage.upsert_profile(company_id=company_id, area=area, profile_payload=profile_payload)
