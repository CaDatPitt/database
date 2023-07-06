import pandas as pd
from .encoding_schemes import LIST


def decode_values(df=pd.DataFrame) -> pd.DataFrame:
    """
    Replaces encoded values in the specified dataset column(s) with the 
    corresponding decoded values, then returns decoded dataset.

    Parameters
    ----------
    df: pd.DataFrame
        a pandas DataFrame

    Returns
    -------
    pd.DataFrame

    """

    # pre-process and decode fields in specified column(s)
    encoded_columns = {
    'language': ['iso639-2b'],
    'coverage': ['marccountry', 'marcgac'],
    }
    encoding_dict = {}

    for column in encoded_columns.keys():
        # build dictionary from appropriate encoding schemes for column
        for encoding_scheme in encoded_columns[column]:
            encoding_dict.update(LIST[encoding_scheme])

        # pre-process and decode fields in column and keep count of total and 
        # decoded values
        if column in df.columns:
            for i in df.index:
                field_data = df.at[i, column]
                field_list = []
                decoded_field_list = []
                if isinstance(field_data, str):
                    field_list = (field_data).split('|||')
                    for value in field_list:
                        processed_value = value.strip('-\n\t ').lower()
                        decoded_value = ""
                        for code in encoding_dict.keys():
                            if processed_value == code:
                                decoded_value = processed_value.replace(
                                    code, encoding_dict[code])
                                break
                            else:
                                decoded_value = value
                        decoded_field_list.append(decoded_value)
                df.at[i, column] = "|||".join(set(decoded_field_list))

    return df
