import copy
from itertools import zip_longest
import os
from pytest import approx
from click.testing import CliRunner
from biom import load_table
from qiime2 import Artifact, Metadata
from qiime2.plugins import qurro as q2qurro
import qurro.scripts._plot as rrvp
from qurro._rank_utils import read_rank_file
from qurro._metadata_utils import read_metadata_file
from qurro._df_utils import (
    replace_nan,
    match_table_and_data,
    biom_table_to_sparse_df,
)
from qurro._json_utils import get_jsons


def run_integration_test(
    input_dir_name,
    output_dir_name,
    ranks_name,
    table_name,
    sample_metadata_name,
    feature_metadata_name=None,
    use_q2=False,
    q2_ranking_tool="songbird",
    expected_unsupported_samples=0,
    expected_unsupported_features=0,
    expect_all_unsupported_samples=False,
    q2_table_biom_format="BIOMV210Format",
    extreme_feature_count=None,
):
    """Runs qurro, and validates the output somewhat.

    Note that this is a pretty outdated function (as in, it doesn't support
    checking many of the corner cases/etc. that happen when running Qurro).
    The main purpose of this function is just checking at a high level that
    things look good, and that data is faithfully represented in the output
    main.js file.
    """

    in_dir = os.path.join("qurro", "tests", "input", input_dir_name)
    rloc = os.path.join(in_dir, ranks_name)
    tloc = os.path.join(in_dir, table_name)
    sloc = os.path.join(in_dir, sample_metadata_name)
    floc = None
    if feature_metadata_name is not None:
        floc = os.path.join(in_dir, feature_metadata_name)
    out_dir = os.path.join("docs", "demos", output_dir_name)

    rrv_qzv = result = None
    if use_q2:
        if q2_ranking_tool == "songbird":
            q2_action = q2qurro.actions.differential_plot
            q2_rank_type = "FeatureData[Differential]"
        elif q2_ranking_tool == "DEICODE":
            q2_action = q2qurro.actions.loading_plot
            q2_rank_type = "PCoAResults % Properties(['biplot'])"
        else:
            raise ValueError(
                "Unknown q2_ranking_tool: {}".format(q2_ranking_tool)
            )
        # Import all of these files as Q2 artifacts or metadata.
        rank_qza = Artifact.import_data(q2_rank_type, rloc)
        table_qza = Artifact.import_data(
            "FeatureTable[Frequency]", tloc, view_type=q2_table_biom_format
        )
        sample_metadata = Metadata.load(sloc)
        feature_metadata = None
        if floc is not None:
            feature_metadata = Metadata.load(floc)

        # Now that everything's imported, try running qurro
        rrv_qzv = q2_action(
            ranks=rank_qza,
            table=table_qza,
            sample_metadata=sample_metadata,
            feature_metadata=feature_metadata,
            extreme_feature_count=extreme_feature_count,
        )
        # Output the contents of the visualization to out_dir.
        rrv_qzv.visualization.export_data(out_dir)
    else:
        # Run qurro "standalone" -- i.e. outside of QIIME 2
        runner = CliRunner()
        args = [
            "--ranks",
            rloc,
            "--table",
            tloc,
            "--sample-metadata",
            sloc,
            "--output-dir",
            out_dir,
        ]
        if floc is not None:
            args += ["--feature-metadata", floc]
        if extreme_feature_count is not None:
            args += ["--extreme-feature-count", extreme_feature_count]
        result = runner.invoke(rrvp.plot, args)
        # Validate that the correct exit code and output were recorded
        validate_standalone_result(
            result,
            expected_unsupported_samples=expected_unsupported_samples,
            expect_all_unsupported_samples=expect_all_unsupported_samples,
            expected_unsupported_features=expected_unsupported_features,
        )
    # If we expected this test to fail due to invalid inputs, don't bother
    # doing any JSON validation.
    # (Input validity checking is done in generate.process_input(), before
    # any output files are created in generate.gen_visualization() -- so no
    # output should be created anyway in these cases.)
    if expect_all_unsupported_samples or expected_unsupported_features > 0:
        return None, None
    else:
        # Only validate JSONs if -x wasn't specified (i.e. the passed
        # extreme feature count is None)
        validate_jsons = extreme_feature_count is None
        rank_json, sample_json, count_json = validate_main_js(
            out_dir, rloc, tloc, sloc, validate_jsons=validate_jsons
        )
        return rank_json, sample_json, count_json


