# Prime Number Verifier — Parallel Benchmark

This project implements prime number verification in **Java**, comparing:

* **Sequential execution (1 thread)**
* **Parallel execution (5 threads)**
* **Parallel execution (10 threads)**
  and allows experimenting with an arbitrary number of threads to find the optimal configuration.

Results are collected, analyzed, and visualized using **Python** scripts.

---

## 📦 Prerequisites

* **Java JDK 11+**
  Ensure `javac` and `java` are available on your PATH:

  ```bash
  java -version
  javac -version
  ```

* **Python 3.8+** with:

  * `pandas`
  * `matplotlib`

  Install dependencies:

  ```bash
  pip install pandas matplotlib
  ```

* Input file: `data/Entrada01.txt` (already included in this repo).

---

## ⚙️ Compilation

Compile the Java sources to `target/classes`:

```bash
rm -rf target/classes
mkdir -p target/classes
javac -d target/classes -sourcepath src src/app/*.java
```

This produces compiled classes in `target/classes/app/`.

---

## ▶️ Running the Programs

### Sequential version

```bash
java -cp target/classes app.Main seq data/Entrada01.txt out/primes_seq.txt
```

### Parallel version with 5 threads

```bash
java -cp target/classes app.Main par data/Entrada01.txt out/primes_t5.txt 5
```

### Parallel version with 10 threads

```bash
java -cp target/classes app.Main par data/Entrada01.txt out/primes_t10.txt 10
```

### Parallel version with arbitrary thread count

```bash
java -cp target/classes app.Main par data/Entrada01.txt out/primes_tN.txt N
```

Each run appends timing results to `out/results.csv`.

---

## 📊 Benchmarking Script

To automate **10 iterations** for each version (seq, par-5, par-10) and generate performance plots:

```bash
python3 analysis/benchmark_and_plot.py
```

This script will:

* Recompile the project,
* Run each scenario 10×,
* Save consolidated results in `out/results.csv`,
* Generate two plots:

  * `out/performance_ms.png` — execution time per iteration (line chart),
  * `out/performance_speedup.png` — average speedup vs sequential (bar chart).

---

## 🔍 Finding the Optimal Number of Threads

Use the separate script:

```bash
python3 analysis/find_opt_threads.py
```

Options:

* `--iters N` : number of iterations per thread count (default: 10)
* `--tmin M`  : minimum number of threads (default: 1)
* `--tmax K`  : maximum number of threads (default: 2 × CPU cores)
* `--patience P` : stop if no relevant gain after P consecutive thread counts (default: 2)
* `--min_gain G` : minimum relative gain to continue (default: 0.02 = 2%)

Example:

```bash
python3 analysis/find_opt_threads.py --iters 8 --tmin 1 --tmax 16 --patience 3 --min_gain 0.03
```

This will:

* Compile and run the program with different thread counts,
* Collect timings into memory,
* Determine the optimal number of threads (lowest mean time),
* Produce two plots:

  * `out/threads_sweep.png` — mean time vs thread count (columns with error bars),
  * `out/threads_runs.png` — execution time per iteration for each thread count (line chart).

---

## 📁 Project Structure

```
prime-verifier/
├── analysis/
│   ├── benchmark_and_plot.py   # Fixed scenarios (1, 5, 10 threads)
│   └── find_opt_threads.py     # Sweep to find optimal threads
├── data/
│   └── Entrada01.txt           # Input numbers
├── out/
│   ├── results.csv             # Benchmark results (auto-generated)
│   ├── performance_ms.png
│   ├── performance_speedup.png
│   ├── threads_sweep.png
│   └── threads_runs.png
├── src/
│   └── app/
│       ├── Main.java
│       ├── ParallelPrimeFinder.java
│       ├── PrimeUtils.java
│       └── SequentialPrimeFinder.java
└── target/
    └── classes/                # Compiled .class files
```

---

## 📝 Notes

* Output prime numbers are written in the **same order** as in the input file.
* Parallelization uses **multiple threads with a shared index and lock**:

  * Each thread picks the next number to process atomically,
  * Synchronization is done via `ReentrantLock` on the shared index,
  * No explicit task objects or blocking queues are used.
* Sequential version runs in a single thread.
* For reliable benchmarks, run on a machine with minimal background load.
