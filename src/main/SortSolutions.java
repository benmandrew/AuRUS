package main;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import owl.ltl.tlsf.Tlsf;
import utils.TlsfUtils;
import utils.MaximalSolutions;

public class SortSolutions {
    private static List<String> filterDuplicateSpecs(List<String> specifications_filenames) {
        Set<String> uniqueSpecs = new HashSet<>();
        List<String> filteredFilenames = new LinkedList<>();
        int n_duplicates = 0;
        for (String filename : specifications_filenames) {
            try {
                String specString = Files.readString(Paths.get(filename));
                if (!uniqueSpecs.contains(specString)) {
                    uniqueSpecs.add(specString);
                    filteredFilenames.add(filename);
                } else {
                    n_duplicates++;
                }
            } catch (IOException e) {
                System.err.println("Error reading file: " + filename);
            }
        }
        System.out.println("Removed " + n_duplicates + "/" + specifications_filenames.size() + " duplicate specifications.");
        return filteredFilenames;
    }

    private static List<Tlsf> parseTlsfFiles(List<String> specifications_filenames) throws IOException, InterruptedException {
        List<Tlsf> specifications = new LinkedList<>();
        for (String filename : specifications_filenames) {
            Tlsf spec = TlsfUtils.toBasicTLSF(new File(filename));
            specifications.add(spec);
        }
        return specifications;
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        String directoryName = "";
        String outputFilename = "";
        int limit = -1;
        for (String arg : args) {
            if (arg.startsWith("-d=")) {
                directoryName = arg.replace("-d=", "");
            } else if (arg.startsWith("-limit=")) {
                limit = Integer.parseInt(arg.replace("-limit=", ""));
            } else if (arg.startsWith("-out=")) {
                outputFilename = arg.replace("-out=", "");
            }
        }
        if (directoryName.isEmpty()) {
            System.out.println("directory name is missing.");
            System.exit(0);
        }
        if (outputFilename.isEmpty()) {
            System.out.println("output file name is missing.");
            System.exit(0);
        }
        Path dirPath = Paths.get(directoryName);
        Stream<Path> walk = Files.walk(dirPath);
        List<String> specifications_filenames = walk.map(Path::toString)
                .filter(f -> f.endsWith(".tlsf") && !f.endsWith("_basic.tlsf")).collect(Collectors.toList());
        walk.close();
        if (limit > 0 && limit < specifications_filenames.size()) {
            specifications_filenames = specifications_filenames.subList(0, limit);
            System.out.println("Limited to first " + limit + " specifications");
        }
        specifications_filenames = filterDuplicateSpecs(specifications_filenames);
        System.out.println("Parsing " + specifications_filenames.size() + " TLSF specifications...");
        List<Tlsf> specifications = parseTlsfFiles(specifications_filenames);
        System.out.println("Finding the maximal solutions...");
        List<Integer> maximalElements = MaximalSolutions.getMaximalElements(specifications, Optional.empty());
        List<String> maximalSpecs = new ArrayList<>(maximalElements.size());
        for (int i = 0; i < maximalElements.size(); i++) {
            String path = Paths.get(specifications_filenames.get(maximalElements.get(i))).toAbsolutePath().toString();
            maximalSpecs.add(path);
        }
        Path outputPath = Paths.get(outputFilename);
        if (outputPath.getParent() != null) {
            Files.createDirectories(outputPath.getParent());
        }
        Files.write(outputPath, maximalSpecs);
        System.out.println("Wrote " + maximalSpecs.size() + " maximal specifications to " + outputPath.toAbsolutePath());
        System.out.println("Elapsed: " + MaximalSolutions.getElapsedDuration());
    }
}
