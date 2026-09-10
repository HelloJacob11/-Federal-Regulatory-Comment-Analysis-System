import json
from transformers import pipeline
import os
from dotenv import load_dotenv
from collections import Counter
from .dataCollection import fetch_docket_info



# Load environment variables
load_dotenv()

hf_token = os.getenv("HF_TOKEN")
LABELS = []
LABLE_SHORT = {}
MODELS = [
    "facebook/bart-large-mnli",
    "cross-encoder/nli-deberta-v3-large",
    "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
    "valhalla/distilbart-mnli-12-3", 
    "FacebookAI/roberta-large-mnli",
]

"""classifier = pipeline(
    "zero-shot-classification",
    model="cardiffnlp/twitter-roberta-base-stance-abortion",
    token=hf_token
)
labels = ['support', 'oppose', 'neutral']"""

def load_models():
    classifier = []
    for model_name in MODELS:
        try:
            print(f"Loading model: {model_name}")
            clf = pipeline(
                "zero-shot-classification",
                model=model_name, 
                token=hf_token)
            classifier.append(clf)
            print(f"Model loaded successfully: {model_name}")
        except Exception as e:
            print(f"Failed to load model {model_name}: {e}")
    return classifier
        
    
def classify_stance(text,classifier):
    if not text or not text.strip():
        return None
    t = text.split()[:512]
    t = " ".join(t)
    votes = []
    scores = {}
    for model in classifier:
        result = model(t, LABELS)
        predicted = result["labels"][0]
        votes.append(predicted)
        #confidence = round(result['scores'][0], 2)
        for label, score in zip(result['labels'], result['scores']):
            scores[label] = scores.get(label, 0) + score
    #print(scores)
    vote_count = Counter(votes)
    top_label, top_votes = vote_count.most_common(1)[0]

    if list(votes).count(top_votes) > 1:
        tied = [l for l,v in vote_count.items() if v == top_votes]
        top_label = max(tied, key=lambda l: scores[l])
        
    return {
        'stance': top_label,
        'votes': dict(vote_count),
        'avg_confidence': round(scores[top_label] / len(scores),3)        
        }

def classify_docketID_Data(docket_id, data):
    data_class = {}
    dockers_info = {}
    for comment in data:
        if comment['docketID'] not in dockers_info:
            dockers_info[comment['docketID']] = fetch_docket_info(docket_id)
            data_class[comment['docketID']] = [comment]
        else:
            data_class[comment['docketID']].append(comment)
    return data_class, dockers_info

def count_stance(data, classifier,docket_info):
    global LABELS, LABLE_SHORT
    if isinstance(docket_info, list):
        docket_info = docket_info[0]
    #print(f"Counting stance for docket: {docket_info}")


    counts = Counter()
    result = {}
    opposed_data = []
    support_data = []
    netural_data = []

    LABELS =[
        f"This comment supports: {docket_info['title']} - {docket_info.get('dkAbstract', '')[:200]}", 
        f"This comment opposes: {docket_info['title']} - {docket_info.get('dkAbstract', '')[:200]}", 
        f"This comment is neutral regarding: {docket_info['title']} - {docket_info.get('dkAbstract', '')[:200]}"
    ]
    LABLE_SHORT = {
        LABELS[0]: "Support",
        LABELS[1]: "Oppose",
        LABELS[2]: "Neutral"
    }

    for comment in data:
        #print("Processing comment ID: ", comment)
        text = comment['cleaned_text']
        result = classify_stance(text, classifier)
        if result is None:
            continue
        counts[result['stance']] += 1

        if result['stance'] == 'Support':
            support_data.append(comment)
        elif result['stance'] == 'Oppose':
            opposed_data.append(comment)
        else:
            netural_data.append(comment)

    result[id] = counts
    return result, [support_data, opposed_data, netural_data]

if __name__ =='__main__':
    result = []
    data = json.load(open('COMMENT_CLEAN.json'))
    print(data)
    classifier = load_models()
    #text = "Pursuant to the Federal Trade Commission Act (‘‘FTC Act’’), the Federal Trade Commission (‘‘Commission’’) is issuing the Non-Compete Clause Rule (‘‘the final rule’’). The final rule provides that it is an unfair method of competition for persons to, among other things, enter into non-compete clauses (‘‘non-competes’’) with workers on or after the final rule’s effective date. With respect to existing non-competes—i.e., non-competes entered into before the effective date—the final rule adopts a different approach for senior executives than for other workers. For senior executives, existing non-competes can remain in force, while existing non-competes with other workers are not enforceable after the effective date. \n\n"
    #text = cleanText(text)
    DOCKET_IDs = json.load(open("recentDocketIDs.json"))
    print(f"Recent Docket IDs: {DOCKET_IDs[0]}")
    ans = count_stance(data, classifier, DOCKET_IDs[0])
    print(f"Stance counts for {DOCKET_IDs[0]}: {ans}")
    '''
    count_stance = Counter()
    for d in data:
        stance_result = classify_stance(d['cleaned_text'],classifier)
        print(f"Comment ID: {d['id']}...")  
        result.append({
            "docketID": d['docketID'],
            "id": d['id'],
            "title": d['title'],
            "postedDate": d['postedDate'],
            'cleaned_text': d['cleaned_text'],
            'votes': stance_result['votes'],
            'avg_confidence': stance_result['avg_confidence'],
            'stance': stance_result['stance']
        })
        short_votes = {}
        for k, v in stance_result['votes'].items():
            if 'support' in k:
                short_votes['Support'] = v
                count_stance['Support'] += v
            elif 'oppose' in k:
                short_votes['Oppose'] = v
                count_stance['Oppose'] += v
            elif 'neutral' in k:
                short_votes['Neutral'] = v
                count_stance['Neutral'] += v
        #print(f'Votes: {short_votes}, Avg Confidence: {stance_result["avg_confidence"]}')
    print(f'Total Comments Processed: {len(result)}')
    print(f"Stance Distribution: {count_stance}")
    '''


                          
