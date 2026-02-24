import re
from pathlib import Path


class FileManager:

    JAVA_PACKAGE = "biblioteca"

    # Import standard che potrebbero servire, controllati automaticamente
    AUTO_IMPORTS = {
        "Objects.":         "import java.util.Objects;",
        "LocalDate":        "import java.time.LocalDate;",
        "LocalDateTime":    "import java.time.LocalDateTime;",
        "List":             "import java.util.List;",
        "ArrayList":        "import java.util.ArrayList;",
        "Map":              "import java.util.Map;",
        "HashMap":          "import java.util.HashMap;",
    }

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._java_cleaned = False  # pulizia eseguita una sola volta per run

    def _fix_imports(self, content: str) -> str:
        """Aggiunge gli import mancanti se il codice li usa ma non li dichiara."""
        for symbol, import_stmt in self.AUTO_IMPORTS.items():
            uses_symbol = symbol in content
            already_imported = import_stmt in content
            if uses_symbol and not already_imported:
                # Inserisce l'import subito dopo la riga "package ..."
                content = re.sub(
                    r'(^package\s+\S+;)',
                    rf'\1\n{import_stmt}',
                    content,
                    count=1,
                    flags=re.MULTILINE
                )
                print(f"  🔧  Import aggiunto automaticamente: {import_stmt}")
        return content

    def _clean_java(self, content: str) -> str:
        """Rimuove token spazzatura del modello e markdown dal codice Java."""

        # Token speciali deepseek / llama
        content = content.replace('<｜begin▁of▁sentence｜>', '')
        content = content.replace('\uff5c', '')
        content = content.replace('\u2581', '')

        # Backtick e blocchi markdown
        content = re.sub(r'```[a-zA-Z]*', '', content)
        content = content.replace('`', '')

        # Righe // FILE: ... e intestazioni markdown (#)
        content = re.sub(r'^//\s*FILE:.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^#{1,6} .*$', '', content, flags=re.MULTILINE)

        # Parti il contenuto da "package ..." — tutto prima e spazzatura
        match = re.search(r'^package\s+\S+;', content, re.MULTILINE)
        if match:
            content = content[match.start():]

        # Taglia tutto dopo l'ultima } della classe
        last_brace = content.rfind('}')
        if last_brace != -1:
            content = content[:last_brace + 1]
        else:
            content = content.rstrip() + '\n}'

        # Normalizza package a com.biblioteca
        content = re.sub(
            r'^package\s+com\.\w+;',
            f'package com.{self.JAVA_PACKAGE};',
            content,
            count=1,
            flags=re.MULTILINE
        )

        # Fix import mancanti
        content = self._fix_imports(content)

        # Riduci righe vuote eccessive
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def _clean_java_folder(self):
        """Cancella i vecchi file .java — una sola volta per run.
        Non usa shutil.rmtree per evitare PermissionError su Windows
        quando la cartella e' aperta in un altro processo (es. PyCharm)."""
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
        """Salva un file generico nella cartella output."""
        filepath = self.output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        print(f"  ✔  Salvato: {filepath}")
        return filepath

    def save_java(self, filename: str, content: str) -> Path:
        """Pulisce e salva un file Java nella cartella com/biblioteca/."""
        self._clean_java_folder()  # cancella solo al primo file del run

        content = self._clean_java(content)

        java_dir = (
            self.output_dir / "java" / "src" / "main" / "java" / "com" / self.JAVA_PACKAGE
        )
        java_dir.mkdir(parents=True, exist_ok=True)

        filepath = java_dir / filename
        filepath.write_text(content, encoding="utf-8")
        print(f"  ✔  Java salvato: java/src/main/java/com/{self.JAVA_PACKAGE}/{filename}")
        return filepath

    def save_pom(self) -> Path:
        """Genera il pom.xml con groupId fisso com.biblioteca."""
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
        </plugins>
    </build>

</project>"""
        java_dir = self.output_dir / "java"
        java_dir.mkdir(parents=True, exist_ok=True)
        filepath = java_dir / "pom.xml"
        filepath.write_text(content, encoding="utf-8")
        print("  ✔  pom.xml generato")
        return filepath
