#!/usr/bin/env bash
# Nightly OCR: one recursive folder job per group.
# Each line: "<group folder id> <its Processed folder id>"
# Get IDs from the Drive URL: https://drive.google.com/drive/folders/<ID>
set -u

API="http://localhost:8000"
API_KEY="YOUR_KEY"

GROUPS=(
  "GROUP_A_FOLDER_ID PROCESSED_GROUP_A_FOLDER_ID"
  "GROUP_B_FOLDER_ID PROCESSED_GROUP_B_FOLDER_ID"
  "GROUP_C_FOLDER_ID PROCESSED_GROUP_C_FOLDER_ID"
)

for entry in "${GROUPS[@]}"; do
  read -r folder processed <<< "$entry"
  echo "$(date '+%F %T') starting $folder"
  curl -s -X POST "$API/ocr/folder/$folder" \
    -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
    -d "{\"recursive\": true, \"processed_folder_id\": \"$processed\"}"
  echo
done
