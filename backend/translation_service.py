from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

MODEL_NAME = "facebook/nllb-200-distilled-600M"

LANGUAGES = {
    "en": "eng_Latn",
    "ta": "tam_Taml"
}

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


def translate_text(text, target_language):
    if not text:
        return text

    if target_language not in LANGUAGES:
        raise ValueError("Unsupported language")

    # Detect the input language and choose the opposite language
    source_language = "ta" if target_language == "en" else "en"

    tokenizer.src_lang = LANGUAGES[source_language]

    inputs = tokenizer(
        str(text),
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(
                LANGUAGES[target_language]
            ),
            max_new_tokens=200
        )

    return tokenizer.batch_decode(
        outputs,
        skip_special_tokens=True
    )[0]


def translate_report(report, target_language):
    translated = {}

    for key, value in report.items():
        if isinstance(value, str):
            translated[key] = translate_text(value, target_language)

        elif isinstance(value, list):
            translated[key] = [
                translate_text(item, target_language)
                if isinstance(item, str) else item
                for item in value
            ]

        else:
            translated[key] = value

    return translated