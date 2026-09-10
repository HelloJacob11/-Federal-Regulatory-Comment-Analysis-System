# Federal Regulatory Comment Analysis System

This project builds an end-to-end pipeline for collecting, processing, classifying, and analyzing public comments submitted to U.S. federal regulatory agencies through the [Regulations.gov API](https://open.gsa.gov/api/regulationsgov/). The system retrieves public comments for a given docket, cleans and preprocesses the text, classifies each comment's stance toward the proposed regulation (**Support**, **Oppose**, or **Neutral**), and serves the results through a web dashboard.

The project is designed to support policy researchers, journalists, and civic technologists who want to understand public opinion on federal regulations at scale.

**Note:** The FTC Non-Compete Rule docket (`FTC-2023-0007`) is used as the primary demonstration case, but the collection scripts also pull comments across a rotating batch of recently-modified dockets from any federal agency.

---

# Progress

- [x] Retrieve docket information (title, abstract, last-modified date)
- [x] Discover recently-modified dockets across agencies (`fetch_dockets_names`)
- [x] Fetch all comment metadata for a given docket ID
- [x] Fetch full comment text for each individual comment
- [x] Save raw comment data to dated local JSON files and merge them into one file
- [x] Clean and preprocess comment text
- [x] Classify comments as **Support**, **Oppose**, or **Neutral** using an ensemble of 5 zero-shot models
- [x] Aggregate predictions using ensemble majority voting
- [x] Generate overall stance distribution for a docket
- [x] Small-scale manual accuracy check per model against 10 hand-labeled comments (`evaluate.py`)
- [x] Serve a FastAPI backend (`main.py`) with an `/api/data` endpoint
- [x] Build a web dashboard (Overview, Where People Stand, Read the Comments) wired to the API
- [ ] Wire the dashboard to the real computed stance counts (currently serving placeholder values while the UI is being built out — see [Web Dashboard](#web-dashboard))
- [ ] Validate predictions at scale against a larger manually-labeled sample
- [ ] Perform topic modeling / theme extraction
- [ ] Identify and flag mass comment campaigns (duplicate / near-duplicate comments)
- [ ] Generate summary report of findings
- [ ] Persist results in a database instead of local JSON files (`pymongo` is already a dependency)

---

# Project Structure

```
.
├── README.md
├── requirements.txt
├── .env                        # API keys (not committed)
└── app/
    ├── main.py                 # FastAPI app: serves the dashboard + /api/data
    ├── recentDocketIDs.json    # cache of recently-modified docket IDs
    ├── COMMENT_RAW.json        # merged raw comments (all batches combined)
    ├── COMMENT_RAW_*.json      # one file per collection run, dated
    ├── COMMENT_CLEAN.json      # cleaned/preprocessed comments
    ├── backend/
    │   ├── dataCollection.py   # Regulations.gov API client + collection script
    │   ├── scraping.py         # HTML/entity cleanup of raw comment text
    │   ├── stance.py           # ensemble zero-shot stance classification
    │   └── evaluate.py         # per-model accuracy check against labeled samples
    └── templates/
        └── frontend.html       # dashboard UI (see note below)
```

---

# Requirements

- Python 3.7+
- `requests`
- `python-dotenv`
- `transformers`
- `torch`
- `fastapi`
- `uvicorn`
- `pydantic`
- `jinja2`
- `pymongo`

Install dependencies:

```bash
pip install -r requirements.txt
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

---

# Usage

## Step 1 — Collect comments

From `app/`, run:

```bash
python3 backend/dataCollection.py
```

This script has two phases:

1. **Discover dockets** — `fetch_dockets_names(count)` pulls the `count` most recently-modified dockets across all agencies and caches them to `recentDocketIDs.json`.
2. **Fetch comments** — for a slice of those dockets (set in the `if __name__ == "__main__":` block, e.g. `dockets[120:132]`), it fetches comment metadata (`fetch_comments`) then the full text of each comment (`fetch_comments_details`), and writes the results to `COMMENT_RAW_<today's date>.json`.

Notes:

- The dockets fetched must stay within the count passed to `fetch_dockets_names` — e.g. slicing `dockets[120:132]` requires `fetch_dockets_names(132)` or higher, or the slice comes back empty.
- Each run only writes its own dated file; nothing is written if the script is interrupted partway through, since the JSON dump happens once at the end of the loop.
- `main.py` automatically merges every `COMMENT_RAW_*.json` file in `app/` into `COMMENT_RAW.json` on startup.

## Step 2 — Clean and preprocess comments

```bash
python3 backend/scraping.py
```

Reads `COMMENT_RAW.json`, strips HTML tags/entities from each comment via `cleanText()`, skips empty comments, and writes `COMMENT_CLEAN.json`.

## Step 3 — Classify comment stance

```bash
python3 backend/stance.py
```

1. Loads the cleaned comments and the five zero-shot NLI models (`load_models()`).
2. Builds three docket-specific candidate labels from the docket's title and abstract (Support / Oppose / Neutral).
3. Each model independently predicts a stance per comment (`classify_stance`).
4. The final stance is chosen by majority vote across the five models, with ties broken by summed confidence scores.
5. `count_stance()` aggregates per-docket stance counts and buckets comments into support/oppose/neutral lists.

## Step 4 — Run the web dashboard

From `app/`, run:

```bash
python3 main.py
```

This starts a FastAPI server on `http://localhost:8000` serving `templates/frontend.html` and an `/api/data` endpoint.

**Important:** `main.py` is started with `uvicorn.run(app, ...)` and no `--reload`, so it does **not** hot-reload. Any time `main.py` is edited, the process must be restarted (kill it and re-run `python3 main.py`) for changes to take effect.

---

# Web Dashboard

`app/main.py` serves a single-page dashboard (`frontend.html`) with three sections:

- **Overview** — docket ID, title, comment period, and abstract, plus a search box to switch between a few sample dockets.
- **Where People Stand** — support / oppose / neutral counts.
- **Read the Comments** — a sample of comments split into "support" and "oppose" cards.

The page is a self-contained bundled HTML file (originally exported from a design tool) that renders itself client-side, then a small inline script fetches `/api/data` and patches the docket ID, title, abstract, stance counts, and comment lists into the page after it mounts.

`/api/data` currently returns placeholder values (see `get_data()` in `main.py`) while the dashboard wiring is being built out. The real computation — pulling the docket's title/abstract via `fetch_docket_info` and the stance counts via `count_stance` — is written but commented out in `main.py`, pending the topic modeling / campaign detection work above it in the pipeline.

**Note on `frontend.html`:** most of the page's markup lives as a single very large escaped JSON string inside a `<script type="__bundler/template">` tag (a bundled/exported design artifact, not hand-authored HTML). It's easy for an editor to truncate this file when saving, since it's essentially one enormous line — if the dashboard ever starts throwing "missing bundle data" or a JSON parsing error in the browser console, check that this file hasn't been corrupted before assuming the bug is elsewhere.

---

# Ensemble Models

Rather than relying on a single classifier, this project uses an ensemble of five zero-shot Natural Language Inference (NLI) models.

Each model independently classifies every comment as one of:

- **Support**
- **Oppose**
- **Neutral**

The final prediction is determined by majority vote.

If multiple labels receive the same number of votes, the tie is resolved using the cumulative confidence scores from all models.

## Models Used

| Model | Description |
|------|-------------|
| `facebook/bart-large-mnli` | BART-large fine-tuned on MNLI. A widely used baseline for zero-shot classification. |
| `cross-encoder/nli-deberta-v3-large` | DeBERTa-v3-large trained on SNLI and MNLI. Strong NLI cross-encoder. |
| `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` | DeBERTa-v3-large trained on multiple NLI datasets for broad zero-shot generalization. |
| `valhalla/distilbart-mnli-12-3` | Distilled BART model with faster inference and smaller memory footprint. |
| `FacebookAI/roberta-large-mnli` | RoBERTa-large fine-tuned on MNLI. Strong encoder-based baseline. |

## Accuracy check

`backend/evaluate.py` runs each of the five models individually against 10 hand-labeled sample comments and prints a per-model accuracy score. This is a quick sanity check on model choice, not a substitute for validating the ensemble's actual output at scale (see the Progress checklist).

---

# How It Works

## `backend/dataCollection.py`

- **`fetch_dockets_names(count)`** — retrieves the `count` most recently-modified docket IDs from the `/dockets` endpoint and caches them to `recentDocketIDs.json`.
- **`fetch_comments(docket_id, max_pages)`** — retrieves comment metadata from `/comments`, paginating 25 at a time, stopping early if a page comes back empty. Waits 1.5 seconds between requests.
- **`fetch_comments_details(comment_id)`** — retrieves the full text for a single comment via `/comments/{commentId}`. Returns an empty string on failure or if the API returns a null comment body.
- **`fetch_docket_info(docket_id)`** — retrieves a docket's title, abstract, and last-modified date.

## `backend/scraping.py`

- **`jsonLoad(inputFile, outputFile)`** — loads raw comments, skips empty entries, cleans each one via `cleanText()`, and writes the result.
- **`cleanText(text)`** — strips HTML tags, collapses whitespace, and converts/removes common HTML entities.

## `backend/stance.py`

- **`load_models()`** — loads all five Hugging Face zero-shot classification pipelines.
- **`classify_stance(text, classifier)`** — truncates a comment to 512 words, runs it through all five models, and returns the majority-vote stance with vote counts and average confidence.
- **`classify_docketID_Data(docket_id, data)`** — groups comments by docket and fetches docket info for each group.
- **`count_stance(data, classifier, docket_info)`** — builds the docket-specific Support/Oppose/Neutral labels, classifies every comment, and returns per-stance counts plus the comments bucketed by predicted stance.

## `backend/evaluate.py`

- **`evaluate_model(model_name)`** — runs one model against the 10 hand-labeled samples and prints per-sample and overall accuracy.

## `main.py`

- Merges every `COMMENT_RAW_*.json` in `app/` into `COMMENT_RAW.json` and cleans it into `COMMENT_CLEAN.json` on startup.
- **`GET /`** — serves `templates/frontend.html`.
- **`GET /api/data`** — returns the docket/stance/comment data the dashboard renders (currently placeholder values, see [Web Dashboard](#web-dashboard)).

---

# Output

## `COMMENT_RAW_<date>.json` / `COMMENT_RAW.json`

Raw comments from a single collection run / the merge of all runs. Each object includes:

- `docketID`
- `id`
- `title`
- `postedDate`
- `printtext`

## `COMMENT_CLEAN.json`

Cleaned comments. Each object includes:

- `docketID`
- `id`
- `title`
- `postedDate`
- `cleaned_text`

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
| `FTC-2023-0007` | FTC Non-Compete Rulemaking (primary demonstration case) |
| `EPA-HQ-OAR-2003-0129` | EPA Air Quality Regulation |
| `FAA-2018-1084` | FAA Aviation Regulation |

---

# Future Work

Planned extensions include:

- Wiring the dashboard to real computed stance data instead of placeholders
- BERTopic / LDA topic modeling
- Duplicate and near-duplicate detection
- Identification of mass comment campaigns
- Named entity extraction
- Automated summary report generation
- Persisting results in MongoDB instead of local JSON files

---

# License

This project uses the Regulations.gov public API.

All data retrieved through the API are public-domain U.S. government records.
