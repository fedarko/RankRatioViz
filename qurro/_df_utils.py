#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Copyright (c) 2018--, Qurro development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# ----------------------------------------------------------------------------

import logging
import pandas as pd


def ensure_df_headers_unique(df, df_name):
    """Raises an error if the index or columns of the DataFrame aren't unique.

    (If both index and columns are non-unique, the index error will take
    precedence.)

    If these fields are unique, no errors are raised and nothing (None) is
    implicitly returned.

    Parameters
    ----------

    df: pandas.DataFrame
    df_name: str
        The "name" of the DataFrame -- this is displayed to the user in the
        error message thrown if the DataFrame has any non-unique IDs.
    """
    if len(df.index.unique()) != df.shape[0]:
        raise ValueError(
            "Indices of the {} DataFrame are not" " unique.".format(df_name)
        )

    if len(df.columns.unique()) != df.shape[1]:
        raise ValueError(
            "Columns of the {} DataFrame are not" " unique.".format(df_name)
        )


def validate_df(df, name, min_row_ct, min_col_ct):
    """Does some basic validation on the DataFrame.

    1. Calls ensure_df_headers_unique() to ensure that index and column
       names are unique.
    2. Checks that the DataFrame has at least min_row_ct rows.
    3. Checks that the DataFrame has at least min_col_ct columns.
    """
    ensure_df_headers_unique(df, name)
    logging.debug("Ensured uniqueness of {}.".format(name))
    if df.shape[0] < min_row_ct:
        raise ValueError(
            "Less than {} rows found in the {}.".format(min_row_ct, name)
        )
    if df.shape[1] < min_col_ct:
        raise ValueError(
            "Less than {} columns found in the {}.".format(min_col_ct, name)
        )


def fix_id(fid):
    """As a temporary measure, escapes certain special characters in a name.

    Right now, a measure like this is required to make Vega* work properly
    with various field names.

    See https://github.com/vega/vega-lite/issues/4965.
    """

    new_id = ""
    for c in fid:
        if c == ".":
            new_id += ":"
        elif c == "]":
            new_id += ")"
        elif c == "[":
            new_id += "("
        elif c == "'" or c == '"':
            # Don't bother replacing quotes
            pass
        elif c == "\\":
            new_id += "|"
        else:
            new_id += c
    return new_id


def escape_columns(df, df_name):
    """Calls str() then fix_id() on each of the column names of the DF."""
    new_cols = []
    for col in df.columns:
        new_cols.append(fix_id(str(col)))
    df.columns = new_cols
    # Ensure that this didn't make the column names non-unique
    ensure_df_headers_unique(df, df_name)
    return df


def replace_nan(df, new_nan_val=None):
    """Replaces all occurrences of NaN values in the DataFrame with a specified
    value.

    Note that this solution seems to result in the DataFrame's columns'
    dtypes being changed to object. (This shouldn't change much due to how
    we handle metadata files, though.)

    Based on the solution described here:
    https://stackoverflow.com/a/14163209/10730311
    """
    return df.where(df.notna(), new_nan_val)


def biom_table_to_sparse_df(table, min_row_ct=2, min_col_ct=1):
    """Loads a BIOM table as a pd.SparseDataFrame. Also calls validate_df().

    We need to use a helper function for this because old versions of BIOM
    accidentally produce an effectively-dense DataFrame when using
    biom.Table.to_dataframe() -- see
    https://github.com/biocore/biom-format/issues/808.

    To get around this, we extract the scipy.sparse.csr_matrix data from the
    BIOM table and directly convert that to a pandas SparseDataFrame.
    """
    logging.debug("Creating a SparseDataFrame from BIOM table.")
    table_sdf = pd.SparseDataFrame(table.matrix_data, default_fill_value=0.0)

    # The csr_matrix doesn't include column/index IDs, so we manually add them
    # in to the SparseDataFrame.
    table_sdf.index = table.ids(axis="observation")
    table_sdf.columns = table.ids(axis="sample")

    # Validate the table DataFrame -- should be ok since we loaded this through
    # the biom module, but might as well check
    validate_df(table_sdf, "BIOM table", min_row_ct, min_col_ct)

    logging.debug("Converted BIOM table to SparseDataFrame.")
    return table_sdf


