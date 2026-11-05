"""Minimal Telegram Bot API client over HTTPS, using only the standard library."""

import json
import urllib.error
import urllib.request

MAX_MESSAGE_LENGTH = 4096


class TelegramError(Exception):
    pass


class TelegramClient:
    def __init__(self, token: str):
        self._base_url = f"https://api.telegram.org/bot{token}/"

    def get_updates(self, offset: int | None, timeout: int) -> list[dict]:
        """Long-poll for new messages. Blocks up to `timeout` seconds."""
        params = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        return self._call("getUpdates", params, http_timeout=timeout + 10)

    def send_message(self, chat_id: int, text: str) -> None:
        for chunk in split_message(text):
            self._call("sendMessage", {"chat_id": chat_id, "text": chunk})

    def _call(self, method: str, params: dict, http_timeout: float = 30):
        request = urllib.request.Request(
            self._base_url + method,
            data=json.dumps(params).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=http_timeout) as response:
                body = json.load(response)
        except urllib.error.HTTPError as e:
            # Telegram puts the reason in a JSON body. Don't include the URL: it has the token.
            try:
                description = json.load(e).get("description", "")
            except ValueError:
                description = ""
            raise TelegramError(f"{method} failed: HTTP {e.code} {description}") from None
        if not body.get("ok"):
            raise TelegramError(f"{method} failed: {body.get('description')}")
        return body["result"]


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split text into chunks Telegram accepts, breaking at newlines where possible."""
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    chunks.append(text)
    return chunks
