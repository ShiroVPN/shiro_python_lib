# pyright: reportUnusedParameter=false

__all__ = [
    "TELEGRAM_BOT_TASK_PREFIX",
    "TelegramBotTaskName",
    "notify_subscription",
    "notify_topup",
    "notify_chargeback",
    "notify_referral_bonus",
]

from enum import StrEnum

from shiro.util.tasks import get_declare_task_wrapper

from . import models as m

TELEGRAM_BOT_TASK_PREFIX = "telegram_bot"


class TelegramBotTaskName(StrEnum):
    notify_subscription = "notify_subscription"
    notify_topup = "notify_topup"
    notify_chargeback = "notify_chargeback"
    notify_referral_bonus = "notify_referral_bonus"


declare_telegram_bot_task = get_declare_task_wrapper(TELEGRAM_BOT_TASK_PREFIX)


@declare_telegram_bot_task(TelegramBotTaskName.notify_subscription)
async def notify_subscription(
    notification: m.SubscriptionNotification,
) -> None: ...


@declare_telegram_bot_task(TelegramBotTaskName.notify_topup)
async def notify_topup(notification: m.TopupNotification) -> None: ...


@declare_telegram_bot_task(TelegramBotTaskName.notify_chargeback)
async def notify_chargeback(notification: m.ChargebackNotification) -> None: ...


@declare_telegram_bot_task(TelegramBotTaskName.notify_referral_bonus)
async def notify_referral_bonus(
    notification: m.ReferralBonusNotification,
) -> None: ...
