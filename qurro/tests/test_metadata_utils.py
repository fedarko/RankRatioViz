import os
import pytest
from pandas import Index
from pandas.testing import assert_frame_equal
from pandas.errors import ParserError
import qiime2
from qurro._df_utils import replace_nan
from qurro._metadata_utils import read_metadata_file


def test_read_metadata_file_basic():
    """Tests that read_metadata_file() works + handles bools ok.

    Mainly, we're checking here that True / False values get (eventually)
    treated as strings, NOT as bools. This preserves their "case" (i.e. they
    won't get turned into true / false in the JS side of things), and
    reduces headaches for us all around.
    """
    simple_md = os.path.join(
        "qurro", "tests", "input", "metadata_tests", "md1.tsv"
    )
    simple_df = read_metadata_file(simple_md)
    assert simple_df.index.dtype == "object"
    assert simple_df.dtypes[0] == "object"
    assert simple_df.dtypes[1] == "object"
    assert simple_df.at["S1", "MD1"] == "1.0"
    assert simple_df.at["S2", "MD1"] == "3.0"
    assert simple_df.at["S1", "MD2"] == "2.0"
    assert simple_df.at["S2", "MD2"] == "4.0"

    has_bool_md = os.path.join(
        "qurro", "tests", "input", "metadata_tests", "md2.tsv"
    )
    has_bool_df = read_metadata_file(has_bool_md)
    assert has_bool_df.index.dtype == "object"
    # This should be an object, NOT a bool! This is because
    # read_metadata_file() explicitly converts bool columns to object columns
    # (containing strings).
    assert has_bool_df.dtypes[0] == "object"
    assert has_bool_df.dtypes[1] == "object"
    assert has_bool_df.at["S1", "MD1"] == "True"
    assert has_bool_df.at["S2", "MD1"] == "False"
    assert has_bool_df.at["S1", "MD2"] == "5"
    assert has_bool_df.at["S2", "MD2"] == "6"

    one_bool_md = os.path.join(
        "qurro", "tests", "input", "metadata_tests", "md3.tsv"
    )
    one_bool_df = read_metadata_file(one_bool_md)
    assert one_bool_df.index.dtype == "object"
    assert one_bool_df.dtypes[0] == "object"
    assert one_bool_df.dtypes[1] == "object"
    assert one_bool_df.at["S1", "MD1"] == "True"
    assert one_bool_df.at["S2", "MD1"] == "WHAAAT"
    assert one_bool_df.at["S1", "MD2"] == "5"
    assert one_bool_df.at["S2", "MD2"] == "Missing: Not provided"


def test_read_metadata_file_complex():
    """Tests some corner cases in replace_nan(read_metadata_file())."""

    weird = os.path.join(
        "qurro", "tests", "input", "metadata_tests", "weird_metadata.tsv"
    )
    weird_df = replace_nan(read_metadata_file(weird))

    # Check that dtypes match up (should all be object)
    assert weird_df.index.dtype == "object"
    for col in weird_df.columns:
        assert weird_df[col].dtype == "object"

    # Check that index IDs were treated as strings (issue #116 on the Qurro
    # GitHub page)
    assert weird_df.index.equals(
        Index(["01", "02", "03", "04", "05", "06", "07", "08"])
    )

    # Check that all of the weird stuff in this file was correctly handled
    # (i.e. all ""s were converted to Nones, and everything else is preserved
    # as a string)
    assert weird_df.at["01", "Metadata1"] is None
    assert weird_df.at["01", "Metadata2"] is None
    assert weird_df.at["01", "Metadata3"] is None

    assert weird_df.at["02", "Metadata1"] == "4"
    assert weird_df.at["02", "Metadata2"] == "'5'"
    assert weird_df.at["02", "Metadata3"] == "MISSING LOL"

    assert weird_df.at["03", "Metadata1"] is None
    assert weird_df.at["03", "Metadata2"] == "8"
    assert weird_df.at["03", "Metadata3"] == "9"

    assert weird_df.at["04", "Metadata1"] == "10"
    assert weird_df.at["04", "Metadata2"] == "null"
    assert weird_df.at["04", "Metadata3"] == "12"

    assert weird_df.at["05", "Metadata1"] == "13"
    assert weird_df.at["05", "Metadata2"] is None
    assert weird_df.at["05", "Metadata3"] is None

    assert weird_df.at["06", "Metadata1"] == "16"
    assert weird_df.at["06", "Metadata2"] == "17"
    assert weird_df.at["06", "Metadata3"] is None

    assert weird_df.at["07", "Metadata1"] == "NaN"
    assert weird_df.at["07", "Metadata2"] is None
    assert weird_df.at["07", "Metadata3"] == "21"

    assert weird_df.at["08", "Metadata1"] == "22"
    assert weird_df.at["08", "Metadata2"] is None
    assert weird_df.at["08", "Metadata3"] == "Infinity"

    assert_frame_equal(
        weird_df, replace_nan(qiime2.Metadata.load(weird).to_dataframe())
    )


