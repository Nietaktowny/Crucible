"""Entry point for `python -m crucible`, delegating to the CLI."""

from crucible.cli import CrucibleCli

if __name__ == "__main__":
    cli = CrucibleCli()
    cli.run()
