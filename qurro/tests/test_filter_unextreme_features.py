import biom
from numpy import arange
from pandas import DataFrame
from pandas.testing import assert_frame_equal
import pytest
from qurro._rank_utils import filter_unextreme_features
from qurro.generate import biom_table_to_sparse_df, process_input
from qurro.tests.test_df_utils import get_test_data as get_test_data_2


def get_test_data():
    """Returns a ranks DataFrame and a BIOM table for use in testing."""

    feature_ids = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
    sample_ids = ["S1", "S2", "S3", "S4", "S5"]
    ranks = DataFrame(
        {
            "Rank 0": [1, 2, 3, 4, 5, 6, 7, 8],
            "Rank 1": [8, 7, 6, 5, 4, 3, 2, 1],
        },
        index=feature_ids,
    )
    # Based on the BIOM docs' example of initialization using a np ndarray --
    # http://biom-format.org/documentation/table_objects.html#examples
    #
    # arange(40) generates a numpy ndarray that just goes from 0 to 39 (i.e.
    # contains 40 numbers). We reshape this ndarray to give it a sort of
    # "tabular" structure (a 2-D array containing 8 arrays, each with 5
    # numbers).
    underlying_table_data = arange(40).reshape(8, 5)
    # Set the third sample in the data to contain all zeros, except for a
    # count for F4 (so we can test what this function does with so-called
    # "empty" samples after filtering out F4).
    underlying_table_data[:, 2] = 0.0
    underlying_table_data[3, 2] = 1.0
    # Finally, use the data to create a BIOM table object.
    biom_table = biom.Table(underlying_table_data, feature_ids, sample_ids)
    # ...And yeah we're actually making it into a Sparse DF because that's what
    # I changed filter_unextreme_features() to expect now.
    # (TODO: simplify this code in the future?)
    output_table = biom_table_to_sparse_df(biom_table)

    return output_table, ranks


def test_filtering_basic():
    """Tests the standard behavior of filter_unextreme_features()."""

    table, ranks = get_test_data()
    filtered_table, filtered_ranks = filter_unextreme_features(table, ranks, 2)
    # Check that the appropriate features/samples were filtered out of the
    # table. NOTE -- I know this is sloppy code. Would like to fix it in the
    # future.
    for fid in ["F1", "F2", "F7", "F8"]:
        assert fid in filtered_table.index
    for fid in ["F3", "F4", "F5", "F6"]:
        assert fid not in filtered_table.index
    # Check that all samples were preserved.
    # (The removal of empty features is done *after*
    # filter_unextreme_features() is called in normal Qurro execution, so we
    # should expect all samples -- even empty ones -- to remain here.
    for sid in ["S1", "S2", "S3", "S4", "S5"]:
        assert sid in filtered_table.columns

    # Check that the appropriate data is left in the table.
    assert list(filtered_table.loc["F1"]) == [0, 1, 0, 3, 4]
    assert list(filtered_table.loc["F2"]) == [5, 6, 0, 8, 9]
    assert list(filtered_table.loc["F7"]) == [30, 31, 0, 33, 34]
    assert list(filtered_table.loc["F8"]) == [35, 36, 0, 38, 39]

    # Check that the rank filtering worked as expected.
    expected_filtered_ranks = DataFrame(
        {"Rank 0": [1, 2, 7, 8], "Rank 1": [8, 7, 2, 1]},
        index=["F1", "F2", "F7", "F8"],
    )
    assert_frame_equal(
        filtered_ranks, expected_filtered_ranks, check_like=True
    )


def test_filtering_large_efc():
    """Tests filter_unextreme_features() when (the extreme feature count * 2)
    is greater than or equal to the number of ranked features.
    """

    table, ranks = get_test_data()

    # The number of ranked features is 8.
    filtered_table, filtered_ranks = filter_unextreme_features(table, ranks, 4)
    assert_frame_equal(table, filtered_table)
    assert_frame_equal(ranks, filtered_ranks)

    filtered_table, filtered_ranks = filter_unextreme_features(table, ranks, 8)
    assert_frame_equal(table, filtered_table)
    assert_frame_equal(ranks, filtered_ranks)


def test_filtering_no_efc():
    """Tests filter_unextreme_features() when the extreme feature count is None
    (i.e. the user didn't use the -x option, and no filtering should be
    done).
    """

    table, ranks = get_test_data()

    filtered_table, filtered_ranks = filter_unextreme_features(
        table, ranks, None
    )
    assert_frame_equal(table, filtered_table)
    assert_frame_equal(ranks, filtered_ranks)


def test_filtering_invalid_efc():
    """Tests that filter_unextreme_features() throws an error when the
    extreme feature count is less than 1 and/or not an integer.
    """

    table, ranks = get_test_data()

    with pytest.raises(ValueError):
        filter_unextreme_features(table, ranks, 0)

    with pytest.raises(ValueError):
        filter_unextreme_features(table, ranks, -1)

    with pytest.raises(ValueError):
        filter_unextreme_features(table, ranks, -2)

    with pytest.raises(ValueError):
        filter_unextreme_features(table, ranks, 1.5)

    with pytest.raises(ValueError):
        filter_unextreme_features(table, ranks, 5.5)


def test_filtering_to_empty_features():
    """Integration test for the odd corner case where the "extreme" features
    are all empty.
    """
    # Sorry this code is kinda gross
    table, metadata, ranks = get_test_data_2()

    # Zero out the table DataFrame
    table[:] = 0
    # Make the non-extreme features (F3 through F6) all non-empty, while
    # *leaving* the extreme features (F1, F2, F7, F8) as empty
    # (Note that our definition of "extreme" here is just based on -x 2)
    table.loc["F3"] = table.loc["F4"] = table.loc["F5"] = table.loc["F6"] = 5

    # Convert the table DataFrame to an actual BIOM table
    # (so we can throw it into process_input())
    biom_table = biom.Table(table.values, table.index, table.columns)

    # Without a -x parameter (or with a -x parameter of > 2), this should work
    # fine since the non-empty features will be preserved
    process_input(ranks, metadata, biom_table)
    process_input(ranks, metadata, biom_table, extreme_feature_count=3)
    process_input(ranks, metadata, biom_table, extreme_feature_count=4)

    # This, however, should cause an error!
    # All the non-extreme features will be filtered out, leaving only empty
    # features. This means that there'll be an empty table.
    with pytest.raises(ValueError) as exception_info:
        process_input(ranks, metadata, biom_table, extreme_feature_count=2)
    assert "table is empty" in str(exception_info.value)
