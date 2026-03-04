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
import csv
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crew.crew import create_crew_with_explicit_context
from requirements_dialog import collect_requirements
from utils.file_manager import FileManager
from utils.config import Config


# ══════════════════════════════════════════════════════════════════
#  QUESTIONARIO GEQ — adattato per tool di generazione codice
#  Scala: 0=Per niente  1=Poco  2=Abbastanza  3=Molto  4=Moltissimo
# ══════════════════════════════════════════════════════════════════

GEQ_COMPONENTI = [
    {
        "componente": "Competence",
        "descrizione": "Quanto ti sei sentito capace e in controllo",
        "domande": [
            {"id": "comp_1", "testo": "Mi sentivo competente nell'utilizzare il sistema"},
            {"id": "comp_2", "testo": "Ero bravo a descrivere il problema al sistema"},
            {"id": "comp_3", "testo": "Il sistema ha capito bene quello che volevo"},
        ]
    },
    {
        "componente": "Immersion",
        "descrizione": "Quanto eri coinvolto e concentrato",
        "domande": [
            {"id": "imm_1", "testo": "Ero concentrato sull'interazione con il sistema"},
            {"id": "imm_2", "testo": "Mi sono dimenticato di tutto il resto mentre lo usavo"},
            {"id": "imm_3", "testo": "L'esperienza era coinvolgente"},
        ]
    },
    {
        "componente": "Flow",
        "descrizione": "Quanto l'interazione era fluida e naturale",
        "domande": [
            {"id": "flow_1", "testo": "L'interazione con il sistema era fluida e naturale"},
            {"id": "flow_2", "testo": "Non mi sono mai bloccato senza sapere cosa fare"},
            {"id": "flow_3", "testo": "Il sistema rispondeva come mi aspettavo"},
        ]
    },
    {
        "componente": "Tension",
        "descrizione": "Quanto ti ha innervosito o messo in difficolta'",
        "domande": [
            {"id": "tens_1", "testo": "Il sistema mi ha confuso o messo in difficolta'"},
            {"id": "tens_2", "testo": "Mi sono sentito frustrato in qualche momento"},
            {"id": "tens_3", "testo": "Qualcosa non funzionava come mi aspettavo"},
        ]
    },
    {
        "componente": "Challenge",
        "descrizione": "Quanto era difficile da usare",
        "domande": [
            {"id": "chal_1", "testo": "Descrivere il problema al sistema era complicato"},
            {"id": "chal_2", "testo": "Era difficile capire cosa il sistema si aspettava da me"},
            {"id": "chal_3", "testo": "Ho fatto fatica a ottenere il risultato che volevo"},
        ]
    },
    {
        "componente": "Negative Affect",
        "descrizione": "Sensazioni negative durante l'utilizzo",
        "domande": [
            {"id": "neg_1", "testo": "Ho trovato il sistema noioso"},
            {"id": "neg_2", "testo": "Ho perso la pazienza durante l'utilizzo"},
            {"id": "neg_3", "testo": "Mi sono sentito annoiato o demotivato"},
        ]
    },
    {
        "componente": "Positive Affect",
        "descrizione": "Sensazioni positive durante l'utilizzo",
        "domande": [
            {"id": "pos_1", "testo": "Ho trovato il sistema interessante e stimolante"},
            {"id": "pos_2", "testo": "Mi sono sentito soddisfatto del risultato finale"},
            {"id": "pos_3", "testo": "Userei di nuovo questo sistema in futuro"},
        ]
    },
]

PROFILO = [
    {
        "id": "profilo_java",
        "testo": "Qual e' il tuo livello di esperienza con la programmazione Java?",
        "tipo": "scelta",
        "opzioni": [
            "Nessuna esperienza",
            "Principiante (conosco le basi)",
            "Intermedio (ho sviluppato progetti autonomamente)",
            "Avanzato (sviluppo Java regolarmente)"
        ]
    },
    {
        "id": "profilo_ai",
        "testo": "Hai mai usato strumenti AI per generare codice?",
        "tipo": "scelta",
        "opzioni": [
            "No, mai",
            "Si, qualche volta (es. ChatGPT, Copilot)",
            "Si, lo uso regolarmente"
        ]
    },
]

