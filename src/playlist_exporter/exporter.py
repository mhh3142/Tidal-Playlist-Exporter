import pandas as pd

"""
    exports the data frame to an excel document. This function is VERY basic and will soon be improved to include some os stuff to maybe make a nice folder. Eventually I'd
    like to export different sheets all at different stages of cleaning.
"""
def export_to_excel(playlist_frame: pd.DataFrame) -> None:

    file_name = "TestExcel.xlsx"

    playlist_frame.to_excel(file_name, index=False)