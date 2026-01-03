from nych.visualizer import NychVisualizer
from nych.lexicon import LEXICON

# Initialize visualizer
viz = NychVisualizer()

# Pick symbols to inspect
symbols = [
    LEXICON["👁️"],
    LEXICON["🧠"],
    LEXICON["⚖️"],
    LEXICON["🤝"],
]

# Plot them
viz.plot_symbols(symbols)

# Focus on a local region (acts like Gaussian window)
viz.focus_window(center=(0, 0, 0), radius=1.5)

# Launch viewer
viz.show()
viz.render(save_path="out.png", show=False)
