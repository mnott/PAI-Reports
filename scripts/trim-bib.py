#!/usr/bin/env python3
"""Trim a paper's bibliography down to exactly the entries it cites.

Usage: python3 -I scripts/trim-bib.py <full.bib> <paper-dir>

Reads cited keys from <paper-dir>/*.aux (biblatex \\abx@aux@cite{<n>}{<key>};
plain bibtex \\citation{a,b} is also accepted), copies only those entries out of
<full.bib> into <paper-dir>/Bibliography.bib, and drops private/library fields
(bdsk-*, file, abstract, annote, keywords, date-added, date-modified, read,
rating). Prints "<n> entries, missing [keys]".
"""

import glob
import re
import sys

# Fields that belong to a personal reference library, never to a published paper.
DROP = {
    "abstract",
    "annote",
    "bdsk-url-1",
    "bdsk-url-2",
    "date-added",
    "date-modified",
    "file",
    "keywords",
    "note-private",
    "rating",
    "read",
}


def cited_keys(paper_dir):
    """Citation keys from every .aux file in the paper directory."""
    keys = set()
    for aux in glob.glob(f"{paper_dir}/*.aux"):
        with open(aux, encoding="utf-8") as fh:
            text = fh.read()
        # biblatex: \abx@aux@cite{<ordinal>}{<key>}
        keys.update(re.findall(r"\\abx@aux@cite\{[^}]*\}\{([^}]*)\}", text))
        # bibtex: \citation{a,b,c}
        for group in re.findall(r"\\citation\{([^}]*)\}", text):
            keys.update(k.strip() for k in group.split(",") if k.strip())
    return sorted(keys)


def entry_text(src, key):
    """The full entry for `key` in bib source `src`, with dropped fields removed."""
    m = re.search(r"@(\w+)\{" + re.escape(key) + r",", src)
    if not m:
        return None
    # brace-match to the end of the entry
    i, depth = m.end(), 1
    while depth and i < len(src):
        depth += {"{": 1, "}": -1}.get(src[i], 0)
        i += 1
    text = src[m.start():i]

    pat = re.compile(r"\n\s*([A-Za-z0-9_-]+)\s*=\s*")
    fields = [(fm.start(), fm.group(1).lower()) for fm in pat.finditer(text)]
    if not fields:
        return text
    keep = text[:fields[0][0]]
    for n, (start, name) in enumerate(fields):
        end = fields[n + 1][0] if n + 1 < len(fields) else text.rfind("}")
        if name not in DROP and not name.startswith("bdsk-"):
            keep += text[start:end]
    return keep.rstrip().rstrip(",") + "}\n"


def main():
    if len(sys.argv) != 3:
        print(
            "usage: python3 -I scripts/trim-bib.py <full.bib> <paper-dir>",
            file=sys.stderr,
        )
        return 1
    full, paper_dir = sys.argv[1], sys.argv[2].rstrip("/")
    keys = cited_keys(paper_dir)
    with open(full, encoding="utf-8") as fh:
        src = fh.read()

    entries, missing = [], []
    for key in keys:
        entry = entry_text(src, key)
        if entry is None:
            missing.append(key)
        else:
            entries.append(entry)

    out = f"{paper_dir}/Bibliography.bib"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(entries))
    print(f"{out}: {len(entries)} entries, missing {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
