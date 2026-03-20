"""
Gerenciamento de sessões por número de telefone.
Cada usuário tem um estado independente com timeout de 30 min.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


TIMEOUT_MINUTES = 30


@dataclass
class UserSession:
    phone: str
    state: str = "MENU"
    submenu: str = ""
    last_activity: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """Atualiza timestamp de última atividade."""
        self.last_activity = datetime.now()

    def is_expired(self) -> bool:
        """Retorna True se a sessão expirou (30 min de inatividade)."""
        return datetime.now() - self.last_activity > timedelta(minutes=TIMEOUT_MINUTES)

    def reset(self) -> None:
        """Volta sessão ao estado inicial."""
        self.state = "MENU"
        self.submenu = ""
        self.data = {}
        self.touch()


class SessionManager:
    """Gerencia sessões de todos os usuários (em memória)."""

    def __init__(self) -> None:
        self._sessions: dict[str, UserSession] = {}

    def get(self, phone: str) -> UserSession:
        """Retorna sessão existente ou cria uma nova."""
        session = self._sessions.get(phone)
        if session is None or session.is_expired():
            session = UserSession(phone=phone)
            self._sessions[phone] = session
        session.touch()
        return session

    def set_state(self, phone: str, state: str, submenu: str = "") -> None:
        """Define o estado da sessão de um usuário."""
        session = self.get(phone)
        session.state = state
        session.submenu = submenu
        session.touch()

    def reset(self, phone: str) -> None:
        """Reseta a sessão de um usuário."""
        session = self._sessions.get(phone)
        if session:
            session.reset()

    def cleanup_expired(self) -> int:
        """Remove sessões expiradas. Retorna quantidade removida."""
        expired = [p for p, s in self._sessions.items() if s.is_expired()]
        for phone in expired:
            del self._sessions[phone]
        return len(expired)


# Instância global
session_manager = SessionManager()
