package solvers;

import main.Settings;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class LTLSolver {
    public static AtomicInteger numOfTimeout = new AtomicInteger(0);
    public static AtomicInteger numOfError = new AtomicInteger(0);
    public static AtomicInteger numOfCalls = new AtomicInteger(0);

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
        try (InputStream err = process.getErrorStream();
             BufferedReader errReader = new BufferedReader(new InputStreamReader(err))) {
            String line;
            while ((line = errReader.readLine()) != null) {
                hasErrorOutput = true;
                System.out.println("ERR: " + line);
            }
        } catch (IOException e) {
            numOfError.incrementAndGet();
            return SolverResult.ERROR;
        }

        if (hasErrorOutput) {
            numOfError.incrementAndGet();
            return SolverResult.ERROR;
        }

        int exitCode = process.exitValue();
        return exitCode == 0 ? SolverResult.UNSAT : SolverResult.SAT;
    }

    public static SolverResult isSAT(String formula) throws IOException, InterruptedException {
        numOfCalls.incrementAndGet();

        if (formula == null) {
            numOfError.incrementAndGet();
            return SolverResult.ERROR;
        }

        File tempFile = null;
        Process process = null;
        try {
            tempFile = createFormulaFile(formula);
            process = buildProcessBuilder(tempFile).start();
            return executeAndCheckResult(process, Settings.SAT_TIMEOUT);
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

    public enum SolverResult {
        SAT,
        UNSAT,
        TIMEOUT,
        ERROR;

        public boolean inconclusive() {
            return this == TIMEOUT || this == ERROR;
        }
    }
}
