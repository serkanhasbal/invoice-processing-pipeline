"""
AppConfig Client
----------------
WHAT IT IS:
  A small helper module that fetches the invoice pipeline's runtime
  configuration from AWS AppConfig.

WHY IT EXISTS:
  The Lambda handler needs configuration values like the Bedrock model ID,
  temperature, and max_tokens. These live in AppConfig so you can change
  them without redeploying the Lambda function.

  Putting this logic in its own module keeps handler.py clean and makes
  the AppConfig interaction easy to find, read, and test independently.

LAYER: Application code (runs inside AWS Lambda at runtime)

HOW IT CONNECTS:
  - handler.py calls get_config() at the start of each invocation.
  - The three AppConfig IDs (app, environment, profile) are passed in
    from Lambda environment variables set by ProcessingStack.

APPCONFIG SESSION PATTERN:
  The modern AppConfig API works in two steps:
    1. StartConfigurationSession  -- creates a session, returns a token
    2. GetLatestConfiguration     -- uses the token to fetch the config

  Each Lambda invocation creates a fresh session. This is fine for a
  portfolio project. In high-throughput production systems you would
  cache the session token across warm invocations to save API calls,
  but that adds complexity we don't need yet.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)

# boto3 client for AppConfig data plane (reading config values).
# Note: there are TWO AppConfig boto3 clients:
#   "appconfig"       -- management plane (create apps, profiles, etc.)
#   "appconfigdata"   -- data plane (read config values at runtime)
# Lambda always uses appconfigdata.
_appconfig_client = boto3.client("appconfigdata")


def get_config() -> dict:
    """
    Fetch the current configuration from AWS AppConfig.

    Reads the AppConfig application ID, environment ID, and profile ID
    from Lambda environment variables, then retrieves the latest deployed
    configuration content.

    Returns
    -------
    dict
        Parsed configuration dictionary. At minimum contains:
          - bedrock_model_id  (str)
          - temperature       (float)
          - max_tokens        (int)
          - prompt_version    (str)
          - output_format     (str)

    Raises
    ------
    RuntimeError
        If the AppConfig session cannot be started or config cannot
        be retrieved.
    ValueError
        If the returned config content is empty or not valid JSON.
    """
    app_id     = os.environ["APPCONFIG_APP_ID"]
    env_id     = os.environ["APPCONFIG_ENV_ID"]
    profile_id = os.environ["APPCONFIG_PROFILE_ID"]

    logger.info(
        "Starting AppConfig session: app=%s env=%s profile=%s",
        app_id, env_id, profile_id,
    )

    # Step 1: Start a configuration session.
    # This returns an InitialConfigurationToken that we use in the next call.
    try:
        session_response = _appconfig_client.start_configuration_session(
            ApplicationIdentifier=app_id,
            EnvironmentIdentifier=env_id,
            ConfigurationProfileIdentifier=profile_id,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to start AppConfig session: {exc}"
        ) from exc

    token = session_response["InitialConfigurationToken"]

    # Step 2: Retrieve the latest configuration using the session token.
    try:
        config_response = _appconfig_client.get_latest_configuration(
            ConfigurationToken=token,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to retrieve AppConfig configuration: {exc}"
        ) from exc

    # The configuration content is a streaming body; read it into bytes.
    raw_content = config_response["Configuration"].read()

    if not raw_content:
        raise ValueError(
            "AppConfig returned empty configuration. "
            "Make sure a deployment exists for this environment."
        )

    config = json.loads(raw_content)
    logger.info("AppConfig configuration loaded: %s", list(config.keys()))
    return config
