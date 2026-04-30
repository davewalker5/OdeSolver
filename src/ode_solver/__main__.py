from ode_solver.cli.parser import parse
from ode_solver.gui.ode_solver_gui import gui_main

args = parse()
gui_main(args)
