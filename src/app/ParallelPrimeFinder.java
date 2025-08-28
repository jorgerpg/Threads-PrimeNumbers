package app;

import java.io.*;
import java.nio.file.*;
import java.util.*;

/**
 * Paralelo, mantendo a ORDEM de saída igual à do arquivo de entrada.
 * Implementa fila manual (synchronized + wait/notify), sem concurrent.* avançado.
 */
public class ParallelPrimeFinder {

    // Tarefa: (índice, valor)
    private static final class Task {
        final int idx;
        final long value;
        Task(int idx, long value) { this.idx = idx; this.value = value; }
    }

    // Fila manual com fechamento
    private static final class TaskQueue {
        private final Deque<Task> q = new ArrayDeque<>();
        private boolean closed = false;

        public synchronized void put(Task t) {
            q.addLast(t);
            notifyAll();
        }
        public synchronized Task take() throws InterruptedException {
            while (q.isEmpty() && !closed) wait();
            if (q.isEmpty()) return null;
            return q.removeFirst();
        }
        public synchronized void close() {
            closed = true;
            notifyAll();
        }
    }

    public static long run(Path input, Path output, int nThreads) throws IOException, InterruptedException {
        long start = System.nanoTime();

        // 1) Ler tudo mantendo índice (para preservar a ordem depois)
        List<Long> numbers = new ArrayList<>(1 << 20);
        try (BufferedReader br = Files.newBufferedReader(input)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (!line.isEmpty()) numbers.add(Long.parseLong(line));
            }
        }
        final int N = numbers.size();

        // 2) Estruturas de trabalho
        TaskQueue queue = new TaskQueue();
        // resultado: true se é primo no índice i
        final boolean[] isPrime = new boolean[N];

        // 3) Workers
        Thread[] workers = new Thread[nThreads];
        for (int t = 0; t < nThreads; t++) {
            workers[t] = new Thread(() -> {
                try {
                    Task task;
                    while ((task = queue.take()) != null) {
                        isPrime[task.idx] = PrimeUtils.isPrime(task.value);
                    }
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                }
            }, "worker-" + t);
            workers[t].start();
        }

        // 4) Producer: envia tarefas
        for (int i = 0; i < N; i++) {
            queue.put(new Task(i, numbers.get(i)));
        }
        queue.close();

        // 5) Esperar workers
        for (Thread w : workers) w.join();

        // 6) Gravar SAÍDA em ORDEM
        try (BufferedWriter bw = Files.newBufferedWriter(output)) {
            for (int i = 0; i < N; i++) {
                if (isPrime[i]) {
                    bw.write(Long.toString(numbers.get(i)));
                    bw.newLine();
                }
            }
        }

        long end = System.nanoTime();
        return (end - start) / 1_000_000; // ms
    }
}
