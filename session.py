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
