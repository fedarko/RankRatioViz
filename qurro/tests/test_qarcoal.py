#!/usr/bin/env python

from collections import namedtuple
import os

import biom
import numpy as np
import pandas as pd
import pytest
from q2_types.sample_data import SampleData
from qiime2 import Metadata
from qiime2.plugin.testing import TestPluginBase
from qurro.qarcoal import qarcoal, filter_and_join_taxonomy
from qurro.q2._type import LogRatios, LogRatiosDirFmt

MP_URL = "qurro/tests/input/moving_pictures"


class TestTypes(TestPluginBase):
    package = "qurro.tests"

    def test_qlr_semantic_type_registration(self):
        self.assertRegisteredSemanticType(LogRatios)

    def test_qlr_to_qlr_dir(self):
        self.assertSemanticTypeRegisteredToFormat(
            SampleData[LogRatios], LogRatiosDirFmt
        )


def _check_dataframe_equality(df1, df2):
    """Helper function to test whether two dataframes are equal.

    We are using this function instead of the inbuilt testing of dataframes
    to avoid any issues with sparse structures.
    """
    assert df1.shape == df2.shape

    # going to order columns and indices first
    df1 = df1[sorted(df1.columns)]
    df2 = df2[sorted(df2.columns)]

    df1 = df1.reindex(sorted(df1.index))
    df2 = df2.reindex(sorted(df2.index))

    assert list(df1.index) == list(df2.index)
    for col1, col2 in zip(df1.columns, df2.columns):
        assert col1 == col2
        np.testing.assert_equal(df1[col1].values, df2[col1].values)


@pytest.fixture(scope="module")
def get_mp_data():
    biom_url = os.path.join(MP_URL, "feature-table.biom")
    taxonomy_url = os.path.join(MP_URL, "taxonomy.tsv")

    table = biom.load_table(biom_url)
    taxonomy = pd.read_csv(taxonomy_url, sep="\t", index_col=0)
    data = namedtuple("Data", "table taxonomy")
    return data(table, taxonomy)


@pytest.fixture(scope="module")
def get_mp_results(get_mp_data):
    num = "g__Bacteroides"
    denom = "g__Streptococcus"
    q = qarcoal(get_mp_data.table, get_mp_data.taxonomy, num, denom)
    return q


@pytest.fixture(scope="module")
def get_qurro_mp_results():
    qurro_url = os.path.join(MP_URL, "qurro_bacteroides_streptococcus.tsv")
    results = pd.read_csv(qurro_url, sep="\t", index_col=0)
    # index: Sample ID
    # columns: Current_Log_Ratio, BodySite, BodySite
    return results


class TestQarcoalOutput:
    def test_type(self, get_mp_results):
        assert isinstance(get_mp_results, pd.DataFrame)

    def test_shape(self, get_mp_data, get_mp_results, get_qurro_mp_results):
        qurro_results = get_qurro_mp_results.dropna()
        nrow_qurro = qurro_results.shape[0]
        nrow_qarcoal = get_mp_results.shape[0]
        assert nrow_qurro == nrow_qarcoal

    def test_samples(self, get_mp_data, get_mp_results, get_qurro_mp_results):
        qurro_results = get_qurro_mp_results.dropna()
        samp_qurro = set(qurro_results.index)
        samp_qarcoal = set(get_mp_results.index)
        assert samp_qurro == samp_qarcoal

    def test_log_ratios_1(self, get_mp_results, get_qurro_mp_results):
        qurro_results = get_qurro_mp_results.dropna()
        qurro_results = qurro_results[["Current_Log_Ratio"]]
        qurro_results = qurro_results.sort_values(by="Current_Log_Ratio")
        qurro_results = qurro_results.to_numpy()

        qarcoal_results = get_mp_results[["log_ratio"]]
        qarcoal_results = qarcoal_results.sort_values(by="log_ratio")
        qarcoal_results = qarcoal_results.to_numpy()

        assert qarcoal_results - qurro_results == pytest.approx(0)