def validate_standalone_result(
    result,
    expected_unsupported_samples=0,
    expect_all_unsupported_samples=False,
    expected_unsupported_features=0,
):
    """Validates the result (exit code and output) of running rrv standalone.

    Parameters
    ----------
    result: click.testing.Result
       This is returned from click's CliRunner.invoke() method.

    expected_unsupported_samples: int
       The number of samples expected to be unsupported in the BIOM table.
       Defaults to 0 (i.e. all samples are expected to be supported).

    expect_all_unsupported_samples: bool
       Whether or not to expect *all* samples to be unsupported in the BIOM
       table. Defaults to False (i.e. at least one sample is expected to be
       supported). If this is set to True, expected_unsupported_samples will
       not be used.

    expected_unsupported_featuress: int
       The number of features expected to be unsupported in the BIOM table.
       Defaults to 0 (i.e. all features are expected to be supported).
    """
    # NOTE: we expect an error with unsupported feature(s) to take precedence
    # over an error with all unsupported samples. There isn't a super complex
    # reason for this aside from that being how I structured the order of
    # checks in qurro.generate.
    if expected_unsupported_features > 0:
        # The program should fail with a nonzero exit code (indicating some
        # sort of error).
        assert result.exit_code != 0
        assert type(result.exception) == ValueError
        word = "were"
        if expected_unsupported_features == 1:
            word = "was"
        expected_message = (
            "{} {} not present in the input BIOM "
            "table.".format(expected_unsupported_features, word)
        )
        # Checking .stderr didn't seem to work for me, so to check the text of
        # the ValueError we just use its .args property (which should contain
        # the message we passed when raising it)
        assert expected_message in result.exc_info[1].args[0]
    elif expect_all_unsupported_samples:
        assert result.exit_code != 0
        assert type(result.exception) == ValueError
        expected_message = (
            "No samples are shared between the sample metadata file and BIOM "
            "table."
        )
        assert expected_message == result.exc_info[1].args[0]
    else:
        # There shouldn't be any errors in the output!
        # *Maybe* a warning about unsupported samples, but we know that at
        # least one sample should be supported (so rrv can still work).
        assert result.exit_code == 0
        validate_samples_supported_output(
            result.output, expected_unsupported_samples
        )


def validate_main_js(out_dir, rloc, tloc, sloc, validate_jsons=True):
    """Takes care of extracting JSONs from main.js and validating them.

    Parameters
    ----------
    out_dir: str
        The output directory (containing the various "support files" of a
        qurro visualization, including main.js).

    rloc, tloc, sloc: str
        Paths to the ranks file (either DEICODE or songbird), BIOM table,
        and sample metadata file used as input to qurro.

    validate_jsons: bool
        If True (default), this calls validate_rank_plot_json() and
        validate_sample_plot_json(). If False, this will skip that step --
        this is useful for if the test leaves the JSONs in an unexpected
        state (e.g. with certain features or samples dropped out due to,
        say, the -x argument having been passed).
    """

    main_loc = os.path.join(out_dir, "main.js")
    rank_json, sample_json, count_json = get_jsons(main_loc)

    # Validate plot JSONs
    if validate_jsons:
        validate_rank_plot_json(tloc, sloc, rloc, rank_json)
        validate_sample_plot_json(tloc, sloc, sample_json, count_json)

    return rank_json, sample_json, count_json


def validate_samples_supported_output(output, expected_unsupported_samples):
    """Checks that the correct message has been based on BIOM sample support.

    Also, this function is pretty old (it assumes the only way samples will
    be dropped is from the sample metadata file -- not the other way around,
    which is allowed). It might be worth updating this in the future, but
    honestly some of the details in these integration tests are pretty old
    (and it'd be easier to mostly just use unit tests).

    Parameters
    ----------
    output: str
       All of the printed output from running qurro.
       This can be obtained as result.output, if result is the return value
       of click's CliRunner.invoke().

    expected_unsupported_samples: int
       The number of samples expected to be unsupported in the BIOM table.
       If 0, expects all samples to be supported.
    """
    if expected_unsupported_samples > 0:
        expected_msg = (
            "{} sample(s) in the sample metadata file were not present in the "
            "BIOM table.".format(expected_unsupported_samples)
        )
        assert expected_msg in output


def basic_vegalite_json_validation(json_obj):
    """Basic validations of Vega-Lite JSON objects go here."""

    assert json_obj["$schema"].startswith("https://vega.github.io/schema")
    assert json_obj["$schema"].endswith(".json")


