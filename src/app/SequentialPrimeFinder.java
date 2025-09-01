package app;

import java.io.*;
import java.nio.file.*;

/**
 * SequentialPrimeFinder:
 * Versão sequencial do verificador de números primos.
 * Lê números de um arquivo, verifica se são primos e grava os primos no arquivo de saída.
 */
public class SequentialPrimeFinder {

    /**
     * run:
     * Executa a verificação sequencialmente.
     *
     * @param input Arquivo de entrada com números
     * @param output Arquivo de saída para números primos
     * @return Tempo de execução em milissegundos
     * @throws IOException Se houver erro de leitura ou escrita
     */
    public static long run(Path input, Path output) throws IOException {
        long start = System.nanoTime(); // início da contagem de tempo

        // try-with-resources: abre arquivo de leitura e escrita
        try (BufferedReader br = Files.newBufferedReader(input);
             BufferedWriter bw = Files.newBufferedWriter(output)) {

            String line;
            // Lê o arquivo linha a linha
            while ((line = br.readLine()) != null) {
                line = line.trim();  // remove espaços em branco
                if (line.isEmpty()) continue; // ignora linhas vazias

                long val = Long.parseLong(line); // converte para número

                // Verifica primalidade usando PrimeUtils
                if (PrimeUtils.isPrime(val)) {
                    // Grava no arquivo de saída
                    bw.write(Long.toString(val));
                    bw.newLine();
                }
            }
        }

        long end = System.nanoTime(); // fim da contagem de tempo
        return (end - start) / 1_000_000; // retorna tempo em milissegundos
    }
}
