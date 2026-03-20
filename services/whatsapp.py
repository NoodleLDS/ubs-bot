"""
Serviço de comunicação com a WhatsApp Cloud API (Meta).
- Connection pooling (um client reutilizado)
- Retry com backoff exponencial para falhas temporárias
"""

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

# Códigos de erro que merecem retry
RETRIABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # segundos


class WhatsAppService:
    """Cliente assíncrono para a WhatsApp Cloud API com pooling e retry."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.token = os.getenv("WHATSAPP_TOKEN", "")
        self.phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
        self.url = f"{BASE_URL}/{self.phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        # Client externo (injetado no lifespan) ou None
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("WhatsAppService: httpx client não foi injetado. Use o lifespan.")
        return self._client

    # ── Métodos públicos ─────────────────────────────

    async def send_text(self, to: str, body: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        return await self._post(payload)

    async def send_buttons(self, to, body, buttons, header=None) -> dict:
        interactive = {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons[:3]
                ]
            },
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }
        return await self._post(payload)

    async def send_list(self, to, body, button_label, sections, header=None, footer=None) -> dict:
        interactive = {
            "type": "list",
            "body": {"text": body},
            "action": {"button": button_label, "sections": sections},
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }
        return await self._post(payload)

    async def mark_as_read(self, message_id: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        return await self._post(payload)

    # ── Retry com backoff ────────────────────────────

    async def _post(self, payload: dict) -> dict:
        """POST com retry automático para falhas temporárias."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                resp = await self.client.post(
                    self.url, headers=self.headers, json=payload
                )

                # Sucesso
                if resp.status_code < 400:
                    return resp.json()

                # Erro retriável → retry
                if resp.status_code in RETRIABLE_STATUS:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "WhatsApp API %s (tentativa %d/%d) — retry em %.1fs",
                        resp.status_code, attempt + 1, MAX_RETRIES, wait,
                    )
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    await asyncio.sleep(wait)
                    continue

                # Erro definitivo (400, 401, 403, etc.)
                logger.error("WhatsApp API erro %s: %s", resp.status_code, resp.text[:300])
                return {"error": resp.text, "status_code": resp.status_code}

            except httpx.RequestError as exc:
                wait = BACKOFF_BASE * (2 ** attempt)
                logger.warning(
                    "Erro de conexão (tentativa %d/%d): %s — retry em %.1fs",
                    attempt + 1, MAX_RETRIES, exc, wait,
                )
                last_error = str(exc)
                await asyncio.sleep(wait)

        logger.error("WhatsApp API: todas as %d tentativas falharam: %s", MAX_RETRIES, last_error)
        return {"error": last_error or "max retries exceeded"}
