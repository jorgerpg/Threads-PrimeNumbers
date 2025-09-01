package app;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

/**
 * ParallelPrimeFinder:
 * Programa que verifica números primos em paralelo usando threads,
 * mantendo a ordem de saída igual à do arquivo de entrada.
 */
public class ParallelPrimeFinder {

    // Índice global compartilhado entre threads para pegar o próximo número
    private static int currentIndex = 0;

    // Lock para sincronizar o acesso ao currentIndex
    private static final Lock indexLock = new ReentrantLock();

    /**
     * run:
     * Lê números do arquivo de entrada, verifica quais são primos usando nThreads,
     * e grava o resultado em ordem no arquivo de saída.
     *
     * @param input Arquivo de entrada com números
     * @param output Arquivo de saída para números primos
     * @param nThreads Número de threads a serem usadas
     * @return tempo de execução em milissegundos
     */
    public static long run(Path input, Path output, int nThreads) throws IOException, InterruptedException {
        long start = System.nanoTime();

        // 1) Ler todos os números do arquivo
        List<Long> numbers = new ArrayList<>();
        try (BufferedReader br = Files.newBufferedReader(input)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (!line.isEmpty()) numbers.add(Long.parseLong(line));
            }
        }

        final int N = numbers.size();
        // Array booleano para armazenar resultados: true se é primo
        final boolean[] isPrime = new boolean[N];

        // 2) Criar e iniciar threads de trabalho (workers)
        Thread[] workers = new Thread[nThreads];
        for (int t = 0; t < nThreads; t++) {
            workers[t] = new Thread(() -> {
                while (true) {
                    int idx;

                    // 🔒 Pega o índice de forma segura
                    indexLock.lock();
                    try {
                        // Se já processamos todos os números, a thread termina
                        if (currentIndex >= N) break;
                        // Cada thread pega um número único
                        idx = currentIndex++;
                    } finally {
                        indexLock.unlock();
                    }

                    // ⚡ Processamento paralelo: verifica se o número é primo
                    isPrime[idx] = PrimeUtils.isPrime(numbers.get(idx));
                }
            });
            workers[t].start(); // inicia a thread
        }

        // 3) Esperar todas as threads terminarem
        for (Thread w : workers) w.join();

        // 4) Gravar saída em ordem original
        try (BufferedWriter bw = Files.newBufferedWriter(output)) {
            for (int i = 0; i < N; i++) {
                if (isPrime[i]) {
                    bw.write(Long.toString(numbers.get(i)));
                    bw.newLine();
                }
            }
        }

        long end = System.nanoTime();
        return (end - start) / 1_000_000; // tempo em milissegundos
    }
}
