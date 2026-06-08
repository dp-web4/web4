#!/bin/bash
# Manual smoke script for the DynamoDB backend against DynamoDB Local.
#
# This is NOT run by CI — the AWS SDK doesn't have a clean in-process
# emulator, and pulling Docker into the build matrix isn't worth it.
# Run this manually when you change the DynamoDB backend code or want
# to validate against a real-ish DDB.
#
# Prereqs:
#   1. Java 17+ installed.
#   2. DynamoDB Local downloaded + extracted:
#        wget https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.zip
#        unzip dynamodb_local_latest.zip -d ./ddb-local
#   3. AWS CLI installed for inspecting the table after the smoke runs.
#
# What this script does:
#   1. Starts DynamoDB Local on port 8765 in the background.
#   2. Creates the chapter-hub table.
#   3. Runs a small Rust program (./ddb_smoke.rs) that exercises the
#      backend's full HubStore surface: charter, society, ledger
#      append+load, law, proposals.
#   4. Tears down DynamoDB Local.
#
# Why no in-process backend test in cargo test:
#   - AWS SDK's `aws-smithy-runtime` test utilities exist but require
#     hand-authoring HTTP-level mocks; the wire shape for DynamoDB is
#     verbose and brittle. DynamoDB Local is the standard "is the real
#     SDK happy with my wire payloads" check; cargo test stays fast
#     and deps-free.

set -e

DDB_DIR="${DDB_DIR:-./ddb-local}"
DDB_PORT="${DDB_PORT:-8765}"
TABLE="${TABLE:-chapter-hub-smoke}"
HUB_ID="${HUB_ID:-$(uuidgen)}"

if [ ! -f "$DDB_DIR/DynamoDBLocal.jar" ]; then
  echo "DynamoDB Local jar not found at $DDB_DIR/DynamoDBLocal.jar"
  echo "Download with:"
  echo "  wget https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.zip"
  echo "  unzip dynamodb_local_latest.zip -d $DDB_DIR"
  exit 1
fi

echo "=== Starting DynamoDB Local on :$DDB_PORT ==="
cd "$DDB_DIR"
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb -port "$DDB_PORT" > /tmp/ddb-local.log 2>&1 &
DDB_PID=$!
cd - > /dev/null
sleep 2

cleanup() {
  echo ""
  echo "=== Stopping DynamoDB Local ==="
  kill $DDB_PID 2>/dev/null || true
  wait $DDB_PID 2>/dev/null || true
}
trap cleanup EXIT

export AWS_ACCESS_KEY_ID="local"
export AWS_SECRET_ACCESS_KEY="local"
export AWS_DEFAULT_REGION="us-east-1"
ENDPOINT="http://127.0.0.1:$DDB_PORT"

echo ""
echo "=== Creating table $TABLE ==="
aws dynamodb create-table \
  --endpoint-url "$ENDPOINT" \
  --table-name "$TABLE" \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST > /dev/null

echo ""
echo "=== Running the Rust smoke ==="
echo "hub_id = $HUB_ID"
echo "table  = $TABLE"
echo "endpoint = $ENDPOINT"
echo ""
cd "$(dirname "$0")/.."
HUB_ID="$HUB_ID" TABLE="$TABLE" ENDPOINT="$ENDPOINT" \
  cargo run -p hub-lib --features dynamodb --example dynamodb_smoke

echo ""
echo "=== Final table scan ==="
aws dynamodb scan --endpoint-url "$ENDPOINT" --table-name "$TABLE" --query 'Items[*].SK.S' --output text

echo ""
echo "=== DynamoDB smoke OK ==="
