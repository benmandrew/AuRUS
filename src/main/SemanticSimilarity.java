package main;

import owl.ltl.tlsf.Tlsf;
import utils.TlsfUtils;
import geneticalgorithm.AutomataBasedModelCountingSpecificationFitness;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.LinkedList;
import java.util.List;

public class SemanticSimilarity {

    private static List<Path> getSolutionFiles(Path solutionsDir) throws IOException, InterruptedException {
        String maximalSpecsPath = solutionsDir.toAbsolutePath() + "/maximal-specs.txt";
        Path path = Paths.get(maximalSpecsPath);
        if (!Files.exists(path)) {
            throw new IOException("maximal-specs.txt not found at: " + maximalSpecsPath);
        }
        List<String> lines = Files.readAllLines(path);
        List<String> solution_filenames = new LinkedList<>();
        for (String line : lines) {
            String filename = line.substring(line.lastIndexOf('/') + 1);
            String relativePath = solutionsDir.toAbsolutePath() + "/" + filename;
            solution_filenames.add(relativePath);
        }
        List<Path> solutions = new LinkedList<>();
        for (String filename : solution_filenames) {
            solutions.add(Paths.get(filename));
        }
        return solutions;
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        Settings.MC_BOUND = 10000;
        if (args.length != 2) {
            System.err.println("Usage: java main.SemanticSimilarity <original-tlsf-file> <refined-directory>");
            System.exit(1);
        }
        String originalFilePath = args[0];
        String refinedDirectoryPath = args[1];
        Path originalFile = Paths.get(originalFilePath);
        if (!Files.exists(originalFile) || !Files.isRegularFile(originalFile)) {
            System.err.println("Error: Original file " + originalFilePath + " does not exist or is not a file");
            System.exit(1);
        }
        Path refinedDirectory = Paths.get(refinedDirectoryPath);
        if (!Files.exists(refinedDirectory) || !Files.isDirectory(refinedDirectory)) {
            System.err.println("Error: " + refinedDirectoryPath + " is not a valid directory");
            System.exit(1);
        }
        Tlsf original;
        try {
            original = TlsfUtils.toBasicTLSF(originalFile.toFile());
        } catch (Exception e) {
            System.err.println("Error: Failed to parse original file " + originalFilePath + ": " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
            return;
        }
        long startTime_ = System.currentTimeMillis();
        AutomataBasedModelCountingSpecificationFitness fitnessCalculator = new AutomataBasedModelCountingSpecificationFitness(original);
        List<Path> tlsfFiles = getSolutionFiles(refinedDirectory);
        if (tlsfFiles.isEmpty()) {
            System.err.println("No TLSF files found in directory: " + refinedDirectoryPath);
            System.exit(0);
        }
        System.err.println("Total processing time: " + (System.currentTimeMillis() - startTime_) / 1000.0 + " seconds");
        startTime_ = System.currentTimeMillis();
        for (Path tlsfFile : tlsfFiles) {
            try {
                long startTime = System.currentTimeMillis();
                Tlsf refined = TlsfUtils.toBasicTLSF(tlsfFile.toFile());
                double semanticSimilarity = fitnessCalculator.compute_semantic_weakening(original, refined);
                double elapsedTime = (System.currentTimeMillis() - startTime) / 1000.0;
                System.out.println(tlsfFile.getFileName() + "," + semanticSimilarity + "," + elapsedTime);
            } catch (Exception e) {
                System.err.println("Error processing " + tlsfFile.getFileName() + ": " + e.getMessage());
            }
        }
        System.err.println("Total processing time: " + (System.currentTimeMillis() - startTime_) / 1000.0 + " seconds");
        System.out.flush();
        System.err.flush();
        System.exit(0);
    }
}