FEEDBACK_APERTO = [
    {
        "id": "feedback_positivo",
        "testo": "Cosa hai trovato piu' utile o interessante nel sistema?"
    },
    {
        "id": "feedback_miglioramenti",
        "testo": "Cosa cambieresti o miglioreresti? Hai riscontrato problemi o limitazioni?"
    },
]

SCALA = ["0 - Per niente", "1 - Poco", "2 - Abbastanza", "3 - Molto", "4 - Moltissimo"]


def _chiedi_geq(domanda: dict) -> str:
    """Mostra una domanda GEQ su scala 0-4."""
    print(f"\n  {domanda['testo']}")
    for i, label in enumerate(SCALA):
        print(f"    {label}")
    while True:
        try:
            risposta = input("  Inserisci il valore (0-4): ").strip()
            val = int(risposta)
            if 0 <= val <= 4:
                return str(val)
            print("  Inserisci un numero tra 0 e 4")
        except (ValueError, EOFError):
            print("  Inserisci un numero tra 0 e 4")


def _chiedi_scelta(domanda: dict) -> str:
    """Mostra una domanda a scelta multipla."""
    print(f"\n  {domanda['testo']}")
    for i, opzione in enumerate(domanda["opzioni"], 1):
        print(f"    {i}) {opzione}")
    while True:
        try:
            risposta = input("  Inserisci il numero: ").strip()
            idx = int(risposta) - 1
            if 0 <= idx < len(domanda["opzioni"]):
                return domanda["opzioni"][idx]
            print(f"  Inserisci un numero tra 1 e {len(domanda['opzioni'])}")
        except (ValueError, EOFError):
            print(f"  Inserisci un numero tra 1 e {len(domanda['opzioni'])}")


def _chiedi_aperta(domanda: dict) -> str:
    """Mostra una domanda aperta."""
    print(f"\n  {domanda['testo']}")
    print("  (Scrivi la risposta e premi INVIO. Lascia vuoto per saltare.)")
    try:
        risposta = input("  > ").strip()
        return risposta if risposta else "(nessuna risposta)"
    except EOFError:
        return "(nessuna risposta)"


