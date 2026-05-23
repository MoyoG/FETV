# FETV

FETV is a public clip-level dataset for traffic-event and traffic-violation analysis in fisheye surveillance video. The current public dataset contains 200 short MP4 clips and a flat JSON annotation file with one annotation row per clip.

![Examples from the dataset](image.png)

## Authors

- Ahmed Abduljawad
- Nadeem Shahid Shaik
- Mohanrasu S S
- Ming-Ching Chang
- Jun-Wei Hsieh
- Munkhjargal Gochoo

## Dataset

[Link to download dataset](https://drive.google.com/drive/folders/1VMbtNo6zzWzjxVztzy842cn7xQ0rv25G?usp=drive_link)

## Dataset Size

- Public annotated clips: 200
- JSON rows: 200
- Distinct source videos represented: 9
- Annotation JSON size: 498 KiB
- Exported MP4 folder size: 563 MiB
- Clip archive size: 563 MiB

## Annotation Format

`FETV_export_public_230526_1738.json` is a flat JSON array. Each row describes one clip. The `clip_name` field is the clip identifier and each annotation is stored as a `question_*` / `answer_*` pair. Two examples are shown below.

![Driving Wrong way example](wrong_way.png)

```json
{
  "clip_name": "002_014.mp4",
    "question_date": "What is the date of the event? Return format: YYYY-MM-DD.",
    "answer_date": "2018-07-17",
    "question_time": "What is the time of the event? Return format: HH:MM:SS.",
    "answer_time": "17:06:47",
    "question_violation_type": "What is the violation type? Choose one: wrong_way, uturn, jaywalking, red_light, lane_use_control, lane_discipline, no_violation.",
    "answer_violation_type": "wrong_way",
    "question_violator_type": "What is the violator type? Choose one: car, motorcycle, pedestrian, bus, truck, na.",
    "answer_violator_type": "motorcycle",
    "question_color": "What is the violator color? Choose one: dark, light, red, green, yellow, blue, mixed, na.",
    "answer_color": "red",
    "question_initial_position": "What is the initial position of the violator? Choose one: Top-Left, Top-Center, Top-Right, Middle-Left, Middle-Center, Middle-Right, Bottom-Left, Bottom-Center, Bottom-Right, na.",
    "answer_initial_position": "Top-Right",
    "question_final_position": "What is the final position of the violator? Choose one: Top-Left, Top-Center, Top-Right, Middle-Left, Middle-Center, Middle-Right, Bottom-Left, Bottom-Center, Bottom-Right, na.",
    "answer_final_position": "Middle-Left",
    "question_initial_lane": "What is the initial lane? Choose one: 1, 2, 3, 4, na.",
    "answer_initial_lane": "1",
    "question_final_lane": "What is the final lane? Choose one: 1, 2, 3, 4, na.",
    "answer_final_lane": "2",
    "question_intersection_type": "What is the intersection type? Choose one: T-intersection, four-way intersection.",
    "answer_intersection_type": "T-intersection",
    "question_weather": "What is the weather condition? Choose one: clear, rainy, cloudy.",
    "answer_weather": "clear",
    "question_light": "What is the light condition? Choose one: daylight, night.",
    "answer_light": "daylight",
    "question_description": "Write a concise third-person description of the event. Use only visible evidence.",
    "answer_description": "On 2018-07-17 at 17:06:47, a traffic incident occurred at a T-intersection with three road segments and clearly marked lanes. Under clear weather and bright daylight conditions, a red motorcycle committed a wrong-way violation. The motorcycle entered the intersection from the top-right segment via lane 1 and traveled across the intersection to the middle-left segment, exiting through lane 2. It moved against the designated traffic flow, while other scooters were visible moving normally in the background."
}
```

![Jaywalking example](jaywalking.png)

```json
{
    "clip_name": "005_003.mp4",
    "question_date": "What is the date of the event? Return format: YYYY-MM-DD.",
    "answer_date": "2018-07-17",
    "question_time": "What is the time of the event? Return format: HH:MM:SS.",
    "answer_time": "06:04:50",
    "question_violation_type": "What is the violation type? Choose one: wrong_way, uturn, jaywalking, red_light, lane_use_control, lane_discipline, no_violation.",
    "answer_violation_type": "wrong_way",
    "question_violator_type": "What is the violator type? Choose one: car, motorcycle, pedestrian, bus, truck, na.",
    "answer_violator_type": "motorcycle",
    "question_color": "What is the violator color? Choose one: dark, light, red, green, yellow, blue, mixed, na.",
    "answer_color": "dark",
    "question_initial_position": "What is the initial position of the violator? Choose one: Top-Left, Top-Center, Top-Right, Middle-Left, Middle-Center, Middle-Right, Bottom-Left, Bottom-Center, Bottom-Right, na.",
    "answer_initial_position": "Bottom-Left",
    "question_final_position": "What is the final position of the violator? Choose one: Top-Left, Top-Center, Top-Right, Middle-Left, Middle-Center, Middle-Right, Bottom-Left, Bottom-Center, Bottom-Right, na.",
    "answer_final_position": "Top-Right",
    "question_initial_lane": "What is the initial lane? Choose one: 1, 2, 3, 4, na.",
    "answer_initial_lane": "2",
    "question_final_lane": "What is the final lane? Choose one: 1, 2, 3, 4, na.",
    "answer_final_lane": "3",
    "question_intersection_type": "What is the intersection type? Choose one: T-intersection, four-way intersection.",
    "answer_intersection_type": "four-way intersection",
    "question_weather": "What is the weather condition? Choose one: clear, rainy, cloudy.",
    "answer_weather": "clear",
    "question_light": "What is the light condition? Choose one: daylight, night.",
    "answer_light": "daylight",
    "question_description": "Write a concise third-person description of the event. Use only visible evidence.",
    "answer_description": "On 2018-07-17 at 06:04:50, a four-way intersection with multiple lanes is shown under clear daylight conditions. A dark-colored motorcycle violates traffic rules by traveling the wrong way. It enters the intersection from the bottom-left section, initially in lane 2, and proceeds across the intersection to exit at the top-right section in lane 3. The motorcycle crosses the central area and the marked crosswalks, moving against the designated traffic flow."
  }
```

## Fields

- `clip_name`: MP4 filename in the exported clip folder or archive, using `(source_video_number)_(ordered_clip_number).mp4`.
- `question_*`: natural-language question for the corresponding field.
- `answer_date`: event date in `YYYY-MM-DD` format.
- `answer_time`: event time in `HH:MM:SS` format.
- `answer_violation_type`: traffic-event class.
- `answer_violator_type`: object or road-user type.
- `answer_color`: visible color category of the road user or `na`.
- `answer_initial_position`: grid position from which the road user entered the scene or intersection.
- `answer_initial_lane`: initial lane, or `na` when not applicable.
- `answer_final_position`: grid position toward which the road user exited.
- `answer_final_lane`: final lane, or `na` when not applicable.
- `answer_intersection_type`: intersection geometry.
- `answer_weather`: weather condition.
- `answer_light`: lighting condition.
- `answer_description`: natural-language caption/report for the event.

## Intended Use

This dataset is intended for research and development in:

- Traffic-event classification from video clips.
- Traffic-violation attribute prediction.
- Fisheye traffic-scene understanding.
- Captioning or report generation for traffic events.

## Evaluation

The evaluator aligns prediction rows to ground truth by `clip_name` when both files contain unique clip names. Identifier fields such as `clip_name`, `video_id`, `clip_export_name`, `start_time`, and `end_time` are used for matching or provenance only and are not scored.

### Installation

Use Python 3.9 or newer, then install the evaluator dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The first evaluation run may download the BERTScore model, which can be about 1 GB.

### Running Evaluation

Evaluate a submission JSON file against a ground-truth JSON file:

```bash
python evaluate.py submission.json --gt groundtruth.json
```

Detailed scores are written next to the submission as `submission.results.json`.

### Submission Format

Submissions should be a flat JSON array where each object describes one exported clip. Submit `clip_name` and answer fields only. Do not include the `question_*` fields in challenge submissions.

```json
[
  {
  "clip_name": "001_000.mp4",
  "answer_date": "2026-01-01",
  "answer_time": "12:34:56",
  "answer_violation_type": "wrong_way",
  "answer_violator_type": "car",
  "answer_color": "light",
  "answer_initial_position": "Top-Left",
  "answer_initial_lane": "1",
  "answer_final_position": "Middle-Right",
  "answer_final_lane": "2",
  "answer_intersection_type": "T-intersection",
  "answer_weather": "clear",
  "answer_light": "daylight",
  "answer_description": "Dummy event."
  }
]
```

### Ground Truth Format

Ground truth may use the same answer-only structure as submissions. If a full annotation export is used as ground truth, the evaluator ignores `question_*` fields and scores the matching `answer_*` fields.

### Metrics

Categorical answer fields are evaluated with macro-averaged F1. The time field is evaluated as a binary match per row with a 7-second tolerance, then averaged. The description field is evaluated with the average of normalized CIDEr and BERTScore.

```text
MacroF1 = mean(per-field macro-F1 scores and the time-tolerance score)
DescriptionScore = (CIDEr_norm + BERTScore) / 2
FinalScore = (MacroF1 + DescriptionScore) / 2
```

Equivalently:

```text
FinalScore = 0.25 * CIDEr_norm + 0.25 * BERTScore + 0.5 * MacroF1
```

### Output

The result JSON contains per-field scores, the categorical mean, and the final score:

```json
{
  "field_scores": {
    "answer_violation_type": 0.92,
    "answer_violator_type": 0.88,
    "answer_time": 0.95,
    "answer_description": 0.71
  },
  "categorical_mean": 0.89,
  "final_score": 0.80
}
```

### Troubleshooting

- Ensure submission files are valid JSON: `python -m json.tool submission.json > /dev/null`.
- Keep `clip_name` values unchanged from the exported MP4 files.
- If BERTScore fails on the first run, check network access and available disk space for the model download.
