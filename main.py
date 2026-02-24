"""
Agentic AI System per la Progettazione Software
================================================
Sistema multi-agente basato su CrewAI + Groq per:
  1. Dialogo interattivo per raccolta requisiti
  2. Analisi dei requisiti
  3. Generazione diagramma UML (PlantUML)
  4. Generazione codice Java

Autore: Progetto di Tesi in Informatica
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crew.crew import create_crew_with_explicit_context
from requirements_dialog import collect_requirements
from utils.file_manager import FileManager
from utils.config import Config


def ask_problem() -> str:
    print("\n" + "=" * 60)
    print("  AGENTIC AI — PROGETTAZIONE SOFTWARE")
    print("  Sistema Multi-Agente: CrewAI + Groq")
    print("=" * 60)
    print("\n  Agenti:")
    print("  ① DialogAgent    — Raccolta interattiva dei requisiti")
    print("  ② AnalysisAgent  — Analisi dei requisiti")
    print("  ③ UMLAgent       — Diagramma delle classi (PlantUML)")
    print("  ④ CodeAgent      — Implementazione Java")
    print("\n" + "-" * 60)
    print("\n  Descrivi il problema software da modellare:")
    print("  (Scrivi il testo e premi INVIO due volte)\n")

    lines = []
    empty = 0
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "":
            empty += 1
            if empty >= 2:
                break
        else:
            empty = 0
            lines.append(line)

    description = "\n".join(lines).strip()
    if not description:
        print("  Descrizione vuota, riprova.")
        return ask_problem()
    return description


def save_outputs(result, file_manager: FileManager, enriched_description: str = ""):
    """Estrae e salva i file dall'output della crew."""
    output_text = str(result)
    file_manager.save("00_full_output.txt", output_text)

    if enriched_description:
        file_manager.save("00_enriched_description.md", enriched_description)
        print("  ✔  Descrizione arricchita salvata in output/00_enriched_description.md")

    tasks_output = result.tasks_output if hasattr(result, "tasks_output") else []
    class_names = getattr(result, "class_names", [])

    # ── Analisi (task 0) ─────────────────────────────────────────────────
    if len(tasks_output) >= 1:
        file_manager.save("01_analysis.md", tasks_output[0].raw)
        print("  ✔  Analisi salvata in output/01_analysis.md")

    # ── Diagramma UML (task 1) ────────────────────────────────────────────
    if len(tasks_output) >= 2:
        uml_raw = tasks_output[1].raw
        match = re.search(r"(@startuml.*?@enduml)", uml_raw, re.DOTALL)
        uml = match.group(1) if match else uml_raw
        file_manager.save("02_class_diagram.puml", uml)
        print("  ✔  Diagramma UML salvato in output/02_class_diagram.puml")

    # ── Codice Java (task 2 ... n-1) ─────────────────────────────────────
    if len(tasks_output) >= 3:
        java_tasks = tasks_output[2:-1]   # classi Java
        readme_task = tasks_output[-1]    # README

        saved_count = 0

        for i, task in enumerate(java_tasks):
            code_raw = task.raw

            if i < len(class_names):
                class_name = class_names[i]
                filename = f"{class_name}.java"
            else:
                match_class = re.search(r'public\s+class\s+(\w+)', code_raw)
                if not match_class:
                    print(f"  ⚠  Classe non riconosciuta nel task {i+1}, saltato")
                    continue
                class_name = match_class.group(1)
                filename = f"{class_name}.java"

            file_manager.save_java(filename, code_raw)
            saved_count += 1

        print(f"  ✔  {saved_count} file Java salvati in output/java/src/main/java/com/biblioteca/")

        # pom.xml
        file_manager.save_pom()

        # README
        readme_raw = readme_task.raw
        readme_clean = re.sub(r'```[a-zA-Z]*\n?|```', '', readme_raw).strip()
        file_manager.save("java/README.md", readme_clean)
        print("  ✔  README.md salvato")


def main():
    # ── Fase 1: Descrizione iniziale ──────────────────────────────────────
    problem = ask_problem()
    print(f"\n  Descrizione ricevuta ({len(problem)} caratteri).")

    # ── Fase 2: Dialogo interattivo per raccolta requisiti ────────────────
    enriched_problem = collect_requirements(problem)

    if enriched_problem != problem:
        print(f"  Descrizione arricchita ({len(enriched_problem)} caratteri).")

    # ── Fase 3: Pipeline multi-agente ────────────────────────────────────
    print("\n" + "-" * 60)
    print("  Avvio della Crew... (potrebbe richiedere alcuni minuti)")
    print("─" * 60 + "\n")

    try:
        result = create_crew_with_explicit_context(enriched_problem)
    except Exception as e:
        print(f"\n  ERRORE durante l'esecuzione: {e}")
        raise

    print("\n" + "=" * 60)
    print("  Pipeline completata! Salvataggio dei file...")
    print("=" * 60 + "\n")

    fm = FileManager(Config.OUTPUT_DIR)
    save_outputs(result, fm, enriched_description=enriched_problem)

    print("\n" + "=" * 60)
    print("  Tutto completato. Controlla la cartella output/")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()