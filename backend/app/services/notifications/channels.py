"""Notification channels: each channel produces a matching formatter and sender."""

import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from app.core.config import get_settings
from app.domain.models import Client, NotificationChannel, NotificationKind
from app.services.notifications.senders import (
    FakeSmsGateway,
    FakeSmtp,
    InAppSender,
    Message,
    MessageSender,
    SmsGatewaySender,
    SmtpClient,
    SmtpEmailSender,
)


@dataclass(frozen=True)
class NotificationContent:
    """What to tell the client, independent of the channel."""

    kind: NotificationKind
    client_name: str
    tariff_name: str
    start_date: date
    end_date: date
    days_left: int | None = None
    visits_left: int | None = None


def _sentence(content: NotificationContent) -> str:
    match content.kind:
        case NotificationKind.MEMBERSHIP_PURCHASED:
            return (
                f"абонемент «{content.tariff_name}» оформлено, він діє з {content.start_date:%d.%m.%Y} "
                f"по {content.end_date:%d.%m.%Y}"
            )
        case NotificationKind.MEMBERSHIP_EXPIRING:
            return (
                f"абонемент «{content.tariff_name}» закінчується {content.end_date:%d.%m.%Y} "
                f"(через {content.days_left} дн.). Продовжте його на рецепції або в особистому кабінеті"
            )
        case NotificationKind.VISITS_LOW:
            return f"за абонементом «{content.tariff_name}» лишилось {content.visits_left} відвідування"


SUBJECTS = {
    NotificationKind.MEMBERSHIP_PURCHASED: "Абонемент оформлено",
    NotificationKind.MEMBERSHIP_EXPIRING: "Абонемент скоро закінчується",
    NotificationKind.VISITS_LOW: "Відвідування закінчуються",
}


class MessageFormatter(ABC):
    """GoF: Abstract Factory — AbstractProduct A."""

    @abstractmethod
    def format(self, content: NotificationContent) -> Message: ...


class EmailFormatter(MessageFormatter):
    """GoF: Abstract Factory — ConcreteProduct A (e-mail): subject, greeting and signature."""

    def format(self, content: NotificationContent) -> Message:
        first_name = content.client_name.split()[-1]
        sentence = _sentence(content)
        body = f"Вітаємо, {first_name}!\n\nВаш {sentence}.\n\nЗ повагою,\nкоманда FitClub"
        return Message(subject=f"FitClub: {SUBJECTS[content.kind]}", body=body)


class SmsFormatter(MessageFormatter):
    """GoF: Abstract Factory — ConcreteProduct A (SMS): one short line without a subject."""

    LIMIT = FakeSmsGateway.MAX_LENGTH

    def format(self, content: NotificationContent) -> Message:
        text = f"FitClub: {_sentence(content)}."
        if len(text) > self.LIMIT:
            text = text[: self.LIMIT - 1] + "…"
        return Message(subject=None, body=text)


class InAppFormatter(MessageFormatter):
    """GoF: Abstract Factory — ConcreteProduct A (in-app): a title and a short text."""

    def format(self, content: NotificationContent) -> Message:
        sentence = _sentence(content)
        return Message(subject=SUBJECTS[content.kind], body=sentence[0].upper() + sentence[1:] + ".")


class NotificationChannelFactory(ABC):
    """GoF: Abstract Factory — AbstractFactory.

    Creates a family of objects that must match each other: the formatter shapes the text for the
    channel and the sender delivers it there (an SMS-sized text never goes to an e-mail sender).
    """

    channel: NotificationChannel

    @abstractmethod
    def create_formatter(self) -> MessageFormatter: ...

    @abstractmethod
    def create_sender(self) -> MessageSender: ...

    @abstractmethod
    def recipient(self, client: Client) -> str: ...


class EmailChannelFactory(NotificationChannelFactory):
    """GoF: Abstract Factory — ConcreteFactory."""

    channel = NotificationChannel.EMAIL

    def create_formatter(self) -> MessageFormatter:
        return EmailFormatter()

    def create_sender(self) -> MessageSender:
        settings = get_settings()
        return SmtpEmailSender(self._connect, settings.smtp_from)

    def recipient(self, client: Client) -> str:
        return client.user.email

    @staticmethod
    def _connect() -> SmtpClient:
        settings = get_settings()
        if not settings.smtp_host:
            return FakeSmtp()
        smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password or "")
        return smtp


class SmsChannelFactory(NotificationChannelFactory):
    """GoF: Abstract Factory — ConcreteFactory."""

    channel = NotificationChannel.SMS

    def create_formatter(self) -> MessageFormatter:
        return SmsFormatter()

    def create_sender(self) -> MessageSender:
        return SmsGatewaySender(FakeSmsGateway())

    def recipient(self, client: Client) -> str:
        return client.phone


class InAppChannelFactory(NotificationChannelFactory):
    """GoF: Abstract Factory — ConcreteFactory."""

    channel = NotificationChannel.IN_APP

    def create_formatter(self) -> MessageFormatter:
        return InAppFormatter()

    def create_sender(self) -> MessageSender:
        return InAppSender()

    def recipient(self, client: Client) -> str:
        return str(client.id)


_FACTORIES: dict[NotificationChannel, NotificationChannelFactory] = {
    factory.channel: factory
    for factory in (EmailChannelFactory(), SmsChannelFactory(), InAppChannelFactory())
}


def channel_factory(channel: NotificationChannel) -> NotificationChannelFactory:
    return _FACTORIES[channel]
