import pytest
from pandas import DataFrame, Series
from pandas.testing import assert_frame_equal, assert_series_equal
import numpy as np
from qurro._df_utils import (
    ensure_df_headers_unique,
    validate_df,
    replace_nan,
    remove_empty_samples_and_features,
    print_if_dropped,
    match_table_and_data,
    merge_feature_metadata,
    sparsify_count_dict,
    check_column_names,
    add_sample_presence_count,
    vibe_check,
)


def test_ensure_df_headers_unique():
    """Tests the ensure_df_headers_unique() function in generate.py."""

    # Various DFs with nonunique indices and/or columns
    df_bad = DataFrame(
        {"col1": [1, 2, 3], "col2": [6, 7, 8]}, index=["a", "b", "a"]
    )
    df_bad2 = DataFrame(index=["b", "b", "b"])
    df_bad3 = DataFrame(index=[1, 2, 3, 2])

    # We can specify nonunique columns via representing the DF as a 2-D array
    # -- see https://stackoverflow.com/a/20613532/10730311
    df_bad4 = DataFrame(
        [[1, 6], [2, 7], [3, 8]],
        columns=["col1", "col1"],
        index=["a", "b", "c"],
    )
    df_bad5 = DataFrame(
        [[1, 6], [2, 7], [3, 8]],
        columns=["col1", "col1"],
        index=["a", "b", "a"],
    )

    # Various DFs with unique indices and columns
    df_good = DataFrame({"x": [20], "y": [40]}, index=["a", "b"])
    df_good2 = DataFrame({"x": [20], "y": [40]}, index=["x", "y"])
    df_good3 = DataFrame(index=["c"])

    i = 1
    for df in (df_bad, df_bad2, df_bad3, df_bad4, df_bad5):
        df_name = "test #{}".format(i)
        thing_checking = "Indices"
        if i == 4:
            thing_checking = "Columns"
        try:
            ensure_df_headers_unique(df, df_name)
            # If this didn't result in a ValueError being thrown, fail the
            # test! (It should have caused a ValueError.)
            assert False
        except ValueError as err:
            expected_message = (
                "{} of the {} DataFrame are not "
                "unique.".format(thing_checking, df_name)
            )
            assert expected_message == err.args[0]
        i += 1

    i = 1
    for df in (df_good, df_good2, df_good3):
        df_name = "test #{}".format(i)
        # If this fails (i.e. the "good" DF is detected as a bad one),
        # ensure_df_headers_unique() would raise a ValueError, autofailing (or
        # erroring, I guess, but doesn't really matter) this test
        ensure_df_headers_unique(df, df_name)
        i += 1


def test_validate_df():
    """Tests the validate_df() function in generate.py."""

    # Check that the min_row_ct and min_col_ct arguments work properly.
    normal2x2DF = DataFrame({"x": [1, 2], "y": [3, 4]}, index=["a", "b"])
    validate_df(normal2x2DF, "Normal 2x2 DF", 0, 0)
    validate_df(normal2x2DF, "Normal 2x2 DF", 1, 1)
    validate_df(normal2x2DF, "Normal 2x2 DF", 2, 2)
    with pytest.raises(ValueError):
        validate_df(normal2x2DF, "Normal 2x2 DF", 2, 3)
    with pytest.raises(ValueError):
        validate_df(normal2x2DF, "Normal 2x2 DF", 2, 4)
    with pytest.raises(ValueError):
        validate_df(normal2x2DF, "Normal 2x2 DF", 3, 2)
    with pytest.raises(ValueError):
        validate_df(normal2x2DF, "Normal 2x2 DF", 4, 2)

    # Test that the ensure_df_headers_unique() call works. We don't go as in
    # depth here as we do above, but we do still want to make sure that it
    # works as expected.

    # This is just df_bad from test_ensure_df_headers_unique().
    nonuniqueRowDF = DataFrame(
        {"col1": [1, 2, 3], "col2": [6, 7, 8]}, index=["a", "b", "a"]
    )
    with pytest.raises(ValueError):
        validate_df(nonuniqueRowDF, "Non-unique-row DF", 3, 2)

    # Check that errors don't "cancel out" (obviously shouldn't be the case,
    # but might as well be safe)
    with pytest.raises(ValueError):
        validate_df(nonuniqueRowDF, "Non-unique-row DF", 3, 3)

    # This is just df_bad4 from test_ensure_df_headers_unique().
    nonuniqueColDF = DataFrame(
        [[1, 6], [2, 7], [3, 8]],
        columns=["col1", "col1"],
        index=["a", "b", "c"],
    )
    with pytest.raises(ValueError):
        validate_df(nonuniqueColDF, "Non-unique-column DF", 3, 2)

    # This is just df_bad5 from test_ensure_df_headers_unique().
    nonuniqueColRowDF = DataFrame(
        [[1, 6], [2, 7], [3, 8]],
        columns=["col1", "col1"],
        index=["a", "b", "a"],
    )
    with pytest.raises(ValueError):
        validate_df(nonuniqueColRowDF, "Non-unique-column-and-row DF", 3, 2)


