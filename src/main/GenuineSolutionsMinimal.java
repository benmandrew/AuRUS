package main;

import geneticalgorithm.AutomataBasedModelCountingSpecificationFitness;
import geneticalgorithm.SpecificationChromosome;
import owl.ltl.Conjunction;
import owl.ltl.Formula;
import owl.ltl.tlsf.Tlsf;
import owl.ltl.visitors.SolverSyntaxOperatorReplacer;
import solvers.LTLSolver;
import utils.SolverUtils;
import utils.TlsfUtils;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

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
    public static boolean computeFitness = true;

    public static void main(String[] args) throws IOException, InterruptedException {
        List<Tlsf> genuineSolutions = new LinkedList<>();
        List<Tlsf> solutions = new LinkedList<>();
        List<Double> sol_fitness = new LinkedList<>();
        String directoryName;
        List<String> solution_filenames = new LinkedList<>();
        Tlsf original = null;
        for (String arg : args) {
            if (arg.startsWith("-ref=")) {
                String ref_name = arg.replace("-ref=", "");
                Tlsf ref_sol = TlsfUtils.toBasicTLSF(new File(ref_name));
                genuineSolutions.add(ref_sol);
            } else if (arg.startsWith("-o=")) {
                String orig_name = arg.replace("-o=", "");
                original = TlsfUtils.toBasicTLSF(new File(orig_name));
            } else if (arg.startsWith("-noFit")) {
                computeFitness = false;
            } else {
                directoryName = arg;
                Stream<Path> walk = Files.walk(Paths.get(directoryName));
                solution_filenames = walk.map(Path::toString)
                        .filter(f -> f.endsWith(".tlsf") && !f.endsWith("_basic.tlsf")).collect(Collectors.toList());
                for (String filename : solution_filenames) {
                    // System.out.println(filename);
                    Tlsf tlsf = TlsfUtils.toBasicTLSF(new File(filename));
                    solutions.add(tlsf);
                    //read the fitness from file
                    if (!computeFitness) {
                        FileReader f = new FileReader(filename);
                        BufferedReader in = new BufferedReader(f);
                        String aux;
                        double value = 0.0d;
                        while ((aux = in.readLine()) != null) {
                            if ((aux.startsWith("//fitness"))) {
                                value = Double.parseDouble(aux.substring(10));
                            }
                        }
                        sol_fitness.add(value);
                        in.close();
                    }
                }
                walk.close();
            }
        }
        calculateGenuineStatistics(genuineSolutions, solutions);

        if (original != null) {
            if (computeFitness) {
                AutomataBasedModelCountingSpecificationFitness fitness = new AutomataBasedModelCountingSpecificationFitness(original);
                for (Tlsf sol : solutions) {
                    SpecificationChromosome c = new SpecificationChromosome(sol);
                    Double f = fitness.calculate(c);
                    sol_fitness.add(f);
                }
            }
            if (!genuineSolutions.isEmpty()) {
                System.out.println("{\"genuine_solutions\":");
                printJsonList(genuineSolutionsFound, solution_filenames);
                System.out.println(",\"weaker_solutions\":");
                printJsonList(moreGeneralSolutions, solution_filenames);
                System.out.println(",\"stronger_solutions\":");
                printJsonList(lessGeneralSolutions, solution_filenames);
                System.out.println("}");
            }
        }
        System.exit(0);
    }

    private static void printJsonList(Set<Integer> indices, List<String> filenames) {
        List<Integer> list = new LinkedList<>(indices);
        System.out.println("[");
        for (int i = 0; i < list.size(); i++) {
            System.out.print("\"" + filenames.get(list.get(i)).toString() + "\"");
            if (i < list.size() - 1) System.out.println(",");
        }
        System.out.println("]");
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
