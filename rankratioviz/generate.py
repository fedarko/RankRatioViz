#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Copyright (c) 2018--, rankratioviz development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
#
# Generates two JSON files: one for a rank plot and one for a sample
# scatterplot of log ratios.
#
# A lot of the code for processing input data in this file was based on code
# by Jamie Morton, some of which is now located in ipynb/Figure3.ipynb in
# https://github.com/knightlab-analyses/reference-frames.
#
# NOTE: For some reason, the sample plot JSON generated here differs somehow
# from the JSON generated by the notebook I was testing this with. Seems to
# just be an ordering issue, but a TODO is to write code that validates that
# that is the case (and it isn't actually messing up any of the data/metadata).
# ----------------------------------------------------------------------------

import json
import os
from shutil import copyfile, copytree
import pandas as pd
import altair as alt


def matchdf(df1, df2):
    """Filters both DataFrames to just the rows of their shared indices."""
    idx = set(df1.index) & set(df2.index)
    return df1.loc[idx], df2.loc[idx]


def process_input(ordination_file, biom_table, taxam=None):
    """Loads the ordination file, BIOM table, and optionally taxonomy data."""
    V = ordination_file.features
    U = ordination_file.samples
    table = biom_table.to_dataframe().to_dense().T
    # match
    table, V = matchdf(table.T, V)
    table, U = matchdf(table.T, U)

    if taxam is not None:
        # match and relabel
        matched_taxam, V = matchdf(taxam, V)
        if 'Taxon' in matched_taxam.columns:
            if 'Confidence' in matched_taxam.columns:
                # combine and replace
                matched_taxam_zip = zip(
                    matched_taxam.index,
                    matched_taxam.Taxon,
                    matched_taxam.Confidence
                )
                # Assign each taxon in the taxonomy metadata file a label that
                # includes its
                #   1) taxonomy information,
                #   2) confidence, and
                #   3) sequence
                labels = []
                for seq, taxon, confidence in matched_taxam_zip:
                    trimmed_conf = "|(" + str(confidence)[:4] + ")"
                    base_label = (str(taxon) + trimmed_conf).replace(' ', '')
                    labels.append(base_label + '|' + str(seq))

                matched_taxam["Taxon_"] = labels
                V.index = matched_taxam["Taxon_"].values
                table.columns = matched_taxam["Taxon_"].values
            else:
                # only taxa
                V.index = matched_taxam["Taxon"].values
                table.columns = matched_taxam["Taxon"].values

    return V, table


def gen_rank_plot(V, rank_col):
    """Generates altair.Chart object describing the rank plot.

    Arguments:

    V: feature ranks
    rank_col: the column index to use for getting the rank values from a taxon.

    Returns:

    altair.Chart object for the rank plot.
    """

    # Get stuff ready for the rank plot

    # coefs is a pandas Series whose values correspond to the actual ranks
    # associated with each taxon/metabolite.
    coefs = V[rank_col].sort_values()
    # x is just a range -- this can be used as a source of data in a pandas
    # DataFrame
    x = range(coefs.shape[0])

    # Set default classification of every taxon to "None"
    # (This value will be updated when a taxon is selected in the rank plot as
    # part of the numerator, denominator, or both parts of the current log
    # ratio.)
    classification = pd.Series(index=coefs.index).fillna("None")
    rank_data = pd.DataFrame({
        'x': x, 'coefs': coefs, "classification": classification
    })
    # NOTE: The default size value of mark_bar() causes an apparent offset in
    # the interval selection (we're not using that right now, except for the
    # .interactive() thing, though, so I don't think this is currently
    # relevant).
    #
    # Setting size to 1.0 fixes this; using mark_rule() also fixes this,
    # probably because the lines in rule charts are just lines with a width
    # of 1.0.
    rank_chart = alt.Chart(
            rank_data.reset_index(),
            title="Ranks"
    ).mark_bar().encode(
        x=alt.X('x', title="Features", type="quantitative"),
        y=alt.Y('coefs', title="Ranks", type="quantitative"),
        color=alt.Color(
            "classification",
            scale=alt.Scale(
                domain=["None", "Numerator", "Denominator", "Both"],
                range=["#e0e0e0", "#f00", "#00f", "#949"]
            )
        ),
        size=alt.value(1.0),
        tooltip=["x", "coefs", "classification", "index"]
    ).configure_axis(
        # Done in order to differentiate "None"-classification taxa from grid
        # lines (an imperfect solution to the problem mentioned in the NOTE
        # below)
        gridOpacity=0.35
    ).interactive()
    return rank_chart


