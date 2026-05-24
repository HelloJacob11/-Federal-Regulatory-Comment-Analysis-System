import json
from transformers import pipeline
from scraping import cleanText



classifier = pipeline(
    "zero-shot-classification",
    model="cardiffnlp/twitter-roberta-base-stance-abortion"
)
labels = ['support', 'oppose', 'neutral']
def classify_sstance(text):
    t = text.split()[:512]
    t = " ".join(t)
    result = classifier(t,labels)
    values = ['supports', 'oppose','neutral']
    label_dic = {}
    for l,v in zip(labels,values):
        label_dic[l] = v

    print(f'orIGINAL TXT = {text} ans = {result['labels'],result}')

if __name__ =='__main__':
    result = []
    data = json.load(open('COMMENT_CLEAN.json'))
    text = "Pursuant to the Federal Trade Commission Act (‘‘FTC Act’’), the Federal Trade Commission (‘‘Commission’’) is issuing the Non-Compete Clause Rule (‘‘the final rule’’). The final rule provides that it is an unfair method of competition for persons to, among other things, enter into non-compete clauses (‘‘non-competes’’) with workers on or after the final rule’s effective date. With respect to existing non-competes—i.e., non-competes entered into before the effective date—the final rule adopts a different approach for senior executives than for other workers. For senior executives, existing non-competes can remain in force, while existing non-competes with other workers are not enforceable after the effective date. \n\n"
    text = cleanText(text)
    for d in data[:20]:
        stance_result = classify_sstance(d['cleaned_text'])
    



                          
