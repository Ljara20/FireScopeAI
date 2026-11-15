"""Select the United States country CSV from yearly FIRMS archives."""
import re
from pathlib import PurePosixPath

class UsaFilter:
    @staticmethod
    def matches_country_filename(name: str) -> bool:
        """Accept modis_2003_United_States.csv and viirs-jpss1_2020_United_States.csv.

        Do not accidentally include Virgin Islands or Minor Outlying Islands.
        """
        stem = PurePosixPath(name.replace("\\", "/")).stem
        return re.fullmatch(
            r"(?:modis|viirs[-_]snpp|viirs[-_]jpss1|viirs[-_]noaa20)[-_]\d{4}[-_]United[-_]States",
            stem, flags=re.IGNORECASE,
        ) is not None
