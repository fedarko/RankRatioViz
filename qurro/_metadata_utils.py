#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Copyright (c) 2018--, Qurro development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# ----------------------------------------------------------------------------

import pandas as pd
import numpy as np
from io import StringIO
from ._df_utils import replace_nan


def get_q2_comment_lines(md_file_loc):
    """Returns a list of line numbers in the file that start with "#q2:".

    These lines should be skipped when parsing the file outside of Q2 (i.e.
    in pandas). I guess we could also ostensibly use these lines' types here
    eventually, but for now we just skip them.

    Notes:
     -The line numbers are 0-indexed (so they can easily be thrown in to
      pandas.read_csv() as the skiprows parameter)
     -This doesn't check check the first line of the file (assumed to be the
      header)
     -This stops checking lines once it gets to the first non-header line
      that doesn't start with "#q2:". Currently, "#q2:types" is the only Q2
      "comment directive" available, but ostensibly this could detect future
      Q2 comment directives.
     -This checks if md_file_loc is of type StringIO. If so, this will
      handle it properly (iterating over it directly); otherwise, this
      assumes that md_file_loc is an actual filename, and this will open
      it using open().
      (I realize that ideally this wouldn't have to do any type checking,
      but it's either this or do a bunch of weird refactoring to get my test
      code working.)
    """

    def iterate_over_file_obj_lines(file_obj):
        q2_lines = []
        line_num = 0
        for line in file_obj:
            # Don't check for a #q2: comment on the first line of the file,
            # since the first line (should) define the file header.
            if line_num > 0:
                if line.startswith("#q2:"):
                    q2_lines.append(line_num)
                else:
                    # We assume that all #q2: lines will occur at the start of
                    # the file. Once we've reached a line that doesn't start
                    # with "#q2:", we stop checking.
                    break
            line_num += 1
        return q2_lines

    if type(md_file_loc) == StringIO:
        q2_lines = iterate_over_file_obj_lines(md_file_loc)
        # HACK: Allow us to read through this StringIO again --
        # https://stackoverflow.com/a/27261215/10730311
        # Note that we're only ever bothering with StringIOs here during test
        # code, so this weirdness should be ignored during normal operation of
        # Qurro.
        md_file_loc.seek(0)
        return q2_lines
    else:
        with open(md_file_loc, "r") as md_file_obj:
            return iterate_over_file_obj_lines(md_file_obj)


def read_metadata_file(md_file_loc):
    """Reads in a metadata file using pandas.read_csv().

    This treats all metadata values (including the index column) as
    strings, due to the use of dtype=object.

    NOTE THAT THIS WILL CONVERT empty cells in the TSV file to
    np.NaN values in the output DataFrame -- this is done to be
    consistent with QIIME2's Metadata utilities. If you don't want
    NaNs in your DataFrame, just call qurro._df_utils.replace_nan()
    on the DataFrame you get from this function: e.g.
    metadata_df = replace_nan(read_metadata_file(...)). (You can also just
    call read_metadata_file_sane(), which will do this for you.)
    """
    q2_lines = get_q2_comment_lines(md_file_loc)
    metadata_df = pd.read_csv(
        md_file_loc,
        sep="\t",
        na_values=[""],
        keep_default_na=False,
        dtype=object,
        skiprows=q2_lines,
    )

    # Take care of leading/trailing whitespace
    for column in metadata_df.columns:
        # Strip surrounding whitespace from each value
        # This mimics how QIIME 2 ignores this whitespace
        metadata_df[column] = metadata_df[column].str.strip()
    # Sorta the opposite of replace_nan(). Find all of the ""s resulting from
    # removing values with just-whitespace, and convert them to NaNs.
    metadata_df.where(metadata_df != "", np.NaN, inplace=True)

    # If there are any NaNs in the first column (that will end up being the
    # index column), then the user supplied at least one empty ID
    # (remember that we just converted all ""s to NaNs).
    #
    # This is obviously terrible, so just raise an error (this sort of
    # situation also results in an error from qiime2.Metadata).
    if metadata_df[metadata_df.columns[0]].isna().any():
        raise ValueError("Empty ID found in metadata file.")

    # Instead of passing index_col=0 to pd.read_csv(), we delay setting the
    # first column as the index until after we've read in the metadata file.
    #
    # This is because, as of writing, pandas doesn't set the dtype of the
    # index_col (see https://stackoverflow.com/a/35058538/10730311 for a good
    # explanation) -- so if we don't delay setting the index column, then it
    # won't necessarily be read as an object dtype. This can have bad results
    # (e.g. the sample IDs start with 0s, and those 0s will be removed by
    # pandas).
    #
    # This workaround should address this.
    metadata_df.set_index(metadata_df.columns[0], inplace=True)
    return metadata_df


def read_metadata_file_sane(md_file_loc):
    """Convenience function for reading metadata non-intrusively.

    Basically, this just calls read_metadata_file() (also defined in this
    module), then calls replace_nan() on that (note: replacing NaNs with ""
    instead of None), then returns the result.

    If you're just looking in this module for an easy "read my metadata"
    function, you may prefer to use this function instead of
    read_metadata_file().
    """
    return replace_nan(read_metadata_file(md_file_loc), "")
