import requests
from dotenv import load_dotenv
import os
import time

load_dotenv()
API_KEY = os.getenv('REGULATIONS_API_KEY')

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
        time.sleep(0.05)
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
        return data.get("data",{}).get("attributes",{}).get("comment","")
    except Exception as e:
        print(f"    Exception for {commentsID} : {e}")
        return ""


