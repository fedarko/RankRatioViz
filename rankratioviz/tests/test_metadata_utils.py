from io import StringIO
from rankratioviz._metadata_utils import read_metadata_file


def test_read_metadata_file():
    """Tests that read_metadata_file() works + handles bools ok.

       Mainly, we're checking here that True / False values get (eventually)
       treated as strings, NOT as bools. This preserves their "case" (i.e. they
       won't get turned into true / false in the JS side of things), and
       reduces headaches for us all around.
    """
    header = "ID\tMD1\tMD2\n"
    simple_md = StringIO(header + "S1\t1.0\t2.0\n" + "S2\t3.0\t4.0")
    simple_df = read_metadata_file(simple_md)
    assert simple_df.dtypes[0] == "float64"
    assert simple_df.dtypes[1] == "float64"
    assert simple_df.at["S1", "MD1"] == 1.0
    assert simple_df.at["S2", "MD1"] == 3.0
    assert simple_df.at["S1", "MD2"] == 2.0
    assert simple_df.at["S2", "MD2"] == 4.0

    has_bool_md = StringIO(header + "S1\tTrue\t5\n" + "S2\tFalse\t6")
    has_bool_df = read_metadata_file(has_bool_md)
    # This should be an object, NOT a bool! This is because
    # read_metadata_file() explicitly converts bool columns to object columns
    # (containing strings).
    assert has_bool_df.dtypes[0] == "object"
    assert has_bool_df.dtypes[1] == "int64"
    assert has_bool_df.at["S1", "MD1"] == "True"
    assert has_bool_df.at["S2", "MD1"] == "False"
    assert has_bool_df.at["S1", "MD2"] == 5
    assert has_bool_df.at["S2", "MD2"] == 6

    one_bool_md = StringIO(
        header + "S1\tTrue\t5\n" + "S2\tWHAAAT\tMissing: Not provided"
    )
    one_bool_df = read_metadata_file(one_bool_md)
    assert one_bool_df.dtypes[0] == "object"
    assert one_bool_df.dtypes[1] == "object"
    assert one_bool_df.at["S1", "MD1"] == "True"
    assert one_bool_df.at["S2", "MD1"] == "WHAAAT"
    assert one_bool_df.at["S1", "MD2"] == "5"
    assert one_bool_df.at["S2", "MD2"] == "Missing: Not provided"
