# Invoice Processing Pipeline

An end-to-end AWS serverless invoice processing and analytics pipeline.

## Architecture

```
Invoice PDF/JPG/PNG
    ↓
Amazon S3 (raw)
    ↓  [S3 event notification]
AWS Lambda (invoice_processor)
    ├── reads config from AWS AppConfig
    ├── calls Amazon Bedrock
    ├── validates structured JSON response
    └── writes result to S3 (processed)
         ↓
AWS Glue Data Catalog (schema/metadata)
         ↓
Amazon Athena (SQL queries)
         ↓
Amazon QuickSight (manual — configured separately)
```

## Project Structure

```
invoice-processing/
├── app.py                          # CDK entry point
├── cdk.json                        # CDK project config
├── requirements.txt                # CDK Python dependencies
│
├── infrastructure/                 # Infrastructure as Code (CDK)
│   ├── storage_stack.py            # S3 buckets
│   ├── processing_stack.py         # Lambda + AppConfig + IAM + S3 trigger
│   └── analytics_stack.py          # Glue Data Catalog + Athena
│
├── lambda/
│   └── invoice_processor/          # Lambda application code
│       ├── handler.py              # entry point
│       ├── appconfig_client.py     # fetches runtime config from AppConfig
│       ├── bedrock_client.py       # calls Amazon Bedrock
│       ├── invoice_parser.py       # parses and validates Bedrock response
│       └── requirements.txt        # Lambda Python dependencies
│
├── appconfig/
│   └── invoice_config.json         # default AppConfig configuration values
│
└── queries/
    └── sample_queries.sql          # sample Athena SQL queries
```

## Setup

### 1. Install CDK dependencies

```bash
cd invoice-processing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Bootstrap CDK (one-time per AWS account/region)

```bash
cdk bootstrap aws://306616137196/us-east-1
```

### 3. Preview what CDK will create

```bash
cdk synth        # generates CloudFormation templates (no AWS changes)
cdk diff         # shows what will change vs what is deployed
```

### 4. Deploy

```bash
cdk deploy --all
```

### 5. Test

Upload an invoice to the raw prefix:
```bash
aws s3 cp my-invoice.pdf s3://<bucket-name>/raw/invoices/my-invoice.pdf
```

Check Lambda logs:
```bash
aws logs tail /aws/lambda/invoice-processor --follow
```

## CDK Commands Reference

| Command | What it does |
|---------|-------------|
| `cdk synth` | Renders CloudFormation templates locally. No AWS changes. Safe to run anytime. |
| `cdk diff` | Compares your local CDK code against what is currently deployed. Shows additions, changes, deletions. |
| `cdk bootstrap` | Creates a CDK staging bucket in your AWS account. Required once per account/region before first deploy. |
| `cdk deploy --all` | Deploys all stacks to AWS. Creates or updates real resources. |
| `cdk destroy --all` | Deletes all deployed stacks and resources. Use with caution. |

## Cost Notes

- **Bedrock**: Charged per token. A typical invoice costs a few cents.
- **Lambda**: Free tier covers 1M invocations/month.
- **S3**: Negligible for small volumes.
- **Athena**: $5/TB scanned. Small invoice datasets cost fractions of a cent per query.
- **QuickSight**: Separate subscription pricing when you add it manually.
