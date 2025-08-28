package app;

import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.time.format.DateTimeFormatter;

/**
 * Uso:
 *   java -cp target/classes app.Main seq data/Entrada01.txt out/primes_seq.txt
 *   java -cp target/classes app.Main par data/Entrada01.txt out/primes_t5.txt 5
 *   java -cp target/classes app.Main par data/Entrada01.txt out/primes_t10.txt 10
 *
 * Gera (ou acrescenta) resultados em out/results.csv:
 *   version,threads,ms,timestamp
 */
public class Main {

    private static Path ensureParent(Path p) throws IOException {
        if (p.getParent() != null) Files.createDirectories(p.getParent());
        return p;
    }

    private static void appendCSV(Path csv, String version, int threads, long ms) throws IOException {
        boolean exists = Files.exists(csv);
        try (BufferedWriter bw = Files.newBufferedWriter(ensureParent(csv), java.nio.charset.StandardCharsets.UTF_8,
                exists ? java.nio.file.StandardOpenOption.APPEND : java.nio.file.StandardOpenOption.CREATE)) {
            if (!exists) bw.write("version,threads,ms,timestamp\n");
            String ts = ZonedDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
            bw.write(String.format("%s,%d,%d,%s%n", version, threads, ms, ts));
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("Uso: java app.Main <seq|par> <input> <output> [threads]");
            System.exit(2);
        }
        String mode = args[0];
        Path in = Paths.get(args[1]);
        Path out = Paths.get(args[2]);
        Path csv = Paths.get("out", "results.csv");

        long ms;
        switch (mode) {
            case "seq":
                ms = SequentialPrimeFinder.run(in, ensureParent(out));
                appendCSV(csv, "seq", 1, ms);
                System.out.printf("Sequencial: %d ms%n", ms);
                break;
            case "par":
                int threads = (args.length >= 4) ? Integer.parseInt(args[3]) : 5;
                ms = ParallelPrimeFinder.run(in, ensureParent(out), threads);
                appendCSV(csv, "par", threads, ms);
                System.out.printf("Paralelo (%d threads): %d ms%n", threads, ms);
                break;
            default:
                throw new IllegalArgumentException("modo inválido: " + mode);
        }
    }
}
