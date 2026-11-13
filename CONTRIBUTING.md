# Contributing without write access

1. Fork the repository on GitHub and clone your fork.
2. Add the main repository as `upstream` and start from its `main`:
   `git remote add upstream https://github.com/victoriaxhu/scratchwork && git fetch upstream`
3. Use the CLI as normal; it pushes to `origin`, your fork:
   `scratch attempt erdos-647 my-idea --plan "..."`
4. Open a pull request from your `attempt/<problem>/<idea>` branch to `main`, or run `scratch propose --summary "..."`.

A workflow copies every such pull request to `attempt/<problem>/<idea>--<your-github-user>` in the main repository, so the attempt appears on the site whether or not it succeeds. Keep pushing to the same branch; the copy updates. Maintainers merge into `main` only checked results.
