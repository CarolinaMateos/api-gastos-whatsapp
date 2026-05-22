import re

DEFAULT_CATEGORY = "general"

KNOWN_CATEGORIES = {
    "comida",
    "supermercado",
    "transporte",
    "ocio",
    "casa",
    "salud",
    "ropa",
    "viajes",
    "suscripciones",
    "general",
}


def get_available_categories():
    return sorted(KNOWN_CATEGORIES)


def parse_expense_message(message):
    clean_message = message.strip().lower()

    amount_match = re.search(r"(\d+(?:[,.]\d{1,2})?)", clean_message)

    if not amount_match:
        return None

    amount_text = amount_match.group(1)
    amount = float(amount_text.replace(",", "."))

    if amount <= 0:
        return None

    text_without_amount = clean_message.replace(amount_text, "", 1)
    text_without_amount = re.sub(r"\s+", " ", text_without_amount).strip()

    words = [word for word in text_without_amount.split(" ") if word]

    category = DEFAULT_CATEGORY

    detected_category = next(
        (word for word in words if word in KNOWN_CATEGORIES),
        None
    )

    if detected_category:
        category = detected_category

    description_words = [word for word in words if word != category]
    description = " ".join(description_words).strip() or "sin descripción"

    return {
        "amount": amount,
        "category": category,
        "description": description,
    }
