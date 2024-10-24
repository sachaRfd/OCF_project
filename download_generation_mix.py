"""
Script to download generation mix data from carbonintensity API.

We can assume this data is also part of our prediction, as it is a forecast from an ML model :)

"""

import requests
import pandas as pd
from datetime import datetime, timedelta


def get_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch generation mix data from the Carbon Intensity API for a given date range.

    Args:
        start_date (str): Start date in the format 'YYYY-MM-DD'.
        end_date (str): End date in the format 'YYYY-MM-DD'.

    Returns:
        pd.DataFrame: DataFrame containing the generation mix with fuel types as columns.
    """

    from_date = f"{start_date}T00:00Z"
    to_date = f"{end_date}T23:59Z"
    r = requests.get(
        f"https://api.carbonintensity.org.uk/generation/{from_date}/{to_date}",
        params={},
        headers={},
    )
    data = r.json()

    # Convert the response data to a DataFrame
    data_df = pd.DataFrame(data["data"])
    data_df.index = pd.to_datetime(data_df["to"])  # Set 'to' as the index
    data_df.index.name = "Date"
    data_df.drop(columns=["to", "from"], inplace=True)

    # Initialize a new DataFrame to store the generation mix as separate columns
    generationmix_df = pd.DataFrame()

    # Loop through each row and transform 'generationmix' into separate columns
    for i in range(len(data_df)):
        # Extract the generation mix for the current row
        generationmix = data_df.iloc[i].generationmix
        # Convert the list of dictionaries into a dictionary
        mix_dict = clean_dictionary(generationmix)
        # Append the dictionary as a new row in the generationmix_df
        generationmix_df = pd.concat(
            [generationmix_df, pd.DataFrame(mix_dict, index=[data_df.index[i]])]
        )

    # Concatenate the new DataFrame with the original DataFrame
    data_df = pd.concat([data_df, generationmix_df], axis=1)

    # Drop the 'generationmix' column
    data_df.drop(columns=["generationmix"], inplace=True)

    return data_df


def clean_dictionary(sample_list_of_dict: list[dict]) -> dict:
    """
    Convert a list of dictionaries representing fuel types and their percentages into a single dictionary.

    Args:
        sample_list_of_dict (list[dict]): A list of dictionaries, each containing 'fuel' and 'perc' keys.

    Returns:
        dict: A dictionary with fuel types as keys and percentages as values.
    """
    big_dict = {}
    for dic in sample_list_of_dict:
        # Extract the current fuel type and its generation percentage
        fuel = dic["fuel"]
        gen = dic["perc"]
        # Add to the dictionary where the fuel is the key and percentage is the value
        big_dict[fuel] = gen
    return big_dict


def get_data_for_year_by_month(year: int) -> pd.DataFrame:
    """
    Fetch generation mix data month-by-month for a full year.

    Args:
        year (int): The year for which the data is to be fetched.

    Returns:
        pd.DataFrame: DataFrame containing the generation mix for the entire year.
    """

    start_date = datetime(year, 1, 1)
    end_date = datetime(
        year + 1, 1, 1
    )  # Capture the first day of the next year to ensure full year

    # Initialize an empty DataFrame to store the data for the whole year
    full_year_data = pd.DataFrame()

    # Loop through each month
    current_date = start_date
    while current_date < end_date:
        # Calculate the start and end of the current month
        next_month = current_date.replace(day=28) + timedelta(
            days=4
        )  # this will always get you to the next month
        next_month = next_month.replace(day=1)  # first day of next month
        end_of_month = next_month - timedelta(seconds=1)  # end of the current month

        # Fetch data for the current month
        print(
            f"Fetching data for {current_date.strftime('%Y-%m')}"
        )  # Fetch for this month
        monthly_data = get_data(
            current_date.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")
        )

        # Concatenate the monthly data to the full year data
        full_year_data = pd.concat([full_year_data, monthly_data])

        # Move to the next month
        current_date = next_month

    return full_year_data


def main() -> None:
    """
    Main function to fetch data for the year 2022 and one additional day (January 1, 2023),
    then save the result as a CSV file.
    """
    year_data = get_data_for_year_by_month(2022)
    final_date = "2023-01-01"
    final_date = get_data(final_date, final_date)  # jsut want one day
    year_data = pd.concat([year_data, final_date])
    year_data.to_csv("data/generation_data.csv")


if __name__ == "__main__":
    main()
