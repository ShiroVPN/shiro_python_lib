__all__ = [
    "NotificationEvent",
    "SubscriptionNotification",
    "TopupNotification",
    "ChargebackNotification",
    "ReferralBonusNotification",
]

from decimal import Decimal
from enum import StrEnum

from heliclockter import datetime_utc
from pydantic import BaseModel, Field

from shiro.util.types import (
    Money,
    SubscriptionName,
    TelegramID,
    TelegramUsername,
)


class NotificationEvent(StrEnum):
    renewed = "renewed"
    disabled = "disabled"
    expiring = "expiring"
    renewing = "renewing"


class SubscriptionNotification(BaseModel):
    telegram_id: TelegramID
    event: NotificationEvent
    name: SubscriptionName
    expired_at: datetime_utc
    balance: Decimal


class TopupNotification(BaseModel):
    telegram_id: TelegramID
    amount: Money
    balance: Decimal
    return_callback: str | None
    method: str | None
    platega_id: str


class ChargebackNotification(BaseModel):
    telegram_id: TelegramID
    username: TelegramUsername | None
    amount: Money
    platega_id: str
    paid_at: datetime_utc


class ReferralBonusNotification(BaseModel):
    telegram_id: TelegramID
    bonus: Decimal = Field(ge=0)
    balance: Decimal
