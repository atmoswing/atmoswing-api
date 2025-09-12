from atmoswing_api.app.utils.utils import sanitize_unicode_surrogates


def test_sanitize_preserves_accents():
    original = {
        'fr': "Électricité générée à l'épreuve: température élevée – façade intérieure",
        'list': ["élévation", "café", "garçon", "Noël"],
    }
    cleaned = sanitize_unicode_surrogates(original)
    assert cleaned == original, "Accented French characters must be preserved"


def test_sanitize_removes_invalid_surrogates():
    # Inject an unpaired surrogate (invalid in Unicode) inside a string
    bad = "Validé" + "\uD800" + "texte"
    cleaned = sanitize_unicode_surrogates(bad)
    assert "\uD800" not in cleaned
    assert cleaned == "Validétexte", "Surrogate should be stripped without touching other chars"

