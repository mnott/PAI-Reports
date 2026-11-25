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

# Figures check — a lab report publishes graphics with its tables. Runs before anything
# touches the network, --dry-run included.
TEX_COUNT="$(find "$DIR" -maxdepth 1 -name "*.tex" | wc -l | tr -d '[:space:]')"
[ "$TEX_COUNT" -gt 0 ] || { echo "error: no *.tex found in $DIR" >&2; exit 1; }
if ! grep -q '\\includegraphics' "$DIR"/*.tex; then
  echo "error: $(basename "$DIR") has no \\includegraphics in its .tex — lab reports carry figures with their tables" >&2
  echo "refusing to publish — build the figures (figures/make_figures.py) and reference them in the text" >&2
  exit 1
fi

# Bibliography check — runs before anything touches the network, --dry-run included.
BIB="$DIR/Bibliography.bib"
if [ -f "$BIB" ]; then
  bad_fields="$(awk '
    /^[ \t]*[A-Za-z0-9_-]+[ \t]*=/ {
      f=$1; sub(/[ \t]*=.*$/,"",f)
      if (tolower(f) ~ /^bdsk-/) print tolower(f)
      else if (tolower(f) ~ /^(file|abstract|annote|keywords|date-added|date-modified|read|rating)$/) print tolower(f)
    }' "$BIB" | sort -u)"
  if [ -n "$bad_fields" ]; then
    echo "error: $BIB contains private library fields: $(printf '%s ' $bad_fields)" >&2
    echo "refusing to publish — run scripts/trim-bib.py" >&2
    exit 1
  fi

  cited="$(cat "$DIR"/*.tex \
    | tr -d '\n' \
    | grep -oE '\\(cite|citep|citet|parencite|textcite|autocite|footcite)\*?([[:space:]]*\[[^]]*\])*[[:space:]]*\{[^}]*\}' \
    | sed -E 's/.*\{([^}]*)\}/\1/' \
    | tr ',' '\n' \
    | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
    | grep -v '^$' \
    | sort -u \
    | wc -l | tr -d '[:space:]')"
  bib_entries="$(grep -cE '^[[:space:]]*@' "$BIB")"
  if [ "$bib_entries" -gt "$cited" ]; then
    echo "error: $BIB has $bib_entries entries but $DIR cites only $cited unique keys — extra entries would leak uncited library entries" >&2
    echo "refusing to publish — run scripts/trim-bib.py" >&2
    exit 1
  fi
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

# The token travels only in the Authorization header — never in a URL, argv or output.
AUTH="Authorization: Bearer $TOKEN"

# 1. create the deposition from zenodo.json
resp="$(curl -sS -w '\n%{http_code}' -X POST "$API" \
  -H "$AUTH" -H 'Content-Type: application/json' --data @"$METADATA")"
status="${resp##*$'\n'}"
body="${resp%$'\n'*}"
case "$status" in 2*) ;; *) fail "$status" "$body" "POST $API" ;; esac

dep_id="$(printf '%s' "$body" | jq -r '.id')"
bucket="$(printf '%s' "$body" | jq -r '.links.bucket')"
[ -n "$dep_id" ] && [ "$dep_id" != null ] || fail "$status" "$body" "parse deposition id"
[ -n "$bucket" ] && [ "$bucket" != null ] || fail "$status" "$body" "parse bucket link"

# 2. upload the PDF into the record's bucket
fname="$(basename "$PDF")"
resp="$(curl -sS -w '\n%{http_code}' -X PUT "$bucket/$fname" \
  -H "$AUTH" -H 'Content-Type: application/octet-stream' --data-binary @"$PDF")"
status="${resp##*$'\n'}"
body="${resp%$'\n'*}"
case "$status" in 2*) ;; *) fail "$status" "$body" "PUT $bucket/$fname" ;; esac

# 3. publish the record
resp="$(curl -sS -w '\n%{http_code}' -X POST "$API/$dep_id/actions/publish" \
  -H "$AUTH")"
status="${resp##*$'\n'}"
body="${resp%$'\n'*}"
case "$status" in 2*) ;; *) fail "$status" "$body" "POST $API/$dep_id/actions/publish" ;; esac

doi="$(printf '%s' "$body" | jq -r '.metadata.doi // .doi // .links.doi // empty')"
html="$(printf '%s' "$body" | jq -r '.links.latest_html // .links.html // empty')"
[ -n "$doi" ] || { echo "error: published (HTTP $status) but no DOI in response" >&2; exit 1; }

printf '%s\n' "$doi" >"$DOI_FILE"
echo "DOI $doi $html"