def remove_empty_samples_and_features(
    table_sdf, sample_metadata_df, feature_ranks_df
):
    """Removes empty samples and features from the table, sample metadata, and
    feature ranks DataFrames.

    This should be called *after* matching the table with the sample
    metadata and feature ranks -- we assume that the columns of the
    table DataFrame are equivalent to the indices of the sample metadata
    DataFrame, and that the indices (rows) of the table are also equivalent
    to the indices of the feature ranks DataFrame.

    This will raise a ValueError if the input table is empty (i.e. all
    samples/features would be removed).
    """
    logging.debug("Attempting to remove empty samples and features.")

    # Filter out empty samples (columns) and features (rows) from the table
    # This approach based on https://stackoverflow.com/a/21165116/10730311.
    neq_0 = table_sdf != 0
    filtered_table = table_sdf.loc[
        neq_0.any(axis="columns"), neq_0.any(axis="index")
    ]

    # If the table only contains zeros, then attempting to drop all empty
    # samples and/or features results in a 0x0 DataFrame. We raise a ValueError
    # in this case.
    if filtered_table.empty:
        raise ValueError("The table is empty.")

    # Let user know about which samples/features may have been dropped, if any.
    # And, if we filtered out any samples or features, filter the sample
    # metadata and feature ranks (respectively) to match (this is just done by
    # aligning them to the filtered table).
    filtered_metadata = sample_metadata_df
    filtered_ranks = feature_ranks_df

    sample_diff = len(table_sdf.columns) - len(filtered_table.columns)
    if sample_diff > 0:
        # As with match_table_and_data, we have to transpose the sample
        # metadata in order to align it with the table (since samples are
        # stored as columns in the table but as indices in the sample metadata)
        sm_t = sample_metadata_df.T
        filtered_metadata = filtered_table.align(
            sm_t, join="inner", axis="columns"
        )[1].T
        print("Removed {} empty sample(s).".format(sample_diff))
    else:
        logging.debug("Couldn't find any empty samples.")

    feature_diff = len(table_sdf.index) - len(filtered_table.index)
    if feature_diff > 0:
        filtered_ranks = filtered_table.align(
            feature_ranks_df, join="inner", axis="index"
        )[1]
        print("Removed {} empty feature(s).".format(feature_diff))
    else:
        logging.debug("Couldn't find any empty features.")

    return filtered_table, filtered_metadata, filtered_ranks


def print_if_dropped(
    df_old, df_new, axis_num, item_name, df_name, filter_basis_name
):
    """Prints a message if a given DataFrame has been filtered.

    Essentially, this function just checks if
    df_old.shape[axis_num] - df_new.shape[axis_num] > 0.

    If so, this prints a message with a bunch of details (which the _name
    parameters all describe).

    Parameters
    ----------
    df_old: pd.DataFrame (or pd.SparseDataFrame)
         "Unfiltered" DataFrame -- used as the reference when trying to
         determine if df_new has been filtered.

    df_new: pd.DataFrame (or pd.SparseDataFrame)
         A potentially-filtered DataFrame.

    axis_num: int
         The axis in the DataFrames' .shapes to check. This should be either
         0 or 1, but we don't explicitly check for that.

    item_name: str
         The name of the "thing" described by the given axis in these
         DataFrames. In practice, this is either "sample" or "feature".

    df_name: str
         The name of the DataFrame represented by df_old and df_new.

    filter_basis_name: str
         The name of the other DataFrame which caused these items to be
         dropped. For example, if we're checking to see if samples were
         dropped from the sample metadata file due to to samples not being
         in the BIOM table, df_name could be "sample metadata file" and
         filter_basis_name could be "BIOM table".
    """

    dropped_item_ct = df_old.shape[axis_num] - df_new.shape[axis_num]
    if dropped_item_ct > 0:
        print(
            "{} {}(s) in the {} were not present in the {}.".format(
                dropped_item_ct, item_name, df_name, filter_basis_name
            )
        )
        print(
            "These {}(s) have been removed from the "
            "visualization.".format(item_name)
        )


