# Invoice Intelligence

An end-to-end serverless energy invoice processing and analytics pipeline built on AWS.

🌐 **Live Demo:** https://dmihoqb6sgyur.cloudfront.net

> All data shown is synthetically generated for demonstration purposes only. No real company data, personal information, or confidential records are used.

---

## Architecture

```
Invoice PDF/PNG
    ↓
Amazon S3 (raw/invoices/)
    ↓  [S3 event notification]
AWS Lambda (invoice-processor)
    ├── reads config from AWS AppConfig
    │     (model ID, prompt version, USD exchange rates)
    ├── calls Amazon Bedrock (Nova Pro)
    │     extracts: vendor, invoice_number, period, kWh,
    │               base_rate, PUE, currency, amounts
    ├── validates and normalises response
    ├── converts total_amount → USD using AppConfig rates
    └── writes result to S3 (processed/invoices/)
         ↓
AWS Glue Data Catalog (schema/metadata)
         ↓
Amazon Athena (SQL queries)
         ↓
Amazon QuickSight (optional, manual setup)

React Frontend (S3 + CloudFront)
    ↓
API Gateway + Lambda (invoice-api)
    ↓
S3 processed/invoices/*.json
```

---

## Project Structure

```
invoice-processing/
├── app.py                              CDK entry point (4 stacks)
├── cdk.json                            CDK project config
├── requirements.txt                    CDK Python dependencies
│
├── infrastructure/
│   ├── processing_stack.py             S3 + Lambda + AppConfig + IAM + S3 trigger
│   ├── analytics_stack.py              Glue Data Catalog + Athena workgroup
│   ├── frontend_api_stack.py           API Gateway + API Lambda
│   └── frontend_stack.py               S3 + CloudFront (React hosting)
│
├── lambda/
│   ├── invoice_processor/              Invoice processing Lambda
│   │   ├── handler.py                  Entry point / orchestrator
│   │   ├── appconfig_client.py         Fetches runtime config
│   │   ├── bedrock_client.py           Calls Amazon Bedrock (v3 prompt)
│   │   └── invoice_parser.py           Validates, normalises, USD conversion
│   └── api/
│       └── handler.py                  API Lambda (serves React frontend)
│
├── frontend/                           React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Dashboard.jsx           KPI cards + charts
│   │   │   ├── InvoiceTable.jsx        Sortable invoice list
│   │   │   ├── InvoiceModal.jsx        Invoice detail view
│   │   │   ├── UploadSection.jsx       Drag-and-drop upload
│   │   │   ├── TechStack.jsx           Architecture page
│   │   │   └── ...
│   │   └── hooks/useApi.js             API fetch hook
│   └── package.json
│
├── appconfig/
│   └── invoice_config.json             Runtime config (model, rates, flags)
│
├── queries/
│   └── sample_queries.sql              11 Athena SQL queries
│
└── scripts/
    └── generate_energy_invoices.py     Synthetic invoice generator
```

---

## Invoice Schema (v3)

Extracted fields per invoice:

| Field | Type | Description |
|-------|------|-------------|
| `vendor` | string | Issuing company name |
| `invoice_number` | string | Vendor invoice reference |
| `invoice_date` | date | YYYY-MM-DD |
| `period` | string | Billing period (YYYY-MM) |
| `currency` | string | 3-letter ISO code |
| `total_amount` | double | Total due in local currency |
| `tax_amount` | double | Tax portion |
| `usd_rate` | double | Exchange rate (local per 1 USD) |
| `total_amount_usd` | double | USD-normalised total |
| `total_volume_kwh` | double | Energy consumption in kWh |
| `base_rate` | double | Rate per kWh in local currency |
| `current_pue` | double | Actual Power Usage Effectiveness |
| `pue_cap` | double | Contractual PUE maximum |
| `city` | string | Data centre city |
| `country` | string | Data centre country |
| `country_code` | string | ISO 2-letter country code |
| `data_quality_warnings` | array | Non-critical extraction issues |
| `pipeline_version` | string | e.g. "3.0" |

---

## AWS Resources

| Stack | Resources |
|-------|-----------|
| InvoiceProcessingStack | S3 bucket, Lambda (invoice-processor), AppConfig, IAM |
| InvoiceAnalyticsStack | Glue database + table, Athena workgroup |
| InvoiceFrontendApiStack | API Gateway, Lambda (invoice-api), IAM |
| InvoiceFrontendStack | S3 (frontend), CloudFront distribution |

---

## Setup

### Prerequisites
- AWS CLI configured
- Python 3.12+
- Node.js 18+

### 1. Install CDK dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Bootstrap and deploy infrastructure

```bash
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
cdk deploy --all
```

### 3. Set up frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=YOUR_API_GATEWAY_URL" > .env.local
npm run build
```

### 4. Upload frontend to S3

```bash
aws s3 sync dist/ s3://YOUR_FRONTEND_BUCKET/ --delete
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### 5. Test the pipeline

```bash
aws s3 cp your-invoice.pdf s3://invoice-pipeline-dev-306616/raw/invoices/your-invoice.pdf
aws logs tail /aws/lambda/invoice-processor --follow
```

---

## CDK Commands

| Command | Description |
|---------|-------------|
| `cdk synth` | Generate CloudFormation templates locally (no AWS changes) |
| `cdk diff` | Show what will change vs currently deployed |
| `cdk deploy --all` | Deploy all stacks |
| `cdk destroy --all` | Remove all resources |

---

## Estimated Monthly Cost

For ~100 invoices/month:

| Service | Cost |
|---------|------|
| Amazon Bedrock (Nova Pro) | ~$0.32 |
| Amazon S3 | ~$0.01 |
| Amazon Athena | ~$0.01 |
| API Gateway | ~$0.01 |
| CloudFront | ~$0.00 |
| Lambda, AppConfig, Glue | $0.00 |
| **Total** | **~$0.35/month** |

QuickSight (optional): +$18/month (1 Author, Enterprise)

---

## Tech Stack

**Backend:** Python 3.12, AWS CDK v2, Amazon Bedrock (Nova Pro), AWS Lambda, Amazon S3, AWS AppConfig, AWS Glue, Amazon Athena

**Frontend:** React 18, Vite, Tailwind CSS, Recharts, CloudFront

**IaC:** AWS CDK v2 (Python) — all infrastructure defined as code
