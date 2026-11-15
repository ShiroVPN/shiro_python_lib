# pyright: reportUnusedParameter=false

__all__ = [
    "notify_subscription",
    "notify_topup",
    "notify_chargeback",
    "notify_referral_bonus",
]

from . import models as m
from .broker import declare_task


@declare_task(task_name="telegram_bot.notify_subscription")
async def notify_subscription(
    notification: m.SubscriptionNotification,
) -> None: ...


@declare_task(task_name="telegram_bot.notify_topup")
async def notify_topup(notification: m.TopupNotification) -> None: ...


@declare_task(task_name="telegram_bot.notify_chargeback")
async def notify_chargeback(notification: m.ChargebackNotification) -> None: ...


@declare_task(task_name="telegram_bot.notify_referral_bonus")
async def notify_referral_bonus(
    notification: m.ReferralBonusNotification,
) -> None: ...
