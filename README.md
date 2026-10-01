# speech-units

Research code from doctoral work at the Laboratoire Parole et Langage
(Aix-Marseille Université, 2012–2018) on segmenting spontaneous spoken
French into discourse and prosodic units, and on how segmentation
evaluation metrics behave.

`segmentools/` and `metaeval/` implement the comparison published in:

> Peshkov, K. & Prévot, L. (2014). Segmentation evaluation metrics, a
> comparison grounded on prosodic and discourse units. LREC'14,
> Reykjavik, pp. 321–325.
> http://www.lrec-conf.org/proceedings/lrec2014/pdf/931_Paper.pdf

A reference segmentation is perturbed synthetically and scored against
the original with boundary precision/recall, WindowDiff and Boundary
Similarity, to see how each metric responds to each kind of error.
`ml/` is a later experiment, not in the paper: predicting unit
boundaries from linguistic and prosodic features.

Current work on the same questions, in Python 3:
https://github.com/klimpe/llm-segmentation-eval

## Status

Published as it was run, with one exception: the annotator initials in
`cid_access/accessCID.py` are replaced by `coder1`, `coder2`, … The
mapping of which annotator coded which speaker is preserved; nothing
else is changed.

Read it, don't install it:
- Python 2 throughout, not ported.
- Paths to the CID corpus are hardcoded.
- Most files are library modules or one-off drivers, not command-line
  tools.
- `segmentools/eval/` needs `nltk`, `scikit-learn`, `segeval`, and a
  Cohen's-kappa implementation that was vendored and is not republished
  here.

## Contents

- `segmentools/` — multi-tier annotation representations, a French
  rule-based chunker, the synthetic damage module, and the metrics
  themselves under `eval/`.
- `metaeval/` — the drivers that produced the paper's results: generate
  damaged copies, score them, plot.
- `ml/` — per-unit feature extraction and boundary prediction with
  scikit-learn and Weka.
- `cid_access/` — loading the CID discourse-unit and prosodic-unit
  annotations, plus a discourse-marker distribution analysis.

## Data

The CID corpus is not included and is not covered by this licence. It
has its own distribution terms and must be obtained from its
maintainers. No audio, transcripts or annotation files are published
here.

## Third-party code (not included)

SPPAS (B. Bigi) for annotation file I/O, Prosogram (P. Mertens) for the
prosodic data, NLTK, scikit-learn, segeval (C. Fournier) for Boundary
Similarity, and a Cohen's-kappa snippet from yorchopolis/kappa-stats.

## Licence

MIT, for this repository's own code only.
## License

This repository's own code is released under the [MIT License](LICENSE).
This applies only to the code in this repository — it does not extend to,
and does not grant any rights over, the CID corpus or the third-party
tools listed above.
