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
import utils.TopologicalSort;

/* Sort solutions based on the partial order of implication
   Uses a topological sort algorithm to sort the specifications
   such that if spec A implies spec B, then A appears before B in the sorted list
*/

public class SortSolutions {

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
        int limit = -1;
        for (String arg : args) {
            if (arg.startsWith("-d=")) {
                directoryName = arg.replace("-d=", "");
            } else if (arg.startsWith("-limit=")) {
                limit = Integer.parseInt(arg.replace("-limit=", ""));
            }
        }
        if (directoryName.isEmpty()) {
            System.out.println("directory name is missing.");
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
        System.out.println("Found " + specifications_filenames.size() + " specifications, converting to TLSF...");
        List<Tlsf> specifications = parseTlsfFiles(specifications_filenames);
        System.out.println("Starting topological sort based on implication...");
        TopologicalSort topoSort = new TopologicalSort(specifications.size());
        List<Integer> maximalElements = topoSort.getMaximalElements(specifications);
        for (int i = 0; i < maximalElements.size(); i++) {
            System.out.println("Maximal spec " + (i + 1) + ": " +
                    new File(specifications_filenames.get(maximalElements.get(i))).getName());
        }
    }
}
