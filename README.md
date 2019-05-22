# rankratioviz
[![Build Status](https://travis-ci.org/fedarko/rankratioviz.svg?branch=master)](https://travis-ci.org/fedarko/rankratioviz) [![codecov](https://codecov.io/gh/fedarko/rankratioviz/branch/master/graph/badge.svg)](https://codecov.io/gh/fedarko/rankratioviz)

(Name subject to change.)

rankratioviz visualizes the output from a tool like
[songbird](https://github.com/biocore/songbird) or
[DEICODE](https://github.com/biocore/DEICODE). It facilitates viewing
a plot of __feature rankings__  alongside a plot showing the
__log ratios__ of selected features' abundances within samples.

rankratioviz can be used standalone (as a Python 3 script that generates a
folder containing a HTML/JS/CSS visualization) or as a
[QIIME 2](https://qiime2.org/) plugin (that generates a QZV file that can be
visualized at [view.qiime2.org](https://view.qiime2.org/) or by using
`qiime tools view`).

rankratioviz should work with most modern web browsers. Firefox or Chrome are
recommended.

rankratioviz is still being developed, so backwards-incompatible changes might
occur. If you have any questions, feel free to contact the development team at
[mfedarko@ucsd.edu](mailto:mfedarko@ucsd.edu).

## Screenshot and Demo

![Screenshot](https://github.com/fedarko/rankratioviz/blob/master/screenshots/redsea_data.png)

**This visualization (which uses some of the
[Red Sea metagenome data](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5315489/), with ranks generated by
[songbird](https://github.com/biocore/songbird/)) can be viewed online [here](https://view.qiime2.org/visualization/?type=html&src=https%3A%2F%2Fdl.dropbox.com%2Fs%2Fuxpiq53t14lp4t9%2Fredsea_20190520.qzv%3Fdl%3D1).**

## Installation and Usage

The following command will install the most up-to-date version of rankratioviz:

```
pip install git+https://github.com/fedarko/rankratioviz.git
```

A python version of at least 3.5 is required to use rankratioviz.

### Temporary Caveat

**Please make sure that your sample metadata fields do not contain any period or
square bracket characters (`.[]`).** This is due to Vega-Lite's special treatment
of these characters. (Eventually rankratioviz should be able to handle this
accordingly, but in the meantime this is a necessary fix.) See
[this issue](https://github.com/fedarko/rankratioviz/issues/66) for context.

### Integration with metabolomics feature metadata

If you have a GNPS feature metadata file (where each row in the file has a
`parent mass` and `RTConsensus` column), you can pass in the `-gnps`
(`--assume-gnps-feature-metadata`) command-line argument to rankratioviz'
standalone script to make rankratioviz understand the metadata file. **Please
note that this functionality is experimental**; furthermore, it is not yet
available in the QIIME 2 plugin version of rankratioviz.

### Tutorials

Examples of using rankratioviz (both inside and outside of QIIME 2) are
available in rankratioviz' example Jupyter notebooks, which are located
[here](https://github.com/fedarko/rankratioviz/tree/master/example_notebooks):
- [**`deicode_example.ipynb`**](https://github.com/fedarko/rankratioviz/blob/master/example_notebooks/DEICODE_sleep_apnea/deicode_example.ipynb)
  demonstrates using [DEICODE](https://github.com/biocore/DEICODE) and then using rankratioviz to visualize DEICODE's output.
- [**`songbird_example.ipynb`**](https://github.com/fedarko/rankratioviz/blob/master/example_notebooks/songbird_red_sea/songbird_example.ipynb)
  demonstrates using [songbird](https://github.com/biocore/songbird) and then using rankratioviz to visualize songbird's output.

### Interacting with a rankratioviz visualization
The two plots (one of feature rankings, and one of samples' log ratios)
in a rankratioviz visualization are linked [1]: when a change is made to the
selected features in a log ratio, both the rank plot and sample plot are
accordingly modified.

To elaborate on that: clicking on two features in the rank plot sets a new
numerator feature (determined from the first-clicked feature) and a
new denominator feature (determined from the second-clicked feature) for the
abundance log ratios in the sample plot.

You can also run textual queries over the various feature IDs in order to
construct more complicated log ratios (e.g. "the log ratio of the combined
abundances of all features that contain the text 'X' over the combined
abundances of all features that contain the text 'Y'").
Although this method doesn't require you to manually select features on the
rank plot, the rank plot is still updated to indicate the features used in the
log ratios.

## Acknowledgements

### Dependencies

Code files for the following projects are distributed within
`rankratioviz/support_file/vendor/`.
See the `dependency_licenses/` directory for copies of these software projects'
licenses (each of which includes a respective copyright notice).
- [Vega](https://vega.github.io/vega/)
- [Vega-Lite](https://vega.github.io/vega-lite/)
- [Vega-Embed](https://github.com/vega/vega-embed)
- [RequireJS](https://requirejs.org/)

The following software projects are required for rankratioviz's python code
to function, although they are not distributed with rankratioviz (and are
instead installed alongside rankratioviz).
- [Altair](https://altair-viz.github.io/)
- [biom-format](http://biom-format.org/)
- [click](https://palletsprojects.com/p/click/)
- [pandas](https://pandas.pydata.org/)
- [scikit-bio](http://scikit-bio.org/)

### Testing Dependencies

For python testing/style checking, rankratioviz uses
[pytest](https://docs.pytest.org/en/latest/),
[pytest-cov](https://github.com/pytest-dev/pytest-cov),
[flake8](http://flake8.pycqa.org/en/latest/), and
[black](https://github.com/ambv/black).

For JavaScript testing/style checking, rankratioviz uses
[Mocha](https://mochajs.org/), [Chai](https://www.chaijs.com/),
[mocha-headless-chrome](https://github.com/direct-adv-interfaces/mocha-headless-chrome),
[nyc](https://github.com/istanbuljs/nyc), [jshint](https://jshint.com/),
and [prettier](https://prettier.io/).

rankratioviz also uses [Travis-CI](https://travis-ci.org/) and
[Codecov](https://codecov.io/).

### Data Sources

The test data located in `rankratioviz/tests/input/byrd/` are from
[this repository](https://github.com/knightlab-analyses/reference-frames).
These data, in turn, originate from Byrd et al.'s 2017 study on atopic
dermatitis [2].

The test data located in `rankratioviz/tests/input/sleep_apnea/`
(and in `example_notebooks/DEICODE_sleep_apnea/input/`)
are from [this Qiita study](https://qiita.ucsd.edu/study/description/10422),
which is associated with Tripathi et al.'s 2018 study on sleep apnea [4].

The test data located in `rankratioviz/tests/input/moving_pictures/`
are from [the QIIME 2 moving pictures tutorial](https://docs.qiime2.org/2019.1/tutorials/moving-pictures/).
The `ordination.qza` file in this folder was computed based on the
[DEICODE moving pictures tutorial](https://library.qiime2.org/plugins/deicode/19/).
These data (sans the DEICODE ordination) are associated with Caporaso et al. 2011 [5].

Lastly, the data located in `rankratioviz/tests/input/red_sea`
(and in `example_notebooks/songbird_red_sea/input/`, and shown in the
screenshot above) were taken from songbird's GitHub repository in its
[`data/redsea/`](https://github.com/biocore/songbird/tree/master/data/redsea)
folder, and are associated with
[this paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5315489/) [3].

### Special Thanks

The design of rankratioviz was strongly inspired by
[EMPeror](https://github.com/biocore/emperor) and
[q2-emperor](https://github.com/qiime2/q2-emperor/), along with
[DEICODE](https://github.com/biocore/DEICODE). A big shoutout to
Yoshiki Vázquez-Baeza for his help in planning this project, as well as to
Cameron Martino for a ton of work on getting the code in a distributable state
(and making it work with QIIME 2). Thanks also to Jamie Morton, who wrote the
original code for producing rank and sample plots from which this is derived.

## References

[1] Becker, R. A. & Cleveland, W. S. (1987). Brushing scatterplots. _Technometrics, 29_(2), 127-142. (Section 4.1 in particular talks about linking visualizations.)

[2] Byrd, A. L., Deming, C., Cassidy, S. K., Harrison, O. J., Ng, W. I., Conlan, S., ... & NISC Comparative Sequencing Program. (2017). Staphylococcus aureus and Staphylococcus epidermidis strain diversity underlying pediatric atopic dermatitis. _Science translational medicine, 9_(397), eaal4651.

[3] Thompson, L. R., Williams, G. J., Haroon, M. F., Shibl, A., Larsen, P.,
Shorenstein, J., ... & Stingl, U. (2017). Metagenomic covariation along densely
sampled environmental gradients in the Red Sea. _The ISME journal, 11_(1), 138.

[4] Tripathi, A., Melnik, A. V., Xue, J., Poulsen, O., Meehan, M. J., Humphrey, G., ... & Haddad, G. (2018). Intermittent hypoxia and hypercapnia, a hallmark of obstructive sleep apnea, alters the gut microbiome and metabolome. _mSystems, 3_(3), e00020-18.

[5] Caporaso, J. G., Lauber, C. L., Costello, E. K., Berg-Lyons, D., Gonzalez, A., Stombaugh, J., ... & Gordon, J. I. (2011). Moving pictures of the human microbiome. _Genome biology, 12_(5), R50.

## License

This tool is licensed under the [BSD 3-clause license](https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_(%22BSD_License_2.0%22,_%22Revised_BSD_License%22,_%22New_BSD_License%22,_or_%22Modified_BSD_License%22)).
Our particular version of the license is based on [scikit-bio](https://github.com/biocore/scikit-bio)'s [license](https://github.com/biocore/scikit-bio/blob/master/COPYING.txt).
