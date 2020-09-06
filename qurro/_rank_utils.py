#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Copyright (c) 2018--, Qurro development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# ----------------------------------------------------------------------------

import logging
import skbio
import pandas as pd
from qurro._df_utils import escape_columns
from qurro._metadata_utils import get_q2_comment_lines


def read_rank_file(file_loc):
    """Converts an input file of ranks to a DataFrame.

    Also returns a human-readable "rank type" -- either "Differential" or
    "Feature Loading".
    """

    if file_loc.endswith(".tsv"):
        rank_df = differentials_to_df(file_loc)
        rank_type = "Differential"
    else:
        # ordination_to_df() will raise an appropriate error if it can't
        # process this file.
        rank_df = ordination_to_df(file_loc)
        rank_type = "Feature Loading"

    return escape_columns(rank_df, "feature ranks"), rank_type


def rename_loadings(loadings_df):
    """Renames a DataFrame of loadings to say "Axis 1", "Axis 2", etc.

    This should match what Emperor does in its visualizations.
    """

    loadings_df_copy = loadings_df.copy()
    new_column_names = []
    for n in range(1, len(loadings_df_copy.columns) + 1):
        new_column_names.append("Axis {}".format(n))
    loadings_df_copy.columns = new_column_names
    return loadings_df_copy


def ordination_to_df(ordination_file_loc):
    """Returns a DataFrame of feature loadings from a skbio ordination file."""

    # If this fails, it raises an skbio.io.UnrecognizedFormatError.
    ordination = skbio.OrdinationResults.read(ordination_file_loc)

    return rename_loadings(ordination.features)


def differentials_to_df(differentials_loc):
    """Converts a differential rank TSV file to a DataFrame."""

    # As of QIIME 2 2019.7, differentials exported from QIIME 2 can have q2
    # comments! So we need to detect these.
    q2_lines = get_q2_comment_lines(differentials_loc)
    differentials = pd.read_csv(
        differentials_loc,
        sep="\t",
        na_filter=False,
        dtype=object,
        skiprows=q2_lines,
    )
    # Delay setting index column so we can first load it as an object (this
    # saves us from situations where the index col would otherwise be read as a
    # number or something that would mess things up -- read_metadata_file()
    # does the same sorta thing)
    differentials.set_index(differentials.columns[0], inplace=True)
    # Also, we don't bother naming the differentials index (yet). This is
    # actually needed to make some of the tests pass (which is dumb, I know,
    # but if I pass check_names=False to assert_frame_equal then the test
    # doesn't check column names, and I want it to do that...)
    differentials.index.rename(None, inplace=True)

    # This is slow but it should at least *work as intended.*
    # If there are any non-numeric differentials, or any NaN differentials, or
    # any infinity/-infinity differentials (???), then we should raise an
    # error. This code should do that.
    for feature_row in differentials.itertuples():
        for differential in feature_row[1:]:
            try:
                fd = float(differential)
                if pd.isna(fd) or fd == float("inf") or fd == float("-inf"):
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "Missing / nonnumeric differential(s) found for feature "
                    "{}".format(feature_row[0])
                )

    # Now, we should be able to do this freely.
    for column in differentials.columns:
        differentials[column] = differentials[column].astype(float)
    return differentials


