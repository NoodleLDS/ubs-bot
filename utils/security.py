"""
Segurança: verificação HMAC do webhook da Meta e rate limiting.
"""

import hashlib
import hmac
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


# ── Verificação HMAC ─────────────────────────────

def verify_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Verifica se o payload do webhook veio realmente da Meta.
    A Meta envia o header X-Hub-Signature-256 = sha256=<hash>.
    """
    if not signature_header or not app_secret:
        logger.warning("HMAC: signature ou app_secret ausente — ignorando verificação")
        return True  # Permite funcionar sem secret (dev/teste)

    if not signature_header.startswith("sha256="):
        return False

    expected_hash = signature_header[7:]  # Remove "sha256="
    computed_hash = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed_hash, expected_hash)


# ── Rate Limiting ────────────────────────────────

class RateLimiter:
    """
    Rate limiter por número de telefone.
    Limita X mensagens por janela de Y segundos.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, phone: str) -> bool:
        """Retorna True se o número pode enviar mais mensagens."""
        now = time.time()
        cutoff = now - self.window

        # Remove requests antigos
        self._requests[phone] = [
            t for t in self._requests[phone] if t > cutoff
        ]

        if len(self._requests[phone]) >= self.max_requests:
            return False

        self._requests[phone].append(now)
        return True

    def cleanup(self) -> None:
        """Remove entradas expiradas (chamar periodicamente)."""
        now = time.time()
        cutoff = now - self.window
        expired = [
            phone for phone, times in self._requests.items()
            if not times or times[-1] < cutoff
        ]
        for phone in expired:
            del self._requests[phone]


# Instância global: 10 mensagens por minuto por número
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