def test_read_metadata_file_extra_col():
    """Tests the case when there's an extra column in the metadata file."""

    ec = os.path.join(
        "qurro", "tests", "input", "metadata_tests", "extra_column.tsv"
    )
    # The extra column should be counted as a "bad line" in the TSV file --
    # this will cause pd.read_csv() to throw a ParserError
    with pytest.raises(ParserError):
        read_metadata_file(ec)

    with pytest.raises(qiime2.metadata.MetadataFileError):
        qiime2.Metadata.load(ec)


def test_read_metadata_file_whitespace_stripping():
    """Tests that whitespace is properly stripped when reading a metadata
    file.
    """

    ws = os.path.join(
        "qurro", "tests", "input", "metadata_tests", "whitespace.tsv"
    )
    ws_df = replace_nan(read_metadata_file(ws))

    # Following stuff is *mostly* copied from
    # test_read_metadata_file_complex(), with some added tweaks

    # Check that dtypes match up (should all be object)
    assert ws_df.index.dtype == "object"
    for col in ws_df.columns:
        assert ws_df[col].dtype == "object"

    # Check that index IDs were treated as strings (issue #116 on the Qurro
    # GitHub page)
    assert ws_df.index.equals(
        Index(["01", "02", "03", "04", "05", "06", "07", "08"])
    )

    assert ws_df.at["01", "Metadata1"] is None
    assert ws_df.at["01", "Metadata2"] is None
    assert ws_df.at["01", "Metadata3"] is None

    assert ws_df.at["02", "Metadata1"] == "4"
    assert ws_df.at["02", "Metadata2"] == "'5'"
    # The leading spaces in this value should be ignored
    assert ws_df.at["02", "Metadata3"] == "MISSING LOL"

    assert ws_df.at["03", "Metadata1"] is None
    assert ws_df.at["03", "Metadata2"] == "8"
    assert ws_df.at["03", "Metadata3"] == "9"

    assert ws_df.at["04", "Metadata1"] == "10"
    assert ws_df.at["04", "Metadata2"] == "null"
    assert ws_df.at["04", "Metadata3"] == "12"

    assert ws_df.at["05", "Metadata1"] == "13"
    assert ws_df.at["05", "Metadata2"] is None
    assert ws_df.at["05", "Metadata3"] is None

    assert ws_df.at["06", "Metadata1"] == "16"
    # The trailing spaces in this value should be ignored
    assert ws_df.at["06", "Metadata2"] == "17"
    # This entire value should be treated as equivalent to a ""
    assert ws_df.at["06", "Metadata3"] is None

    assert ws_df.at["07", "Metadata1"] == "NaN"
    # This entire value should be treated as equivalent to a ""
    assert ws_df.at["07", "Metadata2"] is None
    assert ws_df.at["07", "Metadata3"] == "21"

    assert ws_df.at["08", "Metadata1"] == "22"
    assert ws_df.at["08", "Metadata2"] is None
    assert ws_df.at["08", "Metadata3"] == "Infinity"

    assert_frame_equal(
        ws_df, replace_nan(qiime2.Metadata.load(ws).to_dataframe())
    )


def test_read_metadata_file_nan_id():
    """Tests the case when there's an empty ID in the metadata file."""

    ni = os.path.join(
        "qurro", "tests", "input", "metadata_tests", "nan_id.tsv"
    )
    with pytest.raises(ValueError):
        read_metadata_file(ni)

    with pytest.raises(qiime2.metadata.MetadataFileError):
        qiime2.Metadata.load(ni)