def validate_rank_plot_json(
    biom_table_loc, metadata_loc, input_ranks_loc, rank_json
):
    """Ensure that the rank plot JSON makes sense."""

    # TODO check that feature metadata annotations were properly applied to the
    # features. Will need the feature metadata file location to be passed here

    ref_feature_ranks, ref_rank_type = read_rank_file(input_ranks_loc)

    # Very quick sanity check: make sure that the identified "rank type"
    # (Differential or Feature Loading) matches
    assert rank_json["datasets"]["qurro_rank_type"] == ref_rank_type

    # Load the table as a Sparse DF, and then match it up with the sample
    # metadata. This is needed in order to ensure that the table only describes
    # samples in the sample metadata.
    # (And the reason we do *that* is so that, when we're trying to figure out
    # if a feature is "empty," we can just compute the sum of that feature's
    # row in the table -- which we couldn't do if the table contained samples
    # that would be filtered out in Qurro.)
    table = biom_table_to_sparse_df(load_table(biom_table_loc))
    sample_metadata = read_metadata_file(metadata_loc)
    table, _ = match_table_and_data(table, ref_feature_ranks, sample_metadata)

    # Validate some basic properties of the plot
    # (This is all handled by Altair, so these property tests aren't
    # exhaustive; they're mainly intended to verify that a general plot
    # matching our specs is being created)
    assert rank_json["mark"] == "bar"
    assert rank_json["title"] == "Features"
    basic_vegalite_json_validation(rank_json)

    # Loop over every feature in the reference feature ranks. Check that each
    # feature's corresponding rank data in the rank plot JSON matches.
    rank_ordering = rank_json["datasets"]["qurro_rank_ordering"]
    rank_json_feature_data = get_data_from_plot_json(
        rank_json, id_field="Feature ID"
    )

    for ref_feature_id in ref_feature_ranks.index:
        # If this feature is empty, it should have been filtered!
        if sum(table.loc[ref_feature_id]) == 0:
            assert ref_feature_id not in rank_json_feature_data
            continue
        # ...If this feature isn't empty, though, it shouldn't have been
        # filtered. (We assume that the user didn't pass in -x in this test.)
        #
        # Check to make sure that this feature ID is actually in the rank plot
        # JSON
        assert ref_feature_id in rank_json_feature_data
        # Get the corresponding feature's ranking information stored in the
        # rank plot JSON
        json_feature_data = rank_json_feature_data[ref_feature_id]

        # Note that we allow for mismatches in ranking names between the
        # reference and JSON feature rank data -- instead, we compare based on
        # the *order* of the feature rankings (aka the order of the columns in
        # either the feature differentials or ordination feature loadings).
        # This is fine, because we may want to rename certain rankings' names
        # (e.g. the axes in DEICODE's feature loadings, which default to just
        # 0, 1, 2)
        for ref_ranking, json_ranking in zip_longest(
            ref_feature_ranks.columns, rank_ordering
        ):
            # We use pytest's approx class to get past floating point
            # imprecisions. Note that we just leave this at the default for
            # approx, so if this starts failing then adjusting the tolerances
            # in approx() might be needed.
            actual_rank_val = ref_feature_ranks[ref_ranking][ref_feature_id]
            assert actual_rank_val == approx(json_feature_data[json_ranking])


