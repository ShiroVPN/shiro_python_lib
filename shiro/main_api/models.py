__all__ = [
    "SubscriptionConfig",
    "ClientGet",
    "ClientPost",
    "ClientUsernamePost",
    "TransactionPost",
    "Transaction",
    "Subscription",
    "SubscriptionPost",
    "SubscriptionDaysPost",
    "SubscriptionDiscountPost",
    "ReferralInfo",
    "BackendStats",
    "UsageStats",
    "UsagePeer",
    "BetaTester",
    "BetaTesterPost",
    "AnnounceGet",
    "FeatureGet",
    "PaymentGet",
    "PaymentPost",
    "PaymentStatus",
    "PeerHubHeartbeatData",
    "Success",
]

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from heliclockter import datetime_utc
from pydantic import BaseModel, Field, StringConstraints

from shiro.util.types import Money, TelegramID, TelegramUsername

PaymentStatus = Literal["PENDING", "CONFIRMED", "CANCELED", "CHARGEBACKED"]


class SubscriptionConfig(BaseModel):
    name: str
    cost: Decimal = Field(ge=0)
    timedelta_in_seconds: int = Field(gt=0)


class Client(BaseModel):
    telegram_id: TelegramID
    balance: Decimal
    activated_trial: bool
    autoupdate_subscriptions: bool
    created_at: datetime_utc
    updated_at: datetime_utc


class ClientGet(BaseModel):
    telegram_id: TelegramID


class ClientPost(ClientGet):
    # Who invited the client (from the bot's deep link). The worker silently
    # drops an unknown or self referrer, so the client is created anyway.
    referrer_telegram_id: TelegramID | None = None


class ClientUsernamePost(ClientGet):
    """`main_api.set_client_username`: the @username Telegram shows for the
    client, None when there is none or it was removed."""

    username: TelegramUsername | None = None


class TransactionPost(ClientGet):
    delta: Decimal


class Transaction(BaseModel):
    old_balance: Decimal
    new_balance: Decimal
    delta: Decimal


class Subscription(BaseModel):
    subscription_config: SubscriptionConfig
    enabled: bool
    autoupdate: bool
    expired_at: datetime_utc
    created_at: datetime_utc


class SubscriptionPost(ClientGet):
    subscription_option_name: str


class SubscriptionDaysPost(ClientGet):
    """`main_api.add_subscription_days`: the days a mini-game reward gifts,
    appended to the subscription's end."""

    days: int = Field(gt=0, le=31)


class SubscriptionDiscountPost(SubscriptionPost):
    """`main_api.post_discounted_subscription`: a purchase at the price a
    mini-game reward discounts it to, in whole rubles off."""

    discount_percent: int = Field(gt=0, le=50)


class ReferralInfo(BaseModel):
    """`main_api.get_referral_info`: the invite program as the backend's
    config has it, and this client's counters (zeros without a client)."""

    enabled: bool
    bonus: Decimal = Field(ge=0)
    trial_name: str
    trial_seconds: int = Field(gt=0)
    invited: int = Field(ge=0)
    paid: int = Field(ge=0)


class UsagePeer(BaseModel):
    """A peer in `top` or `low_traffic` of `BackendStats.usage`."""

    telegram_id: TelegramID
    username: TelegramUsername | None
    tx: int = Field(ge=0)
    rx: int = Field(ge=0)
    seconds_ago: float | None


class UsageStats(BaseModel):
    """`BackendStats.usage`: traffic and last handshakes read from the nodes'
    live counters, not a history — a node that does not answer is counted in
    `hubs_failed` and its peers report nothing."""

    enabled_peers: int = Field(ge=0)
    connected: int = Field(ge=0)
    seen_24h: int = Field(ge=0)
    seen_7d: int = Field(ge=0)
    tx: int = Field(ge=0)
    rx: int = Field(ge=0)
    top: list[UsagePeer]
    low_traffic: list[UsagePeer]
    low_traffic_count: int = Field(ge=0)
    hubs_failed: int = Field(ge=0)


class BackendStats(BaseModel):
    """`main_api.get_stats`: clients, active trials, paying clients and the
    traffic behind them; a backend older than `usage` sends none."""

    clients: int = Field(ge=0)
    active_trial: int = Field(ge=0)
    paying: int = Field(ge=0)
    usage: UsageStats | None = None


class BetaTester(BaseModel):
    """A client `main_api.get_beta_testers` lists."""

    telegram_id: TelegramID
    username: TelegramUsername | None


class BetaTesterPost(BaseModel):
    """`main_api.set_beta_tester`: found by this @username, no `@` and any
    case; the answer is the client's telegram_id, None if there is no such
    client or several have that name."""

    username: TelegramUsername
    beta_tester: bool


class AnnounceGet(BaseModel):
    """`main_api.get_announce_recipients`: who an /announce reaches — every
    client, those with a live subscription (trial included), or beta
    testers."""

    audience: Literal["all", "active", "beta"]


class FeatureGet(ClientGet):
    """`main_api.has_feature`: a name from the backend's `beta_features`."""

    feature: str = Field(min_length=1)


class PaymentGet(BaseModel):
    """`main_api.check_payment`: the payment to ask Platega about."""

    payment_id: UUID


class PaymentPost(ClientGet):
    """`main_api.create_payment`: a Platega payment link that tops up the
    balance once Platega confirms it; `return_callback` is the bot's own data
    that comes back in `telegram_bot.notify_topup`."""

    amount: Money
    return_callback: Annotated[str, StringConstraints(max_length=64)] | None = (
        None
    )


class PeerHubHeartbeatData(BaseModel):
    hub_id: UUID
    server_name: str
    connection_type: str
    country: str
    last_seen_at: datetime_utc


class Success(BaseModel):
    ok: bool = True
