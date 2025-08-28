package app;

public final class PrimeUtils {
    private PrimeUtils() {}

    public static boolean isPrime(long n) {
        if (n < 2) return false;
        if ((n & 1) == 0) return n == 2;
        if (n % 3 == 0) return n == 3;

        // Verificações rápidas com pequenos primos
        int[] small = {5,7,11,13,17,19,23,29,31,37};
        for (int p : small) {
            if (n == p) return true;
            if (n % p == 0) return n == p;
        }

        // Teste 6k ± 1 até sqrt(n)
        long limit = (long)Math.sqrt(n);
        for (long i = 5; i <= limit; i += 6) {
            if (n % i == 0 || n % (i + 2) == 0) return false;
        }
        return true;
    }
}
