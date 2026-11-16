#!/usr/bin/env bash
# Publish one paper as its own Zenodo record: zenodo.json metadata + the PDF as
# the record's file, so Zenodo shows the PDF preview and download.
# Usage: scripts/publish-paper.sh [--dry-run] papers/<dir>
set -euo pipefail

for tool in curl jq; do
  command -v "$tool" >/dev/null 2>&1 || { echo "error: $tool is required" >&2; exit 1; }
done

usage() { echo "usage: scripts/publish-paper.sh [--dry-run] papers/<dir>" >&2; exit 1; }

DRY_RUN=0
DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage ;;
    -*) echo "error: unknown option $1" >&2; usage ;;
    *) [ -z "$DIR" ] || usage; DIR="${1%/}" ;;
  esac
  shift
done
[ -n "$DIR" ] || usage

METADATA="$DIR/zenodo.json"
DOI_FILE="$DIR/zenodo.doi"

[ -d "$DIR" ] || { echo "error: no such directory: $DIR" >&2; exit 1; }
[ -f "$METADATA" ] || { echo "error: missing $METADATA" >&2; exit 1; }

if [ "$DRY_RUN" -eq 0 ] && [ -f "$DOI_FILE" ]; then
  echo "already published: $(cat "$DOI_FILE")"
  exit 0
fi

pdf_count=0
PDF=""
for f in "$DIR"/*.pdf; do
  [ -e "$f" ] || continue
  pdf_count=$((pdf_count + 1))
  PDF="$f"
done
if [ "$pdf_count" -ne 1 ]; then
  echo "error: expected exactly one *.pdf in $DIR, found $pdf_count" >&2
  exit 1
fi

BASE_URL="${ZENODO_BASE_URL:-https://zenodo.org}"
API="$BASE_URL/api/deposit/depositions"

if [ "$DRY_RUN" -eq 0 ]; then
  if [ -n "${ZENODO_TOKEN:-}" ]; then
    TOKEN="$ZENODO_TOKEN"
  elif [ -n "${ZENODO_TOKEN_FILE:-}" ]; then
    [ -f "$ZENODO_TOKEN_FILE" ] || { echo "error: token file not found: $ZENODO_TOKEN_FILE" >&2; exit 1; }
    TOKEN="$(head -n1 "$ZENODO_TOKEN_FILE" | tr -d '[:space:]')"
    [ -n "$TOKEN" ] || { echo "error: token file is empty: $ZENODO_TOKEN_FILE" >&2; exit 1; }
  else
    echo "error: no token — set ZENODO_TOKEN, or ZENODO_TOKEN_FILE pointing at a file holding it" >&2
    exit 1
  fi
fi

fail() {
  local status="$1" body="$2" step="$3"
  local msg
  msg="$(printf '%s' "$body" | jq -r '.message // empty' 2>/dev/null || true)"
  [ -n "$msg" ] || msg="$body"
  echo "error: $step failed with HTTP $status: $msg" >&2
  exit 1
}

title="$(jq -r '.metadata.title' "$METADATA")"
size="$(wc -c <"$PDF" | tr -d '[:space:]')"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "dry run — nothing uploaded:"
  echo "title: $title"
  echo "pdf:   $PDF ($size bytes)"
  echo "would: POST $API with $METADATA, PUT $(basename "$PDF") into the record's bucket, POST actions/publish, write $DOI_FILE"
  exit 0
fi

# 1. create the deposition from zenodo.json
resp="$(curl -sS -w '\n%{http_code}' -X POST "$API?access_token=$TOKEN" \
  -H 'Content-Type: application/json' --data @"$METADATA")"
status="${resp##*$'\n'}"
body="${resp%$'\n'*}"
case "$status" in 2*) ;; *) fail "$status" "$body" "POST $API" ;; esac

dep_id="$(printf '%s' "$body" | jq -r '.id')"
bucket="$(printf '%s' "$body" | jq -r '.links.bucket')"
[ -n "$dep_id" ] && [ "$dep_id" != null ] || fail "$status" "$body" "parse deposition id"
[ -n "$bucket" ] && [ "$bucket" != null ] || fail "$status" "$body" "parse bucket link"

# 2. upload the PDF into the record's bucket
fname="$(basename "$PDF")"
resp="$(curl -sS -w '\n%{http_code}' -X PUT "$bucket/$fname?access_token=$TOKEN" \
  -H 'Content-Type: application/octet-stream' --data-binary @"$PDF")"
status="${resp##*$'\n'}"
body="${resp%$'\n'*}"
case "$status" in 2*) ;; *) fail "$status" "$body" "PUT $bucket/$fname" ;; esac

# 3. publish the record
resp="$(curl -sS -w '\n%{http_code}' -X POST "$API/$dep_id/actions/publish?access_token=$TOKEN")"
status="${resp##*$'\n'}"
body="${resp%$'\n'*}"
case "$status" in 2*) ;; *) fail "$status" "$body" "POST $API/$dep_id/actions/publish" ;; esac

doi="$(printf '%s' "$body" | jq -r '.metadata.doi // .links.doi // empty')"
html="$(printf '%s' "$body" | jq -r '.links.latest_html // empty')"
[ -n "$doi" ] || { echo "error: published (HTTP $status) but no DOI in response" >&2; exit 1; }

printf '%s\n' "$doi" >"$DOI_FILE"
echo "DOI $doi $html"