def test_replace_nan():
    """Tests replace_nan()."""

    # Basic case: other data are ints
    df = DataFrame({"x": [1, np.NaN], "y": [3, 4]}, index=["a", "b"])
    dfC = DataFrame({"x": [1, None], "y": [3, 4]}, index=["a", "b"])
    assert_frame_equal(dfC, replace_nan(df), check_dtype=False)

    # Other data are strs
    df2 = DataFrame(
        {"x": ["abc", np.NaN], "y": ["ghi", "jkl"]}, index=["a", "b"]
    )
    dfC2 = DataFrame(
        {"x": ["abc", None], "y": ["ghi", "jkl"]}, index=["a", "b"]
    )
    assert_frame_equal(dfC2, replace_nan(df2), check_dtype=False)

    # Entire Series of NaNs
    df3 = DataFrame(
        {"x": [np.NaN, np.NaN], "y": ["ghi", "jkl"]}, index=["a", "b"]
    )
    dfC3 = DataFrame(
        {"x": [None, None], "y": ["ghi", "jkl"]}, index=["a", "b"]
    )
    assert_frame_equal(dfC3, replace_nan(df3), check_dtype=False)

    # Entire DataFrame of NaNs
    df4 = DataFrame(
        {"x": [np.NaN, np.NaN], "y": [np.NaN, np.NaN]}, index=["a", "b"]
    )
    dfC4 = DataFrame({"x": [None, None], "y": [None, None]}, index=["a", "b"])
    assert_frame_equal(dfC4, replace_nan(df4), check_dtype=False)

    # If there are already Nones inside the DF for some reason (should never be
    # the case, but might as well be safe and check this)
    df5 = DataFrame(
        {"x": [np.NaN, None], "y": [np.NaN, np.NaN]}, index=["a", "b"]
    )
    dfC5 = DataFrame({"x": [None, None], "y": [None, None]}, index=["a", "b"])
    assert_frame_equal(dfC5, replace_nan(df5), check_dtype=False)

    # Case where the user specifies an alternate value to replace NaNs with
    df6 = DataFrame(
        {"x": [np.NaN, 3], "y": [np.NaN, np.NaN]}, index=["a", "b"]
    )
    dfC6 = DataFrame({"x": ["lol", 3], "y": ["lol", "lol"]}, index=["a", "b"])
    assert_frame_equal(dfC6, replace_nan(df6, "lol"), check_dtype=False)


def get_test_data():
    """Returns test table, metadata, and ranks DataFrames.

    Mostly based on/copied from get_test_data() in
    test_filter_unextreme_features.
    """
    feature_ids = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
    table = DataFrame(
        {
            "Sample1": [1, 2, 3, 4, 5, 6, 7, 8],
            "Sample2": [8, 7, 6, 5, 4, 3, 2, 1],
            "Sample3": [1, 0, 0, 0, 0, 0, 0, 0],
            "Sample4": [0, 0, 0, 1, 0, 0, 0, 0],
        },
        index=feature_ids,
    )
    metadata = DataFrame(
        {
            "Metadata1": [0, 0, 0, 1],
            "Metadata2": [0, 0, 0, 0],
            "Metadata3": [1, 2, 3, 4],
            "Metadata4": [8, 7, 6, 5],
        },
        index=list(table.columns)[:],
    )
    ranks = DataFrame(
        {
            "Rank 0": [1, 2, 3, 4, 5, 6, 7, 8],
            "Rank 1": [8, 7, 6, 5, 4, 3, 2, 1],
        },
        index=list(table.index)[:],
    )
    return table, metadata, ranks


