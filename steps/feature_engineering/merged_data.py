import pandas as pd
from typing_extensions import Annotated
from zenml import step

@step
def merged_data(clean_data: pd.DataFrame, processed_ratings: pd.DataFrame) -> Annotated[pd.DataFrame, "merged_data"]:
    """
    Merges movie and user dataframes on a common key.
    """
    # Specify the merge keys and method inside the function
    merged_data = pd.merge(clean_data, processed_ratings, left_on='id', right_on='movieId', how='inner')
    # Drop the 'movieId' column from the merged DataFrame as it is redundant with 'id'
    merged_data.drop(columns='movieId', inplace=True)

    return merged_data