def validate_sample_plot_json(
    biom_table_loc, metadata_loc, sample_json, count_json
):
    assert sample_json["mark"] == {"type": "circle"}
    assert sample_json["title"] == "Samples"
    basic_vegalite_json_validation(sample_json)
    dn = sample_json["data"]["name"]

    # Assert that sample metadata fields are in alphabetical order, ignoring
    # case. As in Qurro's code, this solution for sorting this way is based on
    # this article:
    # https://www.afternerd.com/blog/python-sort-list/#sort-strings-case-insensitive
    sm_fields = sample_json["datasets"]["qurro_sample_metadata_fields"]
    assert sorted(sm_fields, key=str.lower) == sm_fields

    # Check that each sample's metadata in the sample plot JSON matches with
    # its actual metadata.
    # NOTE: here we make the assumption that all samples are non-empty.
    # If we start using integration test data with empty samples, then we'll
    # need to revise this function to do something akin to what
    # validate_rank_plot_json() does above to ensure that empty features are
    # filtered out.
    sample_metadata = replace_nan(read_metadata_file(metadata_loc))
    for sample in sample_json["datasets"][dn]:

        sample_id = sample["Sample ID"]

        for metadata_col in sample_metadata.columns:
            expected_md = sample_metadata.at[sample_id, metadata_col]
            actual_md = sample[metadata_col]

            try:
                # Either these values are equal, *or* this was a QIIME 2
                # integration test (in which case the metadata files were
                # loaded as qiime2.Metadata objects) and certain columns'
                # values have been treated as numeric (which is fine, but this
                # might result in some things like a value of 53 being
                # interpreted as a value of 53.0 to qiime2.Metadata -- this
                # isn't a problem, so if the first check of equality fails we
                # try a looser check using approx() and float().
                assert expected_md == actual_md or float(
                    expected_md
                ) == approx(float(actual_md))
            except AssertionError:
                # quick and dirty hack to actually give useful information when
                # something goes wrong
                print("PROBLEMATIC METADATA VALUE HERE")
                print(
                    expected_md, actual_md, type(expected_md), type(actual_md)
                )
                raise

        # Not really "metadata", but just as a sanity check verify that the
        # initial qurro_balance of each sample is null (aka None in
        # python) -- this ensures that no samples will show up when the
        # visualization is initially displayed, which is the intended behavior.
        assert sample["qurro_balance"] is None

    # Check that every entry (sample x feature) matches with the BIOM table.
    # If the BIOM table has, say, > 1 million entries, this might be excessive,
    # but the test data right now is small enough that this should be fine.
    table = load_table(biom_table_loc)

    # For each (ranked) feature...
    for feature_id in count_json:
        # For each sample, ensure that the count value in the JSON matches with
        # the count value in the BIOM table.
        for sample_id in count_json[feature_id]:
            actual_count = count_json[feature_id][sample_id]
            expected_count = table.get_value_by_ids(feature_id, sample_id)
            assert actual_count == expected_count


def get_data_from_plot_json(plot_json, id_field="Sample ID"):
    """Given a plot JSON dict, returns a dict where each key corresponds
    to another dict containing all metadata fields for that [sample /
    feature].

    This code is based on the procedure described here:
    https://stackoverflow.com/a/5236375/10730311
    """
    plot_json_copy = copy.deepcopy(plot_json)
    data = {}
    for datum in plot_json_copy["datasets"][plot_json_copy["data"]["name"]]:
        # The use of .pop() here means that we remove the ID field from the
        # datum. This prevents redundancy (i.e. "Sample ID" being provided
        # twice for each sample) in the output.
        datum_id = datum.pop(id_field)
        data[datum_id] = datum
    return data


def validate_sample_stats_test_sample_plot_json(sample_json):
    """This checks that the sample metadata for this test was perfectly read.

    This should already be guaranteed due to the Qurro python metadata tests
    and validate_sample_plot_json() being done during
    run_integration_test(), but we might as well be extra safe.
    """
    dn = sample_json["data"]["name"]
    for sample in sample_json["datasets"][dn]:
        if sample["Sample ID"] == "Sample1":
            assert sample["Metadata1"] == "1"
            assert sample["Metadata2"] == "2"
            assert sample["Metadata3"] == "NaN"
        elif sample["Sample ID"] == "Sample2":
            # These special values should be read as just normal strings
            assert sample["Metadata1"] == "Infinity"
            assert sample["Metadata2"] == "null"
            assert sample["Metadata3"] == "6"
        elif sample["Sample ID"] == "Sample3":
            assert sample["Metadata1"] == "7"
            assert sample["Metadata2"] == "8"
            # all-whitespace should evaluate to just an empty value ("", which
            # is represented in the output JSON as None --> null in JS)
            assert sample["Metadata3"] is None
        elif sample["Sample ID"] == "Sample5":
            assert sample["Metadata1"] == "13"
            assert sample["Metadata2"] == "'14'"
            # missing values should end up as Nones
            assert sample["Metadata3"] is None
        elif sample["Sample ID"] == "Sample6":
            assert sample["Metadata1"] == "Missing: not provided"
            assert sample["Metadata2"] == "17"
            assert sample["Metadata3"] == "18"
        elif sample["Sample ID"] == "Sample7":
            assert sample["Metadata1"] == "19"
            # surrounding whitespace should be stripped
            assert sample["Metadata2"] == "20"
            assert sample["Metadata3"] == "21"
        else:
            raise ValueError("Invalid sample ID found in S.S.T. JSON")
