"""Customer service flow — the main interaction pattern.

This module defines the canonical customer service flow:
1. Greet in customer's language
2. Identify the problem (photo, description, SKU)
3. Search graph for matching product/service
4. Check compatibility
5. Provide solution (replace, repair, book)
6. Handle escalation if needed

The flow is language-agnostic — just swap the YAML config.
"""
from __future__ import annotations
from typing import Any


# Canonical customer service intents
INTENTS = {
    "IDENTIFY": "Customer wants to identify a part or product",
    "COMPATIBILITY": "Customer wants to know if X fits Y",
    "REPLACE": "Customer wants to buy a replacement",
    "BOOK": "Customer wants to book a service",
    "COMPLAIN": "Customer has a problem",
    "PRICING": "Customer wants to know the price",
    "HOURS": "Customer wants to know business hours",
    "RETURN": "Customer wants to return something",
    "UNKNOWN": "Customer intent unclear",
}


def classify_intent(message: str) -> str:
    """Classify customer intent from message."""
    msg = message.lower()
    
    if any(w in msg for w in ["identify", "what is", "hva er", "what's this", "hva er dette"]):
        return "IDENTIFY"
    if any(w in msg for w in ["compatible", "fit", "passer", "kompatibel", "replace", "erstattning"]):
        return "COMPATIBILITY"
    if any(w in msg for w in ["buy", "order", "kjøp", "bestill", "price", "pris"]):
        return "REPLACE"
    if any(w in msg for w in ["book", "appointment", "bestill time", "time"]):
        return "BOOK"
    if any(w in msg for w in ["problem", "broken", "doesn't work", "ødelagt", "fungerer ikke"]):
        return "COMPLAIN"
    if any(w in msg for w in ["how much", "cost", "hvor mye", "pris"]):
        return "PRICING"
    if any(w in msg for w in ["hours", "open", "åpningstider", "når"]):
        return "HOURS"
    if any(w in msg for w in ["return", "refund", "returnere", "refundere"]):
        return "RETURN"
    return "UNKNOWN"


# Canonical response templates per intent and language
RESPONSE_TEMPLATES = {
    "IDENTIFY": {
        "en": "To identify this part, I need: 1) A photo of the part, 2) The model/brand name, 3) Three measurements: backset, centre-to-centre, and screw spacing.",
        "no": "For å identifisere denne delen trenger jeg: 1) Et bilde av delen, 2) Merke/modellnavn, 3) Tre mål: bakstykke, sentrum-til-sentrum, og skrueavstand.",
        "sv": "För att identifiera den här delen behöver jag: 1) En bild på delen, 2) Märke/modellnamn, 3) Tre mål: baksida, centrum-till-centrum, och skruvavstånd.",
    },
    "COMPATIBILITY": {
        "en": "I can check compatibility if you provide: the make/model of your existing part, and photos of the current mechanism.",
        "no": "Jeg kan sjekke kompatibilitet hvis du gir meg: merke/modell på den eksisterende delen, og bilder av gjeldende mekanisme.",
        "sv": "Jag kan kolla kompatibilitet om du ger mig: märke/modell på den befintliga delen, och bilder av nuvarande mekanism.",
    },
    "BOOK": {
        "en": "I can book a slot for you. What date and time work best?",
        "no": "Jeg kan bestille en time for deg. Hvilken dag og tid passer best?",
        "sv": "Jag kan boka en tid åt dig. Vilken dag och tid passar bäst?",
    },
}


def get_response_template(intent: str, language: str) -> str:
    """Get response template for intent and language."""
    templates = RESPONSE_TEMPLATES.get(intent, {})
    return templates.get(language, templates.get("en", ""))