def filter_unextreme_features(
    table: pd.SparseDataFrame, ranks: pd.DataFrame, extreme_feature_count: int
) -> None:
    """Returns copies of the table and ranks with "unextreme" features removed.

    This assumes that the table and ranks have already been matched (i.e.
    their indices are now identical). If this isn't the case, the behavior
    of this function is undefined (I'm pretty sure it will make the print
    messages incorrect at minimum).

    Parameters
    ----------

    table: pd.SparseDataFrame
         A SparseDataFrame representation of a BIOM table. This can be
         generated easily from a biom.Table object using
         qurro._df_utils.biom_table_to_sparse_df().

    ranks: pandas.DataFrame
         A DataFrame where the index consists of ranked features' IDs, and
         the columns correspond to the various ranking(s) for which each
         feature should have a numeric value.

    extreme_feature_count: int
         An integer representing the number of features from each "end" of
         the feature rankings to preserve in the table. If this is None, the
         input table and ranks will just be returned.
         This has to be at least 1.

    Returns
    -------

    (table, ranks): (pandas.SparseDataFrame, pandas.DataFrame)
         Filtered copies of the input table and ranks DataFrames.

    Behavior
    --------

    As an example of how this function works:

    If extreme_feature_count is equal to 3, and if there are 5 "rankings"
    (i.e. non-feature-ID columns) in the ranks DataFrame, then somewhere
    in the inclusive range of 6 to 30 features will be preserved.

    The 3 * 2 = 6 extreme features of the first ranking will be identified,
    and then extrema will be identified for the remaining four rankings. If
    all of the extreme features are the same between rankings, then only the
    six extrema will be preserved; however, if all of the rankings have
    distinct extrema, then each of the 5 rankings will have 6 extreme
    features preserved, making a total of (3 * 2) * 5 = 30 features.

    If (extreme_feature_count * 2) is greater than or equal to the total
    number of features in the ranks DataFrame, this won't do any filtering
    at all. In this case, a warning message will be printed from this
    function, and the given table and ranks inputs will be returned.
    """

    logging.debug('Starting to filter "unextreme" features.')

    if extreme_feature_count is None:
        logging.debug("No extreme feature count specified; not filtering.")
        return table, ranks
    elif extreme_feature_count < 1:
        raise ValueError("Extreme feature count must be at least 1.")
    elif type(extreme_feature_count) != int:
        raise ValueError("Extreme feature count must be an integer.")

    efc2 = extreme_feature_count * 2
    if efc2 >= len(ranks):
        logging.debug("Extreme Feature Count too large to do any filtering.")
        print(
            "The input Extreme Feature Count was {}. {} * 2 = {}.".format(
                extreme_feature_count, extreme_feature_count, efc2
            )
        )
        print(
            "{} is greater than or equal to the number of ranked "
            "features ({}).".format(efc2, len(ranks))
        )
        print("Therefore, no feature filtering will be done now.")
        return table, ranks

    # OK, we're actually going to do some filtering.
    starting_feature_ct = ranks.shape[0]
    print(
        "Will perform feature filtering with e.f.c. of {}.".format(
            extreme_feature_count
        )
    )
    print(
        "Before filtering, the feature ranks and (matched) table contain {} "
        "features.".format(starting_feature_ct)
    )
    logging.debug("Input table has shape {}.".format(table.shape))
    logging.debug("Input feature ranks have shape {}.".format(ranks.shape))
    # We store these features in a set to avoid duplicates -- Python does the
    # hard work here for us
    features_to_preserve = set()
    for ranking in ranks.columns:
        upper_extrema = ranks.nlargest(extreme_feature_count, ranking).index
        lower_extrema = ranks.nsmallest(extreme_feature_count, ranking).index
        features_to_preserve |= set(upper_extrema)
        features_to_preserve |= set(lower_extrema)

    # Now, we actually filter the feature ranks and table. We do this using
    # .loc[]. I benchmarked it, and .loc was about 1.77x as fast as .filter --
    # >>> df = pd.SparseDataFrame(np.zeros(34000000).reshape(17000, 2000))
    # >>> %timeit df.loc[set([16990, 8983, 8982])]
    # 460 ms +/- 17.6 ms per loop
    # >>> %timeit df.filter(items=set([16990, 8983, 8982]), axis="index")
    # 818 ms +/- 25.6 ms per loop
    filtered_ranks = ranks.loc[features_to_preserve]
    filtered_table = table.loc[features_to_preserve]

    filtered_feature_ct = filtered_ranks.shape[0]
    print(
        "After filtering, the feature ranks and (matched) table contain {} "
        "features.".format(filtered_feature_ct)
    )
    print(
        "Filtered {} features in total.".format(
            starting_feature_ct - filtered_feature_ct
        )
    )
    logging.debug("Output table has shape {}.".format(filtered_table.shape))
    logging.debug(
        "Output feature ranks have shape {}.".format(filtered_ranks.shape)
    )
    logging.debug("Done with filtering unextreme features.")

    return filtered_table, filtered_ranks
