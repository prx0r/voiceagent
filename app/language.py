"""Language adapter — makes the kernel work in any language.

The graph is already language-agnostic (YAML config).
This module adds:
1. Language detection from customer message
2. Response translation
3. Voice selection per language
4. Template system for quick language addition
"""
from __future__ import annotations
import re
from typing import Any

# Language detection patterns — order matters (most specific first)
LANG_PATTERNS = {
    "no": [r"\b(hei|hallo|hva\s+er|hvor\s+mye|kan\s+jeg|jeg\s+har|jeg\s+trenger|takk\s+for|dørlås|vindu|espagnolette|mekanisme|bestille\s+time|montering|lås\s+som|reservdel|skyvedør|hvilke\s+mål|returnere|åpne\s+i)\b"],
    "sv": [r"\b(hej|hallå|vad\s+är|hur\s+mycket|jag\s+har|jag\s+behöver|tack\s+för|dörr|fönster|lås|mekanism)\b"],
    "fi": [r"\b(moi|hei|mikä|miten|kiitos|kyllä|ei|ovi|ikkuna|lukko|mekanismi)\b"],
    "da": [r"\b(hej|hej|hvad|hvordan|tak\s+for|ja\s+|nej\s+|dør|vindue|lås|mekanisme)\b"],
    "de": [r"\b(hallo|wie\s+geht|was\s+kostet|danke|ja\s+|nein\s+|tür|fenster|schloss)\b"],
    "fr": [r"\b(bonjour|comment|merci\s+beaucoup|oui\s+|non\s+|porte|fenêtre|serrure)\b"],
    "en": [r"\b(hello|hi\s|what\s+is|how\s+much|thank\s+you|yes\s+|no\s+|door|window|lock)\b"],
}

# Voice mappings per language
VOICE_MAP = {
    "no": "nb-NO-PernilleNeural",
    "nb": "nb-NO-PernilleNeural",
    "nn": "nn-NO-NynorskNeural",
    "sv": "sv-SE-SofieNeural",
    "fi": "fi-FI-SelmaNeural",
    "da": "da-DK-ChristelNeural",
    "en": "en-GB-RyanNeural",
    "de": "de-DE-ConradNeural",
    "fr": "fr-FR-HenriNeural",
}


def detect_language(text: str) -> str:
    """Detect language from text."""
    scores = {}
    for lang, patterns in LANG_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1
        scores[lang] = score
    
    if not scores or max(scores.values()) == 0:
        return "en"  # default
    
    return max(scores, key=scores.get)


def get_voice(language: str) -> str:
    """Get TTS voice for language."""
    return VOICE_MAP.get(language, "en-GB-RyanNeural")


def translate_response(text: str, target_lang: str, source_lang: str = "en") -> str:
    """Translate response to target language.
    
    For MVP: return as-is (LLM handles language matching).
    Production: use DeepL/Google Translate API.
    """
    # The LLM should already respond in the customer's language
    # because the system prompt says "Match the customer's language"
    return text
