from firescope.application.interfaces.harmonizer import Harmonizer
class HarmonizeHotspots:
    def __init__(self, harmonizer: Harmonizer):
        self.harmonizer = harmonizer
    def execute(self, path: str) -> str:
        return self.harmonizer.harmonize(path)
