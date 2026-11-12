"""Inspect a registered dataset without the installed `core-tbi` entry point."""
from core_tbi.cli import datasets_inspect

if __name__ == "__main__":
    import typer
    typer.run(datasets_inspect)
