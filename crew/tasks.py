from crewai import Task


def create_analysis_task(problem_description: str, agent) -> Task:
    return Task(
        description=f"""
Analizza la seguente descrizione di un problema software e produci un documento
di analisi completo in italiano.

DESCRIZIONE DEL PROBLEMA:
{problem_description}

REGOLA FONDAMENTALE:
Includi SOLO le entità, funzionalità e relazioni esplicitamente menzionate nella
descrizione del problema. NON aggiungere classi, funzionalità o concetti che non
siano stati richiesti dall'utente. Se l'utente ha detto "no promozioni", non inserire
promozioni. Se ha detto "poche classi", crea solo quelle strettamente necessarie.

Il documento deve contenere le seguenti sezioni:
1. Descrizione del Dominio
2. Requisiti Funzionali (lista numerata)
3. Requisiti Non Funzionali
4. Entità Principali (nome, descrizione, attributi principali)
5. Relazioni tra Entità
6. Casi d'Uso principali
7. Vincoli e Regole di Business
8. Glossario dei termini

Scrivi tutto in italiano, in modo chiaro e strutturato.
""",
        expected_output=(
            "Un documento Markdown strutturato con tutte le sezioni richieste, "
            "scritto in italiano, che descrive SOLO ed ESCLUSIVAMENTE ciò che "
            "è stato richiesto nella descrizione del problema."
        ),
        agent=agent,
    )


def create_uml_task(agent, context_tasks: list) -> Task:
    return Task(
        description="""
Leggi il documento di analisi dei requisiti prodotto dall'agente precedente e
genera un diagramma delle classi UML usando la sintassi PlantUML.

REGOLA FONDAMENTALE:
Crea SOLO le classi che sono elencate nelle "Entità Principali" del documento
di analisi. NON aggiungere classi extra, classi di supporto o classi non
menzionate esplicitamente. Se il documento dice 2 entità, il diagramma deve
avere 2 classi.

Il diagramma deve:
- Includere SOLO le classi identificate nell'analisi (niente di più)
- Definire attributi con tipo e visibilità (+, -, #)
- Definire i metodi principali con parametri e tipo di ritorno
- Mostrare le relazioni tra le classi presenti
- Includere le cardinalità sulle relazioni
- Usare SOLO tipi Java standard: String, int, double, boolean, LocalDate, List

Restituisci SOLO il codice PlantUML, racchiuso tra @startuml e @enduml.
""",
        expected_output=(
            "Codice PlantUML valido che inizia con @startuml e termina con @enduml, "
            "contenente SOLO le classi esplicitamente richieste nella descrizione."
        ),
        agent=agent,
        context=context_tasks,
    )


