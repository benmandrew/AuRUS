package main;

import owl.ltl.Conjunction;
import owl.ltl.Formula;
import owl.ltl.tlsf.Tlsf;
import owl.ltl.visitors.SolverSyntaxOperatorReplacer;
import solvers.LTLSolver;
import utils.SolverUtils;
import utils.TlsfUtils;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;

import org.apache.commons.lang3.tuple.Pair;
import org.apache.commons.lang3.tuple.ImmutablePair;

public class GenuineSolutionsMinimal {

    // Logically equivalent to a genuine solution
    public static Set<Integer> genuineSolutionsFound = new HashSet<>();
    // Logically weaker than a genuine solution
    public static Set<Integer> moreGeneralSolutions = new HashSet<>();
    // Logically stronger than a genuine solution
    public static Set<Integer> lessGeneralSolutions = new HashSet<>();

    public static void main(String[] args) throws IOException, InterruptedException {
        List<Tlsf> genuineSolutions = new LinkedList<>();
        List<String> solution_filenames = new LinkedList<>();
        List<Tlsf> solutions = new LinkedList<>();
        boolean nSolutionsSpecified = false;
        String directoryName = "";
        for (String arg : args) {
            if (arg.startsWith("--ref=")) {
                String ref_name = arg.replace("--ref=", "");
                Tlsf ref_sol = TlsfUtils.toBasicTLSF(new File(ref_name));
                genuineSolutions.add(ref_sol);
            } else if (arg.startsWith("--n-solutions")) {
                nSolutionsSpecified = true;
            } else {
                directoryName = arg;
                solution_filenames.addAll(getSolutionFilenames(directoryName));
                solutions.addAll(loadSolutions(solution_filenames));
            }
        }
        calculateGenuineStatistics(genuineSolutions, solutions);
        if (nSolutionsSpecified) {
            String finalDirectoryName = Paths.get(directoryName).getFileName().toString();
            System.out.println("{\"run\":" + finalDirectoryName + ",");
            System.out.println("\"n_total_solutions\":" + solutions.size() + ",");
            System.out.println("\"n_genuine_solutions\":" + genuineSolutionsFound.size() + ",");
            System.out.println("\"n_weaker_solutions\":" + moreGeneralSolutions.size() + ",");
            System.out.println("\"n_stronger_solutions\":" + lessGeneralSolutions.size() + "}");
        } else {
            System.out.print("{");
            printSetAsJsonArray("genuine_solutions", getFilenamesFromIndices(genuineSolutionsFound, solution_filenames));
            System.out.print(",");
            printSetAsJsonArray("weaker_solutions", getFilenamesFromIndices(moreGeneralSolutions, solution_filenames));
            System.out.print(",");
            printSetAsJsonArray("stronger_solutions", getFilenamesFromIndices(lessGeneralSolutions, solution_filenames));
            System.out.println("}");
        }
    }

    private static List<String> getSolutionFilenames(String directoryName) throws IOException, InterruptedException {
        String maximalSpecsPath = directoryName + "/maximal-specs.txt";
        Path path = Paths.get(maximalSpecsPath);
        if (!Files.exists(path)) {
            throw new IOException("maximal-specs.txt not found at: " + maximalSpecsPath);
        }
        List<String> lines = Files.readAllLines(path);
        List<String> solution_filenames = new LinkedList<>();
        for (String line : lines) {
            String filename = line.substring(line.lastIndexOf('/') + 1);
            String relativePath = directoryName + "/" + filename;
            solution_filenames.add(relativePath);
        }
        return solution_filenames;
    }

    private static List<Tlsf> loadSolutions(List<String> solution_filenames) throws IOException, InterruptedException {
        List<Tlsf> solutions = new LinkedList<>();
        for (String filename : solution_filenames) {
            Tlsf tlsf = TlsfUtils.toBasicTLSF(new File(filename));
            solutions.add(tlsf);
        }
        return solutions;
    }