def test_remove_empty_samples_and_features_samples():
    """Tests remove_empty_samples_and_features() in the simple cases of
    removing 0, 1, and 2 empty sample(s).
    """

    # TRY REMOVING 0 SAMPLES
    table, metadata, ranks = get_test_data()
    # Check that, when none of the samples are empty, nothing is changed.
    ftable, fmetadata, franks = remove_empty_samples_and_features(
        table, metadata, ranks
    )
    assert_frame_equal(ftable, table)
    assert_frame_equal(fmetadata, metadata)
    assert_frame_equal(franks, ranks)

    # TRY REMOVING 1 SAMPLE
    # Zero out Sample3 (it only has one count, for F1)
    table["Sample3"]["F1"] = 0
    # Check that just the one empty sample (Sample3) was removed, from both the
    # table and the sample metadata.
    ftable, fmetadata, franks = remove_empty_samples_and_features(
        table, metadata, ranks
    )
    assert_series_equal(ftable["Sample1"], table["Sample1"])
    assert_series_equal(ftable["Sample2"], table["Sample2"])
    assert_series_equal(ftable["Sample4"], table["Sample4"])
    assert "Sample3" not in ftable.columns
    assert len(ftable.columns) == 3
    assert len(ftable.index) == len(table.index) == 8

    assert_series_equal(fmetadata.loc["Sample1"], metadata.loc["Sample1"])
    assert_series_equal(fmetadata.loc["Sample2"], metadata.loc["Sample2"])
    assert_series_equal(fmetadata.loc["Sample4"], metadata.loc["Sample4"])
    assert "Sample3" not in fmetadata.index
    assert len(fmetadata.index) == 3
    assert len(fmetadata.columns) == len(metadata.columns) == 4

    assert_frame_equal(franks, ranks)

    # TRY REMOVING 2 SAMPLES
    # Now, zero out Sample4 (it only has one count in F4)
    table["Sample4"]["F4"] = 0
    ftable, fmetadata, franks = remove_empty_samples_and_features(
        table, metadata, ranks
    )
    assert_series_equal(ftable["Sample1"], table["Sample1"])
    assert_series_equal(ftable["Sample2"], table["Sample2"])
    assert "Sample3" not in ftable.columns
    assert "Sample4" not in ftable.columns
    assert len(ftable.columns) == 2
    assert len(ftable.index) == len(table.index) == 8

    assert_series_equal(fmetadata.loc["Sample1"], metadata.loc["Sample1"])
    assert_series_equal(fmetadata.loc["Sample2"], metadata.loc["Sample2"])
    assert "Sample3" not in fmetadata.index
    assert "Sample4" not in fmetadata.index
    assert len(fmetadata.index) == 2

    assert_frame_equal(franks, ranks)


def test_remove_empty_samples_and_features_features():
    """Tests remove_empty_samples_and_features() in the simple cases of
    removing 1 and then 2 empty feature(s).
    """

    table, metadata, ranks = get_test_data()
    # Zero out F8
    table.loc["F8"] = 0
    ftable, fmetadata, franks = remove_empty_samples_and_features(
        table, metadata, ranks
    )
    assert_frame_equal(fmetadata, metadata)
    # Check that F8 was removed from the table and ranks

    def check(new, old):
        assert_frame_equal(new.iloc[0:7], old.iloc[0:7])
        assert "F8" not in new.index
        assert len(new.index) == 7

    check(ftable, table)
    check(franks, ranks)

    # Zero out F6, also
    table.loc["F6"] = 0
    ftable, fmetadata, franks = remove_empty_samples_and_features(
        table, metadata, ranks
    )
    assert_frame_equal(fmetadata, metadata)
    # Check that F1 through F5 (and F7) are still the same

    def check2(new, old):
        assert_frame_equal(new.iloc[0:5], old.iloc[0:5])
        assert_series_equal(new.loc["F7"], old.loc["F7"])
        assert "F6" not in new.index
        assert len(new.index) == 6

    check2(ftable, table)
    check2(franks, ranks)


def test_remove_empty_samples_and_features_both():
    """Tests remove_empty_samples_and_features() when both samples and features
    are empty.
    """

    table, metadata, ranks = get_test_data()
    # Zero out F8 and F7
    table.loc["F8"] = 0
    table.loc["F7"] = 0
    # Zero out Sample2 and Sample4
    table["Sample2"] = 0
    table["Sample4"] = 0
    ftable, fmetadata, franks = remove_empty_samples_and_features(
        table, metadata, ranks
    )

    assert "F8" not in ftable.index
    assert "F7" not in ftable.index
    assert "F8" not in franks.index
    assert "F7" not in franks.index
    assert "Sample2" not in ftable.columns
    assert "Sample4" not in ftable.columns
    assert "Sample2" not in fmetadata.index
    assert "Sample4" not in fmetadata.index
    assert_frame_equal(
        ftable, table[["Sample1", "Sample3"]].iloc[0:6], check_like=True
    )
    assert_frame_equal(
        fmetadata, metadata.loc[set(["Sample1", "Sample3"])], check_like=True
    )
    assert_frame_equal(franks, ranks.iloc[0:6])


