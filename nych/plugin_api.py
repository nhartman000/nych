"""
IDE / MCP insertion point

This is the 'between IDE and model' layer.
"""

from .mapping import map_natural_language
from .inspection import Inspector
from .storage import SymbolStorage

class NychPlugin:
    def __init__(self):
        self.storage = SymbolStorage()
        self.inspector = Inspector(self.storage)

    def process(self, text: str):
        symbols = map_natural_language(text)
        return symbols

    def visualize(self, symbols):
        return [repr(s) for s in symbols]
