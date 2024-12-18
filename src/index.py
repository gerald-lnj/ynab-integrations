from configparser import ConfigParser
from typing import Generator, List, Optional

from ynab_api import ApiClient, ApiException, Configuration
from ynab_api.api.transactions_api import TransactionsApi
from ynab_api.models import SaveTransaction, SaveTransactionsWrapper

from . import logger
from .connectors import get_active_connectors
from .message_parsers import BaseMessageParser, message_parsers
from .utils.constants import YNAB_CONFIG_PATH
from .utils.models import Transaction, Message

config_parser = ConfigParser()
config_parser.read_file(open(YNAB_CONFIG_PATH))

YNAB_ACCESS_TOKEN = config_parser["config"]["YNAB_ACCESS_TOKEN"]
YNAB_BUDGET_ID = config_parser["config"]["YNAB_BUDGET_ID"]
YNAB_API_BASE_URL = config_parser["config"]["YNAB_API_BASE_URL"]
SUCCESS = {"statusCode": 200}

CONFIGURATION = Configuration(
    host=YNAB_API_BASE_URL,
    api_key={"bearer": YNAB_ACCESS_TOKEN},
    api_key_prefix={"bearer": "Bearer"},
)


def fetch_messages() -> Generator[Message, None, None]:
    """Fetch messages from all active connectors."""
    for connector in get_active_connectors():
        for message in connector.get_unread_messages_inbox():
            yield message


def parse_message(message: Message) -> Optional[Transaction]:
    """Parse a message using the first parser that accepts it."""
    parser: Optional[BaseMessageParser] = None
    parser = next(
        (parser for parser in message_parsers if parser.accepts(message)), None
    )
    if parser is None:
        logger.warning(
            f"No message parser found for message {message.body}..., skipping"
        )
        return None
    transaction = parser.parse_message(message)
    logger.info(f"Transaction: {transaction}")
    return transaction


def write_transactions(transactions: List[SaveTransaction]):
    """
    Send a list of SaveTransaction objects to YNAB

    Args:
        transactions (List[SaveTransaction]): List of SaveTransaction objects

    Raises:
        e: ApiException
    """
    if not transactions:
        logger.info("No transactions to write")
    else:
        with ApiClient(CONFIGURATION) as api_client:
            api_instance = TransactionsApi(api_client)
            data = SaveTransactionsWrapper(transactions=transactions)

            try:
                api_instance.create_transaction(YNAB_BUDGET_ID, data)
            except ApiException as e:
                logger.exception(e)
            else:
                logger.info(f"{len(transactions)} transaction(s) written successfully")


def lambda_handler(event, context):
    """Fetch all messages, parse them, and write them to YNAB."""
    transactions: List[Transaction] = []
    for message in fetch_messages():
        transaction = parse_message(message)
        if transaction is not None:
            transactions.append(transaction)
    write_transactions([t.to_savetransaction() for t in transactions])

    return SUCCESS
