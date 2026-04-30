from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table


class LiveTableCallback:
    def __init__(
        self,
        title="ODE Solver Run",
        refresh_per_second=4,
        height=25,
        header_rows=3,
        table_box=box.SIMPLE,
    ):
        self.title = title
        self.refresh_per_second = refresh_per_second
        self.height = height
        self.header_rows = header_rows
        self.table_box = table_box

        self.console = Console()
        self.live = None
        self.rows = []
        self.started = False

    def _make_table(self, visible_rows):
        table = Table(
            title=self.title,
            box=self.table_box,
            show_edge=False,
            padding=(0, 1),
        )

        table.add_column("Method")
        table.add_column("Step", justify="right")
        table.add_column("t", justify="right")
        table.add_column("y", justify="right")
        table.add_column("Step Size", justify="right")
        table.add_column("Diff", justify="right")
        table.add_column("Tolerance", justify="right")

        for row in visible_rows:
            table.add_row(*row)

        return table

    def _render(self):
        visible_capacity = max(1, self.height - self.header_rows)
        visible_rows = self.rows[-visible_capacity:]

        return self._make_table(visible_rows)

    def _start(self):
        self.live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=self.refresh_per_second,
            transient=False,
        )
        self.live.start()
        self.started = True

    def __call__(self, method, i, t, y, step_size, difference, tolerance):
        if not self.started:
            self._start()

        row = [
            str(method),
            str(i),
            str(t),
            str(y),
            str(step_size),
            str(difference),
            str(tolerance),
        ]

        self.rows.append(row)

        self.live.update(self._render(), refresh=True)

    def close(self):
        if self.live is not None:
            self.live.stop()

        self.started = False