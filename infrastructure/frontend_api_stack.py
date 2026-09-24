"""
Frontend API Stack
------------------
WHAT IT IS:
  Creates the API Gateway + Lambda that serves the React frontend.

WHY IT EXISTS:
  The browser cannot call AWS services directly. This stack creates a
  public HTTPS API that the React app calls. The Lambda reads from S3
  and returns JSON. API Gateway handles routing and CORS.

RESOURCES CREATED:
  1. IAM Role        — least-privilege for the API Lambda
  2. Lambda Function — lambda/api/handler.py
  3. API Gateway     — REST API with 4 routes
"""

from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_s3 as s3,
)
from constructs import Construct


class FrontendApiStack(Stack):
    """
    API Gateway + Lambda backend for the React frontend.

    Exposes
    -------
    self.api_url : str
        The base HTTPS URL of the API Gateway.
        React uses this as VITE_API_URL at build time.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        invoice_bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── IAM Role ──────────────────────────────────────────────────────────
        api_role = iam.Role(
            self,
            "ApiLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Least-privilege role for the API Lambda",
        )

        api_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # Read processed invoices
        invoice_bucket.grant_read(api_role, objects_key_pattern="processed/invoices/*")

        # Write raw invoices (for presigned URL generation)
        invoice_bucket.grant_put(api_role, objects_key_pattern="raw/invoices/*")

        # ── Lambda ────────────────────────────────────────────────────────────
        self.api_lambda = lambda_.Function(
            self,
            "ApiHandler",
            function_name="invoice-api",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambda/api"),
            handler="handler.lambda_handler",
            role=api_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "INVOICE_BUCKET":    invoice_bucket.bucket_name,
                "RAW_PREFIX":        "raw/invoices/",
                "PROCESSED_PREFIX":  "processed/invoices/",
            },
        )

        # ── API Gateway ───────────────────────────────────────────────────────
        # RestApi creates a public HTTPS endpoint.
        # default_cors_preflight_options handles OPTIONS requests automatically
        # so the browser's CORS preflight check succeeds.
        api = apigw.RestApi(
            self,
            "InvoiceApi",
            rest_api_name="invoice-api",
            description="REST API for the Invoice Intelligence frontend",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            ),
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        # Lambda integration — all routes proxy to the same Lambda
        integration = apigw.LambdaIntegration(
            self.api_lambda,
            proxy=True,  # passes the full event to Lambda, Lambda handles routing
        )

        # /stats
        stats = api.root.add_resource("stats")
        stats.add_method("GET", integration)

        # /invoices
        invoices = api.root.add_resource("invoices")
        invoices.add_method("GET", integration)

        # /invoices/{id}
        invoice_item = invoices.add_resource("{id}")
        invoice_item.add_method("GET", integration)

        # /upload
        upload = api.root.add_resource("upload")
        upload.add_method("POST", integration)

        # ── Outputs ───────────────────────────────────────────────────────────
        self.api_url = api.url

        CfnOutput(
            self,
            "ApiUrl",
            value=api.url,
            description="API Gateway base URL — set as VITE_API_URL in frontend build",
            export_name="InvoiceApiUrl",
        )

        CfnOutput(
            self,
            "ApiLambdaName",
            value=self.api_lambda.function_name,
            description="API Lambda function name",
        )
