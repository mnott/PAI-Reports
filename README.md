# PAI Papers — Lab Report Series on Local and Hierarchical Coding Agents

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24274093.svg)](https://doi.org/10.5281/zenodo.24274093)

Measured experiments running agentic coding workers on local open-weight models,
on one Apple workstation (M5 Max, 128 GB unified memory), against cloud yardsticks.
Every number in these reports comes from a run on real tasks with recorded logs;
nothing is estimated.

## Papers

| # | Date | Title | Status | PDF |
|---|------|-------|--------|-----|
| 1 | 2026-10-15 | Can open-weight local models act as the workers in an agentic coding workflow? | lab report | [paper.pdf](papers/2026-10-15-local-model-workers/paper.pdf) · [DOI](https://doi.org/10.5281/zenodo.24274880) |
| 2 | 2026-10-16 | Can a local coding setup run beside normal work? (serving stack, prompt shape, harness repair) | lab report | [paper2.pdf](papers/2026-10-16-serving-and-harness/paper2.pdf) · [DOI](https://doi.org/10.5281/zenodo.24274884) |
| 3 | 2026-10-17 | Quantisation, serving and harness repair: what it takes to run a local coder beside real work | lab report — numbers pending daylight build verification | [paper3.pdf](papers/2026-10-17-quant-and-ssd/paper3.pdf) · [DOI](https://doi.org/10.5281/zenodo.24274891) |
| 4 | 2026-11-16 | Planner and worker: when a cloud planner over a local coder pays off | lab report | [paper4.pdf](papers/2026-11-16-planner-and-worker/paper4.pdf) · [DOI](https://doi.org/10.5281/zenodo.24274754) |
| 5 | 2026-11-23 | Engines, quantisation and the harness: which local model and engine make the better worker (Inkling 2 Mini, Hy4-Flash, Signal 2)? | lab report | [paper5.pdf](papers/2026-11-23-engines-and-harness/paper5.pdf) · [DOI](https://doi.org/10.5281/zenodo.24465707) |
| 6 | 2026-11-25 | Claimed and measured: Gyro-S v2 on real coding tasks, and why the test needs testing too | lab report | [paper6.pdf](papers/2026-11-25-claims-vs-real-tasks/paper6.pdf) · [DOI](https://doi.org/10.5281/zenodo.24525503) |

Each directory holds the LaTeX source, the compiled PDF and the shared bibliography.

## Publishing a paper

Each paper is published as its own Zenodo record with the PDF as the record's file
(so Zenodo shows the PDF preview and download); the series DOI stays the concept DOI.
1. Add `papers/<dir>/zenodo.json` — copy an existing one, change title, date, description, keywords.
2. Build the figures: `figures/make_figures.py` in the paper's directory (same style as report 5) and reference each figure next to its table with `\includegraphics`. Lab reports carry graphics along with their tables; `publish-paper.sh` refuses a `.tex` without them.
   The LaTeX layout (`templates/`, `tex/titlepage.tex`) is not tracked here. It lives in the PAI notes at `Notes/LocalModels/` (`templates/cfg/zz_layout.tex`, `zz_config_bib.tex`, `zz_macros.tex`, and `tex/`). Build in a scratch directory that holds a copy of both next to a copy of the paper (copy, not symlink: worker guards block links that point outside the tree): `B=$(mktemp -d); cp -R papers/<dir>/* $B/; cp -R <PAI>/Notes/LocalModels/templates <PAI>/Notes/LocalModels/tex $B/; (cd $B && latexmk -pdf paper6.tex)`, then copy the resulting PDF back and commit only the PDF.
3. Build the paper, then trim its bibliography with `scripts/trim-bib.py <your library.bib> papers/<dir>` before committing.
4. Run `ZENODO_TOKEN=... scripts/publish-paper.sh papers/<dir>` (or `ZENODO_TOKEN_FILE=...`).
5. The script writes the DOI to `papers/<dir>/zenodo.doi`; add it to the table above.
6. For a corrected paper, publish a new version of the same record: `ZENODO_TOKEN=... scripts/publish-paper.sh --new-version papers/<dir>` (add `--dry-run` to see the planned calls). The script opens a draft on the existing record id from `zenodo.doi`, replaces its files with the current PDF, sets `metadata.version` from `\def\tversion` and today's `publication_date`, publishes, writes the new DOI to `zenodo.doi` and keeps the old one in `zenodo.doi.history`.

## Findings in one line each

1. **Paper 1**: No for real application fixes at night-1 state — the local models find
   the code only when the task names the file and function.
2. **Paper 2**: The bottleneck was the serving stack, not the model — fixing the
   prefix-cache path took a local model from unusable to ~2× Sonnet wall time on
   one-function fixes; the harness itself needs repair hooks (path repair) for
   local models to function at all.
3. **Paper 3**: Quant lift replicates across families (4-bit→8-bit: 4/6→5/6 on two
   families); a 30B-A3B at 8-bit delivers rank-1 quality at half the resident memory;
   SSD-paged 125B-class models complete real tasks at ~3 tok/s — paging, not the
   model, is the limit; the remaining failure classes (invented paths, dotted tool
   names) are model-side and partly harness-repairable.
4. **Paper 4**: On small changes the local coder alone is the efficient choice (14/15, no
   cloud cost); on larger multi-file changes a Sonnet planner over the local coder matches
   Sonnet alone at 35 % less cloud cost and about six times the wall time; Sonnet over Haiku
   is cheaper and faster than Sonnet alone; the planner's waiting is a cost of its own.
5. **Paper 5**: The model family matters more than the engine version: Signal 2, a smaller model,
   passes 8 of 10 real tasks in 31 GB and two instances deliver 6.85 passed tasks per hour against 4.56
   for one Gyro-L; Inkling 2 Mini is fast but passes only 2-3 of 5 real tasks, and 7 of its 22 failures
   were faults of our own harness, which the loop guard could not see.
6. **Paper 6**: A claimed fine-tune (Gyro-S v2) fails real tasks it was not trained on —
   3/5 alone, 2/5 beside Signal 2, with early stops and missing answers; two instrument faults
   of the same night (a disabled provider logged as done, a task rewriting the bench's own
   config) would have produced wrong verdicts, so the test itself must be verified before its
   numbers count.

## Method notes

- Suite: paired A/B arms on replayed real fixes with known answers; buildless
  diff-grading during runs, build-verified verdicts in a separate daylight pass.
- Machine: one 128 GB M5 Max, one model server at a time, memory watchdog.
- Replication rule: no single-run verdicts.
- Instrumentation: PAI (open source), runs recorded in the reports.

## Plans

- arXiv submission of the series once the daylight build-verification pass
  confirms paper 3's rankings.

## License and citation

The reports are licensed under [CC BY 4.0](LICENSE). Each paper release is archived on
[Zenodo](https://zenodo.org) with its own DOI; use the "Cite this repository" button on GitHub
(from [CITATION.cff](CITATION.cff)) or the DOI shown on the release.