class TestErrors:
    def test_invalid_num(self, get_mp_data):
        num = "beyblade"
        denom = "Firm"
        with pytest.raises(ValueError) as excinfo:
            qarcoal(get_mp_data.table, get_mp_data.taxonomy, num, denom)
        num_err = "No feature(s) found matching numerator string!"
        assert num_err == str(excinfo.value)

    def test_invalid_denom(self, get_mp_data):
        num = "Firm"
        denom = "beyblade"
        with pytest.raises(ValueError) as excinfo:
            qarcoal(get_mp_data.table, get_mp_data.taxonomy, num, denom)
        denom_err = "No feature(s) found matching denominator string!"
        assert denom_err == str(excinfo.value)

    def test_both_invalid(self, get_mp_data):
        num = "beyblade"
        denom = "yugioh"
        with pytest.raises(ValueError) as excinfo:
            qarcoal(get_mp_data.table, get_mp_data.taxonomy, num, denom)
        both_err = (
            "No feature(s) found matching either numerator or "
            "denominator string!"
        )
        assert both_err == str(excinfo.value)

    def test_shared_features_disallowed(self, get_mp_data):
        num = "Firmicutes"
        denom = "Bacilli"
        with pytest.raises(ValueError) as excinfo:
            qarcoal(
                get_mp_data.table,
                get_mp_data.taxonomy,
                num,
                denom,
                allow_shared_features=False,
            )
        shared_err = "Shared features between num and denom!"
        assert shared_err == str(excinfo.value)

    def test_no_common_samples(self):
        """No samples with both numerator and denominator features.

         -----------------------------------------------
        |                    S0    S1    S2    S3    S4 |
        | F0/Charmander       0     1    10     0     0 |
        | F1/Charmeleon       0     2    15     0     0 |
        | F2/Charizard        0     4     7     0     0 |
        | F3/Bulbasaur        5     0     0     0     6 |
        | F4/Ivysaur          7     0     0     0     4 |
        | F5/Vensaur          9     0     0     0     2 |
         -----------------------------------------------
        """
        samps = ["S{}".format(i) for i in range(5)]
        feats = ["F{}".format(i) for i in range(6)]
        s0 = [0, 0, 0, 5, 7, 9]
        s1 = [1, 2, 4, 0, 0, 0]
        s2 = [10, 15, 7, 0, 0, 0]
        s3 = [0, 0, 0, 0, 0, 0]
        s4 = [0, 0, 0, 6, 4, 2]
        mat = np.matrix([s0, s1, s2, s3, s4]).T
        table = biom.table.Table(mat, feats, samps).to_dataframe()

        tax_labels = [
            "Charmander",
            "Charmeleon",
            "Charizard",
            "Bulbasaur",
            "Ivysaur",
            "Venusaur",
        ]
        confidence = ["0.99"] * 6
        taxonomy = pd.DataFrame([feats, tax_labels, confidence]).T
        taxonomy.columns = ["feature-id", "Taxon", "Confidence"]
        taxonomy.set_index("feature-id", inplace=True, drop=True)

        with pytest.raises(ValueError) as excinfo:
            filter_and_join_taxonomy(table, taxonomy, "Char", "saur")
        assert (
            "No samples contain both numerator and denominator features!"
            == str(excinfo.value)
        )

    def test_negative_counts(self):
        samps = ["S{}".format(i) for i in range(3)]
        feats = ["S{}".format(i) for i in range(4)]
        mat = [np.random.randint(1, 10) for i in range(12)]
        mat = np.reshape(mat, (4, 3))
        mat[0] = -1
        table = biom.table.Table(mat, feats, samps)

        tax_labels = ["AB", "BC", "CD", "DE"]
        confidence = ["0.99"] * 4
        taxonomy = pd.DataFrame([feats, tax_labels, confidence]).T
        taxonomy.columns = ["feature-id", "Taxon", "Confidence"]
        taxonomy.set_index("feature-id", inplace=True, drop=True)

        with pytest.raises(ValueError) as excinfo:
            qarcoal(table, taxonomy, "A", "C")
        assert "Feature table has negative counts!" == str(excinfo.value)


class TestOptionalParams:
    def test_shared_features_allowed(self, get_mp_data):
        num = "Firmicutes"
        denom = "Bacilli"
        qarcoal(
            get_mp_data.table,
            get_mp_data.taxonomy,
            num,
            denom,
            allow_shared_features=True,
        )

    def test_samples_to_use(self, get_mp_data):
        metadata_url = os.path.join(MP_URL, "sample-metadata.tsv")
        sample_metadata = pd.read_csv(
            metadata_url, sep="\t", index_col=0, skiprows=[1], header=0
        )
        gut_samples = sample_metadata[sample_metadata["BodySite"] == "gut"]
        num_gut_samples = gut_samples.shape[0]
        gut_samples = Metadata(gut_samples)

        num = "p__Bacteroidetes"
        denom = "p__Firmicutes"
        q = qarcoal(
            get_mp_data.table,
            get_mp_data.taxonomy,
            num,
            denom,
            samples_to_use=gut_samples,
        )
        assert q.shape[0] == num_gut_samples


