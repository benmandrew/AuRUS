package geneticalgorithm;

import org.junit.jupiter.api.Test;
import owl.ltl.parser.TlsfParser;
import owl.ltl.tlsf.Tlsf;
import utils.TlsfUtils;

import java.io.FileReader;
import java.io.IOException;

class SpecificationMutatorTest {

    @Test
    void testWeakAssumptions0() throws IOException, InterruptedException {
        String filename = "examples/minepump.tlsf";
        FileReader f = new FileReader(filename);
        Tlsf spec = TlsfParser.parse(f);
        Tlsf mutated_spec = SpecificationMutator.mutate(spec);

        System.out.println(TlsfUtils.toTLSF(mutated_spec));
    }

    @Test
    void testWeakGuarantees0() throws IOException, InterruptedException {
        String filename = "examples/minepump.tlsf";
        FileReader f = new FileReader(filename);
        Tlsf spec = TlsfParser.parse(f);
        Tlsf mutated_spec = SpecificationMutator.mutate(spec);

        System.out.println(TlsfUtils.toTLSF(mutated_spec));
    }

    @Test
    void testStrengtenGuarantees0() throws IOException, InterruptedException {
        String filename = "examples/minepump.tlsf";
        FileReader f = new FileReader(filename);
        Tlsf spec = TlsfParser.parse(f);
        Tlsf mutated_spec = SpecificationMutator.mutate(spec);

        System.out.println(TlsfUtils.toTLSF(mutated_spec));
    }
}
