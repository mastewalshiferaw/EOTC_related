def translate_flexible(text, source_lang, target_lang):
    if not text: return ""

    try:
        # SWITCHED TO 1.5 FLASH for stability and higher free limits
        model = "gemini-1.5-flash" 
        
        prompt = f"""
        Translate this text from {source_lang} to {target_lang}.
        If the target is Ge'ez or Amharic, use formal liturgical tone.
        
        Text: {text}
        """

        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"AI Error: {str(e)}"