class TestIrregularData:
    @pytest.fixture(scope="function")
    def get_testing_data(self):
        mat = [np.random.randint(1, 10) for x in range(30)]
        mat = np.reshape(mat, (6, 5))
        samps = ["S{}".format(i) for i in range(5)]
        feats = ["F{}".format(i) for i in range(6)]
        table = biom.table.Table(mat, feats, samps)
        table = table.to_dataframe()
        tax_labels = [
            "Bulbasaur",
            "Ivysaur",
            "Venusaur",
            "Charmander",
            "Charmeleon",
            "Charizard",
        ]
        confidence = ["0.99"] * 6
        taxonomy = pd.DataFrame([feats, tax_labels, confidence]).T
        taxonomy.columns = ["feature-id", "Taxon", "Confidence"]
        taxonomy.set_index("feature-id", inplace=True, drop=True)
        data = namedtuple("Data", "table taxonomy")
        return data(table, taxonomy)

    def _check_missing_features_dfs(self, table, taxonomy):
        """Auxillary function to test missing features

        test_taxonomy_missing_features and test_feat_table_missing_features
        are essentially the same code, only differing in whether a feature
        is removed from the table or the taxonomy.
        """
        num_df, denom_df = filter_and_join_taxonomy(
            table,
            taxonomy,
            "Char",
            "saur",
        )
        assert "F5" not in num_df.index

        num_features = ["F3", "F4"]
        denom_features = ["F0", "F1", "F2"]
        sample_order = ["S{}".format(i) for i in range(5)]

        table_num_taxon_filt = pd.DataFrame(table.loc[num_features])
        table_denom_taxon_filt = pd.DataFrame(table.loc[denom_features])

        num_df_taxon_filt = num_df.loc[num_features]
        denom_df_taxon_filt = denom_df.loc[denom_features]

        # set operations in Qarcoal change order of samples
        # want to make sure order is the same when comparing
        table_num_taxon_filt = table_num_taxon_filt[sample_order]
        table_denom_taxon_filt = table_denom_taxon_filt[sample_order]
        num_df_taxon_filt = num_df_taxon_filt[sample_order]
        denom_df_taxon_filt = denom_df_taxon_filt[sample_order]

        # test that num/denom df accurately extract values from table
        _check_dataframe_equality(
            table_num_taxon_filt,
            num_df_taxon_filt,
        )

        _check_dataframe_equality(
            table_denom_taxon_filt,
            denom_df_taxon_filt,
        )

    def test_taxonomy_missing_features(self, get_testing_data):
        """Taxonomy file missing features that are present in feature table"""
        table = get_testing_data.table
        taxonomy = get_testing_data.taxonomy
        taxonomy_miss = taxonomy.iloc[:-1, :]  # remove F5 from taxonomy
        self._check_missing_features_dfs(table, taxonomy_miss)

    def test_feat_table_missing_features(self, get_testing_data):
        """Feature table missing features that are present in taxonomy"""
        table = get_testing_data.table
        table = table.iloc[:-1, :]  # remove F5 from feature table
        self._check_missing_features_dfs(table, get_testing_data.taxonomy)

    def test_overlapping_columns(self, get_testing_data):
        """Feature table and taxonomy have overlapping column(s)

        This test is basically making sure that Qarcoal drops all columns
        except Taxon in the taxonomy table. If there are overlapping columns
        between the feature table and the taxonomy table (i.e. a sample named
        Confidence), want to ensure that the feature table columns are retained
        without causing Pandas join errors.
        """
        table = get_testing_data.table
        taxonomy = get_testing_data.taxonomy

        taxonomy["Overlap1"] = [np.random.randint(1, 10) for x in range(6)]
        table["Overlap1"] = [np.random.randint(1, 10) for x in range(6)]
        taxonomy["Overlap2"] = [np.random.randint(1, 10) for x in range(6)]
        table["Overlap2"] = [np.random.randint(1, 10) for x in range(6)]
        table = table.apply(lambda x: x.astype(np.float64))

        num_df, denom_df = filter_and_join_taxonomy(
            table,
            taxonomy,
            "Char",
            "saur",
        )

        num_features = ["F3", "F4", "F5"]
        denom_features = ["F0", "F1", "F2"]

        table_num_taxon_filt = table.loc[num_features]
        table_denom_taxon_filt = table.loc[denom_features]

        num_df_taxon_filt = num_df.loc[num_features]
        denom_df_taxon_filt = denom_df.loc[denom_features]

        # test that num/denom df accurately extract table values for
        # Overlap1 and Overlap2
        _check_dataframe_equality(
            table_num_taxon_filt,
            num_df_taxon_filt,
        )

        _check_dataframe_equality(
            table_denom_taxon_filt,
            denom_df_taxon_filt,
        )

    def test_taxon_as_sample_name(self, get_testing_data):
        """Feature table has sample called Taxon"""
        table = get_testing_data.table
        table["Taxon"] = [np.random.randint(1, 10) for x in range(6)]
        table["Taxon"] = table["Taxon"].astype(np.float64)

        num_df, denom_df = filter_and_join_taxonomy(
            table,
            get_testing_data.taxonomy,
            "Char",
            "saur",
        )

        # test that num/denom df accurately extract table values for Taxon
        num_features = ["F3", "F4", "F5"]
        denom_features = ["F0", "F1", "F2"]

        table_num_taxon_filt = table.loc[num_features]
        table_denom_taxon_filt = table.loc[denom_features]

        num_df_taxon_filt = num_df.loc[num_features]
        denom_df_taxon_filt = denom_df.loc[denom_features]

        _check_dataframe_equality(
            num_df_taxon_filt,
            table_num_taxon_filt,
        )

        _check_dataframe_equality(
            denom_df_taxon_filt,
            table_denom_taxon_filt,
        )

    def test_large_numbers(self):
        """Test large numbers on which Qurro fails.

        Qurro fails when |x| > 2^53 - 1 due to JS implementation.
        Make a sample feature table with large numbers:

           ----------------------------------- ** 53
          |                    S0    S1    S2 |
          | F0/Charmander     2.0   2.5   2.2 |
          | F1/Charmeleon     3.2   2.6   3.5 |
          | F2/Charizard      4.1   2.9   3.1 |
          | F3/Bulbasaur      6.2   5.2   3.0 |
          | F4/Ivysaur        4.3   2.1   2.2 |
          | F5/Venusaur       3.7   2.5   4.0 |
           -----------------------------------

        Num: Char
        Denom: saur

        Output should be (from WolframAlpha):

           -----------------
          |       log_ratio |
          | S0     -21.9188 |
          | S1     -30.9458 |
          | S2     -7.07556 |
           -----------------
        """
        samps = ["S{}".format(i) for i in range(3)]
        feats = ["F{}".format(i) for i in range(6)]
        s0 = [x ** 53 for x in (2.0, 3.2, 4.1, 6.2, 4.3, 3.7)]
        s1 = [x ** 53 for x in (2.5, 2.6, 2.9, 5.2, 2.1, 2.5)]
        s2 = [x ** 53 for x in (2.2, 3.5, 3.1, 3.0, 2.2, 4.0)]
        confidence = ["0.99"] * 6
        tax_labels = [
            "Charmander",
            "Charmeleon",
            "Charizard",
            "Bulbasaur",
            "Ivysaur",
            "Vensaur",
        ]
        mat = np.matrix([s0, s1, s2]).T
        table = biom.table.Table(mat, feats, samps)

        taxonomy = pd.DataFrame([feats, tax_labels, confidence]).T
        taxonomy.columns = ["feature-id", "Taxon", "Confidence"]
        taxonomy.set_index("feature-id", inplace=True, drop=True)

        q = qarcoal(
            table,
            taxonomy,
            "Char",
            "saur",
        )
        wolfram_alpha_vals = np.array([-21.9188, -30.9458, -7.07556])
        qarcoal_vals = q.sort_index()["log_ratio"].to_numpy()
        diff = wolfram_alpha_vals - qarcoal_vals

        # differences are ~ 10^-6
        assert diff == pytest.approx(0, abs=1e-5)
