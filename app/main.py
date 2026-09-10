#from dataCollection import fetch_comments,fetch_comments_details
import json
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import uvicorn
from backend.dataCollection import fetch_docket_info
from backend.stance import count_stance, load_models, classify_docketID_Data
from backend.scraping import jsonLoad
import glob


BASE_DIR = Path(__file__).resolve().parent          # app/

files = glob.glob('COMMENT_RAW_*.json')
merge = []
for path in files:
    data = json.load(open(path, encoding='utf-8'))
    merge.extend(data)
    print(f"{path}: {len(data)}")
json.dump(merge, open('COMMENT_RAW.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

OUTPUT_FILE = 'COMMENT_RAW.json'
CLEAN_FILE = jsonLoad("COMMENT_RAW.json","COMMENT_CLEAN.json")

#DOCKET_ID = 'FTC-2023-0007'
DOCKET_IDs = data = json.load(open("backend/recentDocketIDs.json"))
"""
MODELS = load_models()
DOCKEY_INFOs, COUNT = count_stance(json.load(open('COMMENT_CLEAN.json')), MODELS,DOCKET_IDs[0])
print("Docket Info: ", DOCKEY_INFOs[DOCKET_IDs[0]])
"""

MODELS = load_models()
current_data, DOCKEY_INFOs = classify_docketID_Data(DOCKET_IDs[0], json.load(open('COMMENT_CLEAN.json')))
#print("current = ", current_data)
COUNT, ans_comments = count_stance(current_data[DOCKET_IDs[0]], MODELS, DOCKEY_INFOs[DOCKET_IDs[0]])
#print("Docket Info: ", DOCKEY_INFOs[DOCKET_IDs[0]])
print("Stance Counts: ", COUNT.get(DOCKET_IDs[0], {}))
print("Comments: ", [len(ans_comments[0]), len(ans_comments[1]), len(ans_comments[2])])


app = FastAPI()

@app.get("/")
def read_root(request: Request):
    return FileResponse(BASE_DIR / "templates" / "frontend.html")




@app.get("/api/data")
def get_data():
    
    #docket_info = DOCKEY_INFOs.get(DOCKET_IDs[0])
    
    print(f"Counts: {COUNT.get(DOCKET_IDs[0],{})}")
    return {
            'docket_id': DOCKET_IDs[0],
            'title' : DOCKEY_INFOs[DOCKET_IDs[0]].get('title', 'N/A'),
            'dkAbstract' : DOCKEY_INFOs[DOCKET_IDs[0]].get('dkAbstract', 'N/A'), 
            'support' : COUNT.get(DOCKET_IDs[0],{}).get('support', 0),
            'oppose' : COUNT.get(DOCKET_IDs[0],{}).get('oppose', 0),
            'neutral' : COUNT.get(DOCKET_IDs[0],{}).get('neutral', 0),
            'modifyDate' : DOCKEY_INFOs[DOCKET_IDs[0]].get('modifyDate', 'N/A'),
            'support_comments': ans_comments[0],
            'oppose_comments': ans_comments[1],
            'neutral_comments': ans_comments[2]
        }
    """
    return {
            'docket_id': "Docket ID Placeholder",
            'title' : "Title Placeholder",
            'dkAbstract' : "Abstract Placeholder",
            'support' : 10,
            'oppose' : 3,
            'neutral' : 0,
            'modifyDate' : "2026-09-08",
            'support_comments': ["data1","data2","data3","data4","data5",],
            'oppose_comments': ["data1","data2","data3","data4","data5",],
        }
    """
    


if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    '''
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
    '''

