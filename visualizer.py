from typing import List, Optional
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

from .symbols import Symbol
from .lexicon import LEXICON


class NychVisualizer:
    """
    NYCH Locality Explorer

    Visualizes NYCH symbols as addressable points in X/Y/Z axis space.
    Higher dimensions remain latent.
    """

    def __init__(self):
        self.fig = plt.figure(figsize=(8, 8))
        self.ax = self.fig.add_subplot(111, projection="3d")

        self.ax.set_xlabel("X axis")
        self.ax.set_ylabel("Y axis")
        self.ax.set_zlabel("Z axis")

        self.ax.set_title("NYCH Locality Explorer")

    def _extract_xyz(self, address):
        """
        Safely extract X/Y/Z from an Address object
        without assuming internal representation.
        """

        # Case 1: explicit attributes
        if all(hasattr(address, a) for a in ("x", "y", "z")):
            return address.x, address.y, address.z

        # Case 2: iterable (list / tuple)
        if hasattr(address, "__iter__"):
            vals = list(address)
            x = vals[0] if len(vals) > 0 else 0.0
            y = vals[1] if len(vals) > 1 else 0.0
            z = vals[2] if len(vals) > 2 else 0.0
            return x, y, z

        # Case 3: axis dictionary
        if hasattr(address, "axes"):
            axes = address.axes
            return (
                axes.get("x", 0.0),
                axes.get("y", 0.0),
                axes.get("z", 0.0),
            )

        # Fallback: origin
        return 0.0, 0.0, 0.0

    def plot_symbols(self, symbols: List[Symbol]):
        xs, ys, zs, labels = [], [], [], []

        for sym in symbols:
            if not sym.address:
                x, y, z = 0.0, 0.0, 0.0
            else:
                x, y, z = self._extract_xyz(sym.address)

            xs.append(x)
            ys.append(y)
            zs.append(z)
            labels.append(sym.glyph)

        self.ax.scatter(xs, ys, zs, s=80)

        for x, y, z, label in zip(xs, ys, zs, labels):
            self.ax.text(x, y, z, label, fontsize=10)

        # draw reference axes
        self.ax.plot([-1, 1], [0, 0], [0, 0], linewidth=0.5)
        self.ax.plot([0, 0], [-1, 1], [0, 0], linewidth=0.5)
        self.ax.plot([0, 0], [0, 0], [-1, 1], linewidth=0.5)

    def render(
        self,
        symbols: Optional[List[Symbol]] = None,
        save_path: Optional[str] = None,
        show: bool = True,
    ):
        if symbols is None:
            symbols = list(LEXICON.values())

        self.plot_symbols(symbols)

        if save_path:
            plt.savefig(save_path, dpi=200)

        if show:
            plt.show()

        plt.close(self.fig)
