from ode_solver.cli.parser import parse
from ode_solver.gui.ode_solver_gui import gui_main
from ode_solver.cli.ode_solver_cli import cli_main

args = parse()
if args.no_gui:
    cli_main(args)
else:
    gui_main(args)
