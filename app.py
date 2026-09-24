#!/usr/bin/env python3
"""
CDK Entry Point
---------------
Instantiates all stacks for the Invoice Intelligence pipeline.

Stack dependency order:
  1. InvoiceProcessingStack  — S3 bucket + Lambda + AppConfig (owns the data)
  2. InvoiceAnalyticsStack   — Glue + Athena (reads from processing stack bucket)
  3. FrontendApiStack        — API Gateway + Lambda (reads from processing stack bucket)
  4. FrontendStack           — S3 + CloudFront (hosts the React app)
"""

import aws_cdk as cdk
from infrastructure.processing_stack   import ProcessingStack
from infrastructure.analytics_stack    import AnalyticsStack
from infrastructure.frontend_api_stack import FrontendApiStack
from infrastructure.frontend_stack     import FrontendStack

app = cdk.App()

env = cdk.Environment(
    account="306616137196",
    region="us-east-1",
)

# Stack 1: Processing (S3 + Lambda + AppConfig)
processing = ProcessingStack(app, "InvoiceProcessingStack", env=env)

# Stack 2: Analytics (Glue + Athena)
analytics = AnalyticsStack(
    app,
    "InvoiceAnalyticsStack",
    invoice_bucket=processing.invoice_bucket,
    env=env,
)

# Stack 3: Frontend API (API Gateway + Lambda)
frontend_api = FrontendApiStack(
    app,
    "InvoiceFrontendApiStack",
    invoice_bucket=processing.invoice_bucket,
    env=env,
)

# Stack 4: Frontend hosting (S3 + CloudFront)
frontend = FrontendStack(app, "InvoiceFrontendStack", env=env)

app.synth()
