"""Session store interface and in-memory implementation.

Provides an abstract ``SessionStore`` base class and a ``dict``-backed
``InMemorySessionStore`` for Phase 1.  The interface is designed so that
Phase 2 backends (Redis, Firestore) can be dropped in without changing
call-sites.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ivf_advisor.models import Session


class SessionStore(ABC):
    """Abstract base class for session persistence backends."""

    @abstractmethod
    def create(self, session: Session) -> Session:
        """Persist a new session and return it.

        Args:
            session: The ``Session`` object to store.

        Returns:
            The stored ``Session`` (same object, allows chaining).

        Raises:
            ValueError: If a session with the same ``session_id`` already exists.
        """

    @abstractmethod
    def get(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            The ``Session`` if found, otherwise ``None``.
        """

    @abstractmethod
    def update(self, session: Session) -> Session:
        """Overwrite an existing session with updated data.

        Args:
            session: The updated ``Session`` object.

        Returns:
            The updated ``Session``.

        Raises:
            KeyError: If no session with ``session.session_id`` exists.
        """

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Remove a session and all associated data (including profile).

        After this call, ``get(session_id)`` MUST return ``None``.

        Args:
            session_id: The unique identifier of the session to remove.
        """


class InMemorySessionStore(SessionStore):
    """Thread-unsafe, in-process session store backed by a plain ``dict``.

    Suitable for Phase 1 (single-process CLI / Gradio UI).  All data is
    lost when the process exits.
    """

    def __init__(self) -> None:
        self._store: dict[str, Session] = {}

    # ------------------------------------------------------------------
    # SessionStore interface
    # ------------------------------------------------------------------

    def create(self, session: Session) -> Session:
        """Store a new session.

        Raises:
            ValueError: If ``session.session_id`` is already present.
        """
        if session.session_id in self._store:
            raise ValueError(
                f"Session '{session.session_id}' already exists. "
                "Use update() to modify an existing session."
            )
        self._store[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Return the session or ``None`` if not found."""
        return self._store.get(session_id)

    def update(self, session: Session) -> Session:
        """Replace the stored session with the provided one.

        Raises:
            KeyError: If ``session.session_id`` does not exist in the store.
        """
        if session.session_id not in self._store:
            raise KeyError(
                f"Session '{session.session_id}' not found. "
                "Use create() to add a new session."
            )
        self._store[session.session_id] = session
        return session

    def delete(self, session_id: str) -> None:
        """Remove the session entirely.

        Silently does nothing if the session does not exist, so callers
        do not need to guard with a prior ``get()``.
        """
        self._store.pop(session_id, None)