def match_table_and_data(table, feature_ranks, sample_metadata):
    """Matches feature rankings and then sample metadata to a table.

    TODO: Some of the logic in this function for matching the feature ranks
    and sample metadata could probably be abstracted out to another
    function. This individual function isn't directly unit-tested, but its
    behavior should be mostly tested in the "matching" integration tests
    (...that being said, it'd be a lot easier + sustainable to also add
    direct unit tests for this function).

    Parameters
    ----------

    table: pd.DataFrame (or pd.SparseDataFrame)
         A DataFrame created from a BIOM table. The index of this DataFrame
         should correspond to observations (i.e. features), and the columns
         should correspond to samples.

         Note that the input BIOM table might contain features or samples
         that are not included in feature_ranks or sample_metadata,
         respectively -- this is totally fine. The opposite, though, is
         where things get to be a problem: if any of the features in
         feature_ranks are not present in the table, or if all of the
         samples in sample_metadata are not in the table, then this will
         raise errors.

    feature_ranks: pd.DataFrame
         A DataFrame describing features' "ranks" along ranking(s). The
         index of this DataFrame should correspond to feature IDs, and the
         columns should correspond to different rankings' names.

    sample_metadata: pd.DataFrame
         A DataFrame describing sample metadata. The index of this DataFrame
         should describe sample IDs, and the columns should correspond to
         different sample metadata fields' names.

    Returns
    -------

    (m_table, m_sample_metadata): both pd.[Sparse]DataFrame
         Versions of the input table and sample metadata only containing
         samples shared by both datasets. The table will also only contain
         features shared by both the table and the feature ranks.

         (None of the features in the feature ranks should be dropped during
         this operation, so we don't bother returning the feature ranks
         DataFrame.)

    Raises
    ------

    If any of the features described in feature_ranks are not present in
    the table, this will raise a ValueError.

    If all of the samples described in sample_metadata are not present
    in the table, this will raise a ValueError.
    """
    logging.debug("Starting matching table with feature ranks.")
    featurefiltered_table, m_feature_ranks = table.align(
        feature_ranks, axis="index", join="inner"
    )
    logging.debug("Matching table with feature ranks done.")
    # Ensure that every ranked feature was present in the BIOM table. Raise an
    # error if this isn't the case.
    if m_feature_ranks.shape[0] < feature_ranks.shape[0]:
        unsupported_feature_ct = (
            feature_ranks.shape[0] - m_feature_ranks.shape[0]
        )
        # making this error message as pretty as possible
        word = "were"
        if unsupported_feature_ct == 1:
            word = "was"
        raise ValueError(
            "Of the {} ranked features, {} {} not present in "
            "the input BIOM table.".format(
                feature_ranks.shape[0], unsupported_feature_ct, word
            )
        )
    print_if_dropped(
        table,
        featurefiltered_table,
        0,
        "feature",
        "BIOM table",
        "feature rankings",
    )

    # We transpose the sample metadata instead of the actual table because
    # transposing in pandas, at least from some personal testing, can be really
    # expensive for huge (EMP-scale) DataFrames. Since sample metadata will
    # generally be smaller than the actual table, we transpose that.
    #
    # (The reason we have debug log messages around these statements is because
    # of how expensive transposing can be -- this is a rudimentary way to check
    # for bottlenecks when really large datasets are passed into Qurro.)
    logging.debug(
        "Temporarily transposing sample metadata to make matching easier."
    )
    sample_metadata_transposed = sample_metadata.T
    logging.debug("Transposing done.")
    logging.debug("Starting matching table with (tranposed) sample metadata.")
    m_table, m_sample_metadata_transposed = featurefiltered_table.align(
        sample_metadata_transposed, axis="columns", join="inner"
    )
    logging.debug("Matching table with sample metadata done.")
    logging.debug("Transposing sample metadata again to reset it.")
    m_sample_metadata = m_sample_metadata_transposed.T
    logging.debug("Transposing done.")
    # Allow for dropped samples (e.g. negative controls), but ensure that at
    # least one sample is supported by the BIOM table.
    #
    # We only need to check m_sample_metadata.shape[0] here since it should be
    # equal to m_table.shape[1] at this point (due to our use of .align()).
    if m_sample_metadata.shape[0] < 1:
        raise ValueError(
            "No samples are shared between the sample metadata file and BIOM "
            "table."
        )
    print_if_dropped(
        sample_metadata,
        m_sample_metadata,
        0,
        "sample",
        "sample metadata file",
        "BIOM table",
    )
    print_if_dropped(
        featurefiltered_table,
        m_table,
        1,
        "sample",
        "BIOM table",
        "sample metadata file",
    )

    return m_table, m_sample_metadata


