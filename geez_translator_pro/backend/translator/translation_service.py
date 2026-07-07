from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

# Load model and tokenizer
# 'distilled-600M' is a good balance between speed and accuracy
MODEL_NAME = "facebook/nllb-200-distilled-600M"

print("Loading Translation Model... This may take a minute on first run.")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

def translate_text(text, target_lang="amh_Ethi"):
    """
    Translates text to Amharic (amh_Ethi) or English (eng_Latn).
    Since Ge'ez is a parent to Amharic, NLLB handles the script well.
    """
    if not text or len(text.strip()) == 0:
        return ""

    # Prepare the input
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)

    # Generate translation
    with torch.no_grad():
        translated_tokens = model.generate(
            **inputs, 
            forced_bos_token_id=tokenizer.lang_code_to_id[target_lang], 
            max_length=500
        )

    # Decode the output
    result = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
    return result