    private static boolean moreGeneral(Formula as_solution, Formula g_solution, Formula as_genuine, Formula g_genuine, SolverSyntaxOperatorReplacer visitor)  throws IOException, InterruptedException {
        //check isMoreGeneral?
        //check as_solution => as_genuine = UNSAT(as_solution & !as_genuine)
        LTLSolver.SolverResult sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(as_solution, as_genuine.not()).accept(visitor)));
        if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
            //check g_genuine => g_solution = UNSAT(g_genuine & !g_solution)
            sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(g_genuine, g_solution.not()).accept(visitor)));
            if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
                return true;
            }
        }
        return false;
    }

    private static boolean lessGeneral(Formula as_solution, Formula g_solution, Formula as_genuine, Formula g_genuine, SolverSyntaxOperatorReplacer visitor)  throws IOException, InterruptedException {
        //check isLessGeneral?
        //check as_genuine => as_solution = UNSAT(as_genuine & !as_solution)
        LTLSolver.SolverResult sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(as_genuine, as_solution.not()).accept(visitor)));
        if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
            //check g_solution => g_genuine = UNSAT(g_solution & !g_genuine)
            sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(g_solution, g_genuine.not()).accept(visitor)));
            if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
                return true;
            }
        }
        return false;
    }

    private static List<Pair<Formula, Formula>> getGenuineAssumeGuaranteePairs(List<Tlsf> genuineSolutions) {
        List<Pair<Formula, Formula>> pairs = new LinkedList<>();
        for (Tlsf genuine : genuineSolutions) {
            pairs.add(ImmutablePair.of(genuine.assume(), Conjunction.of(genuine.guarantee())));
        }
        return pairs;
    }

    private static Set<String> getFilenamesFromIndices(Set<Integer> indices, List<String> filenames) {
        Set<String> result = new HashSet<>();
        for (Integer index : indices) {
            String fullPath = filenames.get(index);
            String filename = fullPath.substring(fullPath.lastIndexOf('/') + 1);
            result.add(filename);
        }
        return result;
    }

    private static void printSetAsJsonArray(String key, Set<String> set) {
        System.out.print("\"" + key + "\":[" );
        boolean first = true;
        for (String value : set) {
            if (!first) {
                System.out.print(",");
            }
            System.out.print("\"" + value + "\"");
            first = false;
        }
        System.out.print("]");
    }

    public static void calculateGenuineStatistics(List<Tlsf> genuineSolutions, List<Tlsf> solutions) throws IOException, InterruptedException {
        SolverSyntaxOperatorReplacer visitor = new SolverSyntaxOperatorReplacer();
        List<Pair<Formula, Formula>> genuinePairs = getGenuineAssumeGuaranteePairs(genuineSolutions);
        for (int i = 0; i < solutions.size(); i++) {
            Tlsf solution = solutions.get(i);
            if (genuineSolutions.contains(solution)) {
                genuineSolutionsFound.add(i);
            } else {
                Formula as_solution = solution.assume();
                Formula g_solution = Conjunction.of(solution.guarantee());
                for (Pair<Formula, Formula> genuinePair : genuinePairs) {
                    Formula as_genuine = genuinePair.getLeft();
                    Formula g_genuine = genuinePair.getRight();
                    boolean isMoreGeneral = moreGeneral(as_solution, g_solution, as_genuine, g_genuine, visitor);
                    boolean isLessGeneral = lessGeneral(as_solution, g_solution, as_genuine, g_genuine, visitor);
                    if (isMoreGeneral && isLessGeneral && !genuineSolutionsFound.contains(i)) {
                        genuineSolutionsFound.add(i);
                        break;
                    } else if (isMoreGeneral && !moreGeneralSolutions.contains(i)) {
                        moreGeneralSolutions.add(i);
                    } else if (isLessGeneral) {
                        lessGeneralSolutions.add(i);
                    }
                }
            }
        }
        System.out.println();
    }
}
