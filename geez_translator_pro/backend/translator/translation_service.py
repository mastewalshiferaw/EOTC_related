from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

# Load model and tokenizer
# 'distilled-600M' is a good balance between speed and accuracy
MODEL_NAME = "facebook/nllb-200-distilled-600M"

print("Loading Translation Model... This may take a minute on first run.")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

def translate_text(text, target_lang="amh_Ethi"):
    if not text or len(text.strip()) == 0:
        return ""

    try:
        # Prepare the input
        inputs = tokenizer(text, return_tensors="pt")

        # GENERATION FIX: Using the target lang code correctly
        # We manually set the target language ID
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang)

        with torch.no_grad():
            translated_tokens = model.generate(
                **inputs, 
                forced_bos_token_id=forced_bos_token_id, 
                max_length=500
            )

        result = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        return result
    except Exception as e:
        return f"Translation Logic Error: {str(e)}"