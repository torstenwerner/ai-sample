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

        double median = endValues[repetitions / 2];
        double lowQuartile = endValues[repetitions / 4];
        double highQuartile = endValues[3 * repetitions / 4];

        System.out.println("median: " + median);
        System.out.println("low quartile (25%): " + lowQuartile);
        System.out.println("high quartile (75%): " + highQuartile);

        double min = endValues[0];
        double max = endValues[endValues.length - 1];

        System.out.println("min: " + min);
        System.out.println("max: " + max);
    }
}
