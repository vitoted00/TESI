import re
from pathlib import Path


class FileManager:

    JAVA_PACKAGE = "progetto_generato"

    AUTO_IMPORTS = {
        "Objects.":         "import java.util.Objects;",
        "LocalDate":        "import java.time.LocalDate;",
        "LocalDateTime":    "import java.time.LocalDateTime;",
        "List":             "import java.util.List;",
        "ArrayList":        "import java.util.ArrayList;",
        "Map":              "import java.util.Map;",
        "HashMap":          "import java.util.HashMap;",
    }

    # Valori di default per tipo Java
    _JAVA_DEFAULTS = {
        "String":        '"esempio"',
        "int":           "1",
        "Integer":       "1",
        "long":          "1L",
        "Long":          "1L",
        "double":        "1.0",
        "Double":        "1.0",
        "float":         "1.0f",
        "Float":         "1.0f",
        "boolean":       "true",
        "Boolean":       "true",
        "LocalDate":     "LocalDate.now()",
        "LocalDateTime": "LocalDateTime.now()",
    }

    # Valori di default per nome parametro — piu' realistici di "esempio"
    # Funziona per qualsiasi dominio (libreria, pizzeria, ospedale, ecc.)
    _PARAM_NAME_DEFAULTS = {
        "nome":              '"Mario"',
        "cognome":           '"Rossi"',
        "titolo":            '"Titolo Esempio"',
        "autore":            '"Mario Rossi"',
        "email":             '"test@email.it"',
        "indirizzoEmail":    '"test@email.it"',
        "password":          '"password123"',
        "isbn":              '"978-0000000000"',
        "codiceIsbn":        '"978-0000000000"',
        "indirizzo":         '"Via Roma 1"',
        "telefono":          '"3331234567"',
        "numeroDiTelefono":  '"3331234567"',
        "descrizione":       '"Descrizione esempio"',
        "tipo":              '"tipo_esempio"',
        "tipoDiPagamento":   '"contanti"',
        "categoria":         '"categoria_esempio"',
        "ruolo":             '"amministratore"',
        "codice":            '"COD001"',
        "codiceFiscale":     '"RSSMRA80A01H501Z"',
        "targa":             '"AB123CD"',
        "modello":           '"Modello Esempio"',
        "marca":             '"Marca Esempio"',
        "colore":            '"rosso"',
        "via":               '"Via Roma 1"',
        "citta":             '"Roma"',
        "cap":               '"00100"',
        "username":          '"utente123"',
        "cf":                '"RSSMRA80A01H501Z"',
        "piva":              '"12345678901"',
        "partitaIva":        '"12345678901"',
        "specializzazione":  '"Medicina Generale"',
        "reparto":           '"Cardiologia"',
        "ingrediente":       '"Pomodoro"',
        "piatto":            '"Margherita"',
        "materia":           '"Matematica"',
        "corso":             '"Informatica"',
    }

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._java_cleaned = False

    def _fix_imports(self, content: str) -> str:
        for symbol, import_stmt in self.AUTO_IMPORTS.items():
            if symbol in content and import_stmt not in content:
                content = re.sub(
                    r'(^package\s+\S+;)',
                    rf'\1\n{import_stmt}',
                    content, count=1, flags=re.MULTILINE
                )
                print(f"  🔧  Import aggiunto automaticamente: {import_stmt}")
        return content

    def _clean_java(self, content: str) -> str:
        content = content.replace('<｜begin▁of▁sentence｜>', '')
        content = content.replace('\uff5c', '')
        content = content.replace('\u2581', '')
        content = re.sub(r'```[a-zA-Z]*', '', content)
        content = content.replace('`', '')
        content = re.sub(r'^//\s*FILE:.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^#{1,6} .*$', '', content, flags=re.MULTILINE)

        match = re.search(r'^package\s+\S+;', content, re.MULTILINE)
        if match:
            content = content[match.start():]

        last_brace = content.rfind('}')
        if last_brace != -1:
            content = content[:last_brace + 1]
        else:
            content = content.rstrip() + '\n}'

        content = re.sub(
            r'^package\s+com\.\w+;',
            f'package com.{self.JAVA_PACKAGE};',
            content, count=1, flags=re.MULTILINE
        )
        content = self._fix_imports(content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    def _clean_java_folder(self):
        if not self._java_cleaned:
            java_dir = (
                self.output_dir / "java" / "src" / "main" / "java" / "com" / self.JAVA_PACKAGE
            )
            if java_dir.exists():
                for f in java_dir.glob("*.java"):
                    try:
                        f.unlink()
                    except PermissionError:
                        print(f"  ⚠  Impossibile eliminare {f.name}, verra' sovrascritta.")
                print("  🗑  File Java precedenti eliminati.")
            self._java_cleaned = True

    def save(self, filename: str, content: str) -> Path:
        filepath = self.output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        print(f"  ✔  Salvato: {filepath}")
        return filepath

    def save_java(self, filename: str, content: str) -> Path:
        self._clean_java_folder()
        content = self._clean_java(content)
        java_dir = (
            self.output_dir / "java" / "src" / "main" / "java" / "com" / self.JAVA_PACKAGE
        )
        java_dir.mkdir(parents=True, exist_ok=True)
        filepath = java_dir / filename
        filepath.write_text(content, encoding="utf-8")
        print(f"  ✔  Java salvato: java/src/main/java/com/{self.JAVA_PACKAGE}/{filename}")
        return filepath

    def _parse_constructor(self, class_name: str) -> list:
        """
        Legge il file .java e restituisce lista di tuple (tipo, nome_parametro)
        dal primo costruttore pubblico trovato.
        """
        java_dir = (
            self.output_dir / "java" / "src" / "main" / "java" / "com" / self.JAVA_PACKAGE
        )
        java_file = java_dir / f"{class_name}.java"
        if not java_file.exists():
            return None

        source = java_file.read_text(encoding="utf-8")
        pattern = rf'public\s+{re.escape(class_name)}\s*\(([^)]*)\)'
        match = re.search(pattern, source)
        if not match:
            return []

        params_str = match.group(1).strip()
        if not params_str:
            return []

        params = []
        for param in params_str.split(","):
            param = param.strip()
            if param:
                tokens = param.split()
                tipo = tokens[0].split("<")[0]
                nome = tokens[1] if len(tokens) > 1 else "valore"
                params.append((tipo, nome))
        return params

    def _extract_valid_string_values(self, class_name: str) -> list:
        """
        Legge il sorgente Java e cerca valori String validi nelle validazioni,
        tipo: if (!stato.equalsIgnoreCase("disponibile") && ...)
        Restituisce lista di valori gia' quotati, es: ['"disponibile"', '"prestato"']
        """
        java_dir = (
            self.output_dir / "java" / "src" / "main" / "java" / "com" / self.JAVA_PACKAGE
        )
        java_file = java_dir / f"{class_name}.java"
        if not java_file.exists():
            return []

        source = java_file.read_text(encoding="utf-8")
        raw = re.findall(r'equalsIgnoreCase\("([^"]+)"\)|\.equals\("([^"]+)"\)', source)
        result = []
        seen = set()
        for v1, v2 in raw:
            val = v1 if v1 else v2
            # Escludi messaggi di errore: troppo lunghi o con spazi
            if val and len(val) < 25 and " " not in val and val not in seen:
                seen.add(val)
                result.append(f'"{val}"')
        return result

    def _get_string_value_for_param(self, param_name: str, valid_values: list) -> str:
        """
        Sceglie il valore String piu' appropriato per un parametro:
        1. Cerca corrispondenza esatta nel dizionario _PARAM_NAME_DEFAULTS
        2. Cerca corrispondenza per sottostringa (es. "stato" in "statoOrdine")
        3. Se il nome suggerisce un campo con enum (stato, tipo, categoria...)
           usa il primo valore valido trovato nel sorgente
        4. Fallback: "esempio"
        """
        param_lower = param_name.lower()

        # 1. Corrispondenza esatta
        if param_name in self._PARAM_NAME_DEFAULTS:
            return self._PARAM_NAME_DEFAULTS[param_name]

        # 2. Corrispondenza per sottostringa
        for key, value in self._PARAM_NAME_DEFAULTS.items():
            if key.lower() in param_lower or param_lower in key.lower():
                return value

        # 3. Campo che probabilmente ha valori enum → usa valore dal sorgente
        enum_keywords = ["stato", "status", "tipo", "type", "categoria",
                         "category", "ruolo", "role", "modalita", "fase"]
        if any(kw in param_lower for kw in enum_keywords):
            if valid_values:
                return valid_values[0]

        # 4. Fallback generico
        return valid_values[0] if valid_values else '"esempio"'

    def _build_constructor_call(self, class_name: str, params: list,
                                all_classes: list) -> str:
        """
        Costruisce new ClassName(arg1, arg2, ...) con valori appropriati:
        - String: usa il valore piu' sensato in base al nome del parametro
        - Classi del progetto: usa l'istanza objCls gia' creata
        - Altri tipi: usa i default standard (LocalDate.now(), 1, 1.0, ecc.)
        """
        valid_strings = self._extract_valid_string_values(class_name)

        args = []
        for tipo, nome in params:
            if tipo == "String":
                args.append(self._get_string_value_for_param(nome, valid_strings))
            elif tipo in self._JAVA_DEFAULTS:
                args.append(self._JAVA_DEFAULTS[tipo])
            elif tipo in all_classes:
                args.append(f"obj{tipo}")
            else:
                args.append("null")
        return f"new {class_name}({', '.join(args)})"

    def save_main(self, class_names: list, analysis_text: str) -> Path:
        """
        Genera Main.java leggendo costruttori reali e nomi dei parametri
        dai file .java appena salvati, cosi' i valori di esempio sono sempre
        compatibili con le validazioni presenti nel codice.
        """
        pkg = self.JAVA_PACKAGE

        # ── 1. Analizza costruttori ───────────────────────────────────────
        constructors = {}
        for cls in class_names:
            params = self._parse_constructor(cls)
            constructors[cls] = params if params is not None else []
            n = len(constructors[cls])
            print(f"  🔍  Costruttore {cls}: ({n} param)")
            valid = self._extract_valid_string_values(cls)
            if valid:
                print(f"       Valori validi rilevati: {valid}")

        # ── 2. Genera il codice ───────────────────────────────────────────
        lines = []
        lines.append(f"package com.{pkg};")
        lines.append("")
        lines.append("import java.time.LocalDate;")
        lines.append("import java.time.LocalDateTime;")
        lines.append("import java.util.ArrayList;")
        lines.append("")
        lines.append("/**")
        lines.append(" * Main generato automaticamente — testa ogni classe del progetto.")
        lines.append(" * Compilare con:  mvn clean compile")
        lines.append(" * Eseguire con:   mvn exec:java")
        lines.append(" */")
        lines.append("public class Main {")
        lines.append("")
        lines.append("    public static void main(String[] args) {")
        lines.append(f'        System.out.println("=== Test progetto generato ===");')
        lines.append(f'        System.out.println("Classi: {", ".join(class_names)}");')
        lines.append(f'        System.out.println();')
        lines.append("")

        for cls in class_names:
            lines.append(f'        // ── {cls} ──────────────────────────────────────────')
            lines.append(f'        System.out.println("--- {cls} ---");')
            lines.append(f'        {cls} obj{cls} = null;')
            lines.append(f'        try {{')
            params = constructors[cls]
            call = self._build_constructor_call(cls, params, class_names)
            lines.append(f'            obj{cls} = {call};')
            lines.append(f'            System.out.println("  toString : " + obj{cls});')
            lines.append(f'            System.out.println("  OK");')
            lines.append(f'        }} catch (Exception e) {{')
            lines.append(f'            System.out.println("  ERRORE: " + e.getMessage());')
            lines.append(f'        }}')
            lines.append(f'        System.out.println();')
            lines.append("")

        lines.append(f'        System.out.println("=== Fine test ===");')
        lines.append("    }")
        lines.append("}")

        content = "\n".join(lines)

        java_dir = (
            self.output_dir / "java" / "src" / "main" / "java" / "com" / self.JAVA_PACKAGE
        )
        java_dir.mkdir(parents=True, exist_ok=True)
        filepath = java_dir / "Main.java"
        filepath.write_text(content, encoding="utf-8")
        print(f"  ✔  Main.java generato in java/src/main/java/com/{self.JAVA_PACKAGE}/Main.java")
        return filepath

    def save_pom(self) -> Path:
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.{self.JAVA_PACKAGE}</groupId>
    <artifactId>gestione-{self.JAVA_PACKAGE}</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.release>17</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <exec.mainClass>com.{self.JAVA_PACKAGE}.Main</exec.mainClass>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.1.2</version>
            </plugin>
            <plugin>
                <groupId>org.codehaus.mojo</groupId>
                <artifactId>exec-maven-plugin</artifactId>
                <version>3.1.0</version>
                <configuration>
                    <mainClass>com.{self.JAVA_PACKAGE}.Main</mainClass>
                </configuration>
            </plugin>
        </plugins>
    </build>

</project>"""
        java_dir = self.output_dir / "java"
        java_dir.mkdir(parents=True, exist_ok=True)
        filepath = java_dir / "pom.xml"
        filepath.write_text(content, encoding="utf-8")
        print("  ✔  pom.xml generato")
        return filepath
