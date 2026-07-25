import json
from transformers import pipeline
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

hf_token = os.getenv("HF_TOKEN")

# 평가할 모델 목록
MODELS = [
    "facebook/bart-large-mnli",
    "cross-encoder/nli-deberta-v3-large",
    "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
    "valhalla/distilbart-mnli-12-3", 
    "FacebookAI/roberta-large-mnli",
]

LABELS = ["support", "oppose", "neutral"]

# 정답 레이블 직접 붙인 샘플 10개
SAMPLES = [
    {"text": "I fully support the plan to make non-compete agreements illegal in the workplace. They have caused much harm for many decades.", "answer": "support"},
    {"text": "I am strongly in support of the measure to end non-compete clauses. As a physician, I believe this measure could benefit healthcare.", "answer": "support"},
    {"text": "I am against limiting or prohibiting non competes. Non competes have a very important role to protect small businesses.", "answer": "oppose"},
    {"text": "Non-compete clauses continue to place downward pressure on competition and wages for workers. They should not exist.", "answer": "oppose"},
    {"text": "I urge FTC to eliminate this practice. Noncompete clauses made them the only game in town.", "answer": "oppose"},
    {"text": "I strongly support banning non competes. It is unfair for employers to make physicians sign mandatory noncompete clauses.", "answer": "support"},
    {"text": "I believe there should be an additional exception made for executives who have access to sensitive proprietary information.", "answer": "neutral"},
    {"text": "Non- competes should be restricted to a geographic location that is appropriate. Lets compromise and work on a solution that helps all.", "answer": "neutral"},
    {"text": "I fully support the FTC recommendation to eliminate non-compete clauses. They limit upward mobility for workers.", "answer": "support"},
    {"text": "Non competes have an important role in the creation and survival of businesses. Do not create a law that will have adverse consequences.", "answer": "oppose"},
]

def evaluate_model(model_name):
    print(f"\n{'='*50}")
    print(f"모델: {model_name}")
    print('='*50)

    try:
        clf = pipeline("zero-shot-classification", 
                       model=model_name,
                       token = hf_token)
    except Exception as e:
        print(f"로드 실패: {e}")
        return 0

    correct = 0
    for i, sample in enumerate(SAMPLES):
        result = clf(sample["text"][:512], LABELS)
        predicted = result["labels"][0]
        is_correct = predicted == sample["answer"]
        if is_correct:
            correct += 1

        status = "O" if is_correct else "X"
        print(f"{status} [{i+1}] 정답:{sample['answer']} | 예측:{predicted} ({round(result['scores'][0], 2)})")

    accuracy = correct / len(SAMPLES) * 100
    print(f"\n정확도: {correct}/{len(SAMPLES)} = {accuracy:.0f}%")
    return accuracy

if __name__ == "__main__":
    results = {}
    for model in MODELS:
        acc = evaluate_model(model)
        results[model] = acc

    print(f"\n{'='*50}")
    print("최종 비교")
    print('='*50)
    for model, acc in sorted(results.items(), key=lambda x: -x[1]):
        print(f"{acc:.0f}% - {model}")
