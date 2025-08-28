#!/usr/bin/env python3
"""
Varre quantidades de threads para encontrar a configuração "ótima" (menor tempo médio).
- Compila o projeto (javac)
- Detecta classe principal (app.Main ou src.Main)
- Executa PAR (modo paralelo) para T = tmin..tmax, com N iterações por T
- Aplica parada antecipada: se não houver ganho >= min_gain por 'patience' threads consecutivos, interrompe
- Gera gráficos:
    - out/threads_sweep.png (tempo médio vs threads, com std)
    - out/threads_runs.png  (tempo por execução, linhas por T)

Requisitos:
  - Python 3
  - pandas, matplotlib
  - JDK (javac/java) no PATH
  - data/Entrada01.txt existente
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import math
import statistics
import time

ROOT = Path(__file__).resolve().parents[1]   # raiz do projeto
SRC_ROOT = ROOT / "src"
SRC_APP = SRC_ROOT / "app"
TARGET = ROOT / "target" / "classes"
DATA = ROOT / "data" / "Entrada01.txt"
OUT_DIR = ROOT / "out"

def ensure_dirs():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TARGET.mkdir(parents=True, exist_ok=True)

def detect_main_class():
    app_main = TARGET / "app" / "Main.class"
    src_main = TARGET / "src" / "Main.class"
    if app_main.exists():
        return "app.Main"
    if src_main.exists():
        return "src.Main"
    # inferir pelo fonte
    candidates = [SRC_APP / "Main.java", SRC_ROOT / "Main.java"]
    for m in candidates:
        if m.exists():
            try:
                first = m.read_text(encoding="utf-8").splitlines()[0].strip()
                if first.startswith("package app"):
                    return "app.Main"
                if first.startswith("package src"):
                    return "src.Main"
            except Exception:
                pass
    return "app.Main"

def compile_project():
    java_sources = list(SRC_APP.glob("*.java"))
    if not java_sources:
        java_sources = list(SRC_ROOT.glob("*.java"))
        if not java_sources:
            print("ERRO: não encontrei .java em src/ ou src/app/")
            sys.exit(2)
    cmd = ["javac", "-d", str(TARGET), "-sourcepath", str(SRC_ROOT)] + [str(p) for p in java_sources]
    print("Compilando:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Falha na compilação:\n", res.stdout, "\n", res.stderr)
        sys.exit(2)

def run_java(main_class, threads):
    """
    Executa uma vez o modo paralelo com 'threads' e retorna tempo em ms.
    O Main.java imprime "Paralelo (X threads): Y ms" no stdout.
    """
    output_path = OUT_DIR / f"primes_t{threads}.txt"
    cmd = ["java", "-cp", str(TARGET), main_class, "par", str(DATA), str(output_path), str(threads)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("ERRO ao executar:", " ".join(cmd))
        print("stdout:", res.stdout)
        print("stderr:", res.stderr)
        raise RuntimeError("Falha na execução Java")
    # extrair último número "Y ms"
    line = res.stdout.strip().splitlines()[-1]
    # busca padrão simples
    # ex: "Paralelo (10 threads): 2055 ms"
    try:
        ms_token = [tok for tok in line.split() if tok.isdigit() or tok.endswith("ms")][-1]
        ms_val = int(ms_token.replace("ms", ""))
        return ms_val
    except Exception:
        # fallback: não conseguiu parsear — tenta achar número
        import re
        m = re.search(r"(\d+)\s*ms", line)
        if not m:
            raise RuntimeError(f"Não consegui extrair ms a partir de: {line}")
        return int(m.group(1))

def sweep_threads(main_class, iters, tmin, tmax, patience, min_gain):
    """
    Varre threads de tmin..tmax, iters vezes cada.
    Parada antecipada: se não houver melhoria relativa >= min_gain por 'patience' threads consecutivos, interrompe.
    Retorna DataFrame com colunas: threads, run_idx, ms
    """
    records = []
    best_mean = math.inf
    no_improve = 0

    for t in range(tmin, tmax + 1):
        times = []
        print(f"== Threads {t} ==")
        for i in range(1, iters + 1):
            ms = run_java(main_class, t)
            times.append(ms)
            records.append({"threads": t, "run_idx": i, "ms": ms})
            print(f"  iteração {i}/{iters}: {ms} ms")
        mean_t = statistics.mean(times)
        std_t = statistics.pstdev(times) if len(times) > 1 else 0.0
        print(f"  média: {mean_t:.1f} ms  |  std: {std_t:.1f} ms")

        if mean_t + 1e-9 < best_mean:  # melhoria estrita
            gain = (best_mean - mean_t) / best_mean if best_mean < math.inf else 1.0
            print(f"  --> NOVO MELHOR: {mean_t:.1f} ms (ganho {gain*100:.2f}%)")
            best_mean = mean_t
            no_improve = 0
        else:
            # ver se ainda assim há um ganho relativo suficiente
            gain = 0.0
            if best_mean < math.inf:
                gain = (best_mean - mean_t) / best_mean
            if gain >= min_gain:
                print(f"  ganho >= min_gain ({min_gain*100:.2f}%), continua")
                no_improve = 0
            else:
                no_improve += 1
                print(f"  sem ganho relevante (<{min_gain*100:.2f}%), no_improve={no_improve}/{patience}")
                if no_improve >= patience:
                    print("Parada antecipada por ausência de ganho relevante.")
                    break

    df = pd.DataFrame.from_records(records)
    return df

def plot_thread_sweep(df):
    # --- Gráfico 1: tempo médio vs threads (em colunas, com barras de erro) ---
    agg = df.groupby("threads", as_index=False)["ms"].agg(["mean", "std"]).reset_index()
    agg.rename(columns={"mean": "ms_mean", "std": "ms_std"}, inplace=True)

    plt.figure()
    plt.bar(
        agg["threads"],
        agg["ms_mean"],
        yerr=agg["ms_std"].fillna(0),
        capsize=5,
        width=0.6,          # largura maior -> colunas
        align="center"      # centraliza no eixo x
    )
    plt.xticks(agg["threads"])  # garante rótulo numérico exato em cada coluna
    plt.xlabel("Threads")
    plt.ylabel("Tempo médio (ms)")
    plt.title("Varredura de Threads — Tempo médio por configuração")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "threads_sweep.png", dpi=150)

    # Gráfico 2: cada execução (linhas por T)
    plt.figure()
    for t, g in df.groupby("threads"):
        # ordenar por run_idx
        g = g.sort_values("run_idx")
        plt.plot(g["run_idx"], g["ms"], marker="o", label=f"t={t}")
    plt.xlabel("Iteração")
    plt.ylabel("Tempo (ms)")
    plt.title("Tempo por iteração para cada nº de threads")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "threads_runs.png", dpi=150)

def main():
    parser = argparse.ArgumentParser(description="Encontrar número de threads ótimo (parada antecipada).")
    default_tmax = max(2, (os.cpu_count() or 4) * 2)  # até 2x núcleos lógicos
    parser.add_argument("--iters", type=int, default=10, help="Iterações por configuração (default: 10)")
    parser.add_argument("--tmin", type=int, default=1, help="Threads mínimas (default: 1)")
    parser.add_argument("--tmax", type=int, default=default_tmax, help=f"Threads máximas (default: {default_tmax})")
    parser.add_argument("--patience", type=int, default=2, help="Parar após 'patience' threads sem ganho relevante (default: 2)")
    parser.add_argument("--min_gain", type=float, default=0.02, help="Ganho mínimo relativo (ex: 0.02 = 2%%) (default: 0.02)")
    args = parser.parse_args()

    if not DATA.exists():
        print(f"ERRO: Arquivo de entrada não encontrado: {DATA}")
        sys.exit(2)

    ensure_dirs()
    compile_project()
    main_class = detect_main_class()
    print("Main class:", main_class)
    print(f"Varredura de threads: {args.tmin}..{args.tmax}, iterações={args.iters}, patience={args.patience}, min_gain={args.min_gain*100:.2f}%")

    df = sweep_threads(main_class, args.iters, args.tmin, args.tmax, args.patience, args.min_gain)

    if df.empty:
        print("Nenhum dado coletado.")
        sys.exit(2)

    # Seleciona o T ótimo (menor média)
    agg = df.groupby("threads", as_index=False)["ms"].mean().rename(columns={"ms":"ms_mean"})
    best_row = agg.loc[agg["ms_mean"].idxmin()]
    best_t = int(best_row["threads"])
    best_ms = float(best_row["ms_mean"])
    print("\n===== RESULTADO =====")
    print(f"Threads ótimas (menor tempo médio): {best_t}  |  {best_ms:.1f} ms")

    plot_thread_sweep(df)

if __name__ == "__main__":
    main()