def test_remove_empty_samples_and_features_allempty():
    """Tests remove_empty_samples_and_features() on an empty table."""

    table, metadata, ranks = get_test_data()
    table["Sample1"] = np.zeros(len(table.index))
    table["Sample2"] = np.zeros(len(table.index))
    table["Sample3"] = np.zeros(len(table.index))
    table["Sample4"] = np.zeros(len(table.index))
    with pytest.raises(ValueError):
        remove_empty_samples_and_features(table, metadata, ranks)


def test_print_if_dropped(capsys):

    table, metadata, ranks = get_test_data()

    # Neither of these should result in anything being printed
    print_if_dropped(table, table, 0, "feature", "table", "n/a")
    captured = capsys.readouterr()
    assert captured.out == ""

    print_if_dropped(table, table, 1, "sample", "table", "n/a")
    captured = capsys.readouterr()
    assert captured.out == ""

    # This should result in something, though!
    table_f = table.drop(["F3", "F4", "F5", "F1", "F7"], axis="index")
    print_if_dropped(table, table_f, 0, "feature", "table", "n/a")
    captured = capsys.readouterr()
    expected_output = (
        "5 feature(s) in the table were not present in the n/a.\n"
        "These feature(s) have been removed from the visualization.\n"
    )
    assert captured.out == expected_output

    # As should this. (Check filtering against another axis.)
    table_f = table.drop(["Sample2"], axis="columns")
    print_if_dropped(table, table_f, 1, "sample", "table", "n/a")
    captured = capsys.readouterr()
    expected_output = (
        "1 sample(s) in the table were not present in the n/a.\n"
        "These sample(s) have been removed from the visualization.\n"
    )
    assert captured.out == expected_output

    # Test behavior when *all* features are dropped.
    # Should never happen -- we'd raise an error before this -- but good to
    # check this, at least.
    table_f = table.drop(list(table.index), axis="index")
    print_if_dropped(table, table_f, 0, "feature", "table", "n/a")
    captured = capsys.readouterr()
    expected_output = (
        "8 feature(s) in the table were not present in the n/a.\n"
        "These feature(s) have been removed from the visualization.\n"
    )
    assert captured.out == expected_output

    # Lastly, test behavior when everything is dropped -- i.e. this is an empty
    # table. Should also never happen in practice.
    # NOTE how we now modify table_f in place to make it truly empty.
    table_f.drop(list(table_f.columns), axis="columns", inplace=True)
    assert table_f.empty

    print_if_dropped(table, table_f, 1, "sample", "table", "n/a")
    captured = capsys.readouterr()
    expected_output = (
        "4 sample(s) in the table were not present in the n/a.\n"
        "These sample(s) have been removed from the visualization.\n"
    )
    assert captured.out == expected_output


def test_merge_feature_metadata():

    ranks = DataFrame({"R1": [1, 2], "R2": [2, 1]}, index=["F1", "F2"])
    fm = DataFrame(
        {"FM1": [None, None], "FM2": [1, 2], "FM3": [8, 7]}, index=["F1", "F2"]
    )
    # When feature metadata is None, the ranks DF should stay the same.
    result = merge_feature_metadata(ranks, None)
    assert_frame_equal(ranks, result[0])
    assert result[1] == []

    # Check that this works properly in the normal case
    expected = ranks.copy()
    expected["FM1"] = [None, None]
    expected["FM2"] = [1, 2]
    expected["FM3"] = [8, 7]
    result = merge_feature_metadata(ranks, fm)
    assert_frame_equal(expected, result[0], check_dtype=False)
    assert (result[1] == ["FM1", "FM2", "FM3"]).all()

    # Check that this works properly when not all features match up exactly
    # (F3 isn't in ranks, and F2 isn't in fm. So F2 should just have None for
    # all feature metadata fields.)
    fm.index = ["F1", "F3"]
    expected = ranks.copy()
    expected["FM1"] = [None, None]
    expected["FM2"] = [1, None]
    expected["FM3"] = [8, None]
    result = merge_feature_metadata(ranks, fm)
    assert_frame_equal(expected, result[0], check_dtype=False)
    assert (result[1] == ["FM1", "FM2", "FM3"]).all()

    # Check that this works properly when no features match up exactly
    fm.index = ["F3", "F4"]
    expected = ranks.copy()
    expected["FM1"] = [None, None]
    expected["FM2"] = [None, None]
    expected["FM3"] = [None, None]
    result = merge_feature_metadata(ranks, fm)
    assert_frame_equal(expected, result[0], check_dtype=False)
    assert (result[1] == ["FM1", "FM2", "FM3"]).all()

    # Check that this raises an error if feature metadata and ranking columns
    # are not distinct (shouldn't happen if check_column_names() used, but
    # might as well be careful)
    fm.columns = ["FM1", "R2", "FM3"]
    with pytest.raises(ValueError):
        merge_feature_metadata(ranks, fm)


