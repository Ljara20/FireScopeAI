from firescope.infrastructure.processing.usa_filter import UsaFilter

def test_country_filename_variants():
    for path in [
        "modis/2003/modis_2003_United_States.csv",
        "viirs-snpp/2017/viirs-snpp_2017_United_States.csv",
        "viirs-jpss1/2020/viirs-jpss1_2020_United_States.csv",
    ]:
        assert UsaFilter.matches_country_filename(path)

def test_territories_not_merged():
    for path in [
        "modis_2003_United_States_Virgin_Islands.csv",
        "viirs-jpss1_2020_United_States_Minor_Outlying_Islands.csv",
        "viirs-snpp_2017_United_Kingdom.csv",
    ]:
        assert not UsaFilter.matches_country_filename(path)
