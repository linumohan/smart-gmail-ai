from transformers import pipeline

print("Loading local AI models...")

# LIGHT models only

tone_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

generator = pipeline(
    "text-generation",
    model="google/flan-t5-small"
)


classifier = pipeline(
    "zero-shot-classification",
    model="typeform/distilbert-base-uncased-mnli"
)

print("Models loaded.")

def detect_tone(text):
    return tone_model(text)[0]["label"]

def rewrite_professional(text):
    prompt = f"Rewrite professionally:\n{text}"
    return generator(prompt, max_new_tokens=120)[0]["generated_text"]

def summarize(text):
    prompt = f"Summarize:\n{text}"
    return generator(prompt, max_new_tokens=120)[0]["generated_text"]

def classify_email(text):
    labels = ["job","shopping","education","travel","personal"]
    return classifier(text, labels)["labels"][0]
