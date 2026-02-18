package solvers;

import main.Settings;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class LTLSolver {
    public static AtomicInteger numOfTimeout = new AtomicInteger(0);
    public static AtomicInteger numOfError = new AtomicInteger(0);
    public static AtomicInteger numOfCalls = new AtomicInteger(0);
    public static AtomicInteger numOfOom = new AtomicInteger(0);

    private static final int MAX_OOM_RETRIES = 2;
    private static final long OOM_RETRY_BACKOFF_MILLIS = 1000;
    private static final ConcurrentHashMap<String, SolverResult> cache = new ConcurrentHashMap<>();

    private static File createFormulaFile(String formula) throws IOException {
        File tempFile = File.createTempFile("ltl_formula_", ".ltl");
        try (FileWriter writer = new FileWriter(tempFile)) {
            writer.write(formula);
        }
        return tempFile;
    }

    private static ProcessBuilder buildProcessBuilder(File formulaFile) {
        String shellCmd = "ltl2tgba -F '" + formulaFile.getAbsolutePath() + "' | autfilt --is-empty";
        return new ProcessBuilder("bash", "-c", shellCmd);
    }

    private static SolverResult executeAndCheckResult(Process process, int timeoutSeconds) throws InterruptedException {
        if (!process.waitFor(timeoutSeconds, TimeUnit.SECONDS)) {
            numOfTimeout.incrementAndGet();
            process.destroyForcibly();
            return SolverResult.TIMEOUT;
        }

        try (InputStream out = process.getInputStream();
             BufferedReader reader = new BufferedReader(new InputStreamReader(out))) {
            while (reader.readLine() != null) {
                // drain output to avoid blocking
            }
        } catch (IOException e) {
            numOfError.incrementAndGet();
            return SolverResult.ERROR;
        }

        boolean hasErrorOutput = false;
        boolean hasOomOutput = false;
        try (InputStream err = process.getErrorStream();
             BufferedReader errReader = new BufferedReader(new InputStreamReader(err))) {
            String line;
            while ((line = errReader.readLine()) != null) {
                hasErrorOutput = true;
                if (isOomErrorLine(line)) {
                    hasOomOutput = true;
                }
                System.out.println("ERR: " + line);
            }
        } catch (IOException e) {
            numOfError.incrementAndGet();
            return SolverResult.ERROR;
        }

        int exitCode = process.exitValue();
        if (hasOomOutput || isOomExitCode(exitCode)) {
            numOfOom.incrementAndGet();
            return SolverResult.OOM;
        }

        if (hasErrorOutput) {
            numOfError.incrementAndGet();
            return SolverResult.ERROR;
        }

        return exitCode == 0 ? SolverResult.UNSAT : SolverResult.SAT;
    }

    public static SolverResult isSAT(String formula) throws IOException, InterruptedException {
        if (formula == null) {
            numOfError.incrementAndGet();
            return SolverResult.ERROR;
        }

        // Check cache first
        SolverResult cachedResult = cache.get(formula);
        if (cachedResult != null) {
            return cachedResult;
        }

        int attempt = 0;
        while (true) {
            numOfCalls.incrementAndGet();
            attempt++;
            File tempFile = null;
            Process process = null;
            try {
                tempFile = createFormulaFile(formula);
                process = buildProcessBuilder(tempFile).start();
                SolverResult result = executeAndCheckResult(process, Settings.SAT_TIMEOUT);
                if (result == SolverResult.OOM && attempt <= MAX_OOM_RETRIES) {
                    Thread.sleep(OOM_RETRY_BACKOFF_MILLIS * attempt);
                    continue;
                }
                // Cache only conclusive results (SAT/UNSAT)
                if (!result.inconclusive()) {
                    cache.put(formula, result);
                }
                return result;
            } catch (IOException e) {
                numOfError.incrementAndGet();
                throw e;
            } finally {
                if (process != null) {
                    process.destroy();
                    process.destroyForcibly();
                }
                if (tempFile != null && tempFile.exists()) {
                    tempFile.delete();
                }
            }
        }
    }

    private static boolean isOomExitCode(int exitCode) {
        return exitCode == 137;
    }

    private static boolean isOomErrorLine(String line) {
        if (line == null) {
            return false;
        }
        String lower = line.toLowerCase();
        return lower.contains("out of memory") || lower.contains("oom") || lower.contains("killed");
    }

    public enum SolverResult {
        SAT,
        UNSAT,
        TIMEOUT,
        ERROR,
        OOM;

        public boolean inconclusive() {
            return this == TIMEOUT || this == ERROR || this == OOM;
        }
    }
}
