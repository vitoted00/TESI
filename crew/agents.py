import os
from crewai import Agent, LLM

from utils.config import Config

os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY


def get_analysis_llm() -> LLM:
    return LLM(
        model=f"groq/{Config.ANALYSIS_MODEL}",
        temperature=0.3,
    )


def get_code_llm() -> LLM:
    return LLM(
        model=f"groq/{Config.CODE_MODEL}",
        temperature=0.2,
    )


def create_analysis_agent() -> Agent:
    return Agent(
        role="Analista dei Requisiti Software",
        goal=(
            "Analizzare la descrizione di un problema software fornita dall'utente, "
            "identificare le entità principali, i requisiti funzionali e non funzionali, "
            "e produrre un documento di analisi strutturato e completo in italiano."
        ),
        backstory=(
            "Sei un esperto analista software con oltre 15 anni di esperienza nella "
            "raccolta e analisi dei requisiti. Produci sempre documenti chiari, "
            "strutturati e completi."
        ),
        llm=get_analysis_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_uml_agent() -> Agent:
    return Agent(
        role="Progettista UML",
        goal=(
            "Tradurre il documento di analisi in un diagramma delle classi UML "
            "completo usando la sintassi PlantUML."
        ),
        backstory=(
            "Sei un progettista software specializzato in modellazione UML. "
            "I tuoi diagrammi sono sempre precisi e fedeli ai requisiti."
        ),
        llm=get_analysis_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_code_agent() -> Agent:
    return Agent(
        role="Sviluppatore Java Senior",
        goal=(
            "Implementare il codice Java completo a partire dal diagramma UML, "
            "con Javadoc, validazione input, e pronto per Maven."
        ),
        backstory=(
            "Sei uno sviluppatore Java senior esperto in Java 17 e best practices. "
            "Scrivi codice pulito, documentato e compilabile."
        ),
        llm=get_code_llm(),
        verbose=True,
        allow_delegation=False,
    )