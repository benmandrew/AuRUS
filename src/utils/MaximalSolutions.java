package utils;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.CompletionService;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorCompletionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

import owl.ltl.Formula;
import owl.ltl.tlsf.Tlsf;
import owl.ltl.visitors.SolverSyntaxOperatorReplacer;
import solvers.LTLSolver;
import java.util.concurrent.atomic.AtomicBoolean;

public class MaximalSolutions {
    private static long startTimeMillis;

    private static boolean implies(String f1, String f2) throws IOException, InterruptedException {
        String negImplication = f1 + "& !(" + f2 + ")";
        LTLSolver.SolverResult res = LTLSolver.isSAT(negImplication);
        return res.equals(LTLSolver.SolverResult.UNSAT);
    }

    private static List<String> getFormulae(List<Tlsf> specs) {
        List<String> formulae = new ArrayList<>();
        SolverSyntaxOperatorReplacer visitor = new SolverSyntaxOperatorReplacer();
        for (Tlsf spec : specs) {
            Formula f = spec.toFormula().formula();
            formulae.add(SolverUtils.toSolverSyntax(f.accept(visitor)));
        }
        return formulae;
    }

    private interface ComparisonTask {
        void compare(int from, int to) throws IOException, InterruptedException;
    }

    private static void runParallelComparisons(int size, List<String> formulae, int totalComparisons,
                                        AtomicInteger skippedComparisons, AtomicInteger performedComparisons,
                                        ComparisonTask task, Optional<Integer> parallelism) throws IOException, InterruptedException {
        // int parallelism = Runtime.getRuntime().availableProcessors();
        // System.out.println("Using parallelism: " + parallelism);
        int actualParallelism = parallelism.orElse(Runtime.getRuntime().availableProcessors());
        ExecutorService executor = Executors.newWorkStealingPool(actualParallelism);
        CompletionService<Void> completionService = new ExecutorCompletionService<>(executor);
        List<int[]> comparisonPairs = new ArrayList<>();
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                if (i != j) {
                    comparisonPairs.add(new int[]{i, j});
                }
            }
        }
        Collections.shuffle(comparisonPairs);
        int submittedTasks = 0;
        for (int[] pair : comparisonPairs) {
            final int from = pair[0];
            final int to = pair[1];
            completionService.submit(() -> {
                try {
                    task.compare(from, to);
                } catch (IOException | InterruptedException e) {
                    throw new RuntimeException(e);
                }
                return null;
            });
            submittedTasks++;
        }
        try {
            for (int k = 0; k < submittedTasks; k++) {
                try {
                    completionService.take().get();
                } catch (ExecutionException e) {
                    Throwable cause = e.getCause();
                    if (cause instanceof IOException) {
                        throw (IOException) cause;
                    }
                    if (cause instanceof InterruptedException) {
                        throw (InterruptedException) cause;
                    }
                    throw new RuntimeException("Implication task failed", cause);
                }
            }
        } finally {
            executor.shutdownNow();
        }
    }

    private static String formatDuration(long millis) {
        if (millis < 0) millis = 0;
        long seconds = millis / 1000;
        long minutes = seconds / 60;
        long hours = minutes / 60;
        if (hours > 0) {
            return String.format("%dh %dm %ds", hours, minutes % 60, seconds % 60);
        } else if (minutes > 0) {
            return String.format("%dm %ds", minutes, seconds % 60);
        } else {
            return String.format("%ds", seconds);
        }
    }

    public static String getElapsedDuration() {
        long elapsed = System.currentTimeMillis() - startTimeMillis;
        return formatDuration(elapsed);
    }

    public static List<Integer> getMaximalElements(List<Tlsf> specs, Optional<Integer> parallelism) throws IOException, InterruptedException {
        List<String> formulae = getFormulae(specs);
        int totalComparisons = specs.size() * (specs.size() - 1);
        AtomicInteger skippedComparisons = new AtomicInteger(0);
        AtomicInteger performedComparisons = new AtomicInteger(0);
        AtomicBoolean[] subsumed = new AtomicBoolean[specs.size()];
        for (int i = 0; i < specs.size(); i++) {
            subsumed[i] = new AtomicBoolean(false);
        }
        startTimeMillis = System.currentTimeMillis();
        runParallelComparisons(specs.size(), formulae, totalComparisons, skippedComparisons, performedComparisons, (from, to) -> {
            if (subsumed[from].get() || subsumed[to].get()) {
                skippedComparisons.incrementAndGet();
                return;
            }
            if (implies(formulae.get(from), formulae.get(to))) {
                subsumed[to].set(true);
            }
            performedComparisons.incrementAndGet();
        }, parallelism);
        // int performed = performedComparisons.get();
        // int skipped = skippedComparisons.get();
        // double reductionPct = (totalComparisons == 0) ? 0.0 : (100.0 * skipped / (double) totalComparisons);
        // System.out.println("Total comparisons: performed=" + performed +
        //          ", skipped=" + skipped +
        //          ", reduction=" + String.format("%.1f", reductionPct) + "%");
        List<Integer> maximalIndices = new ArrayList<>();
        for (int i = 0; i < specs.size(); i++) {
            if (!subsumed[i].get()) {
                maximalIndices.add(i);
            }
        }
        // If all specs were marked subsumed, equivalent specs caused a race where both
        // directions of implication completed before either result was visible. In that
        // case no spec is strictly dominated, so keep all of them.
        if (maximalIndices.isEmpty()) {
            for (int i = 0; i < specs.size(); i++) {
                maximalIndices.add(i);
            }
        }
        // System.out.println("Maximal elements: " + maximalIndices.size() + " out of " + specs.size() +
        //                  " (removed: " + (specs.size() - maximalIndices.size()) + ")");
        return maximalIndices;
    }
}
