# pyright: reportUnusedParameter=false

__all__ = [
    "get_client",
    "post_client",
    "post_transaction",
    "get_subscription",
    "get_subscription_options",
    "get_trial_subscription_config",
    "post_trial_subscription",
    "post_new_subscription",
    "renew_subscription",
    "update_subscription",
    "get_connection_config",
    "notify_client",
    "update_peerhub_heartbeat",
    "set_client_username",
    "get_stats",
    "get_referral_info",
    "has_feature",
    "set_beta_tester",
    "get_beta_testers",
    "get_announce_recipients",
    "add_subscription_days",
    "post_discounted_subscription",
    "create_payment",
    "check_payment",
    "expire_subscriptions",
    "poll_payments",
    "poll_chargebacks",
    "warn_expiring_subscriptions",
]

from shiro.peerhub.models import WgConfig, XuiConfig

from . import models as m
from .broker import declare_task


@declare_task(task_name="main_api.get_client")
async def get_client(client_data: m.ClientGet) -> m.Client: ...


@declare_task(task_name="main_api.post_client")
async def post_client(
    client_data: m.ClientPost,
) -> m.Client: ...


@declare_task(task_name="main_api.post_transaction")
async def post_transaction(
    transaction_data: m.TransactionPost,
) -> m.Transaction: ...


@declare_task(task_name="main_api.get_subscription")
async def get_subscription(client_data: m.ClientGet) -> m.Subscription: ...


@declare_task(task_name="main_api.get_subscription_options")
async def get_subscription_options() -> list[m.SubscriptionConfig]: ...


@declare_task(task_name="main_api.get_trial_subscription_config")
async def get_trial_subscription_config() -> m.SubscriptionConfig: ...


@declare_task(task_name="main_api.post_trial_subscription")
async def post_trial_subscription(
    client_data: m.ClientGet,
) -> m.Subscription: ...


@declare_task(task_name="main_api.post_new_subscription")
async def post_new_subscription(
    sub_data: m.SubscriptionPost,
) -> m.Subscription: ...


@declare_task(task_name="main_api.renew_subscription")
async def renew_subscription(
    client_data: m.ClientGet,
) -> m.Subscription: ...


@declare_task(task_name="main_api.update_subscription")
async def update_subscription(
    client_data: m.ClientGet,
) -> m.Subscription: ...


@declare_task(task_name="main_api.get_connection_config")
async def get_connection_config(
    client_data: m.ClientGet,
) -> WgConfig | XuiConfig: ...


@declare_task(task_name="main_api.notify_client")
async def notify_client(
    client_data: m.ClientGet,
) -> m.Success: ...


@declare_task(task_name="main_api.update_peerhub_heartbeat")
async def update_peerhub_heartbeat(
    peerhub_heartbeat_data: m.PeerHubHeartbeatData,
) -> m.Success: ...


@declare_task(task_name="main_api.set_client_username")
async def set_client_username(
    client_data: m.ClientUsernamePost,
) -> bool | None: ...


@declare_task(task_name="main_api.get_stats")
async def get_stats() -> m.BackendStats: ...


@declare_task(task_name="main_api.get_referral_info")
async def get_referral_info(client_data: m.ClientGet) -> m.ReferralInfo: ...


@declare_task(task_name="main_api.has_feature")
async def has_feature(feature_data: m.FeatureGet) -> bool: ...


@declare_task(task_name="main_api.set_beta_tester")
async def set_beta_tester(beta_tester_data: m.BetaTesterPost) -> int | None: ...


@declare_task(task_name="main_api.get_beta_testers")
async def get_beta_testers() -> list[m.BetaTester]: ...


@declare_task(task_name="main_api.get_announce_recipients")
async def get_announce_recipients(
    announce_data: m.AnnounceGet,
) -> list[int]: ...


@declare_task(task_name="main_api.add_subscription_days")
async def add_subscription_days(
    sub_days_data: m.SubscriptionDaysPost,
) -> m.Subscription: ...


@declare_task(task_name="main_api.post_discounted_subscription")
async def post_discounted_subscription(
    sub_data: m.SubscriptionDiscountPost,
) -> m.Subscription: ...


@declare_task(task_name="main_api.create_payment")
async def create_payment(payment_data: m.PaymentPost) -> str: ...


@declare_task(task_name="main_api.check_payment")
async def check_payment(payment_data: m.PaymentGet) -> m.PaymentStatus: ...


@declare_task(task_name="main_api.expire_subscriptions")
async def expire_subscriptions() -> int: ...


@declare_task(task_name="main_api.poll_payments")
async def poll_payments() -> int: ...


@declare_task(task_name="main_api.poll_chargebacks")
async def poll_chargebacks() -> int: ...


@declare_task(task_name="main_api.warn_expiring_subscriptions")
async def warn_expiring_subscriptions() -> int: ...
