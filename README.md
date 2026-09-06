# speech-units

Research code for automatic discourse/prosodic unit segmentation and its
evaluation, written between **2012 and 2018** during a PhD at the
[Laboratoire Parole et Langage](http://www.lpl-aix.fr/) (Aix-Marseille
Université), on spontaneous spoken French from the CID corpus.

**This is historical research code, published as-is.** It is not
maintained, not packaged, and most of it is not runnable standalone — see
[Status](#status) below. Nothing here has been rewritten, cleaned up, or
modernised for this release: it is published unchanged because its value
is in being what was actually run at the time, not as a usable library.
Expect Python 2, hardcoded local paths, missing modules, and dead ends.

## Related publication

Peshkov, K. & Prévot, L. (2014). *Segmentation evaluation metrics, a
comparison grounded on prosodic and discourse units*. LREC'14, Reykjavik,
pp. 321–325.
http://www.lrec-conf.org/proceedings/lrec2014/pdf/931_Paper.pdf

The `segmentools/` and `metaeval/` code below implements the boundary
precision/recall, WindowDiff, and Boundary Similarity comparisons discussed
in that paper (synthetic "damaged" segmentations compared against a
reference, across several evaluation metrics). The `ml/` code is a
separate, later experiment — not covered by the paper — on predicting
discourse-unit boundaries from linguistic/prosodic features with
scikit-learn.

## Status

None of the four directories below is a packaged, `pip install`-able
library, and most scripts are fragments (library modules or one-off
drivers) rather than turnkey command-line tools. Concretely:

- Everything is **Python 2** (print statements, `.iteritems()`, etc.). It
  has not been ported to Python 3.
- Most scripts assume the CID corpus is available locally at hardcoded
  paths (typically under something like `/Users/<name>/work/data/CID/...`)
  and will not run without it.
- `segmentools/eval/` originally depended on **NLTK**, **scikit-learn**, and
  a small third-party Cohen's-kappa snippet
  ([yorchopolis/kappa-stats](https://github.com/yorchopolis/kappa-stats))
  that were vendored in the original codebase. Those third-party files are
  **not included in this repository** (see [Third-party
  code](#third-party-code-not-included)), so `segmentools/eval/` will not
  import as-is — install `nltk` and `scikit-learn` and reconstruct
  `kappa.py` from the linked gist if you need it working again.
- `segmentools/eval/eval.py` also imports
  [**segeval**](https://github.com/cfournie/segmentation.evaluation) (the
  Boundary Similarity metric used in the LREC'14 paper) — this was always
  a genuine external dependency, never vendored, so just `pip install
  segeval` (Python 2-era versions only; it has not been maintained for
  Python 3 either).
- `metaeval/`'s scripts (`testdmg*.py`, `metaeval_run.py`, etc.) were run
  from a Python path that also had `segmentools/` and the vendored
  annotation-format library (see below) importable; they are not
  self-contained.
- `cid_access/accessCID.py` needs the (unpublished) CID corpus, and its
  own annotation-format dependency, to actually load anything.

If you want to run any of this today, treat it as a reading reference for
the approach, not a library to import.

## What's in each directory

### `segmentools/`
The core evaluation-metrics package: representations for multi-tier
annotations (`corpus.py`, `groupsegm.py`), a French rule-based chunker
(`chunker_fr.py`), a "damage" module that generates synthetically perturbed
segmentations for metric comparison (`damaged.py`, `dambatch.py`,
`damcopy.py`, `damdata.py`, `damgroup.py`, `metaeval.py`), plotting helpers
(`plotting.py`, `metaplot.py`), and the evaluation metrics themselves
under `eval/` (precision/recall, WindowDiff, kappa — `tierpr.py`,
`tierwd.py`, `kappatier.py`, `eval.py`). This is the code behind the
LREC'14 paper's metric comparisons.

### `metaeval/`
Driver and smoke-test scripts that call into `segmentools` to run the
actual meta-evaluation experiments: generate damaged copies of a reference
segmentation, evaluate each against the reference with several metrics,
and plot the results (`metaeval_run.py`, `metaeval_plot.py`,
`metaeval_multigen.py`, `checks.py`, `ipython_log.py`, and several
`test*.py` smoke tests). These are the scripts actually invoked to produce
the paper's results, kept as they were run rather than as a single
polished entry point.

### `ml/`
A separate, later experiment: extracting linguistic and prosodic features
per discourse/prosodic unit (`extract/`: `extractor.py`, `duextractor.py`,
`puextractor.py`, `data_access.py`) and testing which features predict
unit boundaries with scikit-learn and Weka (`eval/classifiers.py`,
`eval/evalcv.py`, `predict/`). The Weka-based scripts (`predict2.py`,
`weka__predict.py`) shell out to a local Weka CLI installation via
`subprocess` — Weka itself is not included or required by the Python code
directly.

### `cid_access/`
Utility scripts for loading the CID corpus's discourse-unit (DU) and
prosodic-unit (PU) annotations (`accessCID.py`), a document-vector distance
measure (`scam_dist.py`), Cython bindings to the CMU Flite text-to-speech
library (`flite.pyx`), and a small standalone analysis of discourse-marker
distribution across long/short units (`dmstats.py`, `plot_xy.py`,
`plot_xy_both.py`).

`accessCID.py`'s `NAIVE_CODERS_DU`/`NAIVE_CODERS_PU` dictionaries, which
originally listed the initials of the human annotators who manually
segmented each speaker's data, have been **pseudonymized** for this
release (`coder1`, `coder2`, ...) — the mapping preserves which annotator
coded which speakers, but not their real identities. Everything else in
this file is unchanged.

## Data: the CID corpus is not included

This code was written against the **Corpus of Interactional Data (CID)**,
produced at the Laboratoire Parole et Langage. The corpus itself — audio,
transcripts, and annotations — is **not included in this repository** and
is not covered by any license here: it has its own distribution terms and
must be obtained separately from its maintainers. No corpus audio,
transcripts, or annotation files are published in this repository.

## Third-party code (not included)

The original working codebase depended on and, in places, vendored a copy
of several third-party tools. None of that third-party code is republished
here; where scripts in this repository import it, you will need to obtain
it yourself:

- **[SPPAS](http://www.sppas.org/)** (Brigitte Bigi, LPL) — the annotation
  file I/O and data-model library (`annotationdata`) most of this code was
  originally built on top of.
- **[Prosogram](https://sites.google.com/site/prosogram/)** (Piet Mertens)
  — a Praat-based prosodic analysis tool used to generate some of the
  pitch/prosody data this code processes.
- **NLTK** and **scikit-learn** — standard PyPI packages
  (`nltk.metrics.agreement`, `sklearn.metrics`) that earlier versions of
  `segmentools/eval/` vendored a copy of; install them from PyPI instead.
- **[segeval](https://github.com/cfournie/segmentation.evaluation)**
  (Chris Fournier) — the Boundary Similarity metric implementation used by
  `segmentools/eval/eval.py`. Unlike the tools above, this one was never
  vendored in the original codebase; it was always a plain external
  dependency (`pip install segeval`), listed here only so the import in
  `eval.py` doesn't look unexplained.
- A small Cohen's-kappa implementation from
  [yorchopolis/kappa-stats](https://github.com/yorchopolis/kappa-stats).

## License

This repository's own code is released under the [MIT License](LICENSE).
This applies only to the code in this repository — it does not extend to,
and does not grant any rights over, the CID corpus or the third-party
tools listed above.
