from qurro.tests.testing_utilities import run_integration_test


def test_dropping_features():
    """Tests that Qurro raises an error when > 0 feature(s) are unsupported."""

    # Test that dropping 1 feature produces an error
    run_integration_test(
        "matching_test",
        "matching_test/dropped_feature",
        "differentials.tsv",
        "dropped_feature.biom",
        "sample_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
        expected_unsupported_features=1,
    )
    # Test that dropping 2 features produces an error
    run_integration_test(
        "matching_test",
        "matching_test/dropped_features",
        "differentials.tsv",
        "dropped_features.biom",
        "sample_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
        expected_unsupported_features=2,
    )


def test_dropping_all_samples():
    """Tests that Qurro raises an error when all samples are unsupported."""
    run_integration_test(
        "matching_test",
        "matching_test/all_samples_dropped",
        "differentials.tsv",
        "all_samples_dropped.biom",
        "sample_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
        expect_all_unsupported_samples=True,
    )


def test_dropping_all_samples_and_features():
    """Tests Qurro's behavior when > 0 feature(s) and all samples are unsupported.

    In particular, qurro should just throw an error about the
    feature(s) being unsupported -- the feature check should come before the
    sample check (not for any particular reason, that's just how I wrote the
    code).
    """
    run_integration_test(
        "matching_test",
        "matching_test/all_samples_and_one_feature_dropped",
        "differentials.tsv",
        "all_samples_and_one_feature_dropped.biom",
        "sample_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
        expect_all_unsupported_samples=True,
        expected_unsupported_features=1,
    )
    run_integration_test(
        "matching_test",
        "matching_test/all_samples_and_two_features_dropped",
        "differentials.tsv",
        "all_samples_and_two_features_dropped.biom",
        "sample_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
        expect_all_unsupported_samples=True,
        expected_unsupported_features=2,
    )


def test_feature_metadata_and_dropped_sample():
    """Tests the behavior of Qurro in matching sample metadata, feature
    metadata, ranks, and the BIOM table together.
    """

    rank_json, sample_json, count_json = run_integration_test(
        "matching_test",
        "matching_test",
        "differentials.tsv",
        "mt.biom",
        "sample_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
        expected_unsupported_samples=1,
    )

    data_name = rank_json["data"]["name"]

    # Check that feature metadata annotations were done correctly
    for feature in rank_json["datasets"][data_name]:
        txid = feature["Feature ID"]
        if feature["Feature ID"] == "Taxon3":
            assert feature["FeatureMetadata1"] == "Yeet"
            # this should be interpreted this as a string, since "lol" is in
            # the same column
            assert feature["FeatureMetadata2"] == "100"
        elif feature["Feature ID"] == "Taxon5":
            # This should be interpeted as a string, also
            assert feature["FeatureMetadata1"] == "null"
            assert feature["FeatureMetadata2"] == "lol"
        else:
            # Check that the other taxa haven't been annotated with any
            # metadata.
            assert feature["FeatureMetadata1"] is None
            assert feature["FeatureMetadata2"] is None

    # Assert that Sample4 was dropped from the "main" dataset of the plot
    data_name = sample_json["data"]["name"]
    for sample in sample_json["datasets"][data_name]:
        assert sample["Sample ID"] != "Sample4"

    for txid in count_json:
        # Assert that Sample4 was also dropped from the counts data in the JSON
        assert "Sample4" not in count_json[txid]
