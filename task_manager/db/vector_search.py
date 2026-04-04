"""AlloyDB vector search using pgvector and Google text-embedding-004."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Embedding dimension for text-embedding-004
EMBEDDING_DIM = 768


def _get_embedding(text: str) -> list[float]:
    """Generate embedding using Google's text-embedding-004 model via Vertex AI."""
    try:
        from google.cloud import aiplatform
        from vertexai.language_models import TextEmbeddingModel

        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    except Exception as exc:
        logger.error("Failed to generate embedding: %s", exc)
        return []


async def init_vector_extensions(engine: Any) -> None:
    """Enable pgvector extension and add embedding columns if not present.

    Run once at startup on AlloyDB. Safe to call multiple times (idempotent).
    """
    try:
        async with engine.begin() as conn:
            # Enable pgvector
            await conn.execute(
                __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
            )
            # Add embedding column to notes if not exists
            await conn.execute(__import__("sqlalchemy").text("""
                ALTER TABLE notes
                ADD COLUMN IF NOT EXISTS embedding vector(768)
            """))
            # Add embedding column to pathology_results if not exists
            await conn.execute(__import__("sqlalchemy").text("""
                ALTER TABLE pathology_results
                ADD COLUMN IF NOT EXISTS embedding vector(768)
            """))
            # Add embedding column to medication_schedules if not exists
            await conn.execute(__import__("sqlalchemy").text("""
                ALTER TABLE medication_schedules
                ADD COLUMN IF NOT EXISTS embedding vector(768)
            """))
            # Create vector indexes for fast similarity search
            await conn.execute(__import__("sqlalchemy").text("""
                CREATE INDEX IF NOT EXISTS notes_embedding_idx
                ON notes USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            await conn.execute(__import__("sqlalchemy").text("""
                CREATE INDEX IF NOT EXISTS pathology_results_embedding_idx
                ON pathology_results USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
        logger.info("Vector extensions and indexes initialized successfully")
    except Exception as exc:
        logger.warning("Vector extension init failed (may not be AlloyDB): %s", exc)


async def upsert_note_embedding(conn: Any, note_id: str, title: str, body: str) -> None:
    """Generate and store embedding for a note."""
    text = f"{title}\n{body}"
    embedding = _get_embedding(text)
    if not embedding:
        return
    from sqlalchemy import text
    await conn.execute(
        text("UPDATE notes SET embedding = :emb WHERE id = :id"),
        {"emb": str(embedding), "id": note_id},
    )


async def upsert_pathology_embedding(
    conn: Any, result_id: str, test_name: str, value: str, unit: str
) -> None:
    """Generate and store embedding for a pathology result."""
    text_content = f"{test_name}: {value} {unit}"
    embedding = _get_embedding(text_content)
    if not embedding:
        return
    from sqlalchemy import text
    await conn.execute(
        text("UPDATE pathology_results SET embedding = :emb WHERE id = :id"),
        {"emb": str(embedding), "id": result_id},
    )


async def semantic_search_notes(
    session_factory: Any,
    query: str,
    limit: int = 5,
) -> list[dict]:
    """Search notes using semantic similarity via AlloyDB vector search.

    Falls back to keyword search if embeddings are not available.

    Args:
        session_factory: SQLAlchemy async session factory.
        query: Natural language search query.
        limit: Maximum number of results to return.

    Returns:
        List of matching note dicts ordered by similarity.
    """
    query_embedding = _get_embedding(query)

    if not query_embedding:
        # Fallback to keyword search
        logger.warning("Embedding unavailable, falling back to keyword search")
        return await _keyword_search_notes(session_factory, query, limit)

    from sqlalchemy import text

    sql = text("""
        SELECT id, title, body, tags, created_at, updated_at,
               1 - (embedding <=> :query_vec::vector) AS similarity
        FROM notes
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :query_vec::vector
        LIMIT :limit
    """)

    try:
        async with session_factory() as session:
            result = await session.execute(
                sql,
                {"query_vec": str(query_embedding), "limit": limit},
            )
            rows = result.fetchall()
            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "body": row.body,
                    "tags": row.tags,
                    "similarity": float(row.similarity),
                }
                for row in rows
            ]
    except Exception as exc:
        logger.error("Vector search failed, falling back to keyword: %s", exc)
        return await _keyword_search_notes(session_factory, query, limit)


async def semantic_search_pathology(
    session_factory: Any,
    query: str,
    patient_id: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Search pathology results using semantic similarity.

    Useful for queries like 'show me abnormal hormone results' or
    'find my AMH test results'.

    Args:
        session_factory: SQLAlchemy async session factory.
        query: Natural language search query.
        patient_id: Optional patient filter.
        limit: Maximum results.

    Returns:
        List of matching pathology result dicts ordered by similarity.
    """
    query_embedding = _get_embedding(query)
    if not query_embedding:
        return []

    from sqlalchemy import text

    patient_filter = "AND po.patient_id = :patient_id" if patient_id else ""
    sql = text(f"""
        SELECT pr.id, pr.test_name, pr.value, pr.unit, pr.reference_range,
               pr.abnormal, pr.recorded_at, po.patient_id,
               1 - (pr.embedding <=> :query_vec::vector) AS similarity
        FROM pathology_results pr
        JOIN pathology_orders po ON pr.order_id = po.id
        WHERE pr.embedding IS NOT NULL
        {patient_filter}
        ORDER BY pr.embedding <=> :query_vec::vector
        LIMIT :limit
    """)

    params: dict = {"query_vec": str(query_embedding), "limit": limit}
    if patient_id:
        params["patient_id"] = patient_id

    try:
        async with session_factory() as session:
            result = await session.execute(sql, params)
            rows = result.fetchall()
            return [
                {
                    "id": row.id,
                    "test_name": row.test_name,
                    "value": row.value,
                    "unit": row.unit,
                    "reference_range": row.reference_range,
                    "abnormal": row.abnormal,
                    "recorded_at": str(row.recorded_at),
                    "patient_id": row.patient_id,
                    "similarity": float(row.similarity),
                }
                for row in rows
            ]
    except Exception as exc:
        logger.error("Pathology vector search failed: %s", exc)
        return []


async def _keyword_search_notes(
    session_factory: Any, keyword: str, limit: int
) -> list[dict]:
    """Fallback keyword search for notes."""
    from sqlalchemy import text
    sql = text("""
        SELECT id, title, body, tags, created_at, updated_at
        FROM notes
        WHERE LOWER(title) LIKE :kw OR LOWER(body) LIKE :kw
        LIMIT :limit
    """)
    async with session_factory() as session:
        result = await session.execute(
            sql, {"kw": f"%{keyword.lower()}%", "limit": limit}
        )
        rows = result.fetchall()
        return [
            {"id": r.id, "title": r.title, "body": r.body, "tags": r.tags}
            for r in rows
        ]
