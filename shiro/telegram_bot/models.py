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
    """`telegram_bot.notify_subscription`: the subscription was renewed,
    disabled, or is about to expire — `renewing` when it would renew itself
    if the balance stays as it is now, `expiring` when it would not."""

    telegram_id: TelegramID
    event: NotificationEvent
    name: str
    expired_at: datetime_utc
    balance: Decimal


class TopupNotification(BaseModel):
    """`telegram_bot.notify_topup`: Platega confirmed the payment and the
    backend credited it. `return_callback` is the bot's own data from
    `main_api.create_payment`, `method` Platega's name (e.g. SBPQR, None
    until the payer picks one)."""

    telegram_id: TelegramID
    amount: Money
    balance: Decimal
    return_callback: str | None
    method: str | None
    platega_id: str


class ChargebackNotification(BaseModel):
    """`telegram_bot.notify_chargeback`: the payer's bank charged the payment
    back weeks or months later. The balance stays as it is; the bot tells the
    client and the admins."""

    telegram_id: TelegramID
    username: TelegramUsername | None
    amount: Money
    platega_id: str
    paid_at: datetime_utc


class ReferralBonusNotification(BaseModel):
    """`telegram_bot.notify_referral_bonus`: the invited friend paid for the
    first time, the bonus is already on the inviter's balance."""

    telegram_id: TelegramID
    bonus: Decimal = Field(ge=0)
    balance: Decimal
