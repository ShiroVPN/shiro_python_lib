__all__ = [
    "Country",
    "Money",
    "ServerName",
    "SubscriptionName",
    "TelegramID",
    "TelegramUsername",
]

from decimal import Decimal
from typing import Annotated

from pydantic import Field, StringConstraints

Money = Annotated[Decimal, Field(gt=0, decimal_places=2)]
TelegramID = Annotated[int, Field(ge=0, lt=2**63)]
TelegramUsername = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9_]{1,32}$")
]
SubscriptionName = Annotated[
    str, StringConstraints(min_length=1, max_length=20)
]
ServerName = Annotated[str, StringConstraints(min_length=1, max_length=15)]
Country = Annotated[str, StringConstraints(min_length=1, max_length=15)]
