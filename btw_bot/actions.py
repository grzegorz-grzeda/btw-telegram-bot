"""What the handler asks the polling loop to do. Plain data, no Telegram I/O."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Button:
    label: str
    data: str


# Rows of buttons, top to bottom (Telegram's inline keyboard).
Buttons = list[list[Button]]


@dataclass(frozen=True)
class SendMessage:
    chat_id: int
    text: str
    buttons: Buttons | None = None


@dataclass(frozen=True)
class EditMessage:
    chat_id: int
    message_id: int
    text: str
    buttons: Buttons | None = None


@dataclass(frozen=True)
class AnswerTap:
    """Acknowledge a button tap so Telegram's spinner clears; `notice` is an optional short popup."""

    tap_id: str
    notice: str | None = None


Action = SendMessage | EditMessage | AnswerTap
