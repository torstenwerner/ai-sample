import java.text.DecimalFormat;
import java.util.Random;
import java.util.Arrays;

public class MonteCarloRetirement {

    public static void main(String[] args) {
        double mu = 0.08;    // Erwartete jährliche Rendite (8%) S&P 500
        double sigma = 0.18; // Jährliche Standardabweichung (18%)
        int years = 30; 
        int repetitions = 10_000;
        double startValue = 1000000;
        double startWithdrawal = 40000;
        double inflationRate = 0.03;

        double[] endValues = new double[repetitions];

        Random random = new Random();
        // random.setSeed(12345L);

        for (int i = 0; i < repetitions; i++) {
            double value = startValue;
            double withdrawal = startWithdrawal;
            for (int year = 0; year < years; year++) {
                // withdrawal at the start of the year 
                value -= withdrawal;
                // return at the end of the year
                double returnRate = mu + sigma * random.nextGaussian();
                value *= 1.0 + returnRate;
                // inflation
                withdrawal *= 1.0 + inflationRate;
            }
            endValues[i] = value;
        }

        Arrays.sort(endValues);

        DecimalFormat df = new DecimalFormat("#,###");
        System.out.printf(" 1%%: %10s%n", df.format(endValues[repetitions / 100]));
        System.out.printf("10%%: %10s%n", df.format(endValues[repetitions / 10]));
        System.out.printf("50%%: %10s%n", df.format(endValues[repetitions / 2]));
        System.out.printf("90%%: %10s%n", df.format(endValues[repetitions * 9 / 10]));
        System.out.printf("99%%: %10s%n", df.format(endValues[repetitions * 99 / 100]));
    }
}
