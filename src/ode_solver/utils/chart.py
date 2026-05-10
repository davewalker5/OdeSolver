import matplotlib
import matplotlib.pyplot as plt

# Use a non-interactive backend for file export so this helper does not depend
# on, or interfere with, any GUI backend used elsewhere in the application.
matplotlib.use("Agg")


def export_chart(history, filepath, simulation_options):
    """
    Plot a chart of a run history and export it to a file

    :param history: List of dictionaries representing points in the solution
    :param filepath: Path to the output file
    :param title: Chart title
    """
    # Extract separate lists of the independent and dependent variable values
    t = [d["t"] for d in history]
    y = [d["y_normalised"] if simulation_options["normalise"] else d["y"] for d in history]

    # Determine scaling
    auto_scale = simulation_options["chart_auto_scale"]

    # Chart the data using an off-screen Figure and Axes
    fig, ax = plt.subplots()

    try:
        ax.plot(t, y)
        ax.set_xlabel("x")
        if not auto_scale:
            ax.set_xlim(0.0, simulation_options["chart_max_x"])

        ax.set_ylabel("y")
        if not auto_scale:
            ax.set_ylim(simulation_options["chart_min_y"], simulation_options["chart_max_y"])

        ax.set_title(simulation_options["chart_title"])

        # Enable major grid lines
        ax.grid(True, which="major", linestyle="--", linewidth=0.5)

        fig.tight_layout()
        fig.savefig(filepath)
    finally:
        plt.close(fig)
