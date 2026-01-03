"""
NYCH Visualizer

Tuple-safe locality visualizer.
Interprets plotted output as an artifact of address topology,
not semantic meaning.

X = time
Y = region
Z = volume
"""

from typing import List
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

from .symbols import Symbol
from .addressing import project_xyz


class NychVisualizer:
    def __init__(self):
        self.fig = plt.figure(figsize=(9, 9))
        self.ax = self.fig.add_subplot(111, projection="3d")

        self.ax.set_xlabel("Time (X)")
        self.ax.set_ylabel("Region (Y)")
        self.ax.set_zlabel("Volume (Z)")
        self.ax.set_title("NYCH Locality Explorer")

    def plot_symbols(self, symbols: List[Symbol]) -> None:
        """
        Plot symbols using positional XYZ projection only.
        """
        for sym in symbols:
            if not sym.address:
                continue

            x, y, z = project_xyz(sym.address)
            self.ax.scatter(x, y, z, s=60)
            self.ax.text(x, y, z, sym.glyph, fontsize=12)

    def render(self, save_path: str = None, show: bool = True) -> None:
        """
        Render the visualization.
        """
        if save_path:
            plt.savefig(save_path, dpi=200)

        if show:
            plt.show()

        plt.close(self.fig)

    def run(self, symbols: List[Symbol]) -> None:
        """
        Convenience entrypoint.
        """
        self.plot_symbols(symbols)
        self.render()
