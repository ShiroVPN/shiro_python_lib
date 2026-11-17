__all__ = [
    "NotificationEvent",
    "SubscriptionNotification",
    "TopupNotification",
    "ChargebackNotification",
    "ReferralBonusNotification",
]

from decimal import Decimal
from typing import Literal

from heliclockter import datetime_utc
from pydantic import BaseModel, Field

from shiro.util.types import Money, TelegramID, TelegramUsername

NotificationEvent = Literal["renewed", "disabled", "expiring", "renewing"]


class SubscriptionNotification(BaseModel):
    telegram_id: TelegramID
    event: NotificationEvent
    name: str
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