def merge_feature_metadata(feature_ranks, feature_metadata=None):
    """Attempts to merge feature metadata into a feature ranks DataFrame.

    Parameters
    ----------

    feature_ranks: pd.DataFrame
         A DataFrame defining feature rankings, where the index corresponds
         to feature IDs and the columns correspond to ranking names.

    feature_metadata: pd.DataFrame or None
         A DataFrame defining feature metadata, where the index corresponds
         to feature IDs and the columns correspond to feature metadata
         names. It isn't expected that every feature ID be passed.

    Returns
    -------

    (output_feature_data, feature_metadata_cols): (pd.DataFrame, list)
         The input feature ranks DataFrame, with any available feature
         metadata merged in; and a list of any columns in the feature
         metadata (or [] if the feature metadata was None).

    Raises
    ------

    ValueError: if column name(s) are shared between the feature ranks and
                feature metadata DataFrames. See #55 for context.
    """
    feature_metadata_cols = []
    if feature_metadata is not None:
        feature_metadata_cols = feature_metadata.columns
        # Use of suffixes=(False, False) ensures that columns are unique
        # between feature metadata and feature ranks.
        # That should never happen if check_column_names() has been called on
        # the input DataFrames, but we might as well be careful.
        output_feature_data = feature_ranks.merge(
            feature_metadata,
            how="left",
            left_index=True,
            right_index=True,
            suffixes=(False, False),
        )
        output_feature_data = replace_nan(output_feature_data)
    else:
        output_feature_data = feature_ranks

    return output_feature_data, feature_metadata_cols


def sparsify_count_dict(count_dict):
    """Returns a "sparse" representation of a dict of counts data.

    We expect that the input dict is of the format {feature ID: {sample ID:
    count, sample 2 ID: count, ...}, ...}. In theory you could also totally
    pass in a transposed dict here (where samples are the "outer layer" of
    the dict), but the variable names would need to be flipped to make this
    function make sense. (See #175 on GitHub for context.)

    Anyway, this function returns the input dict, but without references to
    0-count samples for a given feature. (Since we filter out empty
    features, we expect that every feature should have at least one sample
    with a nonzero count of that feature.)
    """
    logging.debug("Sparsifying count data.")
    sparse_count_dict = {}
    for feature_id, sample_counts in count_dict.items():
        # This will be the new sample_counts dict for this feature ID, but only
        # containing sample IDs with nonzero counts.
        fdict = {}
        for sample_id, count in sample_counts.items():
            if count != 0:
                fdict[sample_id] = count
        sparse_count_dict[feature_id] = fdict
    logging.debug("Done sparsifying count data.")
    return sparse_count_dict


def add_sample_presence_count(feature_data, table_sdf):
    """Adds a "qurro_spc" column to a DataFrame of feature information.

    The value in this column corresponds to the number of samples a given
    feature is present in, as determined by the count data given in the
    table_sdf argument.

    Parameters
    ----------

    feature_data: pd.DataFrame
         A DataFrame containing some sort of feature information. At the
         point in Qurro this is called, this will likely include both
         feature ranking information and feature metadata information.

    table_sdf: pd.SparseDataFrame
         Representation of a BIOM table containing count data. The index
         contains feature IDs, and the columns contain sample IDs.
         This table should only contain samples that will be used in the
         Qurro visualization (i.e. this table should be the output of all
         the matching, filtering, removing empty, etc. steps), since the
         presence of irrelevant samples will result in inaccurate SPC values
         being computed.

    Returns
    -------

    output_feature_data: pd.DataFrame
         feature_data, with a qurro_spc column added.

    Raises
    ------

    ValueError: if feature_data already contains a column named "qurro_spc".
                (Assuming you've already called check_column_names() on this
                data this shouldn't be a problem, but this checks anyway.)
    """
    # Convert the table into a presence-absence representation (every count
    # value > 0 is replaced with 1).
    #
    # When I was looking around for ways to do this, I googled "pandas
    # dataframe presence absence" and one of the first hits was the docs for
    # DF.where() (which led me to DF.mask). Nowhere on either of these pages
    # is "presence" or "absence" mentioned. But, uh, thanks Google for reading
    # my mind?
    table_pa = table_sdf.mask(table_sdf > 0, 1)
    # Sum each row of the presence-absence table, producing a series with
    # qurro_spc values
    spc_series = table_pa.sum(axis="columns")
    spc_series.name = "qurro_spc"

    # Return merged copy of the feature data with the series named "qurro_spc"
    # Note the use of suffixes=(False, False) -- this will throw a ValueError
    # if feature_data already contains a column called "qurro_spc".
    return feature_data.merge(
        spc_series,
        how="left",
        left_index=True,
        right_index=True,
        suffixes=(False, False),
    )


