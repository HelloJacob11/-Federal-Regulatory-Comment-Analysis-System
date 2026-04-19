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

def fetch_comments_details(commentsID):
    try:
        response = requests.get(
            f"https://api.regulations.gov/v4/comments/{commentsID}",
            params={
                "api_key" : API_KEY
            }
        )
        if response.status_code != 200:
            print(f"Error {response.status_code} : {response.text}")
            return ""
        data = response.json()
        return data.get(data.get("data",{}).get("attributes",{}).get("comment"),"")
    except Exception as e:
        print(f"    Exception for {commentsID} : {e}")
        return ""


if __name__ == "__main__":
    print(f"Step 1: Fetching comments for docget: {DOCKET_ID}")
    comments = fetch_comments(DOCKET_ID, 20)

    print(f"Step 2: Fetching comment details")
    result = []
    for comment in comments:
        comment_id = comment["id"]
        attrs = comment["attributes"]
        text = fetch_comments_details(comment_id)

        result.append({
            "id" : comment_id,
            "title" : attrs.get("title"),
            "postedDate" : attrs.get("postedDate"),
            "text" : text
        })
        time.sleep(1.5)

    with open(OUTPUT_FILE,"w") as f:
        json.dump(comments,f,indent=2,ensure_ascii=False)
    
    print(f"\n\nDone. {len(comments)} comments save to {OUTPUT_FILE}")