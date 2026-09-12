# Figure dataset overview: caption and dataset description

## Caption

**Figure 1 | Scale and coverage of the binary and ternary vapor--liquid equilibrium datasets.** **a,** Experimental VLE state points, unique unordered chemical systems, and molecular components. The binary dataset contains 23,061 state points, 700 systems, and 333 components; the ternary dataset contains 5,229 state points, 126 systems, and 125 components. **b,** Temperature--pressure coverage. Pressure is logarithmic, density contours indicate the principal sampling regions, and a broken temperature axis retains 25 observations above 650 K. **c,** Chemical-family coverage assigned by prioritized RDKit/SMARTS rules; c1 and c2 share the same absolute bubble-area scale for unique-system counts. **c1,** Binary family-pair distribution, with each unordered pair shown once in the upper triangle; bubble area denotes unique systems and color denotes experimental VLE points. **c2,** The 18 ternary family triplets with the most experimental points among all 49 observed triplets. **d,** Composition-space coverage for binary liquid and vapor mole fractions and ternary liquid compositions. Ternary vertices denote source-record component positions and do not imply common chemical identities across systems. **e,** Coverage of the three binary subsystems associated with each ternary system. All system identities are independent of component order.

## Dataset coverage

The combined workbooks contain 28,290 experimental VLE state points: 23,061 binary and 5,229 ternary records spanning 700 binary and 126 ternary systems. Binary temperatures and pressures span 153.23--1550 K and 0.010--50,180 kPa; ternary values span 253.27--1400 K and 0.010--15,000 kPa. Most observations occupy common experimental ranges, with smaller high-temperature and high-pressure tails.

The dataset covers 79 binary family pairs and 49 ternary family triplets with a long-tailed distribution. The 18 ternary triplets displayed in panel c2 contribute 4,083 experimental points and 80 ternary systems, or 78.1% and 63.5% of their respective totals. `unresolved` denotes a component without a reliable molecular structure and does not imply a chemical family.

Binary records span near-pure endpoints and the interior of composition space; 18.1% lie at $x_1\leq0.05$ or $x_1\geq0.95$, and the median $|y_1-x_1|$ is 0.152. Among ternary liquid records, 68.7% have all three mole fractions at least 0.05 and 7.0% lie near a vertex with one mole fraction at least 0.90. Of the 126 ternary systems, 30 have all three corresponding binary subsystems, 22 have two, 69 have one, and 5 have none.

## Data representation

The analysis reads `binary_vle_english.xlsx` and `ternary_vle_english.xlsx`. Each record retains component names, molecular formulae, available SMILES, thermodynamic-consistency quality codes, temperature, pressure, phase compositions, and DOI. Temperature is converted by $T\,(\mathrm{K})=T\,(^{\circ}\mathrm{C})+273.15$ and pressure by $1\ \mathrm{mmHg}=0.133322368\ \mathrm{kPa}$. Binary closure gives $x_2=1-x_1$ and $y_2=1-y_1$; ternary closure gives $x_3=1-x_1-x_2$ and $y_3=1-y_1-y_2$.

Component names undergo Unicode, case, and whitespace normalization. Parseable SMILES are canonicalized with RDKit and linked to InChIKeys. A missing SMILES is linked only when normalized name and molecular formula identify an existing structure uniquely; otherwise the analysis uses a stable fallback identity without inventing a molecular structure. System identifiers sort stable component identities, so component permutations refer to the same system. Quality codes follow `1 = passed`, `0 = failed`, and `-1 = not evaluated`. Each standardized record preserves its source file, workbook row, and DOI.
