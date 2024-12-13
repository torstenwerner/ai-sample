import java.util.Random;
import java.util.Arrays;

public class SP500MonteCarlo {

    public static void main(String[] args) {
        double mu = 0.08;    // Erwartete jährliche Rendite (8%)
        double sigma = 0.18; // Jährliche Standardabweichung (18%)
        int years = 30; 
        int repetitions = 10_000;

        double[] endValues = new double[repetitions];

        Random random = new Random();
        // random.setSeed(12345L);

        for (int i = 0; i < repetitions; i++) {
            double value = 1;
            for (int year = 0; year < years; year++) {
                double returnRate = mu + sigma * random.nextGaussian();
                value *= (1.0 + returnRate);
            }
            endValues[i] = value;
        }

        Arrays.sort(endValues);

        System.out.printf(" 1%%: %10.4f%n", endValues[repetitions / 100]);
        System.out.printf("10%%: %10.4f%n", endValues[repetitions / 10]);
        System.out.printf("50%%: %10.4f%n", endValues[repetitions / 2]);
        System.out.printf("90%%: %10.4f%n", endValues[repetitions * 9 / 10]);
        System.out.printf("99%%: %10.4f%n", endValues[repetitions * 99 / 100]);
    }
}
