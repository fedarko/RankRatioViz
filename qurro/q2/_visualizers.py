# ----------------------------------------------------------------------------
# Copyright (c) 2018--, Qurro development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# ----------------------------------------------------------------------------
import qiime2
import skbio
import pandas as pd
import biom
from .._rank_utils import rename_loadings
from ._visualizer_utils import create_q2_visualization


def differential_plot(
    output_dir: str,
    ranks: pd.DataFrame,
    table: biom.Table,
    sample_metadata: qiime2.Metadata,
    feature_metadata: qiime2.Metadata = None,
    extreme_feature_count: int = None,
    debug: bool = False,
) -> None:
    """Generates a Qurro visualization using differentials.

    (...Also, the reason the order of parameters here differs from
    qurro/scripts/_plot.py is that the first parameter has to be
    output_dir: str, per QIIME 2's plugin requirements.)
    """

    create_q2_visualization(
        output_dir,
        ranks,
        "Differential",
        table,
        sample_metadata,
        feature_metadata,
        extreme_feature_count,
        debug,
    )


def loading_plot(
    output_dir: str,
    ranks: skbio.OrdinationResults,
    table: biom.Table,
    sample_metadata: qiime2.Metadata,
    feature_metadata: qiime2.Metadata = None,
    extreme_feature_count: int = None,
    debug: bool = False,
) -> None:
    """Generates a Qurro visualization using feature loadings in a biplot."""

    create_q2_visualization(
        output_dir,
        rename_loadings(ranks.features),
        "Feature Loading",
        table,
        sample_metadata,
        feature_metadata,
        extreme_feature_count,
        debug,
    )
