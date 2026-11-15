__all__ = [
    "Money",
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
