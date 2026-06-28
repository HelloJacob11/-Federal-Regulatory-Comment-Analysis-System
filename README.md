# Federal Regulatory Comment Analysis System

This project builds an end-to-end pipeline for collecting, processing, classifying, and analyzing public comments submitted to U.S. federal regulatory agencies through the [Regulations.gov API](https://open.gsa.gov/api/regulationsgov/). The system automatically retrieves every public comment for a given docket, cleans and preprocesses the text, classifies each comment's stance toward the proposed regulation (**Support**, **Oppose**, or **Neutral**), and prepares the data for downstream analyses such as topic modeling, duplicate detection, and visualization.

The project is designed to support policy researchers, journalists, and civic technologists who want to understand public opinion on federal regulations at scale.

**Note:** The FTC Non-Compete Rule docket (`FTC-2023-0007`) is currently used as a demonstration case to validate the pipeline. The system is designed to work with any public docket available through Regulations.gov.

---

# Progress

- [x] Retrieve docket information (title and abstract)
- [x] Fetch all comment metadata for a given docket ID
- [x] Fetch full comment text for each individual comment
- [x] Save raw comment data to a local JSON file
- [x] Clean and preprocess comment text
- [x] Classify comments as **Support**, **Oppose**, or **Neutral**
- [x] Aggregate predictions using ensemble majority voting
- [x] Generate overall stance distribution for an entire docket
- [ ] Validate predictions against manually labeled public comments
- [ ] Perform topic modeling / theme extraction
- [ ] Identify and flag mass comment campaigns (duplicate / near-duplicate comments)
- [ ] Generate summary report of findings
- [ ] Build visualization dashboard

---

# Requirements

- Python 3.7+
- `requests`
- `python-dotenv`
- `transformers`
- `torch`

Install dependencies:

```bash
pip install requests python-dotenv transformers torch
```

---

# Setup

### 1. Get a Regulations.gov API key

Obtain an API key from [api.data.gov](https://api.data.gov/signup/).

The `DEMO_KEY` can be used for testing but has much stricter rate limits.

### 2. Get a Hugging Face token

Create an access token from:

https://huggingface.co/settings/tokens

This is required for downloading some Hugging Face models.

### 3. Create a `.env` file

Create a `.env` file in the project root:

```text
REGULATIONS_API_KEY=your_api_key_here
HF_TOKEN=your_huggingface_token_here
```

### 4. Set the target docket

In `main.py`:

```python
DOCKET_ID = "FTC-2023-0007"
```

A docket ID uniquely identifies a federal rulemaking. The format is typically:

```
AGENCY-YEAR-NUMBER
```

For example,

```
FTC-2023-0007
```

refers to the FTC's 2023 Non-Compete Rulemaking.

---

# Usage

## Step 1 — Fetch comments

Run:

```bash
python main.py
```

The script runs in two phases.

### Phase 1 — Fetch comment metadata

Retrieves every comment associated with the specified docket, paginating through the Regulations.gov API 25 comments at a time.

Example output:

```
Step 1: Fetching comments for docket: FTC-2023-0007

Page 1 - 25 comments (Total: 25)
Page 2 - 25 comments (Total: 50)
...
```

### Phase 2 — Fetch full comment text

Each comment returned in Phase 1 only contains metadata. The script makes an additional API request for every comment to retrieve the full comment body.

Each output record contains:

- comment ID
- title
- posted date
- full comment text

Example:

```
Step 2: Fetching comment details

0 comment:
comment ID: FTC-XXXX-0001
comment length: 2150

...

Done.
475 comments saved to COMMENT_RAW.json
```

---

## Step 2 — Clean and preprocess comments

Run:

```bash
python scrap.py
```

This script reads `COMMENT_RAW.json`, removes HTML and formatting artifacts, and writes the cleaned results to `COMMENT_CLEAN.json`.

Example output:

```
# of skipped_empty: 3
# of data: 472
```

---

## Step 3 — Classify comment stance

Run:

```bash
python classify.py
```

*(Replace with your actual filename if different.)*

The classifier performs the following steps:

1. Loads the cleaned comments.
2. Retrieves the docket title and abstract from Regulations.gov.
3. Dynamically constructs three candidate labels:

```
This comment supports: <docket title> - <docket summary>

This comment opposes: <docket title> - <docket summary>

This comment is neutral regarding: <docket title> - <docket summary>
```

4. Loads five zero-shot Natural Language Inference (NLI) models.
5. Each model independently predicts the comment stance.
6. The final stance is selected using majority voting.
7. If multiple labels receive the same number of votes, the tie is broken using the summed confidence scores.

Example output:

```
Loading model: facebook/bart-large-mnli
Loading model: cross-encoder/nli-deberta-v3-large
Loading model: MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli
...

Total Comments Processed: 472

Stance Distribution:

Support: 281
Oppose: 165
Neutral: 26
```

---

# Ensemble Models

Rather than relying on a single classifier, this project uses an ensemble of five zero-shot Natural Language Inference (NLI) models.

Each model independently classifies every comment as one of:

- **Support**
- **Oppose**
- **Neutral**

The final prediction is determined by majority vote.

If multiple labels receive the same number of votes, the tie is resolved using the cumulative confidence scores from all models.

---

## Models Used

| Model | Description |
|------|-------------|
| `facebook/bart-large-mnli` | BART-large fine-tuned on MNLI. A widely used baseline for zero-shot classification. |
| `cross-encoder/nli-deberta-v3-large` | DeBERTa-v3-large trained on SNLI and MNLI. Strong NLI cross-encoder. |
| `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` | DeBERTa-v3-large trained on multiple NLI datasets for broad zero-shot generalization. |
| `valhalla/distilbart-mnli-12-3` | Distilled BART model with faster inference and smaller memory footprint. |
| `FacebookAI/roberta-large-mnli` | RoBERTa-large fine-tuned on MNLI. Strong encoder-based baseline. |

---

# How It Works

## `main.py`

### `fetch_comments(docket_id, max_pages)`

Retrieves comment metadata from the Regulations.gov `/comments` endpoint.

- Filters by docket ID
- Retrieves up to `max_pages × 25` comments
- Automatically stops when no additional pages are returned
- Waits 1.5 seconds between API requests to respect rate limits

---

### `fetch_comments_details(comment_id)`

Retrieves the complete text for a single public comment using the `/comments/{commentId}` endpoint.

Returns the comment text or an empty string if the request fails.

---

### `fetch_docket_info(docket_id)`

Retrieves the docket title and abstract.

These are later used to build context-aware zero-shot classification labels.

---

## `scrap.py`

### `jsonLoad(inputFile, outputFile)`

Loads the raw JSON file, removes empty entries, cleans each comment using `cleanText()`, and saves the processed comments.

---

### `cleanText(text)`

Applies the following transformations:

| Step | Regex | Purpose |
|------|-------|---------|
| 1 | `<[^>]+>` | Remove HTML tags |
| 2 | `\s+` | Collapse repeated whitespace |
| 3 | `&#39;` | Convert HTML apostrophe entity |
| 4 | `&rsquo;` | Convert quotation entity |
| 5 | `&amp;` | Convert ampersand entity |
| 6 | `&[a-zA-Z]+;` | Remove remaining HTML entities |

---

## `classify.py`

### `load_models()`

Loads all five Hugging Face zero-shot classification models.

---

### `classify_stance(text, classifier)`

For each comment:

1. Truncates the input to 512 words.
2. Runs inference across all five models.
3. Records each model's prediction.
4. Performs majority voting.
5. Resolves ties using cumulative confidence scores.
6. Returns:

- predicted stance
- vote counts
- average confidence

---

# Configuration

| Variable | Description | Default |
|-----------|-------------|---------|
| `DOCKET_ID` | Target Regulations.gov docket | `FTC-2023-0007` |
| `OUTPUT_FILE` | Raw output JSON filename | `COMMENT_RAW.json` |
| `max_pages` | Maximum number of pages to fetch | `20` |
| `MODELS` | Ensemble of Hugging Face NLI models | See `classify.py` |
| `LABELS` | Dynamically generated Support / Oppose / Neutral prompts based on the docket title and abstract | Generated automatically |

---

# Output

## `COMMENT_RAW.json`

Contains the raw comments.

Each object includes:

- `id`
- `title`
- `postedDate`
- `printtext`

---

## `COMMENT_CLEAN.json`

Contains cleaned comments.

Each object includes:

- `id`
- `title`
- `postedDate`
- `cleaned_text`

---

## `COMMENT_CLASSIFIED.json`

Contains the final stance predictions.

Each object includes:

- `id`
- `title`
- `postedDate`
- `cleaned_text`
- `stance`
- `votes`
- `avg_confidence`

---

# Rate Limits

The Regulations.gov API enforces request limits.

This project includes a 1.5-second delay between requests (`time.sleep(1.5)`) to reduce the likelihood of exceeding the limit.

With a personal API key, the API currently allows approximately **1,000 requests per hour**.

The `DEMO_KEY` has substantially lower limits and is not recommended for large-scale data collection.

---

# Pagination Note

The Regulations.gov API limits individual queries to approximately **5,000 records**.

If a docket exceeds this size, additional pagination logic (such as using `lastModifiedDate` as a cursor) will be required.

See the official Regulations.gov API documentation for details.

---

# Example Docket IDs

| Docket ID | Description |
|-----------|-------------|
| `FTC-2023-0007` | FTC Non-Compete Rulemaking (demonstration case used in this project) |
| `EPA-HQ-OAR-2003-0129` | EPA Air Quality Regulation |
| `FAA-2018-1084` | FAA Aviation Regulation |

---

# Future Work

Planned extensions include:

- BERTopic / LDA topic modeling
- Duplicate and near-duplicate detection
- Identification of mass comment campaigns
- Named entity extraction
- Automated summary report generation
- Interactive visualization dashboard

---

# License

This project uses the Regulations.gov public API.

All data retrieved through the API are public-domain U.S. government records.