import re
import time

from crewai import Crew, Process, Task

from crew.agents import create_analysis_agent, create_uml_agent, create_code_agent
from crew.tasks import create_analysis_task, create_uml_task


def create_crew_with_explicit_context(problem_description: str):
    """
    Pipeline in tre step:
    1. AnalysisAgent + UMLAgent → analisi e diagramma
    2. CodeAgent → genera ogni classe Java separatamente (una alla volta)
    3. CodeAgent → genera README.md
    """

    # ── Step 1: Analisi + UML ─────────────────────────────────────────────
    analysis_agent = create_analysis_agent()
    uml_agent = create_uml_agent()

    analysis_task = create_analysis_task(problem_description, analysis_agent)
    uml_task = create_uml_task(uml_agent, context_tasks=[analysis_task])

    crew_step1 = Crew(
        agents=[analysis_agent, uml_agent],
        tasks=[analysis_task, uml_task],
        process=Process.sequential,
        verbose=True,
    )

    result_step1 = crew_step1.kickoff()

    tasks_output = result_step1.tasks_output if hasattr(result_step1, "tasks_output") else []
    analysis_text = tasks_output[0].raw if len(tasks_output) >= 1 else ""
    uml_text = tasks_output[1].raw if len(tasks_output) >= 2 else ""

    # ── Step 2: Estrai lista classi dal diagramma UML ─────────────────────
    class_names = re.findall(r'class\s+(\w+)', uml_text)
    class_names = list(dict.fromkeys(class_names))  # rimuove duplicati

    if not class_names:
        class_names = ["Utente", "Libro", "Prenotazione"]

    print(f"\n  Classi individuate dal diagramma UML: {class_names}\n")

    # ── Step 3: Genera ogni classe Java separatamente ─────────────────────
    class_results = []

    for class_name in class_names:
        print(f"  Generazione di {class_name}.java...")
        code_agent = create_code_agent()
        code_task = _create_single_class_task(code_agent, class_name, analysis_text, uml_text)

        crew_class = Crew(
            agents=[code_agent],
            tasks=[code_task],
            process=Process.sequential,
            verbose=False,
        )

        result_class = crew_class.kickoff()
        class_raw = str(result_class).strip()
        class_results.append((class_name, class_raw))
        print(f"  ✔  {class_name}.java generato.")
        if class_name != class_names[-1]:
            print("  ⏳  Attesa 15s per evitare rate limit Groq...")
            time.sleep(15)

    # ── Step 4: Genera README.md ──────────────────────────────────────────
    print("\n  Generazione README.md...")
    code_agent = create_code_agent()
    readme_task = _create_readme_task(code_agent, analysis_text)

    crew_readme = Crew(
        agents=[code_agent],
        tasks=[readme_task],
        process=Process.sequential,
        verbose=False,
    )

    result_readme = crew_readme.kickoff()
    readme_raw = str(result_readme).strip()
    print("  ✔  README.md generato.")

    return _StructuredResult(result_step1, class_results, readme_raw)


def _create_single_class_task(agent, class_name: str, analysis: str, uml_diagram: str) -> Task:
    return Task(
        description=(
            f"Implementa SOLO la classe Java '{class_name}' basandoti sul diagramma UML e sull'analisi forniti.\n"
            f"\n"
            f"ATTENZIONE: il nome della classe e' '{class_name}'.\n"
            f"La dichiarazione DEVE essere esattamente: public class {class_name}\n"
            f"\n"
            f"══════════════════════════════════════════\n"
            f"DIAGRAMMA UML (PlantUML):\n"
            f"══════════════════════════════════════════\n"
            f"{uml_diagram}\n"
            f"\n"
            f"══════════════════════════════════════════\n"
            f"DOCUMENTO DI ANALISI:\n"
            f"══════════════════════════════════════════\n"
            f"{analysis}\n"
            f"══════════════════════════════════════════\n"
            f"\n"
            f"Crea SOLO il file {class_name}.java con:\n"
            f"- Package: com.progetto_generato\n"
            f"- Usa java.time.LocalDate per le date (MAI tipi inventati come Data, Ora, Datetime)\n"
            f"- Javadoc completo sulla classe e su ogni metodo pubblico\n"
            f"- Costruttore con validazione degli input (Objects.requireNonNull, controllo stringa vuota)\n"
            f"- Tutti i getter e setter COMPLETI — mai scrivere // ... altri getter e setter\n"
            f"- toString(), equals(), hashCode() implementati completamente\n"
            f"- Logica di business realistica, mai stub vuoti\n"
            f"\n"
            f"REGOLE ASSOLUTE — RISPETTA SEMPRE:\n"
            f"1. Il codice deve iniziare ESATTAMENTE con 'package com.progetto_generato;' — nulla prima\n"
            f"2. La classe si chiama {class_name} — NON usare altri nomi\n"
            f"3. NON usare backtick o blocchi markdown\n"
            f"4. NON scrivere testo prima o dopo il codice Java\n"
            f"5. NON troncare il codice — scrivi la classe fino all'ultima graffa di chiusura\n"
            f"6. USA SOLO tipi Java standard: String, int, double, boolean, LocalDate, List, ArrayList\n"
        ),
        expected_output=(
            f"Solo il codice Java della classe {class_name}, "
            f"che inizia con 'package com.progetto_generato;', "
            f"contiene 'public class {class_name}' e termina con la graffa di chiusura."
        ),
        agent=agent,
    )


def _create_readme_task(agent, analysis: str) -> Task:
    return Task(
        description=(
            "Genera il file README.md per il progetto Java.\n"
            "\n"
            "Il README.md deve contenere:\n"
            "- Descrizione del progetto\n"
            "- Prerequisiti (Java 17, Maven)\n"
            "- Come compilare: mvn clean compile\n"
            "- Come eseguire i test: mvn test\n"
            "- Struttura del progetto\n"
            "\n"
            f"Analisi del progetto:\n{analysis}\n"
            "\n"
            "Scrivi solo il contenuto markdown, senza backtick iniziali o finali.\n"
        ),
        expected_output="Il file README.md completo in formato markdown.",
        agent=agent,
    )


class _StructuredResult:
    """
    Mantiene i risultati strutturati per classe.
    tasks_output: [analysis, uml, class1, class2, ..., readme]
    """

    class _FakeTaskOutput:
        def __init__(self, raw: str):
            self.raw = raw

    def __init__(self, result_step1, class_results: list, readme_raw: str):
        tasks1 = result_step1.tasks_output if hasattr(result_step1, "tasks_output") else []
        class_tasks = [self._FakeTaskOutput(raw) for _, raw in class_results]
        readme_task = self._FakeTaskOutput(readme_raw)
        self.tasks_output = list(tasks1) + class_tasks + [readme_task]
        self.class_names = [name for name, _ in class_results]

    def __str__(self):
        return "\n\n".join(t.raw for t in self.tasks_output)