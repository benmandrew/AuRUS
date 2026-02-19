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

public class GenuineSolutionsMinimal {

    // Logically equivalent to a genuine solution
    public static Set<Integer> genuineSolutionsFound = new HashSet<>();
    // Logically weaker than a genuine solution
    public static Set<Integer> moreGeneralSolutions = new HashSet<>();
    // Logically stronger than a genuine solution
    public static Set<Integer> lessGeneralSolutions = new HashSet<>();
    // Logically equivalent to the original solution
    public static Set<Integer> equalToOriginalSolutions = new HashSet<>();
    // Logically weaker than the original solution
    public static Set<Integer> moreGeneralThanOriginalSolutions = new HashSet<>();
    // Logically stronger than the original solution
    public static Set<Integer> lessGeneralThanOriginalSolutions = new HashSet<>();

    public static void main(String[] args) throws IOException, InterruptedException {
        List<Tlsf> genuineSolutions = new LinkedList<>();
        List<Tlsf> solutions = new LinkedList<>();
        String directoryName;
        for (String arg : args) {
            if (arg.startsWith("-ref=")) {
                String ref_name = arg.replace("-ref=", "");
                Tlsf ref_sol = TlsfUtils.toBasicTLSF(new File(ref_name));
                genuineSolutions.add(ref_sol);
            } else {
                directoryName = arg;
                solutions.addAll(loadSolutionsFromMaximalSpecs(directoryName));
            }
        }
        calculateGenuineStatistics(genuineSolutions, solutions);
        System.out.println("{\"n_total_solutions\":" + solutions.size() + ",");
        System.out.println("\"n_genuine_solutions\":" + genuineSolutionsFound.size() + ",");
        System.out.println("\"n_weaker_solutions\":" + moreGeneralSolutions.size() + ",");
        System.out.println("\"n_stronger_solutions\":" + lessGeneralSolutions.size() + "}");
    }

    private static List<Tlsf> loadSolutionsFromMaximalSpecs(String directoryName) throws IOException, InterruptedException {
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
        List<Tlsf> solutions = new LinkedList<>();
        for (String filename : solution_filenames) {
            Tlsf tlsf = TlsfUtils.toBasicTLSF(new File(filename));
            solutions.add(tlsf);
        }
        return solutions;
    }

    public static void calculateGenuineStatistics(List<Tlsf> genuineSolutions, List<Tlsf> solutions) throws IOException, InterruptedException {
        SolverSyntaxOperatorReplacer visitor = new SolverSyntaxOperatorReplacer();

        if (genuineSolutions.isEmpty() || solutions.isEmpty())
            return;
        //comparison with genuine solutions
        for (int i = 0; i < solutions.size(); i++) {
            Tlsf solution = solutions.get(i);
            // System.out.print(".");
            if (genuineSolutions.contains(solution)) {
                genuineSolutionsFound.add(i);
            } else {
                for (Tlsf genuine : genuineSolutions) {
                    boolean isMoreGeneral = false;
                    boolean isLessGeneral = false;

                    Formula as_solution = solution.assume();
                    Formula g_solution = Conjunction.of(solution.guarantee());
                    Formula as_genuine = genuine.assume();
                    Formula g_genuine = Conjunction.of(genuine.guarantee());

                    //check isMoreGeneral?
                    //check as_solution => as_genuine = UNSAT(as_solution & !as_genuine)
                    LTLSolver.SolverResult sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(as_solution, as_genuine.not()).accept(visitor)));
                    if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
                        //check g_genuine => g_solution = UNSAT(g_genuine & !g_solution)
                        sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(g_genuine, g_solution.not()).accept(visitor)));
                        if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
                            isMoreGeneral = true;
                        }
                    }

                    //check isLessGeneral?
                    //check as_genuine => as_solution = UNSAT(as_genuine & !as_solution)
                    sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(as_genuine, as_solution.not()).accept(visitor)));
                    if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
                        //check g_solution => g_genuine = UNSAT(g_solution & !g_genuine)
                        sat = LTLSolver.isSAT(SolverUtils.toSolverSyntax(Conjunction.of(g_solution, g_genuine.not()).accept(visitor)));
                        if (!sat.inconclusive() && sat == LTLSolver.SolverResult.UNSAT) {
                            isLessGeneral = true;
                        }
                    }
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
