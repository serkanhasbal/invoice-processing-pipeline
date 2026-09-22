"""
Analytics Stack
---------------
WHAT IT IS:
  A CDK Stack that defines the analytics layer:
  Glue Data Catalog (database + table schema) and Athena (workgroup +
  query results location).

WHY IT EXISTS:
  Athena cannot query S3 data without a schema that describes the columns
  and data types. The Glue Data Catalog holds that schema. This stack
  defines both so that once Lambda writes processed invoices to S3, you
  can immediately run SQL queries against them.

LAYER: Infrastructure as Code (runs on your laptop via cdk deploy)

HOW THE THREE SERVICES RELATE:
  Amazon S3
    - stores the actual processed invoice JSON files
    - is the source of truth for all data

  AWS Glue Data Catalog
    - stores ONLY metadata: table name, column names, data types, S3 location
    - does NOT contain any invoice data itself
    - think of it as the "index" or "table of contents" for S3

  Amazon Athena
    - receives SQL queries from you
    - looks up the schema in Glue to understand what columns exist
    - reads the actual JSON files from S3
    - writes query results (CSV) to athena-results/ in S3

RESOURCES CREATED:
  1. Glue Database    -- logical container named "invoice_db"
  2. Glue Table       -- schema definition for the invoices table
  3. Athena Workgroup -- named query execution environment with result location
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_glue as glue,
    aws_athena as athena,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct


class AnalyticsStack(Stack):
    """
    Defines the Glue Data Catalog and Athena resources for invoice analytics.

    Parameters
    ----------
    invoice_bucket : s3.Bucket
        The S3 bucket from StorageStack. Glue table points to the
        processed/invoices/ prefix; Athena writes results to athena-results/.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        invoice_bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------ #
        # 1. Glue Database                                                    #
        # ------------------------------------------------------------------ #
        # A Glue database is just a logical namespace -- a folder for tables.
        # It does not store any data. Think of it like a database in PostgreSQL
        # that you CREATE DATABASE to organise tables inside.

        glue_database = glue.CfnDatabase(
            self,
            "InvoiceDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="invoice_db",
                description="Glue database for invoice pipeline analytics",
            ),
        )

        # ------------------------------------------------------------------ #
        # 2. Glue Table (invoice schema)                                      #
        # ------------------------------------------------------------------ #
        # This is the schema definition. It tells Athena:
        #   - which S3 path to read from
        #   - what format the files are in (JSON)
        #   - what each column is named and what data type it holds
        #
        # IMPORTANT: This table definition does NOT create or move any data.
        # It is pure metadata. When you run an Athena query, Athena reads
        # this table definition to know how to interpret the JSON files in S3.
        #
        # Column type decisions:
        #   string  -- for IDs, names, status, codes (no arithmetic needed)
        #   double  -- for monetary amounts (supports decimals)
        #   date    -- for invoice_date and due_date (enables date functions)
        #
        # Line items as array<struct<...>>:
        #   Athena natively supports nested arrays of structs.
        #   This lets you query individual line items with CROSS JOIN UNNEST().
        #   The alternative (storing as a plain string) works but makes
        #   line-item queries very awkward.

        processed_location = (
            f"s3://{invoice_bucket.bucket_name}/processed/invoices/"
        )

        glue_table = glue.CfnTable(
            self,
            "InvoiceTable",
            catalog_id=self.account,
            database_name="invoice_db",
            table_input=glue.CfnTable.TableInputProperty(
                name="invoices",
                description="Processed invoice data extracted by Bedrock",
                table_type="EXTERNAL_TABLE",
                parameters={
                    # Tell Glue/Athena the files are JSON, one record per line.
                    "classification": "json",
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    # Where the data lives in S3.
                    location=processed_location,
                    # InputFormat/OutputFormat/SerdeInfo tell Athena how to
                    # read and parse the JSON files.
                    input_format="org.apache.hadoop.mapred.TextInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.openx.data.jsonserde.JsonSerDe",
                        parameters={"serialization.format": "1"},
                    ),
                    # Column definitions — map directly to JSON keys written by Lambda.
                    # Energy invoice schema v3.
                    columns=[
                        # ── Core invoice fields ──────────────────────────────
                        glue.CfnTable.ColumnProperty(name="vendor",             type="string", comment="Company issuing the invoice (energy/colocation provider)"),
                        glue.CfnTable.ColumnProperty(name="invoice_number",     type="string", comment="Vendor invoice reference number"),
                        glue.CfnTable.ColumnProperty(name="invoice_date",       type="date",   comment="Date invoice was issued (YYYY-MM-DD)"),
                        glue.CfnTable.ColumnProperty(name="period",             type="string", comment="Billing period in YYYY-MM format (e.g. 2024-09)"),
                        # ── Location fields ──────────────────────────────────
                        glue.CfnTable.ColumnProperty(name="city",               type="string", comment="City where the data centre is located"),
                        glue.CfnTable.ColumnProperty(name="country",            type="string", comment="Country where the data centre is located"),
                        glue.CfnTable.ColumnProperty(name="country_code",       type="string", comment="2-letter ISO country code e.g. FR GB DE CH NL"),
                        # ── Monetary fields ──────────────────────────────────
                        glue.CfnTable.ColumnProperty(name="currency",           type="string", comment="3-letter ISO currency code e.g. USD EUR GBP CHF"),
                        glue.CfnTable.ColumnProperty(name="total_amount",       type="double", comment="Total amount due in local currency including tax"),
                        glue.CfnTable.ColumnProperty(name="tax_amount",         type="double", comment="Tax portion of total_amount in local currency"),
                        glue.CfnTable.ColumnProperty(name="usd_rate",           type="double", comment="Exchange rate used: local currency units per 1 USD"),
                        glue.CfnTable.ColumnProperty(name="total_amount_usd",   type="double", comment="total_amount converted to USD using usd_rate"),
                        # ── Energy-specific fields ───────────────────────────
                        glue.CfnTable.ColumnProperty(name="total_volume_kwh",   type="double", comment="Total electricity consumption in kWh for the billing period"),
                        glue.CfnTable.ColumnProperty(name="base_rate",          type="double", comment="Energy rate per kWh in local currency"),
                        glue.CfnTable.ColumnProperty(name="current_pue",        type="double", comment="Actual Power Usage Effectiveness for this billing period"),
                        glue.CfnTable.ColumnProperty(name="pue_cap",            type="double", comment="Contractual maximum PUE allowed under service agreement"),
                        # ── Pipeline metadata ────────────────────────────────
                        glue.CfnTable.ColumnProperty(name="processed_at",           type="string",       comment="ISO timestamp when Lambda processed this invoice"),
                        glue.CfnTable.ColumnProperty(name="source_file",            type="string",       comment="Original S3 key of the raw invoice file"),
                        glue.CfnTable.ColumnProperty(name="pipeline_version",       type="string",       comment="Pipeline version e.g. 3.0"),
                        glue.CfnTable.ColumnProperty(name="processing_duration_ms", type="int",          comment="Total Lambda processing time in milliseconds"),
                        glue.CfnTable.ColumnProperty(name="bedrock_model_used",     type="string",       comment="Bedrock model ID used for extraction"),
                        glue.CfnTable.ColumnProperty(name="data_quality_warnings",  type="array<string>",comment="Non-critical issues detected during parsing"),
                    ],
                ),
            ),
            # Explicit dependency: table cannot exist without the database.
        )

        # Tell CloudFormation: create the database BEFORE the table.
        # Without this, CloudFormation may try to create them in parallel
        # and the table creation fails because the database doesn't exist yet.
        glue_table.add_dependency(glue_database)

        # ------------------------------------------------------------------ #
        # 3. Athena Workgroup                                                 #
        # ------------------------------------------------------------------ #
        # A workgroup is a named execution environment in Athena.
        # Benefits of using a workgroup vs the default:
        #   - Forces all queries to write results to a known S3 location
        #   - Lets you set per-query data scan limits (cost control)
        #   - Makes it easy to connect QuickSight to a specific workgroup
        #
        # Without enforcing the result location, each user/tool needs to
        # specify it manually every time they query -- error-prone.

        athena_results_location = (
            f"s3://{invoice_bucket.bucket_name}/athena-results/"
        )

        athena.CfnWorkGroup(
            self,
            "InvoiceWorkgroup",
            name="invoice-analytics",
            description="Athena workgroup for invoice pipeline queries",
            # Recursive delete allows removing the workgroup and its
            # saved queries when you run cdk destroy.
            recursive_delete_option=True,
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                # Enforce that all queries write results here.
                # Individual query callers cannot override this location.
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=athena_results_location,
                ),
                # Limit each query to scanning at most 1 GB of data.
                # At Athena pricing of $5/TB this means each query costs
                # at most $0.005 -- protects against expensive accidental scans.
                bytes_scanned_cutoff_per_query=1_073_741_824,  # 1 GB in bytes
                # Publish query execution metrics to CloudWatch.
                publish_cloud_watch_metrics_enabled=True,
            ),
        )

        # ------------------------------------------------------------------ #
        # 4. IAM Managed Policy for QuickSight                              #
        # ------------------------------------------------------------------ #
        # QuickSight needs explicit permission to:
        #   - Run Athena queries
        #   - Read processed invoice data from S3
        #   - Write Athena query results to S3
        #   - Read Glue Data Catalog metadata
        #
        # This policy is created here so it is ready to attach when you
        # set up QuickSight manually. In the AWS Console you will attach
        # this policy to the QuickSight service role.
        #
        # WHY A MANAGED POLICY instead of inline?
        #   QuickSight's service role is managed by AWS and cannot be
        #   directly modified via CDK. A customer-managed policy can be
        #   attached to it manually in one click.

        quicksight_policy = iam.ManagedPolicy(
            self,
            "QuickSightAthenaPolicy",
            managed_policy_name="InvoicePipeline-QuickSight-AthenaAccess",
            description="Allows QuickSight to query invoice data via Athena",
            statements=[
                # Athena: run queries and check results
                iam.PolicyStatement(
                    sid="AthenaQueryAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "athena:StartQueryExecution",
                        "athena:GetQueryExecution",
                        "athena:GetQueryResults",
                        "athena:StopQueryExecution",
                        "athena:ListQueryExecutions",
                        "athena:GetWorkGroup",
                    ],
                    resources=[
                        f"arn:aws:athena:{self.region}:{self.account}:workgroup/invoice-analytics"
                    ],
                ),
                # Glue: read the table schema
                iam.PolicyStatement(
                    sid="GlueCatalogRead",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "glue:GetDatabase",
                        "glue:GetDatabases",
                        "glue:GetTable",
                        "glue:GetTables",
                        "glue:GetPartition",
                        "glue:GetPartitions",
                        "glue:BatchGetPartition",
                    ],
                    resources=[
                        f"arn:aws:glue:{self.region}:{self.account}:catalog",
                        f"arn:aws:glue:{self.region}:{self.account}:database/invoice_db",
                        f"arn:aws:glue:{self.region}:{self.account}:table/invoice_db/invoices",
                    ],
                ),
                # S3: read processed invoice data + read/write Athena results
                iam.PolicyStatement(
                    sid="S3InvoiceDataAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:ListBucket",
                    ],
                    resources=[
                        invoice_bucket.bucket_arn,
                        f"{invoice_bucket.bucket_arn}/processed/invoices/*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="S3AthenaResultsAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                    ],
                    resources=[
                        invoice_bucket.bucket_arn,
                        f"{invoice_bucket.bucket_arn}/athena-results/*",
                    ],
                ),
            ],
        )

        # ------------------------------------------------------------------ #
        # 5. CloudFormation Outputs                                           #
        # ------------------------------------------------------------------ #
        CfnOutput(
            self,
            "GlueDatabaseName",
            value="invoice_db",
            description="Glue database name -- use in Athena: FROM invoice_db.invoices",
        )

        CfnOutput(
            self,
            "AthenaWorkgroupName",
            value="invoice-analytics",
            description="Athena workgroup to select when running queries",
        )

        CfnOutput(
            self,
            "AthenaResultsLocation",
            value=athena_results_location,
            description="S3 location where Athena writes query result CSV files",
        )

        CfnOutput(
            self,
            "ProcessedDataLocation",
            value=processed_location,
            description="S3 location that the Glue table reads invoice JSON from",
        )

        CfnOutput(
            self,
            "QuickSightPolicyArn",
            value=quicksight_policy.managed_policy_arn,
            description="Attach this policy to the QuickSight service role in IAM",
        )
