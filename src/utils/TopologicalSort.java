package utils;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.CompletionService;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorCompletionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import owl.ltl.Formula;
import owl.ltl.tlsf.Tlsf;
import owl.ltl.visitors.SolverSyntaxOperatorReplacer;
import solvers.LTLSolver;
import java.util.concurrent.atomic.AtomicBoolean;

public class TopologicalSort {
    private int vertices;
    private HashMap<Integer, HashSet<Integer>> adj;
    private Map<Integer, Integer> newToOldIndex;
    private final ReentrantReadWriteLock graphLock = new ReentrantReadWriteLock();
    private long startTimeMillis;

    public TopologicalSort(int v) {
        vertices = v;
        adj = new HashMap<>();
        for (int i = 0; i < v; ++i)
            adj.put(i, new HashSet<>());
    }

    private void addEdge(int u, int v) {
        graphLock.writeLock().lock();
        try {
            adj.get(u).add(v);
        } finally {
            graphLock.writeLock().unlock();
        }
    }

    void dfs(int v, boolean[] visited, Stack<Integer> stack) {
        visited[v] = true;
        HashSet<Integer> neighbors = adj.get(v);
        if (neighbors != null) {
            for (int neighbor : neighbors) {
                if (!visited[neighbor])
                    dfs(neighbor, visited, stack);
            }
        }
        stack.push(v);
    }

    private static boolean implies(String f1, String f2) throws IOException, InterruptedException {
        String negImplication = f1 + "& !(" + f2 + ")";
        LTLSolver.SolverResult res = LTLSolver.isSAT(negImplication);
        return res.equals(LTLSolver.SolverResult.UNSAT);
    }

    private boolean hasPath(int from, int to) {
        graphLock.readLock().lock();
        try {
            if (from == to) return true;
            HashSet<Integer> neighbors = adj.get(from);
            if (neighbors == null || neighbors.isEmpty()) return false;
            if (neighbors.contains(to)) return true;
            // BFS to check for path
            Queue<Integer> queue = new LinkedList<>();
            Set<Integer> visited = new HashSet<>();
            queue.add(from);
            visited.add(from);
            while (!queue.isEmpty()) {
                int current = queue.poll();
                HashSet<Integer> currentNeighbors = adj.get(current);
                if (currentNeighbors != null) {
                    for (int neighbor : currentNeighbors) {
                        if (neighbor == to) return true;
                        if (!visited.contains(neighbor)) {
                            visited.add(neighbor);
                            queue.add(neighbor);
                        }
                    }
                }
            }
            return false;
        } finally {
            graphLock.readLock().unlock();
        }
    }

    private void printProgress(int from, int to, int performed, int skipped, int total) {
        int done = performed + skipped;
        synchronized (System.out) {
            long elapsed = System.currentTimeMillis() - startTimeMillis;
            String timeEstimate = "";
            if (done > 0) {
                long estimatedTotal = (elapsed * total) / done;
                long remaining = estimatedTotal - elapsed;
                timeEstimate = String.format(", ETA: %s", formatDuration(remaining));
            }
            System.out.print("[performed: " + performed + "/" + total + ", skipped: " + skipped + ", done: " + done + timeEstimate + "] \r");
            if (done == total) {
                System.out.println();
            }
        }
    }

