"""
Automatiza 10 iterações de:
  - Sequencial (1 thread)
  - Paralela (5 threads)
  - Paralela (10 threads)

1) Garante pastas (out/, target/classes/)
2) Compila o projeto
3) Limpa (ou cria) out/results.csv
4) Executa 10 vezes cada cenário
5) Gera gráficos:
     - out/performance_ms.png
     - out/performance_speedup.png

Requisitos:
  - Python 3
  - pandas, matplotlib
  - JDK (javac/java) já no PATH
  - Arquivo data/Entrada01.txt existente
"""

import os
import sys
import subprocess
from pathlib import Path
import time
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]   # raiz do projeto
SRC_DIR = ROOT / "src" / "app"
TARGET = ROOT / "target" / "classes"
DATA = ROOT / "data" / "Entrada01.txt"
OUT_DIR = ROOT / "out"
CSV = OUT_DIR / "results.csv"

ITERATIONS = 10

def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TARGET.mkdir(parents=True, exist_ok=True)
    (ROOT / "analysis").mkdir(parents=True, exist_ok=True)

def detect_main_class():
    """
    Detecta automaticamente se o pacote é 'app' ou 'src'
    com base nos .java e no pacote declarado.
    """
    # Preferência: verificar classes já compiladas
    app_main = TARGET / "app" / "Main.class"
    src_main = TARGET / "src" / "Main.class"
    if app_main.exists():
        return "app.Main"
    if src_main.exists():
        return "src.Main"

    # Se não há compilados ainda, tentamos inferir pelo código-fonte
    # Lê a 1a linha de Main.java e procura 'package app;' ou 'package src;'
    main_java = SRC_DIR / "Main.java"
    if not main_java.exists():
        # fallback: talvez user tenha posto sem subpasta; tenta src/Main.java
        main_java = ROOT / "src" / "Main.java"
    if main_java.exists():
        try:
            first_line = main_java.read_text(encoding="utf-8").splitlines()[0].strip()
            if "package app" in first_line:
                return "app.Main"
            if "package src" in first_line:
                return "src.Main"
        except Exception:
            pass

    # fallback final -> assume 'app.Main'
    return "app.Main"

def compile_project():
    """
    Compila com javac, gerando a árvore de pacotes em target/classes.
    Usa -sourcepath para evitar 'src' duplicado no caminho de saída.
    """
    # Decide quais .java compilar
    java_sources = list((ROOT / "src" / "app").glob("*.java"))
    if not java_sources:
        # fallback: todos os .java em src/
        java_sources = list((ROOT / "src").glob("*.java"))
        if not java_sources:
            print("ERRO: não encontrei arquivos .java em src/ ou src/app/")
            sys.exit(2)

    cmd = ["javac", "-d", str(TARGET), "-sourcepath", str(ROOT / "src")] + [str(p) for p in java_sources]
    print("Compilando:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Falha na compilação:\n", res.stdout, "\n", res.stderr)
        sys.exit(2)

def run_command(cmd):
    """
    Executa um comando e retorna (rc, stdout, stderr).
    """
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def clean_csv():
    if CSV.exists():
        CSV.unlink()

def ensure_input():
    if not DATA.exists():
        print(f"ERRO: Arquivo de entrada não encontrado: {DATA}")
        sys.exit(2)

def bench_once(main_class, mode, output_path, threads=None):
    """
    Executa uma única vez e retorna True se ok.
    O próprio Main.java já escreve (append) no out/results.csv.
    """
    cmd = ["java", "-cp", str(TARGET), main_class, mode, str(DATA), str(output_path)]
    if threads is not None:
        cmd.append(str(threads))

    rc, out, err = run_command(cmd)
    if rc != 0:
        print("ERRO ao executar:", " ".join(cmd))
        print("stdout:\n", out)
        print("stderr:\n", err)
        return False
    # Opcional: mostrar linha de tempo que Main imprime
    line = out.strip().splitlines()[-1] if out.strip() else ""
    print(line)
    return True

def run_benchmark():
    ensure_dirs()
    ensure_input()
    compile_project()
    main_class = detect_main_class()
    print("Main class detectada:", main_class)

    clean_csv()

    # 10x sequencial
    for i in range(1, ITERATIONS + 1):
        print(f"[SEQ] Iteração {i}/{ITERATIONS}")
        ok = bench_once(main_class, "seq", OUT_DIR / "primes_seq.txt")
        if not ok: sys.exit(2)

    # 10x paralelo (5 threads)
    for i in range(1, ITERATIONS + 1):
        print(f"[PAR-5] Iteração {i}/{ITERATIONS}")
        ok = bench_once(main_class, "par", OUT_DIR / "primes_t5.txt", threads=5)
        if not ok: sys.exit(2)

    # 10x paralelo (10 threads)
    for i in range(1, ITERATIONS + 1):
        print(f"[PAR-10] Iteração {i}/{ITERATIONS}")
        ok = bench_once(main_class, "par", OUT_DIR / "primes_t10.txt", threads=10)
        if not ok: sys.exit(2)

def plot_results():
    df = pd.read_csv(CSV)

    # --- Gráfico 1: tempo por iteração ---
    plt.figure()
    # ordena por timestamp para não embaralhar
    df = df.sort_values("timestamp")

    # cria coluna label ex: "seq-1", "par-5"
    df["label"] = df["version"] + "-" + df["threads"].astype(str)

    for label, group in df.groupby("label"):
        plt.plot(range(1, len(group) + 1), group["ms"], marker="o", label=label)

    plt.xlabel("Iteração")
    plt.ylabel("Tempo (ms)")
    plt.title("Desempenho em cada execução (10 iterações)")
    plt.legend()
    plt.tight_layout()
    (OUT_DIR / "performance_ms.png").unlink(missing_ok=True)
    plt.savefig(OUT_DIR / "performance_ms.png", dpi=150)

    # --- Gráfico 2: speedup médio ---
    agg = df.groupby(["version","threads"], as_index=False)["ms"].mean()
    seq_row = agg[(agg["version"]=="seq") & (agg["threads"]==1)]
    if len(seq_row)==0:
        print("Não encontrei baseline sequencial (seq,1) no CSV.")
        sys.exit(2)
    seq_mean = float(seq_row["ms"].iloc[0])

    labels = [f'{v}-{int(t)}' for v,t in zip(agg["version"], agg["threads"])]
    speedup = seq_mean / agg["ms"]

    plt.figure()
    plt.bar(labels, speedup)
    plt.ylabel("Speedup (×)")
    plt.title("Speedup médio vs Sequencial")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    (OUT_DIR / "performance_speedup.png").unlink(missing_ok=True)
    plt.savefig(OUT_DIR / "performance_speedup.png", dpi=150)

    print("Gráficos gerados em:")
    print(f" - {OUT_DIR / 'performance_ms.png'} (linhas por iteração)")
    print(f" - {OUT_DIR / 'performance_speedup.png'} (barras com speedup médio)")


def main():
    run_benchmark()
    plot_results()

if __name__ == "__main__":
    main()
