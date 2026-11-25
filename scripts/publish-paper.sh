#!/usr/bin/env bash
# Publish one paper as its own Zenodo record: zenodo.json metadata + the PDF as
# the record's file, so Zenodo shows the PDF preview and download.
# Usage: scripts/publish-paper.sh [--dry-run] [--new-version] papers/<dir>
set -euo pipefail

for tool in curl jq; do
  command -v "$tool" >/dev/null 2>&1 || { echo "error: $tool is required" >&2; exit 1; }
done

usage() { echo "usage: scripts/publish-paper.sh [--dry-run] [--new-version] papers/<dir>" >&2; exit 1; }

DRY_RUN=0
NEW_VERSION=0
DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --new-version) NEW_VERSION=1 ;;
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

if [ "$NEW_VERSION" -eq 0 ] && [ "$DRY_RUN" -eq 0 ] && [ -f "$DOI_FILE" ]; then
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

# Version string for the draft metadata: \def\tversion{...} from the paper's .tex if present.
TEX_VERSION=""
for tex in "$DIR"/*.tex; do
  [ -e "$tex" ] || continue
  v="$(grep -oE '\\def\\tversion\{[^}]*\}' "$tex" | head -n1 | sed -E 's/.*\{([^}]*)\}/\1/' || true)"
  if [ -n "$v" ]; then TEX_VERSION="$v"; break; fi
done

title="$(jq -r '.metadata.title' "$METADATA")"
size="$(wc -c <"$PDF" | tr -d '[:space:]')"
fname="$(basename "$PDF")"

if [ "$NEW_VERSION" -eq 1 ]; then
  [ -f "$DOI_FILE" ] || { echo "error: --new-version needs $DOI_FILE (the published DOI)" >&2; exit 1; }
  old_doi="$(head -n1 "$DOI_FILE" | tr -d '[:space:]')"
  case "$old_doi" in *zenodo.*) ;; *) echo "error: cannot read a Zenodo record id from '$old_doi'" >&2; exit 1 ;; esac
  rec_id="${old_doi##*.}"

  # publication_date today, metadata.version from \def\tversion if present.
  draft_meta="$(TEX_VERSION="$TEX_VERSION" jq --arg date "$(date -u +%Y-%m-%d)" '
    .metadata.publication_date = $date
    | (if ($ENV.TEX_VERSION // "") != "" then .metadata.version = $ENV.TEX_VERSION else del(.metadata.version) end)' \
    "$METADATA")"

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "dry run — nothing uploaded:"
    echo "title: $title"
    echo "pdf:   $PDF ($size bytes)"
    echo "would: POST $API/$rec_id/actions/newversion, take links.latest_draft,"
    echo "       DELETE the draft's carried-over files, PUT $fname into the draft bucket,"
    echo "       PUT metadata (publication_date $(date -u +%Y-%m-%d)${TEX_VERSION:+, version $TEX_VERSION}), POST actions/publish,"
    echo "       write $old_doi to $DOI_FILE.history and the new DOI to $DOI_FILE"
    exit 0
  fi

  # The token travels only in the Authorization header — never in a URL, argv or output.
  AUTH="Authorization: Bearer $TOKEN"

  # 1. open a new version of the existing record
  resp="$(curl -sS -w '\n%{http_code}' -X POST "$API/$rec_id/actions/newversion" \
    -H "$AUTH")"
  status="${resp##*$'\n'}"
  body="${resp%$'\n'*}"
  case "$status" in 2*) ;; *) fail "$status" "$body" "POST $API/$rec_id/actions/newversion" ;; esac

  draft_url="$(printf '%s' "$body" | jq -r '.links.latest_draft')"
  [ -n "$draft_url" ] && [ "$draft_url" != null ] || fail "$status" "$body" "parse latest_draft link"

  # 2. drop the files carried over from the published version — the draft starts clean
  resp="$(curl -sS -w '\n%{http_code}' "$draft_url/files" -H "$AUTH")"
  status="${resp##*$'\n'}"
  body="${resp%$'\n'*}"
  case "$status" in 2*) ;; *) fail "$status" "$body" "GET $draft_url/files" ;; esac

  draft_bucket="$(printf '%s' "$body" | jq -r '.links.bucket')"
  [ -n "$draft_bucket" ] && [ "$draft_bucket" != null ] || fail "$status" "$body" "parse draft bucket link"

  while read -r file_id; do
    [ -n "$file_id" ] || continue
    resp="$(curl -sS -w '\n%{http_code}' -X DELETE "$draft_bucket/$file_id" -H "$AUTH")"
    status="${resp##*$'\n'}"
    body="${resp%$'\n'*}"
    case "$status" in 2*) ;; *) fail "$status" "$body" "DELETE $draft_bucket/$file_id" ;; esac
  done < <(printf '%s' "$body" | jq -r '(.files // .) | .[]?.id // empty')

  # 3. upload the corrected PDF into the draft bucket
  resp="$(curl -sS -w '\n%{http_code}' -X PUT "$draft_bucket/$fname" \
    -H "$AUTH" -H 'Content-Type: application/octet-stream' --data-binary @"$PDF")"
  status="${resp##*$'\n'}"
  body="${resp%$'\n'*}"
  case "$status" in 2*) ;; *) fail "$status" "$body" "PUT $draft_bucket/$fname" ;; esac

  # 4. set the draft's metadata (version + today's publication date)
  resp="$(curl -sS -w '\n%{http_code}' -X PUT "$draft_url/metadata" \
    -H "$AUTH" -H 'Content-Type: application/json' --data "$draft_meta")"
  status="${resp##*$'\n'}"
  body="${resp%$'\n'*}"
  case "$status" in 2*) ;; *) fail "$status" "$body" "PUT $draft_url/metadata" ;; esac

  # 5. publish the new version — same record, new DOI suffix
  resp="$(curl -sS -w '\n%{http_code}' -X POST "$draft_url/actions/publish" \
    -H "$AUTH")"
  status="${resp##*$'\n'}"
  body="${resp%$'\n'*}"
  case "$status" in 2*) ;; *) fail "$status" "$body" "POST $draft_url/actions/publish" ;; esac

  doi="$(printf '%s' "$body" | jq -r '.metadata.doi // .doi // .links.doi // empty')"
  html="$(printf '%s' "$body" | jq -r '.links.latest_html // .links.html // empty')"
  [ -n "$doi" ] || { echo "error: published (HTTP $status) but no DOI in response" >&2; exit 1; }

  # keep the old version's DOI as history, one line per version
  printf '%s\n' "$old_doi" >>"$DOI_FILE.history"
  printf '%s\n' "$doi" >"$DOI_FILE"
  echo "new version: DOI $doi $html (previous $old_doi kept in $DOI_FILE.history)"
  exit 0
fi

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
