"""Delivery of messages: our MessageSender interface and adapters to external e-mail and SMS services."""

import logging
import smtplib
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from email.message import EmailMessage
from itertools import count
from typing import Any, Protocol

logger = logging.getLogger("fitclub.notifications")


@dataclass(frozen=True)
class Message:
    subject: str | None
    body: str


class DeliveryError(Exception):
    """The external service did not accept the message."""


class MessageSender(ABC):
    """GoF: Adapter — Target: the interface the notification code works with."""

    @abstractmethod
    def send(self, recipient: str, message: Message) -> None: ...


# --- adaptees: external services with their own interfaces ---


class SmtpClient(Protocol):
    """The part of smtplib.SMTP the e-mail adapter relies on."""

    def __enter__(self) -> SmtpClient: ...
    def __exit__(self, *args: Any) -> Any: ...
    def sendmail(self, from_addr: str, to_addrs: list[str], msg: str) -> Any: ...


class FakeSmtp:
    """Imitation of an SMTP server with smtplib's interface; letters go to the log and to `outbox`."""

    outbox: list[tuple[str, list[str], str]] = []

    def __enter__(self) -> FakeSmtp:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def sendmail(self, from_addr: str, to_addrs: list[str], msg: str) -> dict:
        FakeSmtp.outbox.append((from_addr, to_addrs, msg))
        logger.info("E-mail (imitation) to %s:\n%s", ", ".join(to_addrs), msg)
        return {}


class FakeSmsGateway:
    """Imitation of a third-party SMS API: a different method name, keyword arguments and a status dict."""

    MAX_LENGTH = 160
    outbox: list[tuple[str, str]] = []
    _ids = count(1)

    def send_sms(self, *, phone: str, text: str) -> dict[str, Any]:
        if len(text) > self.MAX_LENGTH:
            return {"status": "rejected", "reason": f"text longer than {self.MAX_LENGTH} characters"}
        FakeSmsGateway.outbox.append((phone, text))
        logger.info("SMS (imitation) to %s: %s", phone, text)
        return {"status": "queued", "message_id": next(self._ids)}


# --- adapters ---


class SmtpEmailSender(MessageSender):
    """GoF: Adapter — adapts smtplib.SMTP (or its imitation) to MessageSender."""

    def __init__(self, connect: Callable[[], SmtpClient], from_addr: str) -> None:
        self.connect = connect
        self.from_addr = from_addr

    def send(self, recipient: str, message: Message) -> None:
        letter = EmailMessage()
        letter["From"] = self.from_addr
        letter["To"] = recipient
        letter["Subject"] = message.subject or "FitClub"
        letter.set_content(message.body)
        try:
            with self.connect() as smtp:
                smtp.sendmail(self.from_addr, [recipient], letter.as_string())
        except (smtplib.SMTPException, OSError) as exc:
            raise DeliveryError(f"SMTP: {exc}") from exc


class SmsGatewaySender(MessageSender):
    """GoF: Adapter — adapts FakeSmsGateway.send_sms(phone=, text=) -> dict to MessageSender."""

    def __init__(self, gateway: FakeSmsGateway) -> None:
        self.gateway = gateway

    def send(self, recipient: str, message: Message) -> None:
        result = self.gateway.send_sms(phone=recipient, text=message.body)
        if result.get("status") != "queued":
            raise DeliveryError(f"SMS gateway: {result.get('reason', 'unknown error')}")


class InAppSender(MessageSender):
    """In-app notifications need no external service: the stored notification is the delivery."""

    def send(self, recipient: str, message: Message) -> None:
        return None