def esegui_questionario(class_names: list, output_dir: str) -> dict:
    """
    Esegue il questionario GEQ nel terminale al termine del run.
    Salva le risposte in output/questionario_risultati.csv
    """
    print("\n" + "=" * 60)
    print("  QUESTIONARIO DI VALUTAZIONE — GEQ")
    print("  Sistema Multi-Agente per la Generazione di Codice Java")
    print("=" * 60)
    print("\n  Grazie per aver utilizzato il sistema!")
    print("  Ti chiediamo di rispondere a qualche domanda.")
    print("  Ci vorranno circa 5 minuti.\n")
    print("  Scala di risposta:")
    for label in SCALA:
        print(f"    {label}")
    print("-" * 60)

    risposte = {
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "classi_generate": ", ".join(class_names),
        "num_classi":      str(len(class_names)),
    }

    # ── Profilo utente ────────────────────────────────────────────
    print("\n  PROFILO UTENTE")
    print("  " + "-" * 50)
    for domanda in PROFILO:
        risposte[domanda["id"]] = _chiedi_scelta(domanda)

    # ── Domande GEQ per componente ────────────────────────────────
    for comp in GEQ_COMPONENTI:
        print(f"\n  {comp['componente'].upper()} — {comp['descrizione']}")
        print("  " + "-" * 50)
        for domanda in comp["domande"]:
            risposte[domanda["id"]] = _chiedi_geq(domanda)

    # ── Feedback aperto ───────────────────────────────────────────
    print("\n  FEEDBACK LIBERO")
    print("  " + "-" * 50)
    for domanda in FEEDBACK_APERTO:
        risposte[domanda["id"]] = _chiedi_aperta(domanda)

    # ── Salva nel CSV ─────────────────────────────────────────────
    csv_path = Path(output_dir) / "questionario_risultati.csv"
    file_exists = csv_path.exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(risposte.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(risposte)

    print("\n" + "-" * 60)
    print(f"  Risposte salvate in: {csv_path}")
    print("-" * 60)
    print("\n  Grazie per il tuo feedback!")
    print("=" * 60 + "\n")

    return risposte


# ══════════════════════════════════════════════════════════════════
#  FUNZIONI PRINCIPALI
# ══════════════════════════════════════════════════════════════════

def ask_problem() -> str:
    print("\n" + "=" * 60)
    print("  AGENTIC AI — PROGETTAZIONE SOFTWARE")
    print("  Sistema Multi-Agente: CrewAI + Groq")
    print("=" * 60)
    print("\n  Agenti:")
    print("  1. DialogAgent    — Raccolta interattiva dei requisiti")
    print("  2. AnalysisAgent  — Analisi dei requisiti")
    print("  3. UMLAgent       — Diagramma delle classi (PlantUML)")
    print("  4. CodeAgent      — Implementazione Java")
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


def save_outputs(result, file_manager: FileManager, enriched_description: str = "") -> list:
    """Estrae e salva i file dall'output della crew. Restituisce i nomi delle classi salvate."""
    output_text = str(result)
    file_manager.save("00_full_output.txt", output_text)

    if enriched_description:
        file_manager.save("00_enriched_description.md", enriched_description)
        print("  OK  Descrizione arricchita salvata in output/00_enriched_description.md")

    tasks_output = result.tasks_output if hasattr(result, "tasks_output") else []
    class_names = getattr(result, "class_names", [])
    pkg = FileManager.JAVA_PACKAGE

    if len(tasks_output) >= 1:
        file_manager.save("01_analysis.md", tasks_output[0].raw)
        print("  OK  Analisi salvata in output/01_analysis.md")

    if len(tasks_output) >= 2:
        uml_raw = tasks_output[1].raw
        match = re.search(r"(@startuml.*?@enduml)", uml_raw, re.DOTALL)
        uml = match.group(1) if match else uml_raw
        file_manager.save("02_class_diagram.puml", uml)
        print("  OK  Diagramma UML salvato in output/02_class_diagram.puml")

    if len(tasks_output) >= 3:
        java_tasks = tasks_output[2:-1]
        readme_task = tasks_output[-1]
        saved_count = 0
        analysis_text = tasks_output[0].raw if tasks_output else ""

        for i, task in enumerate(java_tasks):
            code_raw = task.raw
            if i < len(class_names):
                class_name = class_names[i]
                filename = f"{class_name}.java"
            else:
                match_class = re.search(r'public\s+class\s+(\w+)', code_raw)
                if not match_class:
                    print(f"  WARN  Classe non riconosciuta nel task {i+1}, saltato")
                    continue
                class_name = match_class.group(1)
                filename = f"{class_name}.java"
            file_manager.save_java(filename, code_raw)
            saved_count += 1

        print(f"  OK  {saved_count} file Java salvati in output/java/src/main/java/com/{pkg}/")
        file_manager.save_main(class_names, analysis_text)
        file_manager.save_pom()

        readme_raw = readme_task.raw
        readme_clean = re.sub(r'```[a-zA-Z]*\n?|```', '', readme_raw).strip()
        file_manager.save("java/README.md", readme_clean)
        print("  OK  README.md salvato")

        print("\n" + "-" * 60)
        print("  Per compilare ed eseguire il progetto Java:")
        print("    cd output/java")
        print("    mvn clean compile")
        print("    mvn exec:java")
        print("-" * 60)

    return class_names


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
    print("-" * 60 + "\n")

    try:
        result = create_crew_with_explicit_context(enriched_problem)
    except Exception as e:
        print(f"\n  ERRORE durante l'esecuzione: {e}")
        raise

    print("\n" + "=" * 60)
    print("  Pipeline completata! Salvataggio dei file...")
    print("=" * 60 + "\n")

    fm = FileManager(Config.OUTPUT_DIR)
    class_names = save_outputs(result, fm, enriched_description=enriched_problem)

    print("\n" + "=" * 60)
    print("  Tutto completato. Controlla la cartella output/")
    print("=" * 60 + "\n")

    # ── Fase 4: Questionario GEQ ──────────────────────────────────────────
    esegui_questionario(class_names, Config.OUTPUT_DIR)


if __name__ == "__main__":
    main()
