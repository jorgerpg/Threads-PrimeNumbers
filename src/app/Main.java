package app;

import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.time.format.DateTimeFormatter;

/**
 * Classe Main:
 * Programa principal para rodar a verificação de números primos de forma sequencial ou paralela.
 *
 * Uso:
 *   java -cp target/classes app.Main seq data/Entrada01.txt out/primes_seq.txt
 *   java -cp target/classes app.Main par data/Entrada01.txt out/primes_t5.txt 5
 *   java -cp target/classes app.Main par data/Entrada01.txt out/primes_t10.txt 10
 *
 * Também registra os resultados em "out/results.csv" no formato:
 *   version,threads,ms,timestamp
 */
public class Main {

    /**
     * Garante que o diretório pai do arquivo existe, criando se necessário.
     */
    private static Path ensureParent(Path p) throws IOException {
        if (p.getParent() != null) Files.createDirectories(p.getParent());
        return p;
    }

    /**
     * Adiciona uma linha no CSV de resultados, criando o arquivo se não existir.
     *
     * @param csv Arquivo CSV
     * @param version "seq" ou "par"
     * @param threads Número de threads usadas
     * @param ms Tempo de execução em milissegundos
     */
    private static void appendCSV(Path csv, String version, int threads, long ms) throws IOException {
        boolean exists = Files.exists(csv);

        try (BufferedWriter bw = Files.newBufferedWriter(
                ensureParent(csv),
                java.nio.charset.StandardCharsets.UTF_8,
                exists ? java.nio.file.StandardOpenOption.APPEND : java.nio.file.StandardOpenOption.CREATE
        )) {
            // Se o arquivo não existia, escreve o cabeçalho
            if (!exists) bw.write("version,threads,ms,timestamp\n");

            // Timestamp no formato ISO com fuso horário
            String ts = ZonedDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);

            // Escreve os dados da execução
            bw.write(String.format("%s,%d,%d,%s%n", version, threads, ms, ts));
        }
    }

    /**
     * Método principal: processa argumentos e executa o programa.
     *
     * Args esperados:
     *   0: modo ("seq" ou "par")
     *   1: arquivo de entrada
     *   2: arquivo de saída
     *   3: número de threads (opcional, padrão 5)
     */
    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("Uso: java app.Main <seq|par> <input> <output> [threads]");
            System.exit(2);
        }

        String mode = args[0];           // seq ou par
        Path in = Paths.get(args[1]);    // arquivo de entrada
        Path out = Paths.get(args[2]);   // arquivo de saída
        Path csv = Paths.get("out", "results.csv"); // CSV de resultados

        long ms; // tempo de execução

        switch (mode) {
            case "seq":
                // Executa versão sequencial
                ms = SequentialPrimeFinder.run(in, ensureParent(out));
                // Grava resultado no CSV
                appendCSV(csv, "seq", 1, ms);
                System.out.printf("Sequencial: %d ms%n", ms);
                break;

            case "par":
                // Número de threads (padrão 5)
                int threads = (args.length >= 4) ? Integer.parseInt(args[3]) : 5;
                // Executa versão paralela
                ms = ParallelPrimeFinder.run(in, ensureParent(out), threads);
                // Grava resultado no CSV
                appendCSV(csv, "par", threads, ms);
                System.out.printf("Paralelo (%d threads): %d ms%n", threads, ms);
                break;

            default:
                throw new IllegalArgumentException("modo inválido: " + mode);
        }
    }
}
