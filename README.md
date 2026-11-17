# shiro_python_lib

The contract library of the ShiroVPN stack: the taskiq task surface of every
service and the pydantic models that cross the queue. The services implement
the tasks and import the models; they never declare their own.

| Module | What it declares |
| --- | --- |
| `shiro.main_api` | Client lifecycle, subscriptions and renewals, balances, referral program, beta testers, announcements, Platega payments |
| `shiro.peerhub` | Peers and their connection config on one VPN node |
| `shiro.telegram_bot` | The notifications a service sends to the Telegram bot |
| `shiro.util` | The shared broker builder, task helpers, settings, telemetry and error codes |

Consumers pin a release tag:

```
poetry add "git+https://github.com/ShiroVPN/shiro_python_lib.git@vX.Y.Z"
```

Usage: [a process that only kicks tasks](examples/example_usage_for_client.py)
and [a process that consumes a queue](examples/example_usage_for_worker.py).

Broker topology, the model/task/error tables of each module, the upgrade notes
and the rules a change has to satisfy live in [AGENTS.md](AGENTS.md).
