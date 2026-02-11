from brain import *

text = "Dear sir you fired me"

print("Tone:", detect_tone(text))
print("Rewrite:", rewrite_professional(text))
print("Summary:", summarize(text))
print("Class:", classify_email(text, ["job","shopping","travel"]))
