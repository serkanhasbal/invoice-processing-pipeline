"""
Processing Stack
----------------
WHAT IT IS:
  A CDK Stack that owns both the S3 bucket (storage) and the Lambda
  function (processing) together.

WHY THEY ARE IN ONE STACK:
  The S3 bucket needs the Lambda ARN to set up the event notification.
  The Lambda needs the bucket ARN for its IAM permissions and environment
  variables. If these were in separate stacks, each stack would depend on
  the other, creating a circular dependency that CloudFormation cannot resolve.

  Since bucket and Lambda are tightly coupled -- the bucket triggers the
  Lambda; the Lambda reads from and writes to the bucket -- combining them
  into one stack is the correct architectural choice.

LAYER: Infrastructure as Code (runs on your laptop via cdk deploy)

RESOURCES CREATED:
  1.  S3 Bucket                -- holds raw invoices, processed data, Athena results
  2.  AppConfig Application    -- top-level config container
  3.  AppConfig Environment    -- "dev" deployment stage
  4.  AppConfig Config Profile -- named slot for the JSON config
  5.  AppConfig Hosted Config  -- the actual JSON config content
  6.  AppConfig Deployment     -- makes config available to Lambda
  7.  IAM Role                 -- least-privilege permissions for Lambda
  8.  Lambda Function          -- the invoice processor
  9.  S3 Event Notification    -- fires Lambda when raw/invoices/* is created
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_appconfig as appconfig,
)
from constructs import Construct


class ProcessingStack(Stack):
    """
    Owns the S3 bucket, Lambda function, AppConfig resources, IAM role,
    and the S3 event notification that wires them together.

    Exposes
    -------
    self.invoice_bucket : s3.Bucket
        The S3 bucket. AnalyticsStack receives this to point Glue and
        Athena at the right S3 locations.
    self.processor_lambda : lambda_.Function
        The invoice processor Lambda (exposed for reference if needed).
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------ #
        # 1. S3 Bucket                                                        #
        # ------------------------------------------------------------------ #
        self.invoice_bucket = s3.Bucket(
            self,
            "InvoiceBucket",
            bucket_name="invoice-pipeline-dev-306616",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            # DESTROY + auto_delete_objects lets `cdk destroy` clean up fully.
            # Change to RETAIN before going to production.
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ------------------------------------------------------------------ #
        # 2. AWS AppConfig                                                    #
        # ------------------------------------------------------------------ #
        # AppConfig stores runtime configuration that can be updated without
        # redeploying the Lambda. Hierarchy: Application > Environment > Profile.

        appconfig_app = appconfig.CfnApplication(
            self,
            "AppConfigApp",
            name="invoice-pipeline",
        )

        appconfig_env = appconfig.CfnEnvironment(
            self,
            "AppConfigEnv",
            application_id=appconfig_app.ref,
            name="dev",
        )

        appconfig_profile = appconfig.CfnConfigurationProfile(
            self,
            "AppConfigProfile",
            application_id=appconfig_app.ref,
            name="invoice-processor-config",
            location_uri="hosted",
        )

        with open("appconfig/invoice_config.json") as f:
            default_config_content = f.read()

        appconfig_hosted_config = appconfig.CfnHostedConfigurationVersion(
            self,
            "AppConfigHostedConfig",
            application_id=appconfig_app.ref,
            configuration_profile_id=appconfig_profile.ref,
            content=default_config_content,
            content_type="application/json",
        )

        # ALL_AT_ONCE deployment: config is applied immediately, no gradual rollout.
        appconfig_deployment_strategy = appconfig.CfnDeploymentStrategy(
            self,
            "AppConfigDeploymentStrategy",
            name="invoice-pipeline-instant",
            deployment_duration_in_minutes=0,
            growth_factor=100,
            replicate_to="NONE",
            final_bake_time_in_minutes=0,
        )

        appconfig.CfnDeployment(
            self,
            "AppConfigDeployment",
            application_id=appconfig_app.ref,
            environment_id=appconfig_env.ref,
            configuration_profile_id=appconfig_profile.ref,
            configuration_version=appconfig_hosted_config.ref,
            deployment_strategy_id=appconfig_deployment_strategy.ref,
        )

        # ------------------------------------------------------------------ #
        # 3. IAM Role for Lambda (least-privilege)                           #
        # ------------------------------------------------------------------ #
        lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Least-privilege role for the invoice processor Lambda",
        )

        # CloudWatch Logs -- required to see any Lambda output or errors.
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )

        # S3 read -- scoped to raw/invoices/ prefix only.
        self.invoice_bucket.grant_read(
            lambda_role,
            objects_key_pattern="raw/invoices/*",
        )

        # S3 write -- scoped to processed/invoices/ prefix only.
        self.invoice_bucket.grant_write(
            lambda_role,
            objects_key_pattern="processed/invoices/*",
        )

        # AppConfig read -- scoped to this application/environment/profile.
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                sid="AppConfigRead",
                effect=iam.Effect.ALLOW,
                actions=[
                    "appconfig:GetLatestConfiguration",
                    "appconfig:StartConfigurationSession",
                ],
                resources=[
                    (
                        f"arn:aws:appconfig:{self.region}:{self.account}:"
                        f"application/{appconfig_app.ref}"
                        f"/environment/{appconfig_env.ref}"
                        f"/configuration/{appconfig_profile.ref}"
                    )
                ],
            )
        )

        # Bedrock invoke -- wildcard on model ID so you can change the model
        # via AppConfig without updating the IAM policy.
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockInvoke",
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/*"
                ],
            )
        )

        # ------------------------------------------------------------------ #
        # 4. Lambda Function                                                  #
        # ------------------------------------------------------------------ #
        self.processor_lambda = lambda_.Function(
            self,
            "InvoiceProcessor",
            function_name="invoice-processor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            code=lambda_.Code.from_asset("lambda/invoice_processor"),
            handler="handler.lambda_handler",
            role=lambda_role,
            timeout=Duration.minutes(5),
            memory_size=512,
            environment={
                "INVOICE_BUCKET":       self.invoice_bucket.bucket_name,
                "RAW_PREFIX":           "raw/invoices/",
                "PROCESSED_PREFIX":     "processed/invoices/",
                "APPCONFIG_APP_ID":     appconfig_app.ref,
                "APPCONFIG_ENV_ID":     appconfig_env.ref,
                "APPCONFIG_PROFILE_ID": appconfig_profile.ref,
            },
        )

        # ------------------------------------------------------------------ #
        # 5. S3 Event Notification                                            #
        # ------------------------------------------------------------------ #
        # Fires Lambda whenever a file is created under raw/invoices/.
        # The prefix filter is CRITICAL: without it, Lambda writing to
        # processed/invoices/ would re-trigger itself endlessly.
        self.invoice_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.processor_lambda),
            s3.NotificationKeyFilter(prefix="raw/invoices/"),
        )

        # ------------------------------------------------------------------ #
        # 6. CloudFormation Outputs                                           #
        # ------------------------------------------------------------------ #
        CfnOutput(
            self,
            "InvoiceBucketName",
            value=self.invoice_bucket.bucket_name,
            description="S3 bucket holding all invoice pipeline data",
            export_name="InvoiceBucketName",
        )

        CfnOutput(
            self,
            "RawInvoicesPrefix",
            value=f"s3://{self.invoice_bucket.bucket_name}/raw/invoices/",
            description="Upload invoices to this S3 path",
        )

        CfnOutput(
            self,
            "ProcessedInvoicesPrefix",
            value=f"s3://{self.invoice_bucket.bucket_name}/processed/invoices/",
            description="Lambda writes processed JSON to this S3 path",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.processor_lambda.function_name,
            description="Name of the invoice processor Lambda function",
        )

        CfnOutput(
            self,
            "AppConfigAppId",
            value=appconfig_app.ref,
            description="AppConfig Application ID",
        )

        CfnOutput(
            self,
            "AppConfigEnvId",
            value=appconfig_env.ref,
            description="AppConfig Environment ID",
        )

        CfnOutput(
            self,
            "AppConfigProfileId",
            value=appconfig_profile.ref,
            description="AppConfig Configuration Profile ID",
        )

        CfnOutput(
            self,
            "LambdaLogGroup",
            value=f"/aws/lambda/{self.processor_lambda.function_name}",
            description="CloudWatch log group -- tail this to debug Lambda",
        )
