# pyright: reportUnusedParameter=false

__all__ = [
    "get_client",
    "post_client",
    "post_transaction",
    "get_subscription",
    "get_subscription_options",
    "post_trial_subscription",
    "post_new_subscription",
    "renew_subscription",
    "update_subscription",
    "get_connection_config",
    "notify_client",
    "update_peerhub_heartbeat",
]

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
) -> str: ...


@declare_task(task_name="main_api.notify_client")
async def notify_client(
    client_data: m.ClientGet,
) -> m.Success: ...


@declare_task(task_name="main_api.update_peerhub_heartbeat")
async def update_peerhub_heartbeat(
    peerhub_heartbeat_data: m.PeerHubHeartbeatData,
) -> m.Success: ...
