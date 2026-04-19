import requests
import json
from dotenv import load_dotenv
import os
import time 
load_dotenv()
API_KEY = os.getenv('REGULATIONS_API_KEY')
DOCKET_ID = 'FTC-2023-0007'
OUTPUT_FILE = 'COMMENT_RAW.json'

def fetch_comments(docket_ID, max_pages = 20):
    all_comments = []
    page = 1
    while page<=max_pages:
        response = requests.get(
            "https://api.regulations.gov/v4/comments",
            params={
                "filter[docketId]": docket_ID,
                "api_key" : API_KEY, 
                "page[number]" : page,
                "page[size]" : 25, 
        
            }
        )

        if response.status_code != 200:
            print(f"Error {response.status_code} : {response.text}")
            break
        data = response.json()
        comments = data.get("data",[])
        if not comments:
            print(f"No more comments at {page}")
            break

        all_comments.extend(comments)
        print(f"Page {page} - {len(comments)} comments (Total: {len(all_comments)})")
        page += 1
        time.sleep(1.5)
    return all_comments


if __name__ == "__main__":
    print(f"Fetching comments for docget: {DOCKET_ID}")
    comments = fetch_comments(DOCKET_ID, 20)
    with open(OUTPUT_FILE,"w") as f:
        json.dump(comments,f,indent=2)
    
    print(f"\n\nDone. {len(comments)} comments save to {OUTPUT_FILE}")