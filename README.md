# Federal Regulatory Comment Analysis System

This project builds an end-to-end pipeline for collecting, processing, and analyzing public comments submitted to U.S. federal regulatory agencies via the [Regulations.gov API](https://open.gsa.gov/api/regulationsgov/). The goal is to extract meaningful insights from large volumes of public comments on regulatory dockets — identifying key themes, sentiment, and patterns in how the public responds to proposed rules. This system is designed to support policy researchers, journalists, and civic technologists who want to understand public opinion on federal regulations at scale.

---

## Progress

- [x] Fetch all comment metadata for a given docket ID
- [x] Fetch full comment text for each individual comment
- [x] Save raw comment data to a local JSON file
- [ ] Clean and preprocess comment text
- [ ] Perform topic modeling / theme extraction
- [ ] Sentiment analysis on comments
- [ ] Identify and flag mass comment campaigns (duplicate/near-duplicate comments)
- [ ] Generate summary report of findings
- [ ] Build visualization dashboard

---

## Requirements

- Python 3.7+
- `requests`
- `python-dotenv`

Install dependencies:

```bash
pip install requests python-dotenv
```

---

## Setup

1. **Get an API key** from [api.data.gov](https://api.data.gov/signup/). The `DEMO_KEY` can be used for testing but has very low rate limits.

2. **Create a `.env` file** in the root of the project:

```
REGULATIONS_API_KEY=your_api_key_here
```

3. **Set your target docket** in `main.py`:

```python
DOCKET_ID = 'FTC-2023-0007'
```

A docket ID is a unique identifier for a regulatory case file. It groups all related documents and public comments for a specific rulemaking. The format is typically `AGENCY-YEAR-NUMBER` (e.g. `FTC-2023-0007` refers to an FTC rulemaking from 2023).

---

## Usage

Run the script:

```bash
python main.py
```

The script runs in two steps:

**Step 1 — Fetch comment list:** Retrieves all comment metadata for the target docket, paginating through results 25 comments at a time.

**Step 2 — Fetch comment details:** For each comment retrieved in Step 1, makes an individual API call to fetch the full comment text and builds a structured result object containing the comment ID, title, posted date, and full text.

Example terminal output:

```
Step 1: Fetching comments for docket: FTC-2023-0007
Page 1 - 25 comments (Total: 25)
Page 2 - 25 comments (Total: 50)
...
Step 2: Fetching comment details
Done. 475 comments saved to COMMENT_RAW.json
```

---

## How it works

### `fetch_comments(docket_id, max_pages)`
Paginates through the `/v4/comments` endpoint filtering by docket ID. Retrieves up to `max_pages x 25` comments. Stops early if the API returns an empty page. Includes a 1.5 second delay between requests to respect rate limits.

### `fetch_comments_details(comment_id)`
Makes an individual request to `/v4/comments/{commentId}` to retrieve the full text of a single comment. Returns the comment text string, or an empty string if the request fails or the comment has no text. Errors are caught and logged without stopping the overall pipeline.

Note: Because Step 2 makes one API call per comment, large dockets with hundreds or thousands of comments will take significant time to process. For a docket with 500 comments, expect approximately 12-15 minutes of runtime due to the rate limit delay.

---

## Configuration

| Variable | Description | Default |
|---|---|---|
| `DOCKET_ID` | The regulations.gov docket ID to fetch comments for | `FTC-2023-0007` |
| `OUTPUT_FILE` | Name of the output JSON file | `COMMENT_RAW.json` |
| `max_pages` | Maximum number of pages to fetch (25 comments per page) | `20` |

---

## Output

Comments are saved to `COMMENT_RAW.json` as a JSON array. Each object in the array contains:

- `id` — unique comment ID
- `title` — comment title
- `postedDate` — date the comment was posted
- `text` — full text of the comment (fetched individually via the details endpoint)

Note: Some fields are agency-configurable and may not always be present. Fields like `email` and `phone` are never returned by the API for privacy reasons.

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