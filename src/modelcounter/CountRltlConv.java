package modelcounter;

import owl.ltl.LabelledFormula;
import utils.SolverUtils;

import java.io.*;
import java.math.BigInteger;
import java.util.List;
import java.util.concurrent.TimeUnit;

public class CountRltlConv {

    public int TIMEOUT = 180;

    public BigInteger countPrefixes(LabelledFormula formula, int bound) throws IOException, InterruptedException {
        String ltlStr = genRltlString(formula);
        return runCount(ltlStr, bound);
    }

    public String genRltlString(LabelledFormula formula) {
        List<String> alphabet = SolverUtils.genAlphabet(formula.variables().size());
        LabelledFormula label_formula = LabelledFormula.of(formula.formula(), alphabet);
        String ltl = SolverUtils.toLambConvSyntax(label_formula.toString());
        String alph = alphabet.toString();

        String form = "LTL=" + ltl;
        if (alph != null && !alph.isEmpty())
            form += ",ALPHABET=" + alph;
        return form;
    }

    private BigInteger runCount(String ltl, int bound) throws IOException, InterruptedException {
        String[] cmd = {"./modelcount-prefixes.sh", ltl, "" + bound};
        Process p = Runtime.getRuntime().exec(cmd);
        boolean timeout = false;
        if (!p.waitFor(TIMEOUT, TimeUnit.SECONDS)) {
            timeout = true; //kill the process.
            p.destroy(); // consider using destroyForcibly instead
        }
        if (timeout)
            throw new RuntimeException("TIMEOUT reached in CountRltlConv.");
        InputStream in = p.getInputStream();
        InputStreamReader inread = new InputStreamReader(in);
        BufferedReader bufferedreader = new BufferedReader(inread);
        String aux;
        String out = "";
        while ((aux = bufferedreader.readLine()) != null) {
            // System.out.println("AUX: " + aux);
            out = aux;
        }
        // Close the InputStream
        bufferedreader.close();
        inread.close();
        in.close();
        OutputStream os = p.getOutputStream();
        if (os != null) os.close();
        p.destroy();

        return new BigInteger(out);
    }
}
