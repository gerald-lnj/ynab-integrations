from datetime import date
from typing import Optional, Union

from pydantic import BaseModel
from ynab_api.models import SaveTransaction


class Transaction(BaseModel):
    """
    Intermediary class that loads basic primitive types from a dict.
    """

    account_id: str
    amount: int
    timestamp: Union[int, float]
    memo: Optional[str] = None
    payee_id: Optional[str] = None
    payee_name: Optional[str] = None
    category_id: Optional[str] = None
    cleared: Optional[bool] = None
    flag_color: Optional[str] = None
    approved: Optional[bool] = False

    def to_savetransaction(self) -> SaveTransaction:
        return SaveTransaction(
            account_id=self.account_id,
            date=date.fromtimestamp(self.timestamp),
            amount=self.amount,
            payee_id=self.payee_id,
            payee_name=self.payee_name,
            category_id=self.category_id,
            memo=self.memo,
            cleared=self.cleared,
            approved=self.approved,
        )
