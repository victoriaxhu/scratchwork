# Erdős problem #647: Divisor counts just below n

**Statement.** Let τ(m) be the number of divisors of m. Is there some n > 24 such that max over m < n of (m + τ(m)) is at most n + 2?

**Known results.** The condition holds at n = 24. Erdős called it 'extremely doubtful' that there are infinitely many such n.

| | |
|---|---|
| Status | open |
| Database label | verifiable (a single finite example would settle it) |
| Prize | £25 |
| Tags | number theory |
| Source | [erdosproblems.com/647](https://www.erdosproblems.com/647) |
| Formal statement | [formal-conjectures 647.lean](https://github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/ErdosProblems/647.lean) |
| OEIS | [A062249](https://oeis.org/A062249), [A087280](https://oeis.org/A087280) |

Check the source page before relying on the status; the database is updated often.

## Working on this problem

```bash
scratch show erdos-647
scratch branches --problem erdos-647
scratch attempt erdos-647 <idea> --plan "one paragraph describing the approach"
```

Attempts live on branches named `attempt/erdos-647/<idea>`, in `problems/erdos-647/attempts/<idea>/`. See [AGENTS.md](../../AGENTS.md).
