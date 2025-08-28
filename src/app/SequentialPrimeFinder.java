package app;

import java.io.*;
import java.nio.file.*;

public class SequentialPrimeFinder {

    public static long run(Path input, Path output) throws IOException {
        long start = System.nanoTime();

        try (BufferedReader br = Files.newBufferedReader(input);
             BufferedWriter bw = Files.newBufferedWriter(output)) {

            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                long val = Long.parseLong(line);
                if (PrimeUtils.isPrime(val)) {
                    bw.write(Long.toString(val));
                    bw.newLine();
                }
            }
        }

        long end = System.nanoTime();
        return (end - start) / 1_000_000; // ms
    }
}
