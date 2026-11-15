from firescope.shared.exceptions import NotImplementedStageError
class SensorHarmonizer:
    def harmonize(self, dataset_path: str) -> str:
        raise NotImplementedStageError("Scientific MODIS/VIIRS harmonization is stage 2; schema union is not harmonization")
