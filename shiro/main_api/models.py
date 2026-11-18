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
    "AudienceGroup",
    "AnnounceGet",
    "FeatureGet",
    "PaymentPost",
    "ConnectionType",
    "PeerHubHeartbeatData",
    "Success",
]

from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from heliclockter import datetime_utc
from pydantic import BaseModel, Field, StringConstraints

from shiro.util.types import (
    Country,
    Money,
    ServerName,
    SubscriptionName,
    TelegramID,
    TelegramUsername,
)


class SubscriptionConfig(BaseModel):
    name: SubscriptionName
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
    referrer_telegram_id: TelegramID | None = None


class ClientUsernamePost(ClientGet):
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
    subscription_option_name: SubscriptionName


class SubscriptionDaysPost(ClientGet):
    days: int = Field(gt=0, le=31)


class SubscriptionDiscountPost(SubscriptionPost):
    discount_percent: int = Field(gt=0, le=50)


class ReferralInfo(BaseModel):
    enabled: bool
    bonus: Decimal = Field(ge=0)
    trial_name: SubscriptionName
    trial_seconds: int = Field(gt=0)
    invited: int = Field(ge=0)
    paid: int = Field(ge=0)


class UsagePeer(BaseModel):
    telegram_id: TelegramID
    username: TelegramUsername | None
    tx: int = Field(ge=0)
    rx: int = Field(ge=0)
    seconds_ago: float | None


class UsageStats(BaseModel):
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
    clients: int = Field(ge=0)
    active_trial: int = Field(ge=0)
    paying: int = Field(ge=0)
    usage: UsageStats | None = None


class BetaTester(BaseModel):
    telegram_id: TelegramID
    username: TelegramUsername | None


class BetaTesterPost(BaseModel):
    username: TelegramUsername
    beta_tester: bool


class AudienceGroup(StrEnum):
    all = "all"
    active = "active"
    beta = "beta"


class AnnounceGet(BaseModel):
    audience: AudienceGroup


class FeatureGet(ClientGet):
    feature: str = Field(min_length=1)


class PaymentPost(ClientGet):
    amount: Money
    return_callback: Annotated[str, StringConstraints(max_length=64)] | None = (
        None
    )


class ConnectionType(StrEnum):
    wireguard = "wireguard"
    xui = "xui"


class PeerHubHeartbeatData(BaseModel):
    hub_id: UUID
    server_name: ServerName
    connection_type: ConnectionType
    country: Country
    last_seen_at: datetime_utc


class Success(BaseModel):
    ok: bool = True