class FirestoreSessionStore(SessionStore):
    """Firestore-backed session store.

    Sessions are stored at ``sessions/{session_id}`` as JSON documents in the
    ``(default)`` Firestore database of the given GCP project.

    All Firestore exceptions are re-raised without swallowing so that callers
    can handle transient failures appropriately.
    """

    _COLLECTION = "sessions"

    def __init__(self, project: str, database: str = "(default)") -> None:
        """Initialise the Firestore client.

        Args:
            project: Google Cloud project ID (from ``GOOGLE_CLOUD_PROJECT``).
            database: Firestore database name. Defaults to ``"(default)"``.
        """
        from google.cloud import firestore  # type: ignore[import-untyped]

        self._db = firestore.Client(project=project, database=database)

    # ------------------------------------------------------------------
    # SessionStore interface
    # ------------------------------------------------------------------

    def create(self, session: Session) -> Session:
        """Persist a new session to Firestore.

        Args:
            session: The ``Session`` object to store.

        Returns:
            The stored ``Session``.

        Raises:
            ValueError: If a session with the same ``session_id`` already exists.
            google.cloud.exceptions.GoogleCloudError: On any Firestore error.
        """
        doc_ref = self._db.collection(self._COLLECTION).document(session.session_id)
        doc = doc_ref.get()
        if doc.exists:
            raise ValueError(
                f"Session '{session.session_id}' already exists. "
                "Use update() to modify an existing session."
            )
        doc_ref.set(session.model_dump(mode="json"))
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Retrieve a session from Firestore by ID.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            The ``Session`` if found, otherwise ``None``.

        Raises:
            google.cloud.exceptions.GoogleCloudError: On any Firestore error.
        """
        doc_ref = self._db.collection(self._COLLECTION).document(session_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        return Session.model_validate(doc.to_dict())

    def update(self, session: Session) -> Session:
        """Overwrite an existing session in Firestore.

        Args:
            session: The updated ``Session`` object.

        Returns:
            The updated ``Session``.

        Raises:
            KeyError: If no session with ``session.session_id`` exists.
            google.cloud.exceptions.GoogleCloudError: On any Firestore error.
        """
        doc_ref = self._db.collection(self._COLLECTION).document(session.session_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise KeyError(
                f"Session '{session.session_id}' not found. "
                "Use create() to add a new session."
            )
        doc_ref.set(session.model_dump(mode="json"))
        return session

    def delete(self, session_id: str) -> None:
        """Remove a session from Firestore.

        Silently does nothing if the session does not exist.

        Args:
            session_id: The unique identifier of the session to remove.

        Raises:
            google.cloud.exceptions.GoogleCloudError: On any Firestore error.
        """
        doc_ref = self._db.collection(self._COLLECTION).document(session_id)
        doc_ref.delete()


class AlloyDBSessionStore(SessionStore):
    """AlloyDB (PostgreSQL) backed session store using a threaded connection pool.

    Sessions are stored in the ``ivf_sessions`` table with the schema::

        CREATE TABLE ivf_sessions (
            session_id   TEXT PRIMARY KEY,
            session_data JSONB NOT NULL,
            created_at   TIMESTAMP NOT NULL,
            updated_at   TIMESTAMP NOT NULL
        );

    The connection pool is initialised eagerly at construction time so that
    misconfigured connection strings fail fast rather than at first use.
    """

    def __init__(self, connection_string: str) -> None:
        """Initialise the connection pool.

        Args:
            connection_string: A PostgreSQL DSN, e.g.
                ``postgresql://user:pass@host:5432/dbname``.

        Raises:
            RuntimeError: If the pool cannot be created or the initial
                connection attempt fails.  The error message includes the
                host extracted from the DSN so operators can diagnose
                misconfigured endpoints quickly.
        """
        import json as _json
        import psycopg2
        import psycopg2.pool
        from urllib.parse import urlparse

        self._json = _json
        self._psycopg2 = psycopg2

        parsed = urlparse(connection_string)
        host = parsed.hostname or connection_string

        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=connection_string,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to connect to AlloyDB at host '{host}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self):
        """Borrow a connection from the pool (context manager)."""
        import contextlib

        @contextlib.contextmanager
        def _ctx():
            conn = self._pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                self._pool.putconn(conn)

        return _ctx()

    # ------------------------------------------------------------------
    # SessionStore interface
    # ------------------------------------------------------------------

    def create(self, session: Session) -> Session:
        """Persist a new session to AlloyDB.

        Args:
            session: The ``Session`` object to store.

        Returns:
            The stored ``Session``.

        Raises:
            ValueError: If a session with the same ``session_id`` already exists.
        """
        import json
        from datetime import datetime

        sql_check = "SELECT 1 FROM ivf_sessions WHERE session_id = %s"
        sql_insert = (
            "INSERT INTO ivf_sessions (session_id, session_data, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s)"
        )
        now = datetime.utcnow()
        data = json.dumps(session.model_dump(mode="json"))

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_check, (session.session_id,))
                if cur.fetchone() is not None:
                    raise ValueError(
                        f"Session '{session.session_id}' already exists. "
                        "Use update() to modify an existing session."
                    )
                cur.execute(sql_insert, (session.session_id, data, now, now))

        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Retrieve a session from AlloyDB by ID.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            The ``Session`` if found, otherwise ``None``.
        """
        import json

        sql = "SELECT session_data FROM ivf_sessions WHERE session_id = %s"

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (session_id,))
                row = cur.fetchone()

        if row is None:
            return None

        raw = row[0]
        # psycopg2 may return a dict (for JSONB) or a string
        if isinstance(raw, str):
            raw = json.loads(raw)
        return Session.model_validate(raw)

    def update(self, session: Session) -> Session:
        """Overwrite an existing session in AlloyDB.

        Args:
            session: The updated ``Session`` object.

        Returns:
            The updated ``Session``.

        Raises:
            KeyError: If no session with ``session.session_id`` exists.
        """
        import json
        from datetime import datetime

        sql_check = "SELECT 1 FROM ivf_sessions WHERE session_id = %s"
        sql_update = (
            "UPDATE ivf_sessions SET session_data = %s, updated_at = %s "
            "WHERE session_id = %s"
        )
        now = datetime.utcnow()
        data = json.dumps(session.model_dump(mode="json"))

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_check, (session.session_id,))
                if cur.fetchone() is None:
                    raise KeyError(
                        f"Session '{session.session_id}' not found. "
                        "Use create() to add a new session."
                    )
                cur.execute(sql_update, (data, now, session.session_id))

        return session

    def delete(self, session_id: str) -> None:
        """Remove a session from AlloyDB.

        Silently does nothing if the session does not exist.

        Args:
            session_id: The unique identifier of the session to remove.
        """
        sql = "DELETE FROM ivf_sessions WHERE session_id = %s"

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (session_id,))