    private void addSpecs(List<Tlsf> specs) throws IOException, InterruptedException {
        List<String> formulae = new ArrayList<>();
        SolverSyntaxOperatorReplacer visitor = new SolverSyntaxOperatorReplacer();
        for (Tlsf spec : specs) {
            Formula f = spec.toFormula().formula();
            formulae.add(SolverUtils.toSolverSyntax(f.accept(visitor)));
        }
        int totalComparisons = specs.size() * (specs.size() - 1);
        AtomicInteger skippedComparisons = new AtomicInteger(0);
        AtomicInteger performedComparisons = new AtomicInteger(0);
        startTimeMillis = System.currentTimeMillis();
        int parallelism = Math.max(2, Runtime.getRuntime().availableProcessors());
        System.out.println("Using parallelism: " + parallelism);
        ExecutorService executor = Executors.newFixedThreadPool(parallelism - 2);
        CompletionService<Void> completionService = new ExecutorCompletionService<>(executor);
        int submittedTasks = 0;
        for (int i = 0; i < specs.size(); i++) {
            for (int j = 0; j < specs.size(); j++) {
                if (i == j) {
                    continue;
                }
                final int from = i;
                final int to = j;
                completionService.submit(() -> {
                    // re-check reachability under lock to preserve transitivity pruning across threads
                    if (hasPath(from, to)) {
                        printProgress(from, to, performedComparisons.get(), skippedComparisons.incrementAndGet(), totalComparisons);
                        return null;
                    }
                    if (implies(formulae.get(from), formulae.get(to))) {
                        addEdge(from, to);
                    }
                    printProgress(from, to, performedComparisons.incrementAndGet(), skippedComparisons.get(), totalComparisons);
                    return null;
                });
                submittedTasks++;
            }
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
        int performed = performedComparisons.get();
        int skipped = skippedComparisons.get();
        double reductionPct = (totalComparisons == 0) ? 0.0 : (100.0 * skipped / (double) totalComparisons);
        System.out.println("Total comparisons: performed=" + performed +
                 ", skipped=" + skipped +
                 ", reduction=" + String.format("%.1f", reductionPct) + "%");
    }

    private Map<Integer, Integer> removeEquivalentSpecs() {
        Map<Integer, Integer> oldToNewIndex = new HashMap<>();
        Set<Integer> toRemove = new HashSet<>();
        // Find equivalent spec pairs
        for (int i = 0; i < vertices; i++) {
            for (int j = i + 1; j < vertices; j++) {
                if (adj.containsKey(i) && adj.containsKey(j) &&
                    adj.get(i).contains(j) && adj.get(j).contains(i)) {
                    toRemove.add(j);
                }
            }
        }
        // Create mapping from old indices to new indices
        int newIndex = 0;
        for (int i = 0; i < vertices; i++) {
            if (!toRemove.contains(i)) {
                oldToNewIndex.put(i, newIndex);
                newIndex++;
            }
        }
        // Rebuild adjacency list with new indices
        HashMap<Integer, HashSet<Integer>> newAdj = new HashMap<>();
        // First, initialize all vertices with empty sets
        for (int i = 0; i < newIndex; i++) {
            newAdj.put(i, new HashSet<>());
        }
        // Then populate with edges
        for (int oldI : oldToNewIndex.keySet()) {
            int newI = oldToNewIndex.get(oldI);
            for (int oldNeighbor : adj.get(oldI)) {
                if (oldToNewIndex.containsKey(oldNeighbor)) {
                    newAdj.get(newI).add(oldToNewIndex.get(oldNeighbor));
                }
            }
        }
        adj = newAdj;
        vertices = newIndex;
        // Create reverse mapping (new to old)
        newToOldIndex = new HashMap<>();
        for (Map.Entry<Integer, Integer> entry : oldToNewIndex.entrySet()) {
            newToOldIndex.put(entry.getValue(), entry.getKey());
        }
        return oldToNewIndex;
    }

    public HashMap<Integer, HashSet<Integer>> getAdjacencyList() {
        return adj;
    }

    public List<Integer> sort(List<Tlsf> specs) throws IOException, InterruptedException {
        addSpecs(specs);
        removeEquivalentSpecs();
        Stack<Integer> stack = new Stack<>();
        boolean[] visited = new boolean[vertices];
        for (int i = 0; i < vertices; i++) {
            if (!visited[i])
                dfs(i, visited, stack);
        }
        List<Integer> sortedIndices = new ArrayList<>();
        while (!stack.isEmpty()) {
            int newIndex = stack.pop();
            // Map back to original index if deduplication occurred
            int originalIndex = (newToOldIndex != null) ? newToOldIndex.get(newIndex) : newIndex;
            sortedIndices.add(originalIndex);
        }
        return sortedIndices;
    }

    private String formatDuration(long millis) {
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

    public String getElapsedDuration() {
        long elapsed = System.currentTimeMillis() - startTimeMillis;
        return formatDuration(elapsed);
    }

    private void printMaxElementsProgress(int from, int to, int performed, int skipped, int total) {
        int done = performed + skipped;
        synchronized (System.out) {
            long elapsed = System.currentTimeMillis() - startTimeMillis;
            String timeEstimate = "";
            if (done > 0) {
                long estimatedTotal = (elapsed * total) / done;
                long remaining = estimatedTotal - elapsed;
                timeEstimate = String.format(", ETA: %s", formatDuration(remaining));
            }
            System.out.print("[performed: " + performed + ", skipped: " + skipped + ", done: " + done + "/" + total + timeEstimate + "] \r");
            if (done == total) {
                System.out.println();
            }
        }
    }

    public List<Integer> getMaximalElements(List<Tlsf> specs) throws IOException, InterruptedException {
        List<String> formulae = new ArrayList<>();
        SolverSyntaxOperatorReplacer visitor = new SolverSyntaxOperatorReplacer();
        for (Tlsf spec : specs) {
            Formula f = spec.toFormula().formula();
            formulae.add(SolverUtils.toSolverSyntax(f.accept(visitor)));
        }
        int totalComparisons = specs.size() * (specs.size() - 1);
        AtomicInteger skippedComparisons = new AtomicInteger(0);
        AtomicInteger performedComparisons = new AtomicInteger(0);
        AtomicBoolean[] subsumed = new AtomicBoolean[specs.size()];
        for (int i = 0; i < specs.size(); i++) {
            subsumed[i] = new AtomicBoolean(false);
        }
        startTimeMillis = System.currentTimeMillis();
        int parallelism = Math.max(2, Runtime.getRuntime().availableProcessors());
        System.out.println("Using parallelism: " + parallelism);
        ExecutorService executor = Executors.newFixedThreadPool(parallelism - 2);
        CompletionService<Void> completionService = new ExecutorCompletionService<>(executor);
        int submittedTasks = 0;
        for (int i = 0; i < specs.size(); i++) {
            for (int j = 0; j < specs.size(); j++) {
                if (i == j) {
                    continue;
                }
                final int from = i;
                final int to = j;
                completionService.submit(() -> {
                    // Skip if target is already subsumed
                    if (subsumed[to].get()) {
                        skippedComparisons.incrementAndGet();
                        printMaxElementsProgress(from, to, performedComparisons.get(), skippedComparisons.get(), totalComparisons);
                        return null;
                    }
                    if (implies(formulae.get(from), formulae.get(to))) {
                        subsumed[to].set(true);
                    }
                    performedComparisons.incrementAndGet();
                    printMaxElementsProgress(from, to, performedComparisons.get(), skippedComparisons.get(), totalComparisons);
                    return null;
                });
                submittedTasks++;
            }
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
        int performed = performedComparisons.get();
        int skipped = skippedComparisons.get();
        double reductionPct = (totalComparisons == 0) ? 0.0 : (100.0 * skipped / (double) totalComparisons);
        System.out.println("Total comparisons: performed=" + performed +
                 ", skipped=" + skipped +
                 ", reduction=" + String.format("%.1f", reductionPct) + "%");
        List<Integer> maximalIndices = new ArrayList<>();
        for (int i = 0; i < specs.size(); i++) {
            if (!subsumed[i].get()) {
                maximalIndices.add(i);
            }
        }
        System.out.println("Maximal elements: " + maximalIndices.size() + " out of " + specs.size() +
                         " (removed: " + (specs.size() - maximalIndices.size()) + ")");
        return maximalIndices;
    }
}
