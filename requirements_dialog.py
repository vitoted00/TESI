"""
requirements_dialog.py
======================
Modulo per la raccolta interattiva dei requisiti tramite dialogo con l'utente.

L'agente analizza la descrizione iniziale, identifica le informazioni mancanti
e pone domande mirate all'utente per arricchire la specifica prima di passarla
all'AnalysisAgent.
"""

import os
from crewai import LLM
from utils.config import Config

os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY


def get_dialog_llm() -> LLM:
    return LLM(
        model=f"groq/{Config.ANALYSIS_MODEL}",
        temperature=0.4,
    )


def collect_requirements(initial_description: str) -> str:
    """
    Avvia un dialogo interattivo con l'utente per raccogliere requisiti mancanti.
    Restituisce la descrizione arricchita con tutte le informazioni raccolte.
    """
    print("\n" + "─" * 60)
    print("  💬  RACCOLTA INTERATTIVA DEI REQUISITI")
    print("─" * 60)
    print("  L'agente analizzerà la tua descrizione e farà domande")
    print("  per raccogliere i requisiti mancanti.")
    print("─" * 60 + "\n")

    llm = get_dialog_llm()

    # Chiedi all'LLM quali domande fare
    questions = _generate_questions(llm, initial_description)

    if not questions:
        print("  ✔  Descrizione sufficientemente dettagliata, nessuna domanda aggiuntiva.\n")
        return initial_description

    # Raccogli le risposte dell'utente
    answers = _ask_user(questions)

    if not answers:
        return initial_description

    # Arricchisci la descrizione con le risposte
    enriched = _enrich_description(llm, initial_description, questions, answers)

    print("\n" + "─" * 60)
    print("  ✔  Requisiti raccolti! Avvio dell'analisi...")
    print("─" * 60 + "\n")

    return enriched


def _generate_questions(llm, description: str) -> list[str]:
    """
    Usa l'LLM per identificare i requisiti mancanti e generare domande.
    Restituisce una lista di domande (max 5).
    """
    prompt = f"""Sei un analista software esperto. Analizza questa descrizione di un sistema software:

DESCRIZIONE:
{description}

Identifica le informazioni MANCANTI che sarebbero utili per progettare il sistema.
Genera da 2 a 5 domande BREVI e SPECIFICHE da fare all'utente per raccogliere i requisiti mancanti.

Le domande devono riguardare aspetti pratici come:
- Ruoli utente (chi usa il sistema?)
- Regole di business specifiche
- Funzionalità richieste non menzionate
- Vincoli tecnici o operativi
- Gestione di casi particolari (penali, notifiche, scadenze, ecc.)

Rispondi SOLO con le domande, una per riga, numerate così:
1. [domanda]
2. [domanda]
...

Non aggiungere altro testo, solo le domande numerate."""

    try:
        response = llm.call([{"role": "user", "content": prompt}])
        questions = _parse_questions(response)
        return questions[:5]  # massimo 5 domande
    except Exception as e:
        print(f"  ⚠  Impossibile generare domande: {e}")
        return []


def _parse_questions(response: str) -> list[str]:
    """Estrae le domande dalla risposta dell'LLM."""
    import re
    lines = response.strip().split("\n")
    questions = []
    for line in lines:
        line = line.strip()
        match = re.match(r"^\d+[\.\)]\s*(.+)", line)
        if match:
            question = match.group(1).strip()
            if question and len(question) > 10:
                questions.append(question)
    return questions


def _ask_user(questions: list[str]) -> dict[str, str]:
    """
    Mostra le domande all'utente e raccoglie le risposte.
    Restituisce un dizionario {domanda: risposta}.
    """
    print(f"  Ho {len(questions)} domanda/e per te:\n")
    answers = {}

    for i, question in enumerate(questions, 1):
        print(f"  {i}. {question}")
        print("     (premi INVIO per saltare)")
        try:
            answer = input("  → ").strip()
        except EOFError:
            answer = ""

        if answer:
            answers[question] = answer
        print()

    return answers


def _enrich_description(llm, original: str, questions: list[str], answers: dict[str, str]) -> str:
    """
    Usa l'LLM per integrare le risposte dell'utente nella descrizione originale,
    producendo una specifica arricchita e coerente.
    """
    if not answers:
        return original

    qa_text = "\n".join(
        f"D: {q}\nR: {answers[q]}"
        for q in questions
        if q in answers
    )

    prompt = f"""Sei un analista software. Hai raccolto informazioni aggiuntive da un utente.

DESCRIZIONE ORIGINALE:
{original}

INFORMAZIONI AGGIUNTIVE RACCOLTE:
{qa_text}

Riscrivi la descrizione del sistema integrando le informazioni aggiuntive in modo naturale e coerente.
La nuova descrizione deve essere completa, chiara e in italiano.
Non aggiungere informazioni inventate, usa SOLO quello che è stato fornito.
Restituisci SOLO la descrizione riscritta, senza commenti o prefazioni."""

    try:
        enriched = llm.call([{"role": "user", "content": prompt}])
        return enriched.strip() if enriched.strip() else original
    except Exception as e:
        print(f"  ⚠  Impossibile arricchire la descrizione: {e}")
        extra = "\n\nInformazioni aggiuntive:\n" + qa_text
        return original + extra