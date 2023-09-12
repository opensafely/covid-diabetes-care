import pandas as pd
from IPython.display import display, HTML

medicines = [
    "dpp4_inhibitors",
    "glp1s",
    "glp1_combined_insulin",
    "glp1_not_combined",
    "insulin",
    "insulin_basal",
    "insulin_non_basal",
    "insulin_mixed_biphasic",
    "metformin",
    "pioglitazone",
    "sglt_2_inhibitors",
    "sulfonylureas",
]

stratifiers = [
    "Total",
    "diabetes",
    "hba1c_cat",
    "age_cat",
    "sex",
    "region",
    "imd",
    "ethnicity",
    "obese",
    "learning_difficulties",
    "cardiovascular_history",
    "ckd5",
]


def read_dataset(year):
    dataset = pd.read_feather(f"../../output/dataset_{year}.arrow")
    dataset = dataset.set_index("patient_id")
    return dataset


def categorise_columns(df):
    df["diabetes"] = "No diabetes"
    df.loc[df["t2dm"].fillna(value=False), "diabetes"] = "t2dm"
    df.loc[df["t1dm"].fillna(value=False), "diabetes"] = "t1dm"
    df["age_cat"] = pd.cut(
        x=df["age"],
        bins=[0, 17, 29, 44, 59, 74, 120],
        labels=["18", "18-29", "30-44", "45-59", "60-74", "75"],
    )
    df["obese"] = pd.cut(
        x=df["bmi"],
        bins=[0, 30, 200],
        right=False,
        labels=["Not obese", "Obese"],
    )
    return df


def crosstab(df, idx):
    return pd.crosstab(idx, df["diabetes"], normalize=False, dropna=False)


def count_meds_by_stratifiers(df):
    dfs = []
    for x in stratifiers:
        dfs.append(df.groupby(x).count()[medicines])
    df_counts = pd.concat(dfs, keys=stratifiers)
    df_counts = df_counts.round(-1)
    return df_counts


def make_tables(year):
    df = read_dataset(year)
    df = categorise_columns(df)
    df["Total"] = "-"
    df_totals = overall_totals(df)
    df_t2dm = df.loc[df["diabetes"] == "t2dm"]
    df = count_meds_by_stratifiers(df)
    df_t2dm = count_meds_by_stratifiers(df_t2dm)

    [rename_categories(x) for x in [df, df_t2dm, df_totals]]

    display(HTML(f"<h1>{year}</h1>"))
    display(HTML("<h3>Population totals</h3>"))
    display(HTML(df_totals.to_html()))
    display(HTML("<h3>Whole population prescribing</h3>"))
    display(HTML(df.to_html()))
    display(HTML("<h3>Type 2 Diabetes only prescribing</h3>"))
    display(HTML(df_t2dm.to_html()))
    df_totals.to_csv(f"../../output/totals_{year}.csv")
    df.to_csv(f"../../output/prescribing_{year}.csv")
    df_t2dm.to_csv(f"../../output/prescribing_t2dm_{year}.csv")


def rename_categories(df):
    high_level_ethnicities = {
        "1": "White",
        "2": "Mixed",
        "3": "South Asian",
        "4": "Black",
        "5": "Other",
    }
    imd_categories = {0: "Missing", 1: "Most deprived 1", 5: "Least deprived 5"}
    df = rename_index_categories(df, "ethnicity", high_level_ethnicities)
    df = rename_index_categories(df, "imd", imd_categories)
    return df


def rename_index_categories(df, attribute, replacement_dict):
    index = df.index.values
    for old, new in replacement_dict.items():
        for i, item in enumerate(index):
            if item == (attribute, old):
                index[i] = (attribute, new)
    df.index = pd.MultiIndex.from_tuples(index)
    return df


def overall_totals(df):
    df_totals = [crosstab(df, df[v]) for v in stratifiers]
    df_totals = pd.concat(
        df_totals, axis=0, keys=stratifiers, names=["Attribute", "Category"]
    )
    df_totals = df_totals.round(-1)
    return df_totals


def get_percentages(df):
    percent = df.groupby(level=0).apply(lambda x: ((x / x.sum()) * 100).round(1))
    return percent
