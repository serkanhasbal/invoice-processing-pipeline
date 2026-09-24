"""
Frontend Stack
--------------
WHAT IT IS:
  Creates the S3 bucket + CloudFront distribution that hosts the React app.

WHY IT EXISTS:
  React builds into static files (HTML, CSS, JS). These are uploaded to S3.
  CloudFront serves them globally over HTTPS with low latency.

  WHY CLOUDFRONT INSTEAD OF JUST S3?
    S3 static websites don't support HTTPS on custom paths. CloudFront adds:
    - HTTPS (required for browser security)
    - Global CDN (fast loading anywhere)
    - Proper SPA routing (redirects 404s to index.html)

RESOURCES CREATED:
  1. S3 Bucket (frontend) — stores the React build output
  2. CloudFront OAC       — lets CloudFront read from S3 privately
  3. CloudFront Distribution — public HTTPS endpoint
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct


class FrontendStack(Stack):
    """
    S3 + CloudFront hosting for the React frontend.

    Exposes
    -------
    self.frontend_bucket       : s3.Bucket
    self.distribution_url      : str   — the public CloudFront HTTPS URL
    self.distribution_id       : str   — used for cache invalidation after deploy
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── S3 Bucket for frontend assets ─────────────────────────────────────
        self.frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            # Block all public access — CloudFront reads via OAC, not public URLs
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── CloudFront Distribution ───────────────────────────────────────────
        # OAC (Origin Access Control) is the modern way to give CloudFront
        # private access to S3. It replaces the older OAI approach.
        self.distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    self.frontend_bucket
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                # Compress assets (gzip/brotli) for faster loading
                compress=True,
            ),
            # SPA routing: any path that doesn't match a file (e.g. /invoices/123)
            # should serve index.html so React Router handles it client-side.
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
            default_root_object="index.html",
            comment="Invoice Intelligence React App",
        )

        self.distribution_url = f"https://{self.distribution.distribution_domain_name}"
        self.distribution_id  = self.distribution.distribution_id

        # ── Outputs ───────────────────────────────────────────────────────────
        CfnOutput(
            self,
            "FrontendUrl",
            value=self.distribution_url,
            description="Public URL of the React frontend — share this link",
            export_name="FrontendUrl",
        )

        CfnOutput(
            self,
            "FrontendBucketName",
            value=self.frontend_bucket.bucket_name,
            description="S3 bucket holding the React build files",
        )

        CfnOutput(
            self,
            "CloudFrontDistributionId",
            value=self.distribution_id,
            description="CloudFront distribution ID — used for cache invalidation",
        )