def test_sparsify_count_dict():

    # Test that it works in basic case
    test_cts = {
        "Feature 1": {"Sample 1": 0, "Sample 2": 3, "Sample 3": 0},
        "Feature 2": {"Sample 1": 2, "Sample 2": 4, "Sample 3": 0},
    }
    assert sparsify_count_dict(test_cts) == {
        "Feature 1": {"Sample 2": 3},
        "Feature 2": {"Sample 1": 2, "Sample 2": 4},
    }

    # Test that it works even when the data is inherently dense (i.e. no zeros)
    test_cts = {
        "Feature 1": {"Sample 1": 1, "Sample 2": 3, "Sample 3": 5},
        "Feature 2": {"Sample 1": 2, "Sample 2": 4, "Sample 3": 6},
    }
    assert sparsify_count_dict(test_cts) == test_cts

    # Test that it works even when the data is totally sparse
    # This should never happen, since we filter out empty features, but good to
    # be sure
    test_cts = {
        "Feature 1": {"Sample 1": 0, "Sample 2": 0, "Sample 3": 0},
        "Feature 2": {"Sample 1": 0, "Sample 2": 0, "Sample 3": 0},
    }
    assert sparsify_count_dict(test_cts) == {"Feature 1": {}, "Feature 2": {}}


def test_check_column_names():

    _, sm, fr = get_test_data()
    fm = fr.copy()
    fm.columns = ["FM1", "FM2"]

    # Shouldn't get an error with default col names
    check_column_names(sm, fr, fm)

    # 1. Check for problematic names in sample metadata columns ("Sample ID",
    # "qurro_balance")

    sm.columns = ["Metadata1", "Sample ID", "Metadata3", "Metadata4"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"Sample ID"' in str(exception_info.value)

    # Shouldn't get an error with different case
    sm.columns = ["Metadata1", "sample id", "Metadata3", "Metadata4"]
    check_column_names(sm, fr, fm)

    sm.columns = ["qurro_balance", "Sample ID", "Metadata3", "Metadata4"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    # Sample ID check has priority in error msg
    assert '"Sample ID"' in str(exception_info.value)

    sm.columns = ["qurro_balance", "Metadata2", "Metadata3", "Metadata4"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_balance"' in str(exception_info.value)

    # reset sample metadata columns to be sane
    sm.columns = ["Metadata1", "Metadata2", "Metadata3", "Metadata4"]

    # 2. Check for problematic names in feature ranking columns ("Feature ID",
    # "qurro_classification", "qurro_spc", "qurro_x")

    fr.columns = ["R1", "Feature ID"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"Feature ID"' in str(exception_info.value)

    # If multiple problematic names are present, the ID one takes precedence,
    # then the _classification one, then the _x one, then the _spc one.
    # (this is just set by the order of "if" statements in
    # check_column_names().)
    # (also this is an arbitrary choice and doesn't really matter that much in
    # the grand scheme of things but I figure we might as well test these cases
    # somewhat.)
    # (also if you somehow have some or all of these column names in a real
    # dataset then I have a lot of questions)
    fr.columns = ["Feature ID", "qurro_classification"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"Feature ID"' in str(exception_info.value)

    fr.columns = ["R1", "qurro_classification"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_classification"' in str(exception_info.value)

    fr.columns = ["qurro_x", "qurro_classification"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_classification"' in str(exception_info.value)

    fr.columns = ["qurro_x", "R2"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_x"' in str(exception_info.value)

    fr.columns = ["qurro_x", "Feature ID"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"Feature ID"' in str(exception_info.value)

    fr.columns = ["qurro_spc", "qurro_x"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_x"' in str(exception_info.value)

    fr.columns = ["qurro_spc", "R2"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_spc"' in str(exception_info.value)

    fr.columns = ["qurro_spc", "qurro_classification"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_classification"' in str(exception_info.value)

    # reset feature ranking columns to be sane
    fr.columns = ["R1", "R2"]

    # 3. Check for problematic names in feature metadata columns ("Feature ID",
    # "qurro_classification", "qurro_spc")
    # This is essentially the same stuff as the feature ranking test above.

    fm.columns = ["FM1", "Feature ID"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"Feature ID"' in str(exception_info.value)

    fm.columns = ["Feature ID", "qurro_classification"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"Feature ID"' in str(exception_info.value)

    fm.columns = ["FM1", "qurro_classification"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_classification"' in str(exception_info.value)

    fm.columns = ["qurro_spc", "qurro_classification"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_classification"' in str(exception_info.value)

    fm.columns = ["qurro_spc", "FM2"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_spc"' in str(exception_info.value)

    fm.columns = ["FM1", "qurro_spc"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert '"qurro_spc"' in str(exception_info.value)

    # reset feature metadata columns to be sane
    fm.columns = ["FM1", "FM2"]

    # 4. Check for the case where the feature ranking and feature metadata
    # columns are not distinct
    fr.columns = ["FM1", "R2"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert "must be distinct" in str(exception_info.value)

    fr.columns = ["FM1", "FM2"]
    with pytest.raises(ValueError) as exception_info:
        check_column_names(sm, fr, fm)
    assert "must be distinct" in str(exception_info.value)


def test_match_table_and_data_no_change(capsys):
    # In basic case, nothing should change
    table, metadata, ranks = get_test_data()

    m_table, m_metadata = match_table_and_data(table, ranks, metadata)
    # Check that table and metadata are actually equal
    assert_frame_equal(table, m_table)
    assert_frame_equal(metadata, m_metadata)
    # Check that nothing was printed (i.e. no "sample/feature dropped" messages
    # or whatever)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_match_table_and_data_table_extra_feature(capsys):
    # Test case where table contains a feature that isn't in the ranks
    table, metadata, ranks = get_test_data()
    new_row = DataFrame(
        [[20, 20, 20, 20]],
        columns=table.columns,
        index=["FeatureInTableButNotRanks"],
    )
    table = table.append(new_row, verify_integrity=True)
    m_table, m_metadata = match_table_and_data(table, ranks, metadata)
    # Only features in the ranks' index should be left in the table's index,
    # and the table and ranks' indices should line up.
    assert len(set(m_table.index) & set(ranks.index)) == len(ranks.index)
    # Sanity check -- another way of verifying the above
    assert "FeatureInTableButNotRanks" not in m_table.index
    # Check that the matched-up fields' data wasn't altered somehow
    assert_frame_equal(table.loc[ranks.index], m_table)
    assert_frame_equal(metadata, m_metadata)
    # Check that a feature-dropping message was printed
    captured = capsys.readouterr()
    expected_msg = (
        "1 feature(s) in the BIOM table were not present in the feature "
        "rankings"
    )
    assert expected_msg in captured.out


def test_match_table_and_data_table_extra_sample(capsys):
    # Test case where table contains a sample that isn't in the metadata
    table, metadata, ranks = get_test_data()

    table["SampleInTableButNotMD"] = 10
    m_table, m_metadata = match_table_and_data(table, ranks, metadata)

    assert len(set(m_table.columns) & set(m_metadata.index)) == len(
        metadata.index
    )
    assert "SampleInTableButNotMD" not in m_table.columns
    assert "SampleInTableButNotMD" not in m_metadata.index
    # Check that the matched-up fields' data wasn't altered somehow
    assert_frame_equal(table[metadata.index], m_table)
    assert_frame_equal(metadata, m_metadata)
    # Check that a message re: the sample being dropped was printed
    captured = capsys.readouterr()
    expected_msg = (
        "1 sample(s) in the BIOM table were not present in the sample "
        "metadata file"
    )
    assert expected_msg in captured.out


def test_match_table_and_data_metadata_extra_sample(capsys):
    # Test case where metadata contains a sample that isn't in the table
    table, metadata, ranks = get_test_data()

    # Add a new row to the metadata
    new_row = DataFrame(
        [[20, 20, 20, 20]],
        columns=metadata.columns,
        index=["SampleInMDButNotTable"],
    )
    metadata = metadata.append(new_row, verify_integrity=True)
    m_table, m_metadata = match_table_and_data(table, ranks, metadata)
    assert len(set(m_table.columns) & set(m_metadata.index)) == len(
        table.columns
    )
    assert "SampleInMDButNotTable" not in m_table.columns
    assert "SampleInMDButNotTable" not in m_metadata.index
    # Check that the matched-up fields' data wasn't altered somehow
    assert_frame_equal(table, m_table)
    assert_frame_equal(metadata.loc[table.columns], m_metadata)
    # Check that a message re: the sample being dropped was printed
    captured = capsys.readouterr()
    expected_msg = (
        "1 sample(s) in the sample metadata file were not present in the BIOM "
        "table"
    )
    assert expected_msg in captured.out


def test_match_table_and_data_ranked_features_not_in_table():
    # Qurro is pretty accepting for mismatched data, but if any of your ranked
    # features aren't in the BIOM Qurro will immediately throw an error.
    # (...because that is not a good situation.)
    table, metadata, ranks = get_test_data()
    new_feature_row = DataFrame([[9, 0]], columns=ranks.columns, index=["F9"])
    ranks_modified = ranks.append(new_feature_row, verify_integrity=True)
    with pytest.raises(ValueError) as exception_info:
        match_table_and_data(table, ranks_modified, metadata)
    expected_message = (
        "Of the 9 ranked features, 1 was not present in the input BIOM table"
    )
    assert expected_message in str(exception_info.value)

    # Try this again; verify it works with more than 1 ranked features not in
    # the table
    # (also, the error message should use "were" instead of "was" now :)
    new_feature_row = DataFrame(
        [[10, -1]], columns=ranks.columns, index=["F10"]
    )
    ranks_modified = ranks_modified.append(
        new_feature_row, verify_integrity=True
    )
    with pytest.raises(ValueError) as exception_info:
        match_table_and_data(table, ranks_modified, metadata)
    expected_message = (
        "Of the 10 ranked features, 2 were not present in the input BIOM table"
    )
    assert expected_message in str(exception_info.value)


def test_match_table_and_data_complete_sample_mismatch():
    # Test that, if no samples are shared between the table and metadata, an
    # error is raised.
    table, metadata, ranks = get_test_data()

    # Instead of Sample1, ... use S1, ...
    metadata.index = ["S1", "S2", "S3", "S4"]
    with pytest.raises(ValueError) as exception_info:
        match_table_and_data(table, ranks, metadata)
    expected_message = (
        "No samples are shared between the sample metadata file and BIOM table"
    )
    assert expected_message in str(exception_info.value)


def test_match_table_and_data_complex(capsys):
    # Test the case where there are multiple sources of mismatched data:
    # -> 1 extra feature in the table ("F9")
    # -> 1 extra sample in the table ("Sample5")
    # -> 1 extra sample in the metadata ("SampleM")
    table, metadata, ranks = get_test_data()

    # Add the extra feature to the table
    new_f_row = DataFrame([[1, 2, 3, 4]], columns=table.columns, index=["F9"])
    table = table.append(new_f_row, verify_integrity=True)

    # Add the extra sample to the table
    table["Sample5"] = 5

    # Add the extra sample to the metadata
    new_s_row = DataFrame(
        [[4, 3, 2, 1]], columns=metadata.columns, index=["SampleM"]
    )
    metadata = metadata.append(new_s_row, verify_integrity=True)

    # Ok, actually run the function!
    m_table, m_metadata = match_table_and_data(table, ranks, metadata)
    captured = capsys.readouterr()

    # ...Now we can check all of the output messages. There'll be a lot.
    expected_message_1 = (
        "1 feature(s) in the BIOM table were not present in the feature "
        "rankings"
    )
    expected_message_2 = (
        "1 sample(s) in the BIOM table were not present in the sample "
        "metadata file"
    )
    expected_message_3 = (
        "1 sample(s) in the sample metadata file were not present in the BIOM "
        "table"
    )
    assert expected_message_1 in captured.out
    assert expected_message_2 in captured.out
    assert expected_message_3 in captured.out


def verify_spc_data_integrity(output_feature_data, initial_feature_data):
    """Checks that add_sample_presence_count() doesn't change any of the
    initially input feature_data -- it just adds a qurro_spc column, and
    doesn't change the DF in any other way.
    """
    ifd_in_ofd = output_feature_data.drop("qurro_spc", axis="columns")
    assert_frame_equal(ifd_in_ofd, initial_feature_data)


def test_add_sample_presence_count_basic():

    # NOTE: for reference, the get_test_data() table initially looks like this:
    # "Sample1": [1, 2, 3, 4, 5, 6, 7, 8],
    # "Sample2": [8, 7, 6, 5, 4, 3, 2, 1],
    # "Sample3": [1, 0, 0, 0, 0, 0, 0, 0],
    # "Sample4": [0, 0, 0, 1, 0, 0, 0, 0],
    table, metadata, ranks = get_test_data()

    # Test a basic case.
    output_feature_data = add_sample_presence_count(ranks, table)
    assert_series_equal(
        output_feature_data["qurro_spc"],
        Series([3, 2, 2, 3, 2, 2, 2, 2], index=ranks.index, name="qurro_spc"),
    )
    # Make sure that the underlying feature data remains the same
    verify_spc_data_integrity(output_feature_data, ranks)


def test_add_sample_presence_count_zeros():
    """Checks the case when some features aren't present in any samples."""

    table, metadata, ranks = get_test_data()

    # Test 1: zero out all counts for feature F3
    table.loc["F3"] = 0
    output_feature_data = add_sample_presence_count(ranks, table)
    assert_series_equal(
        output_feature_data["qurro_spc"],
        Series([3, 2, 0, 3, 2, 2, 2, 2], index=ranks.index, name="qurro_spc"),
    )
    verify_spc_data_integrity(output_feature_data, ranks)

    # Test 2: zero out all counts
    table.loc[:] = 0
    ofd_2 = add_sample_presence_count(ranks, table)
    assert_series_equal(
        ofd_2["qurro_spc"],
        Series([0] * 8, index=ranks.index, name="qurro_spc"),
    )
    verify_spc_data_integrity(ofd_2, ranks)

    # Test 3: just one count for one feature
    table["Sample4"]["F2"] = 1
    ofd_3 = add_sample_presence_count(ranks, table)
    assert_series_equal(
        ofd_3["qurro_spc"],
        Series([0, 1, 0, 0, 0, 0, 0, 0], index=ranks.index, name="qurro_spc"),
    )
    verify_spc_data_integrity(ofd_3, ranks)


def test_add_sample_presence_count_name_error():
    """Checks the case where the feature data already contains a column
    called qurro_spc.

    This should never happen due to check_column_names() being called, but
    we might as well be careful.
    """
    table, metadata, ranks = get_test_data()
    ranks.columns = ["Rank 0", "qurro_spc"]
    with pytest.raises(ValueError):
        add_sample_presence_count(ranks, table)


def test_vibe_check_safe_range_invalid_safe_ranges():
    """Checks cases where the input range specified to vibe_check() is somehow
    invalid.
    """
    table, metadata, ranks = get_test_data()

    ranges = [[1, 2, 3, 4, 5], [], [1], (), (2,)]
    for r in ranges:
        with pytest.raises(ValueError) as exception_info:
            vibe_check(ranks, table, safe_range=r)
        assert "safe_range must have a length of 2." in str(
            exception_info.value
        )

    with pytest.raises(ValueError) as exception_info:
        vibe_check(ranks, table, safe_range=[10, 1])
    assert "safe_range[1] must be GREATER THAN safe_range[0]." in str(
        exception_info.value
    )


def test_vibe_check_successes():
    table, metadata, ranks = get_test_data()

    # Should succeed since all of the test data, by default, is in the default
    # safe range
    vibe_check(ranks, table)

    # Should succeed since the numbers in the test data (table and ranks) range
    # from 0 to 8
    vibe_check(ranks, table, safe_range=[0, 8])


def test_vibe_check_failures():
    table, metadata, ranks = get_test_data()

    # Accordingly, should fail
    with pytest.raises(OverflowError) as exception_info:
        vibe_check(ranks, table, safe_range=[1, 8])
    assert (
        'The input feature table contains entries lower than the "safe" lower '
        "limit for numbers of 1."
    ) in str(exception_info.value)

    # Should also fail
    with pytest.raises(OverflowError) as exception_info:
        vibe_check(ranks, table, safe_range=[0, 7])
    assert (
        'The input feature table contains entries larger than the "safe" '
        "upper limit for numbers of 7."
    ) in str(exception_info.value)

    # Test failure, with the default safe range, on a few small cases.
    lower_lim = -(2 ** 53) - 1
    upper_lim = (2 ** 53) - 1

    weird_small_values = [lower_lim - 1, lower_lim * 2, lower_lim * 3]
    for w in weird_small_values:
        ranks["Rank 0"]["F3"] = w

        with pytest.raises(OverflowError) as exception_info:
            vibe_check(ranks, table)
        assert (
            "The input feature rankings data contains entries lower than the "
            '"safe" lower limit for numbers of -9007199254740991.'
        ) in str(exception_info.value)

    # Test failure, with the default safe range, on a few large cases.
    weird_large_values = [upper_lim + 1, upper_lim * 2, upper_lim * 3]
    for w in weird_large_values:
        ranks["Rank 0"]["F3"] = w

        with pytest.raises(OverflowError) as exception_info:
            vibe_check(ranks, table)
        assert (
            "The input feature rankings data contains entries larger than the "
            '"safe" upper limit for numbers of 9007199254740991.'
        ) in str(exception_info.value)
