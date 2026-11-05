"""Minimal Telegram Bot API client over HTTPS, using only the standard library."""

import json
import urllib.error
import urllib.request

from .actions import MAX_MESSAGE_LENGTH, Buttons


class TelegramError(Exception):
    pass


class TelegramClient:
    def __init__(self, token: str):
        self._base_url = f"https://api.telegram.org/bot{token}/"

    def get_updates(self, offset: int | None, timeout: int) -> list[dict]:
        """Long-poll for new messages and button taps. Blocks up to `timeout` seconds."""
        params = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
        if offset is not None:
            params["offset"] = offset
        return self._call("getUpdates", params, http_timeout=timeout + 10)

    def send_message(self, chat_id: int, text: str, buttons: Buttons | None = None) -> None:
        """Send text, split if too long. Buttons go on the last part."""
        *first, last = split_message(text)
        for chunk in first:
            self._call("sendMessage", {"chat_id": chat_id, "text": chunk})
        params = {"chat_id": chat_id, "text": last}
        if buttons is not None:
            params["reply_markup"] = _keyboard(buttons)
        self._call("sendMessage", params)

    def edit_message(
        self, chat_id: int, message_id: int, text: str, buttons: Buttons | None = None
    ) -> None:
        """Replace a message's text and buttons (no buttons removes them)."""
        params = {"chat_id": chat_id, "message_id": message_id, "text": text}
        params["reply_markup"] = _keyboard(buttons or [])
        try:
            self._call("editMessageText", params)
        except TelegramError as e:
            # Redrawing a list that hasn't changed (e.g. tapping the active filter) is fine.
            if "message is not modified" not in str(e):
                raise

    def answer_tap(self, tap_id: str, notice: str | None = None) -> None:
        """Answer a button tap (callback query) so the client's spinner clears."""
        params = {"callback_query_id": tap_id}
        if notice:
            params["text"] = notice
        self._call("answerCallbackQuery", params)

    def set_commands(self, commands: list[tuple[str, str]]) -> None:
        """Register the "/" menu: (command without slash, short description) pairs."""
        params = {"commands": [{"command": c, "description": d} for c, d in commands]}
        self._call("setMyCommands", params)

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


def _keyboard(buttons: Buttons) -> dict:
    return {
        "inline_keyboard": [
            [{"text": b.label, "callback_data": b.data} for b in row] for row in buttons
        ]
    }


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
