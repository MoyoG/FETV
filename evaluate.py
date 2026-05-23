#!/usr/bin/env python3
"""
Evaluation script for traffic violation detection submissions.
Compares a submission JSON file against a ground-truth JSON file.
- All categorical fields are evaluated using macro F1-score.
- Description fields are evaluated using the average of CIDEr (normalized) and BERTScore.
- The final score averages the categorical/time mean with the description score.
Usage:
    python evaluate.py <submission.json> [--gt groundtruth.json]
"""
from __future__ import annotations

from pyexpat import model
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from sklearn.metrics import f1_score
from bert_score import score as bert_score_fn
import bert_score.utils as _bs_utils
import bert_score.score as _bs_score
# ---------------------------------------------------------------------------
# Monkey-patch: cap model_max_length inside sent_encode to avoid
# OverflowError on Python 3.14 with Rust-backed fast tokenizers.
# The DeBERTa-xlarge-mnli model supports at most 512 tokens anyway,
# so this cap does NOT change evaluation results.
# ---------------------------------------------------------------------------
_original_sent_encode = _bs_utils.sent_encode
def _patched_sent_encode(tokenizer, sent):
    if hasattr(tokenizer, 'model_max_length') and tokenizer.model_max_length > 1_000_000:
        tokenizer.model_max_length = 512
    return _original_sent_encode(tokenizer, sent)
_bs_utils.sent_encode = _patched_sent_encode
_bs_score.sent_encode = _patched_sent_encode
# ---------------------------------------------------------------------------
# CIDEr helpers (self-contained, normalised to [0, 1])
# ---------------------------------------------------------------------------
def _tokenize(text: str) -> list[str]:
    """Simple white-space + punctuation tokenizer, lower-cased."""
    return re.findall(r"\w+", text.lower())
def _compute_ngrams(tokens: list[str], n: int) -> Counter:
    return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))
def _cider_single(candidate: str, reference: str, n: int = 4) -> float:
    """
    Compute a simplified CIDEr-like score between a single candidate and
    a single reference.  Returns a value in roughly [0, 10]; we normalise
    afterwards.
    The implementation follows the original CIDEr-D formulation but with
    a single reference and uniform IDF (since we don't have a corpus of
    reference documents).
    """
    cand_tokens = _tokenize(candidate)
    ref_tokens = _tokenize(reference)
    if not cand_tokens or not ref_tokens:
        return 0.0
    score_sum = 0.0
    for k in range(1, n + 1):
        cand_ngrams = _compute_ngrams(cand_tokens, k)
        ref_ngrams = _compute_ngrams(ref_tokens, k)
        # TF vectors (using shared vocabulary)
        common_keys = set(cand_ngrams.keys()) | set(ref_ngrams.keys())
        if not common_keys:
            continue
        cand_vec = np.array([cand_ngrams.get(ng, 0) for ng in common_keys], dtype=float)
        ref_vec = np.array([ref_ngrams.get(ng, 0) for ng in common_keys], dtype=float)
        norm_c = np.linalg.norm(cand_vec)
        norm_r = np.linalg.norm(ref_vec)
        if norm_c == 0 or norm_r == 0:
            continue
        score_sum += float(np.dot(cand_vec, ref_vec) / (norm_c * norm_r))
    # Average over n-gram orders, scale by 10 (CIDEr convention)
    return (score_sum / n) * 10.0
def cider_norm(candidates: list[str], references: list[str]) -> float:
    """Return the mean CIDEr score normalised to [0, 1]."""
    raw_scores = [
        _cider_single(c, r) for c, r in zip(candidates, references)
    ]
    # CIDEr-D theoretical max is 10; clip just in case
    normalised = [min(s / 10.0, 1.0) for s in raw_scores]
    return float(np.mean(normalised)) if normalised else 0.0
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Fields to skip during evaluation
SKIP_FIELDS = {"Comment", "start_time", "end_time", "video_id", "clip_name", "clip_export_name"}
DESCRIPTION_FIELDS = ("description", "answer_description")
TIME_FIELDS = ("time", "answer_time")
TIME_TOLERANCE_SEC = 7
CLIP_NAME_PATTERN = re.compile(r"^\d{3}_\d{3}\.mp4$")