def check_column_names(sample_metadata, feature_ranks, feature_metadata=None):
    """Checks that column names in input data will work properly in Qurro.

    See https://github.com/biocore/qurro/issues/55 for a list of these
    restrictions.
    """

    sugg = " Try changing the name of this column."
    sm_cols = sample_metadata.columns
    fr_cols = feature_ranks.columns
    fm_cols = []
    if feature_metadata is not None:
        fm_cols = feature_metadata.columns

    if "Sample ID" in sm_cols:
        raise ValueError(
            'Sample metadata can\'t contain any columns called "Sample ID" '
            "(aside from the first column in the metadata).{}".format(sugg)
        )

    if "Feature ID" in fr_cols or "Feature ID" in fm_cols:
        raise ValueError(
            "Feature rankings/metadata can't contain any columns called "
            '"Feature ID" (aside from the first column in these files).'
            "{}".format(sugg)
        )

    if "qurro_balance" in sm_cols:
        raise ValueError(
            "Sample metadata can't contain any columns called "
            '"qurro_balance".{}'.format(sugg)
        )

    if "qurro_classification" in fr_cols or "qurro_classification" in fm_cols:
        raise ValueError(
            "Feature rankings/metadata can't contain any columns called "
            '"qurro_classification".{}'.format(sugg)
        )

    if "qurro_x" in fr_cols or "qurro_x" in fm_cols:
        raise ValueError(
            "Feature rankings/metadata can't contain any columns called "
            '"qurro_x".{}'.format(sugg)
        )

    if "qurro_spc" in fr_cols or "qurro_spc" in fm_cols:
        raise ValueError(
            "Feature rankings/metadata can't contain any columns called "
            '"qurro_spc".{}'.format(sugg)
        )

    if len(set(fr_cols) & set(fm_cols)) > 0:
        raise ValueError(
            "Column names for the feature metadata and feature ranks must be "
            "distinct. Try creating a copy of your feature metadata with "
            "identical columns renamed, and use that with Qurro."
        )


def vibe_check(
    feature_ranks,
    table_sdf,
    safe_range=[-9007199254740991, 9007199254740991],
):
    """Returns an error if the input data can't be safely used in Qurro as is.

    Our definition of "safe" here is that none of these DataFrames contain
    any numeric values that are outside the specified safe numeric range. By
    default, this range is [-(2**53 - 1), (2**53 - 1)].

    Primarily, this is useful for validating the BIOM table and feature
    rankings. I imagine the presence of things like numeric IDs in the
    metadata will make this hard to properly screen for without introducing
    a ton of false positives, which will annoy people; maybe we can make the
    simplifying assumption that if your data is in a categorical metadata
    column then you don't care about its numeric representation?

    Parameters
    ----------

    feature_ranks: pd.DataFrame
         A DataFrame defining feature rankings, where the index corresponds
         to feature IDs and the columns correspond to ranking names.
         Critically, every entry in this should be numeric.

    table_sdf: pd.DataFrame (or pd.SparseDataFrame)
         DataFrame representation of a feature table. Similarly to the
         feature rankings, every entry in this should be numeric.

    safe_range: collection with exactly two entries
         The first entry in the safe_range specifies the minimum value we
         allow, and the second entry specifies the maximum value we allow.
         Any numbers outside of this range are deemed to "fail the vibe
         check," in internet meme parlance circa autumn 2019.

    Returns
    -------

    None

    Raises
    ------

    ValueError: if safe_range does not contain exactly two entries, or
                if the second entry in safe_range is less than or equal to
                the first entry in safe_range

    OverflowError: if the feature rankings or BIOM table inputs contain any
                   numbers outside of the specified safe range
    """
    if len(safe_range) != 2:
        raise ValueError("safe_range must have a length of 2.")
    if safe_range[1] <= safe_range[0]:
        raise ValueError("safe_range[1] must be GREATER THAN safe_range[0].")
    # Note that the above if statement will also cause this to fail if either
    # of the entries in safe_range can't be compared via <=, >, etc. (Per
    # python doctrine, we don't explicitly set type restrictions on
    # safe_range's entries, so its entries can be ints, floats, ...)

    upper_error = (
        "The input THING contains entries larger than the "
        '"safe" upper limit for numbers of {}. This means that the Qurro '
        "visualization interface is not usable, at least not currently. "
        'We suggest using Qurro\'s "Qarcoal" command to compute '
        "log-ratios outside of the Qurro visualization interface."
    ).format(safe_range[1])

    lower_error = (
        "The input THING contains entries lower than the "
        '"safe" lower limit for numbers of {}. This means that the Qurro '
        "visualization interface is not usable, at least not currently. "
        'We suggest using Qurro\'s "Qarcoal" command to compute '
        "log-ratios outside of the Qurro visualization interface."
    ).format(safe_range[0])

    for (df, df_name) in (
        (table_sdf, "feature table"),
        (feature_ranks, "feature rankings data"),
    ):
        if (df > safe_range[1]).any().any():
            raise OverflowError(upper_error.replace("THING", df_name))
        if (df < safe_range[0]).any().any():
            raise OverflowError(lower_error.replace("THING", df_name))
