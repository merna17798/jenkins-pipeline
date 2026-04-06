#!/bin/bash
# ─────────────────────────────────────────────────────────────
# upload-logs-to-s3.sh
# Uploads Jenkins build logs to an S3 bucket
#
# Usage:
#   ./scripts/upload-logs-to-s3.sh <bucket-name> <job-name> <build-number> <log-file>
#
# Example:
#   ./scripts/upload-logs-to-s3.sh jenkins-black-logs my-job 42 black-report.log
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# Parse arguments
BUCKET_NAME="${1:?Error: S3 bucket name is required}"
JOB_NAME="${2:?Error: Job name is required}"
BUILD_NUMBER="${3:?Error: Build number is required}"
LOG_FILE="${4:?Error: Log file path is required}"

# S3 destination path
S3_PATH="s3://${BUCKET_NAME}/logs/${JOB_NAME}/${BUILD_NUMBER}/"

echo "════════════════════════════════════════════"
echo "  Uploading logs to S3"
echo "════════════════════════════════════════════"
echo "  Bucket:       ${BUCKET_NAME}"
echo "  Job:          ${JOB_NAME}"
echo "  Build:        ${BUILD_NUMBER}"
echo "  Log file:     ${LOG_FILE}"
echo "  Destination:  ${S3_PATH}"
echo "════════════════════════════════════════════"

# Check if log file exists
if [ ! -f "${LOG_FILE}" ]; then
    echo "WARNING: Log file '${LOG_FILE}' not found. Creating empty log."
    echo "No log output captured." > "${LOG_FILE}"
fi

# Upload the log file
aws s3 cp "${LOG_FILE}" "${S3_PATH}$(basename "${LOG_FILE}")" \
    --content-type "text/plain"

echo "Upload complete: ${S3_PATH}$(basename "${LOG_FILE}")"
