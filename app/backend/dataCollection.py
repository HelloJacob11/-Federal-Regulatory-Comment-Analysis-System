import requests
from dotenv import load_dotenv
import os
import time
import json
from datetime import date


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
        return data.get("data",{}).get("attributes",{}).get("comment") or ""
    except Exception as e:
        print(f"    Exception for {commentsID} : {e}")
        return ""


def fetch_docket_info(docker_id):
    response = requests.get(f"https://api.regulations.gov/v4/dockets/{docker_id}"
                            ,params={"api_key": API_KEY})
    data = response.json().get("data",{}).get("attributes",{})
    #print(f"Docket Info: {data}")
    return {
        'title': data.get('title', ''),
        'dkAbstract': data.get('dkAbstract', ''),
        'modifyDate': data.get('modifyDate', '')
    }



def fetch_dockets_names(count):
    url = "https://api.regulations.gov/v4/dockets"
    params = {
        "sort" : "-lastModifiedDate",
        "api_key": API_KEY,
        "page[size]": count
    }
    response = requests.get(url, params=params)
    data = response.json().get("data", [])
    ids = [d['id'] for d in data]

    with open('recentDocketIDs.json',"w") as f:
        json.dump(ids,f,indent=2,ensure_ascii=False)
    return ids



if __name__ == "__main__":
    dockets = fetch_dockets_names(132)
    print(f"Recent Dockets: {dockets}")
    result = []
    for docket in dockets[120:132]:

        print(f"Step 1: Fetching comments for docget: {docket}")
        comments = fetch_comments(docket, 4)

        print(f"Step 2: Fetching comment details")
        for i, comment in enumerate(comments):
            print(f"{i} comment" ,end=": ")
            comment_id = comment["id"]
            attrs = comment["attributes"]
            text = fetch_comments_details(comment_id)
            result.append({
                "docketID" : docket,
                "id" : comment_id,
                "title" : attrs.get("title"),
                "postedDate" : attrs.get("postedDate"),
                "printtext" : text
            })
            
            print(f"comment Id: {comment_id}, comment length: {len(text)}")
            time.sleep(0.05)

    with open(f"COMMENT_RAW_{date.today()}.json","w") as f:
        json.dump(result,f,indent=2,ensure_ascii=False)