def _load_json(path: str) -> list | dict:
    """Load a JSON file (must be valid JSON with no comments)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _warn_on_nonstandard_clip_names(rows: list[dict], label: str) -> None:
    clip_names = sorted(
        {
            str(row.get("clip_name", "")).strip()
            for row in rows
            if str(row.get("clip_name", "")).strip()
            and not CLIP_NAME_PATTERN.fullmatch(str(row.get("clip_name", "")).strip())
        }
    )
    if not clip_names:
        return
    preview = ", ".join(clip_names[:5])
    suffix = "..." if len(clip_names) > 5 else ""
    print(
        f"⚠  Warning: {label} contains {len(clip_names)} clip_name values "
        f"that do not match XXX_XXX.mp4: {preview}{suffix}",
        file=sys.stderr,
    )


def _normalize_violations(data: list[dict]) -> list[dict]:
    """
    Normalize supported annotation JSON structures into a flat list of rows.

    Supported formats:
    - New flat export: [{clip_name, answer_violation_type, ...}, ...]
    - Legacy grouped export: [{video_id, violations: [{...}, ...]}, ...]
    """
    violations = []
    if not isinstance(data, list):
        raise ValueError("Annotation JSON must be a list.")

    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Annotation JSON entries must be objects.")

        if "violations" in item:
            if not isinstance(item.get("violations"), list):
                raise ValueError("Legacy grouped entries must contain a list under 'violations'.")
            for violation in item.get("violations", []):
                if not isinstance(violation, dict):
                    raise ValueError("Violation entries must be objects.")
                violations.append(dict(violation))
        else:
            violations.append(dict(item))

    return violations


def _has_unique_clip_names(rows: list[dict]) -> bool:
    clip_names = [str(row.get("clip_name", "")).strip() for row in rows]
    return bool(clip_names) and all(clip_names) and len(set(clip_names)) == len(clip_names)


def _align_by_clip_name(gt_rows: list[dict], sub_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Align rows by clip_name when both files provide unique clip names.
    Falls back to the existing order-based behavior otherwise.
    """
    if not (_has_unique_clip_names(gt_rows) and _has_unique_clip_names(sub_rows)):
        return gt_rows, sub_rows

    sub_by_clip = {str(row["clip_name"]).strip(): row for row in sub_rows}
    aligned_gt = []
    aligned_sub = []
    missing = []
    for gt_row in gt_rows:
        clip_name = str(gt_row["clip_name"]).strip()
        sub_row = sub_by_clip.get(clip_name)
        if sub_row is None:
            missing.append(clip_name)
            continue
        aligned_gt.append(gt_row)
        aligned_sub.append(sub_row)

    extra = sorted(set(sub_by_clip) - {str(row["clip_name"]).strip() for row in gt_rows})
    if missing or extra:
        print(
            f"⚠  Warning: clip_name alignment skipped {len(missing)} missing ground-truth clips "
            f"and {len(extra)} extra submission clips.",
            file=sys.stderr,
        )
    return aligned_gt, aligned_sub


def _time_to_seconds(t: str) -> Optional[float]:
    """Convert a valid HH:MM:SS time string to total seconds."""
    try:
        parts = str(t).strip().split(":")
        if len(parts) != 3:
            return None
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    except (TypeError, ValueError):
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s < 60):
        return None
    return h * 3600 + m * 60 + s


def _detect_fields(first_violation: dict) -> Tuple[List[str], Optional[str], Optional[str]]:
    """
    From the first violation entry, determine which fields are categorical,
    which description field is present, and which time field is present.
    Returns (categorical_fields, description_field, time_field).
    """
    categorical = []
    description_field = None
    time_field = None
    for key in first_violation:
        if key in SKIP_FIELDS or key.startswith("question_"):
            continue
        if key in DESCRIPTION_FIELDS and description_field is None:
            description_field = key
        elif key in TIME_FIELDS and time_field is None:
            time_field = key
        else:
            categorical.append(key)
    return categorical, description_field, time_field
# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------
def evaluate(groundtruth_path: str, submission_path: str) -> dict:
    gt_data = _load_json(groundtruth_path)
    sub_data = _load_json(submission_path)
    gt_violations = _normalize_violations(gt_data)
    sub_violations = _normalize_violations(sub_data)
    _warn_on_nonstandard_clip_names(gt_violations, "ground truth")
    _warn_on_nonstandard_clip_names(sub_violations, "submission")
    gt_violations, sub_violations = _align_by_clip_name(gt_violations, sub_violations)
    if len(gt_violations) != len(sub_violations):
        print(
            f"⚠  Warning: Ground truth has {len(gt_violations)} violations "
            f"but submission has {len(sub_violations)}. "
            f"Evaluating only the first {min(len(gt_violations), len(sub_violations))} entries.",
            file=sys.stderr,
        )
    n = min(len(gt_violations), len(sub_violations))
    gt_violations = gt_violations[:n]
    sub_violations = sub_violations[:n]
    if not gt_violations:
        raise ValueError("No comparable annotation rows found.")
    # Determine evaluable fields from the FIRST ground-truth entry
    categorical_fields, description_field, time_field = _detect_fields(gt_violations[0])
    scores: dict[str, float] = {}
    errors: list[str] = []
    # --- Categorical fields: macro F1 ---
    for field in categorical_fields:
        gt_values = [str(v.get(field, "")).strip().lower() for v in gt_violations]
        sub_values = [str(v.get(field, "")).strip().lower() for v in sub_violations]
        # Build a unified label set for consistent encoding
        all_labels = sorted(set(gt_values) | set(sub_values))
        label_to_idx = {l: i for i, l in enumerate(all_labels)}
        gt_encoded = [label_to_idx[v] for v in gt_values]
        sub_encoded = [label_to_idx[v] for v in sub_values]
        f1 = f1_score(gt_encoded, sub_encoded, average="macro", zero_division=0)
        scores[field] = float(f1)
        print(f"  {field:30s}  macro-F1 = {f1:.4f}")
    # --- Time field: ±7 second tolerance ---
    if time_field:
        time_matches = []
        for idx, (gt_v, sub_v) in enumerate(zip(gt_violations, sub_violations), start=1):
            gt_raw = gt_v.get(time_field, "")
            sub_raw = sub_v.get(time_field, "")
            gt_seconds = _time_to_seconds(gt_raw)
            sub_seconds = _time_to_seconds(sub_raw)
            if gt_seconds is not None and sub_seconds is not None:
                diff = abs(gt_seconds - sub_seconds)
                time_matches.append(1.0 if diff <= TIME_TOLERANCE_SEC else 0.0)
            else:
                time_matches.append(0.0)
                clip_name = str(gt_v.get("clip_name") or sub_v.get("clip_name") or f"row {idx}")
                invalid_parts = []
                if gt_seconds is None:
                    invalid_parts.append(f"ground truth {time_field}={gt_raw!r}")
                if sub_seconds is None:
                    invalid_parts.append(f"submission {time_field}={sub_raw!r}")
                errors.append(
                    f"Invalid time value for {clip_name}: "
                    f"{', '.join(invalid_parts)}. Scored as incorrect."
                )
        time_score = float(np.mean(time_matches)) if time_matches else 0.0
        scores[time_field] = time_score
        print(f"  {f'{time_field} (±7s tolerance)':30s}  score = {time_score:.4f}")
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    # --- Description field: avg(CIDEr_norm, BERTScore) ---
    if description_field:
        gt_descs = [v.get(description_field, "") for v in gt_violations]
        sub_descs = [v.get(description_field, "") for v in sub_violations]
        # Filter out pairs where either side is empty
        paired = [
            (g, s)
            for g, s in zip(gt_descs, sub_descs)
            if g.strip() and s.strip()
        ]
        if paired:
            gt_paired, sub_paired = zip(*paired)
            gt_paired, sub_paired = list(gt_paired), list(sub_paired)
            # CIDEr (normalised)
            cider_val = cider_norm(sub_paired, gt_paired)
            # BERTScore (F1)
            (P, R, F1_bert), hash_val = bert_score_fn(
                sub_paired, gt_paired, model_type="microsoft/deberta-xlarge-mnli", lang="en", verbose=False, return_hash=True
            )
            print("The model's hash is: " + hash_val + "\n")
            bert_val = float(F1_bert.mean())
            desc_score = (cider_val + bert_val) / 2.0
        else:
            cider_val = 0.0
            bert_val = 0.0
            desc_score = 0.0
        scores[description_field] = desc_score
        print(f"  {description_field:30s}  CIDEr_norm={cider_val:.4f}  BERTScore={bert_val:.4f}  avg={desc_score:.4f}")
    # --- Final score: avg(mean_categorical, description) ---
    # Include date, time, and all other categorical fields in the categorical mean
    all_cat_fields = categorical_fields + ([time_field] if time_field else [])
    cat_scores = [scores[f] for f in all_cat_fields if f in scores]
    cat_mean = float(np.mean(cat_scores)) if cat_scores else 0.0
    print(f"\n  {'Categorical Mean':30s}  {cat_mean:.4f}")
    if description_field and description_field in scores:
        final_score = (cat_mean + scores[description_field]) / 2.0
    else:
        final_score = cat_mean
    print(f"\n{'='*60}")
    print(f"  Final Score: {final_score:.4f}")
    print(f"{'='*60}")
    results = {
        "field_scores": scores,
        "categorical_mean": cat_mean,
        "final_score": final_score,
    }
    if errors:
        results["errors"] = errors
    return results
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a traffic-violation submission against ground truth."
    )
    parser.add_argument(
        "submission",
        type=str,
        help="Path to the submission JSON file.",
    )
    parser.add_argument(
        "--gt",
        type=str,
        default=str(
            Path(__file__).resolve().parent / "groundtruth.json"
        ),
        help="Path to the ground-truth JSON file (default: groundtruth.json).",
    )
    args = parser.parse_args()
    results = evaluate(args.gt, args.submission)
    # Optionally dump results to a JSON file
    out_path = Path(args.submission).with_suffix(".results.json")
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nDetailed results saved to {out_path}")
    if results.get("errors"):
        print(
            f"\nEvaluation completed with {len(results['errors'])} error(s).",
            file=sys.stderr,
        )
        raise SystemExit(1)
if __name__ == "__main__":
    main()
