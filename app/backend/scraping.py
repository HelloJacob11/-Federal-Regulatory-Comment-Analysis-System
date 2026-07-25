import json
import re


def jsonLoad(inputFile, outputFile):
    data = json.load(open(inputFile))
    result = []
    skipped_empty = 0
    for d in data:
        if not d:
            skipped_empty += 1
            continue
        text = cleanText(d.get("printtext"))
        result.append({
            'id': d['id'],
            'title': d['title'],
            'postedDate': d['postedDate'],
            'cleaned_text':text})
    print("# of skipped_empty: ", skipped_empty)
    print("# of data: ", len(result))
    

    with open(outputFile,"w") as f:
        json.dump(result,f,indent=2,ensure_ascii=False)

def cleanText(text):
    text = re.sub(r'<[^>]+>',' ',text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'&#39;',"'", text)
    text = re.sub(r'&rsquo;', '"', text)
    text = re.sub(r'&amp;',' and',text)
    text = re.sub(r'&[a-zA-Z]+;',' ', text)
    return text



if __name__ == '__main__':
    jsonLoad("COMMENT_RAW.json","COMMENT_CLEAN.json")