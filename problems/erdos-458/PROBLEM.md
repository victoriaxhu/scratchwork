# Erdős problem #458: lcm across prime gaps

**Statement.** Let pₖ be the k-th prime. Is it true that lcm(1, …, pₖ₊₁ − 1) < pₖ · lcm(1, …, pₖ) for every k ≥ 1?

**Known results.** No partial results are listed in the formal-conjectures entry.

| | |
|---|---|
| Status | open |
| Database label | falsifiable (a single finite counterexample would settle it) |
| Prize | none |
| Tags | number theory, primes |
| Source | [erdosproblems.com/458](https://www.erdosproblems.com/458) |
| Formal statement | [formal-conjectures 458.lean](https://github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/ErdosProblems/458.lean) |
| OEIS | [A056604](https://oeis.org/A056604) |

Check the source page before relying on the status; the database is updated often.

## Working on this problem

```bash
scratch show erdos-458
scratch branches --problem erdos-458
scratch attempt erdos-458 <idea> --plan "one paragraph describing the approach"
```

Attempts live on branches named `attempt/erdos-458/<idea>`, in `problems/erdos-458/attempts/<idea>/`. See [AGENTS.md](../../AGENTS.md).