def gen_sample_plot(table, metadata, category, palette='Set1'):
    """Generates altair.Chart object describing the sample scatterplot.

    Arguments:

    table: pandas DataFrame describing taxon abundances for each sample.
    metadata: pandas DataFrame describing metadata for each sample.

    Returns:

    altair.Chart object for the sample scatterplot.
    """

    # Since we don't bother setting a default log ratio, we set the balance for
    # every sample to NaN so that Altair will filter them out (producing an
    # empty scatterplot by default, which makes sense).
    balance = pd.Series(index=table.index).fillna(float('nan'))
    data = pd.DataFrame({'rankratioviz_balance': balance}, index=table.index)
    # At this point, "data" is a DataFrame with its index as sample IDs and
    # one column ("balance", which is solely NaNs).
    data = pd.merge(data, metadata[[category]], left_index=True,
                    right_index=True)
    # TODO note dropped samples from this merge (by comparing data with
    # metadata and table) and report them to user (#54).

    # Construct unified DataFrame, combining our "data" DataFrame with the
    # "table" variable (in order to associate each sample with its
    # corresponding abundances)
    sample_metadata_and_abundances = pd.merge(
        data, table, left_index=True, right_index=True
    )

    # "Reset the index" -- make the sample IDs a column (on the leftmost side)
    sample_metadata_and_abundances.reset_index(inplace=True)

    # Make note of the column names in the unified data frame.
    # This constructs a dictionary mapping the column names to their integer
    # indices (just the range of [0, m + t], where:
    #   m is the number of metadata columns
    #   t is the number of taxa/metabolites listed in the BIOM table
    # ). Similarly to smaa_i2sid above, we'll preserve this mapping in the
    # sample plot JSON.
    smaa_cols = sample_metadata_and_abundances.columns
    smaa_cn2si = {}
    int_smaa_col_names = [str(i) for i in range(len(smaa_cols))]
    for j in int_smaa_col_names:
        # (Altair doesn't seem to like accepting ints as column names, so we
        # mostly use the new column names as strings when we can.)
        smaa_cn2si[smaa_cols[int(j)]] = j

    # Now, we replace column names (which could include thousands of taxon
    # names) with just the integer indices from before.
    #
    # This saves *a lot* of space in the JSON file for the sample plot, since
    # each column name is referenced once for each sample (and
    # 50 samples * (~3000 taxonomy IDs ) * (~50 characters per ID)
    # comes out to 7.5 MB, which is an underestimate).
    sample_metadata_and_abundances.columns = int_smaa_col_names

    # Create sample plot in Altair.
    # If desired, we can make this interactive by adding .interactive() to the
    # alt.Chart declaration (but we don't do that currently since it makes
    # changing the scale of the chart smoother IIRC)
    sample_logratio_chart = alt.Chart(
        sample_metadata_and_abundances,
        title="Log Ratio of Abundances in Samples"
    ).mark_circle().encode(
        alt.X(smaa_cn2si[category], title=str(category)),
        alt.Y(smaa_cn2si["rankratioviz_balance"],
              title="log(Numerator / Denominator)"),
        color=alt.Color(
            smaa_cn2si[category],
            title=str(category),
            # This is a temporary measure. Eventually the type should be
            # user-configurable -- some of the metadata fields might actually
            # be nominal data, but many will likely be numeric (e.g. SCORAD for
            # dermatits). Exposing this to the user in the visualization
            # interface is probably the best option, for when arbitrary amounts
            # of metadata can be passed.
            type="nominal"
        ),
        tooltip=[smaa_cn2si["index"]])

    # Save JSON for sample plot (including the column-identifying dict from
    # earlier).
    sample_logratio_chart_json = sample_logratio_chart.to_dict()
    col_names_ds = "rankratioviz_col_names"
    sample_logratio_chart_json["datasets"][col_names_ds] = smaa_cn2si
    return sample_logratio_chart_json


def gen_visualization(V, processed_table, df_sample_metadata, category,
                      output_dir):
    """Creates a rankratioviz visualization. This function should be callable
       from both the QIIME 2 and standalone rankratioviz scripts.

       Returns:

       index_path: a path to the index.html file for the output visualization.
                   This is needed when calling q2templates.render().
    """
    rank_plot_chart = gen_rank_plot(V, 0)
    sample_plot_json = gen_sample_plot(processed_table, df_sample_metadata,
                                       category)
    os.makedirs(output_dir, exist_ok=True)
    # copy files for the visualization
    loc_ = os.path.dirname(os.path.realpath(__file__))
    # NOTE: We can just join loc_ with support_files/, since support_files/ is
    # located within the same directory as generate.py. Previously (when this
    # code was contained in q2/_method.py and scripts/_plot.py), I joined loc_
    # with .. and then with support_files since we had to first navigate up to
    # the directory containing generate.py and support_files/. Now, we don't
    # have to do that any more.
    support_files_loc = os.path.join(loc_, 'support_files')
    index_path = None
    for file_ in os.listdir(support_files_loc):
        if file_ != '.DS_Store':
            copy_func = copyfile
            # If we hit a directory in support_files/, just copy the entire
            # directory to our destination using shutil.copytree()
            if os.path.isdir(os.path.join(support_files_loc, file_)):
                copy_func = copytree
            copy_func(
                os.path.join(support_files_loc, file_),
                os.path.join(output_dir, file_)
            )
        if 'index.html' in file_:
            index_path = os.path.join(output_dir, file_)

    if index_path is None:
        # This should never happen -- assuming rankratioviz has been installed
        # fully, i.e. with a complete set of support_files/ -- but we handle it
        # here just in case.
        raise FileNotFoundError("Couldn't find index.html in support_files/")
    # write new files
    rank_plot_loc = os.path.join(output_dir, 'rank_plot.json')
    sample_plot_loc = os.path.join(output_dir, 'sample_logratio_plot.json')
    rank_plot_chart.save(rank_plot_loc)
    # For reference: https://stackoverflow.com/a/12309296
    with open(sample_plot_loc, "w") as jfile:
        json.dump(sample_plot_json, jfile)
    return index_path
