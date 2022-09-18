from aws_cdk import (aws_lambda, aws_lambda_event_sources, aws_lambda_python,
                     aws_sqs)
from aws_cdk import core as cdk
from constructs import Construct

DEFAULT_LAMBDA_TIMEOUT = cdk.Duration.minutes(10)
DEFAULT_LAMBDA_MEMORY = 512
DEFAULT_LAMBDA_QUEUE_VISIBILITY_TIMEOUT = DEFAULT_LAMBDA_TIMEOUT.plus(
    cdk.Duration.minutes(1)
)


class YNABIntegrationsStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        queue = aws_sqs.Queue(
            self,
            "ynab-transactions-queue",
            dead_letter_queue=aws_sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=aws_sqs.Queue(self, "dlq-ynab-transactions-queue"),
            ),
            visibility_timeout=DEFAULT_LAMBDA_QUEUE_VISIBILITY_TIMEOUT,
        )

        TransactionProcessorFn = aws_lambda_python.PythonFunction(
            self,
            "TransactionProcessor",
            entry="../consumer",
            index="./index.py",
            handler="handler",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            timeout=DEFAULT_LAMBDA_TIMEOUT,
            memory_size=DEFAULT_LAMBDA_MEMORY,
            tracing=aws_lambda.Tracing.ACTIVE,
            bundling=aws_lambda_python.BundlingOptions(
                environment={
                    # https://github.com/aws/aws-cdk/issues/21867
                    "POETRY_VIRTUALENVS_IN_PROJECT": "true",
                },
            ),
        )

        TransactionProcessorFn.add_event_source(
            source=aws_lambda_event_sources.SqsEventSource(queue)
        )
