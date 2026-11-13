# Erdős problem #23: Bipartizing triangle-free graphs

**Statement.** Can every triangle-free graph on 5n vertices be made bipartite by deleting at most n² edges?

**Known results.** The balanced blow-up of C₅ shows that n² would be best possible. The case n = 5 follows from Balogh–Clemen–Lidický together with McKay's catalogue of extremal graphs.

| | |
|---|---|
| Status | open |
| Database label | falsifiable (a single finite counterexample would settle it) |
| Prize | none |
| Tags | graph theory |
| Source | [erdosproblems.com/23](https://www.erdosproblems.com/23) |
| Formal statement | [formal-conjectures 23.lean](https://github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/ErdosProblems/23.lean) |
| OEIS | [A389646](https://oeis.org/A389646) |

Check the source page before relying on the status; the database is updated often.

## Working on this problem

```bash
scratch show erdos-23
scratch branches --problem erdos-23
scratch attempt erdos-23 <idea> --plan "one paragraph describing the approach"
```

Attempts live on branches named `attempt/erdos-23/<idea>`, in `problems/erdos-23/attempts/<idea>/`. See [AGENTS.md](../../AGENTS.md).
