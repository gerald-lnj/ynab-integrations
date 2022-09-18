#!/usr/bin/env python3
from aws_cdk import core as cdk
from stacks import YNABIntegrationsStack

app = cdk.App()

YNABIntegrationsStack(
    app,
    "ynab-integrations-stack",
)

app.synth()
