#!/usr/bin/env python3
"""
CDK Entry Point
---------------
This is the first file CDK reads when you run any `cdk` command.

STACK DESIGN DECISION:
  Storage and Processing are combined into one stack (InvoiceProcessingStack).
  They were originally separate, but CDK cannot resolve cross-stack references
  when Stack A needs Stack B's Lambda ARN AND Stack B needs Stack A's bucket ARN
  simultaneously — this creates a circular dependency CloudFormation cannot solve.

  Since the S3 bucket and the Lambda are tightly coupled (the bucket triggers
  the Lambda; the Lambda reads from and writes to the bucket), combining them
  into one stack is the architecturally correct choice.

  AnalyticsStack (Glue + Athena) remains separate because it only reads
  the bucket name as a string — no circular dependency there.
"""

import aws_cdk as cdk
from infrastructure.processing_stack import ProcessingStack
from infrastructure.analytics_stack import AnalyticsStack

app = cdk.App()

env = cdk.Environment(
    account="306616137196",
    region="us-east-1",
)

# Stack 1: Storage + Processing combined
# Creates S3 bucket, Lambda, AppConfig, IAM, and the S3 trigger all together.
processing = ProcessingStack(app, "InvoiceProcessingStack", env=env)

# Stack 2: Analytics
# Creates Glue Data Catalog and Athena workgroup.
# Receives the bucket as a plain string reference (bucket_name) to avoid
# any cross-stack object dependency.
analytics = AnalyticsStack(
    app,
    "InvoiceAnalyticsStack",
    invoice_bucket=processing.invoice_bucket,
    env=env,
)

app.synth()
