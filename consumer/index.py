import os
from typing import Dict, List

import dotenv
from pydantic import ValidationError
from ynab_api import ApiClient, ApiException, Configuration
from ynab_api.apis import TransactionsApi
from ynab_api.models import SaveTransaction, SaveTransactionsWrapper

from .utils.logging import get_logger, get_tracer
from .utils.models import Transaction

dotenv.load_dotenv()

YNAB_ACCESS_TOKEN = os.getenv("YNAB_ACCESS_TOKEN")
YNAB_BUDGET_ID = os.getenv("YNAB_BUDGET_ID")
YNAB_API_BASE_URL = "https://api.youneedabudget.com/v1"
SUCCESS = {"statusCode": 200}

CONFIGURATION = Configuration(
    host=YNAB_API_BASE_URL,
    api_key={"bearer": YNAB_ACCESS_TOKEN},
    api_key_prefix={"bearer": "Bearer"},
)
logger = get_logger()
tracer = get_tracer()


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def handler(event, context):
    return main(event, context)


def main(event: Dict, context: Dict) -> Dict:
    if event["transactions"]:
        transactions = parse_transactions(event["transactions"])
        write_transactions(transactions)

    return SUCCESS


def parse_transactions(raw_transactions: List[Dict]) -> List[SaveTransaction]:
    """
    Parse raw data into a list of SaveTransaction objects,
    with an intemediary validation step with a pydantic model

    Args:
        raw_transactions (List[Dict]): List of JSON dictionaries

    Raises:
        ValidationError: Malformed transaction data

    Returns:
        List[SaveTransaction]: List of SaveTransaction objects
    """

    savetransactions: List[SaveTransaction] = []
    for raw_transaction in raw_transactions:
        try:
            transaction = Transaction(**raw_transaction)
        except ValidationError as e:
            raise ValidationError(
                f"Malformed transaction encountered: {raw_transaction}", Transaction
            ) from e
        savetransactions.append(transaction.to_savetransaction())
    return savetransactions


def write_transactions(transactions: List[SaveTransaction]):
    """
    Send a list of SaveTransaction objects to YNAB

    Args:
        transactions (List[SaveTransaction]): List of SaveTransaction objects

    Raises:
        e: ApiException
    """
    with ApiClient(CONFIGURATION) as api_client:
        # Create an instance of the API class
        api_instance = TransactionsApi(api_client)
        data = SaveTransactionsWrapper(transactions=transactions)

        try:
            api_response = api_instance.create_transaction(YNAB_BUDGET_ID, data)
            logger.info(api_response)
        except ApiException as e:
            logger.exception(e)
