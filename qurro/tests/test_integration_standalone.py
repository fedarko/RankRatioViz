from qurro.tests.testing_utilities import (
    run_integration_test,
    validate_sample_stats_test_sample_plot_json,
)


def test_byrd():
    """Tests Qurro's JSON generation on the Byrd et al. 2017 dataset.

    This is really a test to make sure that qurro can properly handle
    songbird output.
    """
    run_integration_test(
        "byrd",
        "byrd",
        "byrd_differentials.tsv",
        "byrd_skin_table.biom",
        "byrd_metadata.txt",
    )


def test_sleep_apnea():
    """Tests Qurro's JSON generation on a "sleep apnea" dataset.

    This is really a test to make sure that qurro can properly handle
    DEICODE output.
    """
    run_integration_test(
        "sleep_apnea",
        "sleep_apnea",
        "ordination.txt",
        "qiita_10422_table.biom",
        "qiita_10422_metadata.tsv",
        feature_metadata_name="taxonomy.tsv",
    )


def test_red_sea():
    """Tests Qurro's JSON generation on a dataset from a study of the Red
    Sea.

    This is really a test to make sure that qurro can properly handle
    this sort of unconventionally-named-feature data.
    """
    run_integration_test(
        "red_sea",
        "red_sea",
        "differentials.tsv",
        "redsea.biom",
        "redsea_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
    )


def test_sample_dropping_stats():
    """Tests Qurro's JSON generation on a dataset with weird sample
    metadata.

    The output from this test will be used in JS tests -- this verifies that
    both the python and JS parts of Qurro can handle weird metadata
    appropriately.
    """
    rank_json, sample_json, count_json = run_integration_test(
        "sample_stats_test",
        "sample_stats_test",
        "differentials.tsv",
        "sst.biom",
        "sample_metadata.txt",
        expected_unsupported_samples=1,
    )
    validate_sample_stats_test_sample_plot_json(sample_json)


def test_mackerel():
    """Tests Qurro's JSON generation on the mackerel dataset (Qiita Study ID
    11721).

    This is less of a test and more of just a way to ensure that we
    continuously update the mackerel demo whenever we update Qurro.
    """
    run_integration_test(
        "mackerel",
        "mackerel",
        "differentials.tsv",
        "feature-table.biom",
        "sample-metadata.tsv",
        feature_metadata_name="taxonomy.tsv",
        expected_unsupported_samples=1248,
    )
