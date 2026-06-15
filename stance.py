import json
from transformers import pipeline
from scraping import cleanText
import os
from dotenv import load_dotenv
from collections import Counter

# Load environment variables
load_dotenv()

hf_token = os.getenv("HF_TOKEN")

MODELS = [
    "facebook/bart-large-mnli",
    "cross-encoder/nli-deberta-v3-large",
    "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
    "valhalla/distilbart-mnli-12-3", 
    "FacebookAI/roberta-large-mnli",
]

LABELS = ["support", "oppose", "neutral"]

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


if __name__ =='__main__':
    result = []
    data = json.load(open('COMMENT_CLEAN.json'))
    classifier = load_models()
    #text = "Pursuant to the Federal Trade Commission Act (‘‘FTC Act’’), the Federal Trade Commission (‘‘Commission’’) is issuing the Non-Compete Clause Rule (‘‘the final rule’’). The final rule provides that it is an unfair method of competition for persons to, among other things, enter into non-compete clauses (‘‘non-competes’’) with workers on or after the final rule’s effective date. With respect to existing non-competes—i.e., non-competes entered into before the effective date—the final rule adopts a different approach for senior executives than for other workers. For senior executives, existing non-competes can remain in force, while existing non-competes with other workers are not enforceable after the effective date. \n\n"
    #text = cleanText(text)
    for d in data[:20]:
        stance_result = classify_stance(d['cleaned_text'],classifier)
        result.append({
            "id": d['id'],
            "title": d['title'],
            "postedDate": d['postedDate'],
            'cleaned_text': d['cleaned_text'],
            'votes': stance_result['votes'],
            'avg_confidence': stance_result['avg_confidence'],
            'stance': stance_result['stance']
        })
        print(f'Comment ID: {d["id"]}, Stance: {stance_result["stance"]}, Votes: {stance_result["votes"]}, Avg Confidence: {stance_result["avg_confidence"]}')
    



                          
