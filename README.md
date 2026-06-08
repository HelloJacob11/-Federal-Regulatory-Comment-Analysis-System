# Federal Regulatory Comment Analysis System
This project builds an end-to-end pipeline for collecting, processing, and analyzing public comments submitted to U.S. federal regulatory agencies via the [Regulations.gov API](https://open.gsa.gov/api/regulationsgov/). The goal is to extract meaningful insights from large volumes of public comments on regulatory dockets — identifying key themes, sentiment, and patterns in how the public responds to proposed rules. This system is designed to support policy researchers, journalists, and civic technologists who want to understand public opinion on federal regulations at scale.
---
## Progress
- [x] Fetch all comment metadata for a given docket ID
- [x] Fetch full comment text for each individual comment
- [x] Save raw comment data to a local JSON file
- [x] Clean and preprocess comment text
- [x] Evaluate zero-shot classification models for stance detection
- [ ] Test top models against real public comments from Regulations.gov
- [ ] Perform topic modeling / theme extraction
- [ ] Identify and flag mass comment campaigns (duplicate/near-duplicate comments)
- [ ] Generate summary report of findings
- [ ] Build visualization dashboard
---
## Requirements
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
## Setup
1. **Get a Regulations.gov API key** from [api.data.gov](https://api.data.gov/signup/). The `DEMO_KEY` can be used for testing but has very low rate limits.
2. **Get a Hugging Face token** from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). Required to download gated models during evaluation.
3. **Create a `.env` file** in the root of the project:
```
REGULATIONS_API_KEY=your_api_key_here
HF_TOKEN=your_huggingface_token_here
```
4. **Set your target docket** in `main.py`:
```python
DOCKET_ID = 'FTC-2023-0007'
```
A docket ID is a unique identifier for a regulatory case file. It groups all related documents and public comments for a specific rulemaking. The format is typically `AGENCY-YEAR-NUMBER` (e.g. `FTC-2023-0007` refers to an FTC rulemaking from 2023).
---
## Usage
### Step 1 — Fetch comments
Run the main script to collect raw comment data:
```bash
python main.py
```
The script runs in two phases:

**Phase 1 — Fetch comment list:** Retrieves all comment metadata for the target docket, paginating through results 25 comments at a time.

**Phase 2 — Fetch comment details:** For each comment retrieved in Phase 1, makes an individual API call to fetch the full comment text and builds a structured result object containing the comment ID, title, posted date, and full text.

Example terminal output:
```
Step 1: Fetching comments for docket: FTC-2023-0007
Page 1 - 25 comments (Total: 25)
Page 2 - 25 comments (Total: 50)
...
Step 2: Fetching comment details
Done. 475 comments saved to COMMENT_RAW.json
```

### Step 2 — Clean and preprocess
Run the cleaning script to process raw comments into analysis-ready text:
```bash
python scrap.py
```
This reads `COMMENT_RAW.json` and outputs `COMMENT_CLEAN.json`.

Example terminal output:
```
# of skipped_empty:  3
# of data:  472
```

### Step 3 — Evaluate stance detection models
Run the evaluation script to benchmark zero-shot classification models:
```bash
python evaluate.py
```
This tests each candidate model against 10 hand-labeled sample comments, classifying each as **support**, **oppose**, or **neutral** toward the regulation. Each model's predictions are compared against the ground-truth labels and an accuracy score is printed.

Example terminal output:
```
==================================================
Model: facebook/bart-large-mnli
==================================================
O [1] answer:support | predicted:support (0.91)
X [2] answer:support | predicted:neutral (0.45)
...

Accuracy: 7/10 = 70%

==================================================
Final Comparison
==================================================
80% - MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli
80% - cross-encoder/nli-deberta-v3-large
70% - facebook/bart-large-mnli
...
```

#### Candidate models

The following five models were shortlisted for evaluation. All use a zero-shot classification approach where each comment is tested against the candidate labels via natural language inference (NLI).

| Model | Description |
|---|---|
| `facebook/bart-large-mnli` | BART-large fine-tuned on MNLI. Widely used default for zero-shot classification. |
| `cross-encoder/nli-deberta-v3-large` | DeBERTa-v3-large fine-tuned on SNLI + MNLI. Strong NLI cross-encoder. |
| `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` | DeBERTa-v3-large trained on multiple NLI datasets. Built for broad zero-shot coverage. |
| `valhalla/distilbart-mnli-12-3` | Distilled BART model for faster inference with a smaller footprint. |
| `FacebookAI/roberta-large-mnli` | RoBERTa-large fine-tuned on MNLI. Solid baseline encoder model. |

#### Current findings

All five models perform at a similar level on the 10-sample test set, with comparable accuracy and similar failure cases — they tend to get tripped up on the same comments (particularly neutral and indirectly worded opposition). The next step is to validate these results against real public comments fetched from Regulations.gov to see how they perform on noisier, real-world text.

---
## How it works
### `main.py`
#### `fetch_comments(docket_id, max_pages)`
Paginates through the `/v4/comments` endpoint filtering by docket ID. Retrieves up to `max_pages x 25` comments. Stops early if the API returns an empty page. Includes a 1.5 second delay between requests to respect rate limits.
#### `fetch_comments_details(comment_id)`
Makes an individual request to `/v4/comments/{commentId}` to retrieve the full text of a single comment. Returns the comment text string, or an empty string if the request fails or the comment has no text. Errors are caught and logged without stopping the overall pipeline.
Note: Because Step 2 makes one API call per comment, large dockets with hundreds or thousands of comments will take significant time to process. For a docket with 500 comments, expect approximately 12-15 minutes of runtime due to the rate limit delay.
### `scrap.py`
#### `jsonLoad(inputFile, outputFile)`
Loads the raw comment JSON, skips any empty/null entries, runs each comment's text through `cleanText()`, and writes the cleaned results to a new JSON file. Prints a summary of how many entries were skipped and how many were successfully processed.
#### `cleanText(text)`
Applies the following transformations in order:
| Step | Regex | Effect |
|---|---|---|
| 1 | `<[^>]+>` | Strips HTML tags |
| 2 | `\s+` | Collapses multiple whitespace into a single space |
| 3 | `&#39;` | Converts numeric HTML entity to apostrophe (`'`) |
| 4 | `&rsquo;` | Converts right single quotation mark entity to `"` |
| 5 | `&amp;` | Converts ampersand entity to ` and` |
| 6 | `&[a-zA-Z]+;` | Strips any remaining named HTML entities |

### `evaluate.py`
#### `evaluate_model(model_name)`
Loads a zero-shot classification pipeline for the given model, runs it against 10 hand-labeled sample comments using the labels `["support", "oppose", "neutral"]`, and prints per-sample predictions alongside the ground truth. Returns the overall accuracy as a percentage. Input text is truncated to 512 tokens to stay within model limits. If a model fails to load, the error is logged and it returns 0%.
---
## Configuration
| Variable | Description | Default |
|---|---|---|
| `DOCKET_ID` | The regulations.gov docket ID to fetch comments for | `FTC-2023-0007` |
| `OUTPUT_FILE` | Name of the raw output JSON file | `COMMENT_RAW.json` |
| `max_pages` | Maximum number of pages to fetch (25 comments per page) | `20` |
| `MODELS` | List of Hugging Face model IDs to evaluate | See `evaluate.py` |
| `LABELS` | Stance labels used for classification | `["support", "oppose", "neutral"]` |
---
## Output
### `COMMENT_RAW.json`
Raw comments saved as a JSON array. Each object contains:
- `id` — unique comment ID
- `title` — comment title
- `postedDate` — date the comment was posted
- `text` — full text of the comment (fetched individually via the details endpoint)

Note: Some fields are agency-configurable and may not always be present. Fields like `email` and `phone` are never returned by the API for privacy reasons.
### `COMMENT_CLEAN.json`
Cleaned comments saved as a JSON array. Each object contains:
- `id` — unique comment ID
- `title` — comment title
- `postedDate` — date the comment was posted
- `cleaned_text` — preprocessed text with HTML tags, entities, and extra whitespace removed
---
## Rate Limits
The Regulations.gov API enforces rate limits. This script includes a 1.5 second delay between requests (`time.sleep(1.5)`) to avoid hitting the limit. With a real API key the limit is 1,000 requests per hour. The `DEMO_KEY` has much stricter limits and is not recommended for fetching large numbers of comments.
---
## Pagination Note
The API returns a maximum of 5,000 records per query (250 per page × 20 pages). If a docket has more than 5,000 comments, additional pagination logic using `lastModifiedDate` as a cursor will be needed to retrieve all comments. See the [Regulations.gov API documentation](https://open.gsa.gov/api/regulationsgov/) for details.
---
## Example Docket IDs
| Docket ID | Description |
|---|---|
| `FTC-2023-0007` | FTC rulemaking on non-compete clauses |
| `EPA-HQ-OAR-2003-0129` | EPA air quality regulation |
| `FAA-2018-1084` | FAA aviation regulation |
---
## License
This project uses the Regulations.gov public API. Data retrieved is U.S. government public domain data.