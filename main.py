from dataCollection import fetch_comments,fetch_comments_details
import json
import time

OUTPUT_FILE = 'COMMENT_RAW.json'
DOCKET_ID = 'FTC-2023-0007'

if __name__ == "__main__":
    
    print(f"Step 1: Fetching comments for docget: {DOCKET_ID}")
    comments = fetch_comments(DOCKET_ID, 20)

    print(f"Step 2: Fetching comment details")
    result = []
    for i, comment in enumerate(comments):
        print(f"{i} comment" ,end=": ")
        comment_id = comment["id"]
        attrs = comment["attributes"]
        text = fetch_comments_details(comment_id)
        result.append({
            "id" : comment_id,
            "title" : attrs.get("title"),
            "postedDate" : attrs.get("postedDate"),
            "printtext" : text
        })
        
        print(f"comment Id: {comment_id}, comment length: {len(text)}")
        time.sleep(0.05)
    
    with open(OUTPUT_FILE,"w") as f:
        json.dump(result,f,indent=2,ensure_ascii=False)
    
    
    print(f"\n\nDone. {len(comments)} comments save to {OUTPUT_FILE}")
    
    
    """
    data = json.load(open('COMMENT_RAW.json'))
    has_text = [d for d in data if d.get('printtext','').strip()]
    empty = [d for d in data if not d.get('printtext','').strip()]
    print(f'total = {len(data)}')
    print(f"Text O = {len(has_text)}")
    print(f"Empty = {len(empty)}")
    """