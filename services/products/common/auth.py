import os, json, boto3
from datetime import datetime, timezone

TOKENS_EMPLOYEE_TABLE = os.environ["TOKENS_EMPLOYEE_TABLE"]

VALIDAR_TOKEN_FN = os.environ.get("VALIDAR_TOKEN_FN")
_lambda = boto3.client("lambda")

def get_token_from_headers(event):
    headers = event.get("headers") or {}
    token = (headers.get("authorization") or headers.get("Authorization") or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token

def validate_token_and_get_claims(token: str) -> dict:
    if not token:
        return {"statusCode": 403, "body": json.dumps({"error": "Falta token"})}
    resp = _lambda.invoke(
        FunctionName=VALIDAR_TOKEN_FN,
        InvocationType="RequestResponse",
        Payload=json.dumps({"token": token})
    )
    data = json.loads(resp["Payload"].read() or "{}")
    if "body" not in data:
        data["body"] = {}
    return data