define(["display", "mocha", "chai", "testing_utilities"], function (
    display,
    mocha,
    chai,
    testing_utilities
) {
    // Just the output from the python "matching" integration test
    // prettier-ignore
    var rankPlotJSON = {"$schema": "https://vega.github.io/schema/vega-lite/v3.3.0.json", "autosize": {"resize": true}, "background": "#FFFFFF", "config": {"axis": {"gridColor": "#f2f2f2", "labelBound": true}, "mark": {"tooltip": null}, "view": {"height": 300, "width": 400}}, "data": {"name": "data-ceb3e53dd82dc2b785cc2ba76931c96b"}, "datasets": {"data-ceb3e53dd82dc2b785cc2ba76931c96b": [{"Feature ID": "Taxon1", "FeatureMetadata1": null, "FeatureMetadata2": null, "Intercept": 5.0, "Rank 1": 6.0, "Rank 2": 7.0, "Rank 3": 0.0, "Rank 4": 4.0, "qurro_classification": "None", "qurro_spc": 5.0}, {"Feature ID": "Taxon2", "FeatureMetadata1": null, "FeatureMetadata2": null, "Intercept": 1.0, "Rank 1": 2.0, "Rank 2": 3.0, "Rank 3": 0.0, "Rank 4": 4.0, "qurro_classification": "None", "qurro_spc": 5.0}, {"Feature ID": "Taxon3", "FeatureMetadata1": "Yeet", "FeatureMetadata2": "100", "Intercept": 4.0, "Rank 1": 5.0, "Rank 2": 6.0, "Rank 3": 0.0, "Rank 4": 4.0, "qurro_classification": "None", "qurro_spc": 6.0}, {"Feature ID": "Taxon4", "FeatureMetadata1": null, "FeatureMetadata2": null, "Intercept": 9.0, "Rank 1": 8.0, "Rank 2": 7.0, "Rank 3": 0.0, "Rank 4": 4.0, "qurro_classification": "None", "qurro_spc": 6.0}, {"Feature ID": "Taxon5", "FeatureMetadata1": "null", "FeatureMetadata2": "lol", "Intercept": 6.0, "Rank 1": 5.0, "Rank 2": 4.0, "Rank 3": 0.0, "Rank 4": 4.0, "qurro_classification": "None", "qurro_spc": 2.0}], "qurro_feature_metadata_ordering": ["FeatureMetadata1", "FeatureMetadata2"], "qurro_rank_ordering": ["Intercept", "Rank 1", "Rank 2", "Rank 3", "Rank 4"], "qurro_rank_type": "Differential"}, "encoding": {"color": {"field": "qurro_classification", "scale": {"domain": ["None", "Numerator", "Denominator", "Both"], "range": ["#e0e0e0", "#f00", "#00f", "#949"]}, "title": "Log-Ratio Classification", "type": "nominal"}, "tooltip": [{"field": "qurro_x", "title": "Current Ranking", "type": "quantitative"}, {"field": "qurro_classification", "title": "Log-Ratio Classification", "type": "nominal"}, {"field": "qurro_spc", "title": "Sample Presence Count", "type": "quantitative"}, {"field": "Feature ID", "type": "nominal"}, {"field": "FeatureMetadata1", "type": "nominal"}, {"field": "FeatureMetadata2", "type": "nominal"}, {"field": "Intercept", "type": "quantitative"}, {"field": "Rank 1", "type": "quantitative"}, {"field": "Rank 2", "type": "quantitative"}, {"field": "Rank 3", "type": "quantitative"}, {"field": "Rank 4", "type": "quantitative"}], "x": {"axis": {"labelAngle": 0, "ticks": false}, "field": "qurro_x", "scale": {"paddingInner": 0, "paddingOuter": 1, "rangeStep": 1}, "title": "Feature Rankings", "type": "ordinal"}, "y": {"field": "Intercept", "type": "quantitative"}}, "mark": "bar", "selection": {"selector005": {"bind": "scales", "encodings": ["x", "y"], "type": "interval"}}, "title": "Features", "transform": [{"sort": [{"field": "Intercept", "order": "ascending"}], "window": [{"as": "qurro_x", "op": "row_number"}]}]};
    // prettier-ignore
    var samplePlotJSON = {"$schema": "https://vega.github.io/schema/vega-lite/v3.3.0.json", "autosize": {"resize": true}, "background": "#FFFFFF", "config": {"axis": {"labelBound": true}, "mark": {"tooltip": null}, "range": {"category": {"scheme": "tableau10"}, "ramp": {"scheme": "blues"}}, "view": {"height": 300, "width": 400}}, "data": {"name": "data-17ad6d7eb8d11fdb67d65d9f4abd5654"}, "datasets": {"data-17ad6d7eb8d11fdb67d65d9f4abd5654": [{"Metadata1": "1", "Metadata2": "2", "Metadata3": "3", "Sample ID": "Sample1", "qurro_balance": null}, {"Metadata1": "4", "Metadata2": "5", "Metadata3": "6", "Sample ID": "Sample2", "qurro_balance": null}, {"Metadata1": "7", "Metadata2": "8", "Metadata3": "9", "Sample ID": "Sample3", "qurro_balance": null}, {"Metadata1": "13", "Metadata2": "14", "Metadata3": "15", "Sample ID": "Sample5", "qurro_balance": null}, {"Metadata1": "16", "Metadata2": "17", "Metadata3": "18", "Sample ID": "Sample6", "qurro_balance": null}, {"Metadata1": "19", "Metadata2": "20", "Metadata3": "21", "Sample ID": "Sample7", "qurro_balance": null}], "qurro_sample_metadata_fields": ["Metadata1", "Metadata2", "Metadata3", "Sample ID"]}, "encoding": {"color": {"field": "Metadata1", "type": "nominal"}, "tooltip": [{"field": "Sample ID", "type": "nominal"}, {"field": "qurro_balance", "type": "quantitative"}], "x": {"axis": {"labelAngle": -45}, "field": "Metadata1", "scale": {"zero": false}, "type": "nominal"}, "y": {"field": "qurro_balance", "scale": {"zero": false}, "title": "Current Natural Log-Ratio", "type": "quantitative"}}, "mark": {"type": "circle"}, "selection": {"selector006": {"bind": "scales", "encodings": ["x", "y"], "type": "interval"}}, "title": "Samples"};
    // prettier-ignore
    var countJSON = {"Taxon1": {"Sample2": 1.0, "Sample3": 2.0, "Sample5": 4.0, "Sample6": 5.0, "Sample7": 6.0}, "Taxon2": {"Sample1": 6.0, "Sample2": 5.0, "Sample3": 4.0, "Sample5": 2.0, "Sample6": 1.0}, "Taxon3": {"Sample1": 2.0, "Sample2": 3.0, "Sample3": 4.0, "Sample5": 4.0, "Sample6": 3.0, "Sample7": 2.0}, "Taxon4": {"Sample1": 1.0, "Sample2": 1.0, "Sample3": 1.0, "Sample5": 1.0, "Sample6": 1.0, "Sample7": 1.0}, "Taxon5": {"Sample3": 1.0, "Sample5": 2.0}};
    describe("Exporting sample plot data", function () {
        var rrv, dataName;
        beforeEach(async function () {
            rrv = testing_utilities.getNewRRVDisplay(
                rankPlotJSON,
                samplePlotJSON,
                countJSON
            );
            dataName = rrv.samplePlotJSON.data.name;
            await rrv.makePlots();
        });
        afterEach(async function () {
            await rrv.destroy(true, true, true);
        });
        var setAllToNull = function () {
            // set balances to null, mimicking the state of the JSON
            // before any features have been selected
            for (
                var i = 0;
                i < rrv.samplePlotJSON.datasets[dataName].length;
                i++
            ) {
                rrv.samplePlotJSON.datasets[dataName][i].qurro_balance = null;
            }
        };
        describe("'Exclude metadata fields' is false", function () {
            it("Works properly even when all samples' balances are null", function () {
                before(setAllToNull);
                var expectedTSV =
                    '"Sample ID"\tCurrent_Natural_Log_Ratio\tMetadata1\tMetadata1\n' +
                    "Sample1\tnull\t1\t1\n" +
                    "Sample2\tnull\t4\t4\n" +
                    "Sample3\tnull\t7\t7\n" +
                    "Sample5\tnull\t13\t13\n" +
                    "Sample6\tnull\t16\t16\n" +
                    "Sample7\tnull\t19\t19";
                var outputTSV = rrv.getSamplePlotData("Metadata1", "Metadata1");
                chai.assert.equal(expectedTSV, outputTSV);

                var expectedTSV2 =
                    '"Sample ID"\tCurrent_Natural_Log_Ratio\tMetadata1\t"Sample ID"\n' +
                    "Sample1\tnull\t1\tSample1\n" +
                    "Sample2\tnull\t4\tSample2\n" +
                    "Sample3\tnull\t7\tSample3\n" +
                    "Sample5\tnull\t13\tSample5\n" +
                    "Sample6\tnull\t16\tSample6\n" +
                    "Sample7\tnull\t19\tSample7";
                var outputTSV2 = rrv.getSamplePlotData(
                    "Metadata1",
                    "Sample ID"
                );
                chai.assert.equal(expectedTSV2, outputTSV2);
            });
            describe("Works properly when balances are directly set", function () {
                // Update sample plot balances directly.
                // Even samples with a "null" balance (i.e. not currently drawn
                // in the sample plot) are included in the exported data. Some
                // of the comments in the code claimed that these samples were
                // getting filtered out, but that is no longer the case.
                beforeEach(function () {
                    rrv.samplePlotJSON.datasets[dataName][0].qurro_balance = 1;
                    rrv.samplePlotJSON.datasets[
                        dataName
                    ][1].qurro_balance = null;
                    rrv.samplePlotJSON.datasets[dataName][2].qurro_balance = 3;
                    rrv.samplePlotJSON.datasets[
                        dataName
                    ][3].qurro_balance = null;
                    rrv.samplePlotJSON.datasets[
                        dataName
                    ][4].qurro_balance = 6.5;
                    rrv.samplePlotJSON.datasets[dataName][5].qurro_balance = 7;
                });
                it("Works properly when normal metadata categories used", function () {
                    var expectedTSV =
                        '"Sample ID"\tCurrent_Natural_Log_Ratio\tMetadata1\tMetadata3\n' +
                        "Sample1\t1\t1\t3\n" +
                        "Sample2\tnull\t4\t6\n" +
                        "Sample3\t3\t7\t9\n" +
                        "Sample5\tnull\t13\t15\n" +
                        "Sample6\t6.5\t16\t18\n" +
                        "Sample7\t7\t19\t21";
                    var outputTSV = rrv.getSamplePlotData(
                        "Metadata1",
                        "Metadata3"
                    );
                    chai.assert.equal(expectedTSV, outputTSV);
                });
                it("Works properly when sample ID is used", function () {
                    var expectedTSV =
                        '"Sample ID"\tCurrent_Natural_Log_Ratio\t"Sample ID"\t"Sample ID"\n' +
                        "Sample1\t1\tSample1\tSample1\n" +
                        "Sample2\tnull\tSample2\tSample2\n" +
                        "Sample3\t3\tSample3\tSample3\n" +
                        "Sample5\tnull\tSample5\tSample5\n" +
                        "Sample6\t6.5\tSample6\tSample6\n" +
                        "Sample7\t7\tSample7\tSample7";
                    var outputTSV = rrv.getSamplePlotData(
                        "Sample ID",
                        "Sample ID"
                    );
                    chai.assert.equal(expectedTSV, outputTSV);
                });
            });
            // TODO: Ideally we'd test this by selecting features, but the above
            // tests are good enough
            it(
                "Works properly when balances are set from user-based selection"
            );
        });
        describe("'Exclude metadata fields' is true (for merging log-ratios with sample metadata)", function () {
            beforeEach(function () {
                rrv.exclSMFieldsInExport = true;
            });
            it("Works properly even when all samples' balances are null", function () {
                before(setAllToNull);
                var expectedTSV =
                    '"Sample ID"\tCurrent_Natural_Log_Ratio\n' +
                    "Sample1\tnull\n" +
                    "Sample2\tnull\n" +
                    "Sample3\tnull\n" +
                    "Sample5\tnull\n" +
                    "Sample6\tnull\n" +
                    "Sample7\tnull";
                var outputTSV = rrv.getSamplePlotData("Metadata1", "Metadata1");
                chai.assert.equal(expectedTSV, outputTSV);

                // The selected x-axis / color fields really shouldn't change
                // anything, since they're excluded from the exported data :)
                var outputTSV2 = rrv.getSamplePlotData(
                    "Metadata1",
                    "Sample ID"
                );
                chai.assert.equal(expectedTSV, outputTSV2);
                var outputTSV3 = rrv.getSamplePlotData(
                    "Sample ID",
                    "Sample ID"
                );
                chai.assert.equal(expectedTSV, outputTSV3);
            });
            describe("Works properly when balances are directly set", function () {
                beforeEach(function () {
                    rrv.samplePlotJSON.datasets[dataName][0].qurro_balance = 1;
                    rrv.samplePlotJSON.datasets[
                        dataName
                    ][1].qurro_balance = null;
                    rrv.samplePlotJSON.datasets[dataName][2].qurro_balance = 3;
                    rrv.samplePlotJSON.datasets[
                        dataName
                    ][3].qurro_balance = null;
                    rrv.samplePlotJSON.datasets[
                        dataName
                    ][4].qurro_balance = 6.5;
                    rrv.samplePlotJSON.datasets[dataName][5].qurro_balance = 7;
                });
                it("Works properly, regardless of selected sample metadata fields", function () {
                    var expectedTSV =
                        '"Sample ID"\tCurrent_Natural_Log_Ratio\n' +
                        "Sample1\t1\n" +
                        "Sample2\tnull\n" +
                        "Sample3\t3\n" +
                        "Sample5\tnull\n" +
                        "Sample6\t6.5\n" +
                        "Sample7\t7";
                    var outputTSV = rrv.getSamplePlotData(
                        "Metadata1",
                        "Metadata3"
                    );
                    chai.assert.equal(expectedTSV, outputTSV);
                    var outputTSV2 = rrv.getSamplePlotData(
                        "Sample ID",
                        "Sample ID"
                    );
                    chai.assert.equal(expectedTSV, outputTSV2);
                });
            });
        });

        describe("Quoting TSV fields", function () {
            // Quick way to avoid writing out "display.RRVDisplay..." every
            // time we want to call that function
            qfunc = display.RRVDisplay.quoteTSVFieldIfNeeded;
            it("Doesn't modify inputs without whitespace or double-quotes", function () {
                var t1 = "abcdefg";
                chai.assert.equal(t1, qfunc(t1));
                var t2 = "ABC123xyz+-?!@#$%^&*){}|/<>.";
                chai.assert.equal(t2, qfunc(t2));
            });
            it("Quotes fields containing whitespace", function () {
                // Test types of whitespace characters
                var t1 = "abc defg";
                chai.assert.equal('"abc defg"', qfunc(t1));
                var t2 = "abc\tdefg";
                chai.assert.equal('"abc\tdefg"', qfunc(t2));
                var t3 = "abc\ndefg";
                chai.assert.equal('"abc\ndefg"', qfunc(t3));
                // Test leading / trailing whitespace
                var t4 = "   abcdefg";
                chai.assert.equal('"   abcdefg"', qfunc(t4));
                var t5 = "abcdefg   ";
                chai.assert.equal('"abcdefg   "', qfunc(t5));
                var t6 = "   abcdefg   ";
                chai.assert.equal('"   abcdefg   "', qfunc(t6));
                // Test various combinations of above
                var t7 = "  ab\ncd\tefg ";
                chai.assert.equal('"  ab\ncd\tefg "', qfunc(t7));
                var t8 = "a\tb\nc\rd\tefg\r";
                chai.assert.equal('"a\tb\nc\rd\tefg\r"', qfunc(t8));
            });
            it('Quotes fields containing " and replaces those "s', function () {
                var t1 = 'abc"defg';
                chai.assert.equal('"abc""defg"', qfunc(t1));
                var t2 = 'abcd"ef"g';
                chai.assert.equal('"abcd""ef""g"', qfunc(t2));
                var t3 = '"abcdefg"';
                chai.assert.equal('"""abcdefg"""', qfunc(t3));
            });
            it('Properly handles fields with both whitespace and "s', function () {
                var t1 = 'abc "def" g';
                chai.assert.equal('"abc ""def"" g"', qfunc(t1));
                var t2 = 'a"\t"b\nc\rd\tefg""\r';
                chai.assert.equal('"a""\t""b\nc\rd\tefg""""\r"', qfunc(t2));
                var t3 = '  ABC DEF\tG "what" ';
                chai.assert.equal('"  ABC DEF\tG ""what"" "', qfunc(t3));
            });
        });
    });
    describe("Exporting rank plot data", function () {
        var rrv, dataName;
        beforeEach(async function () {
            rrv = testing_utilities.getNewRRVDisplay(
                rankPlotJSON,
                samplePlotJSON,
                countJSON
            );
            dataName = rrv.rankPlotJSON.data.name;
            await rrv.makePlots();
        });
        afterEach(async function () {
            await rrv.destroy(true, true, true);
        });
        it("Works in simple feature / feature log-ratio case", async function () {
            var expectedTSV =
                '"Feature ID"\tLog_Ratio_Classification\n' +
                "Taxon3\tNumerator\n" +
                "Taxon4\tDenominator";

            rrv.newFeatureHigh = testing_utilities.getFeatureRow(rrv, "Taxon3");
            rrv.newFeatureLow = testing_utilities.getFeatureRow(rrv, "Taxon4");
            await rrv.regenerateFromClicking();
            var outputTSV = rrv.getRankPlotData();
            chai.assert.equal(expectedTSV, outputTSV);
        });
        it("Produces a TSV containing just a header if no feature selected", function () {
            chai.assert.equal(
                '"Feature ID"\tLog_Ratio_Classification',
                rrv.getRankPlotData()
            );
        });
        it("Works when multiple features selected in a side of the log-ratio", async function () {
            var expectedTSV =
                '"Feature ID"\tLog_Ratio_Classification\n' +
                "Taxon1\tDenominator\n" +
                "Taxon2\tDenominator\n" +
                "Taxon3\tBoth\n" +
                "Taxon4\tDenominator\n" +
                "Taxon5\tDenominator";
            // NOTE / TODO: this is derived from runFeatureFiltering() in
            // test_rrvdisplay.js. This code assumes that the topSearch
            // and botSearch default to FeatureID, and that the topSearchType
            // and botSearchType default to text. If these defaults change,
            // this test will almost certainly break.
            // Ideally, runFeatureFiltering() should be located in
            // testing_utilities, so that all of the JS tests can reuse it
            // without introducing a bunch of lines of redundant code.
            document.getElementById("topText").value = "3";
            document.getElementById("botText").value = "Taxon";
            await document.getElementById("multiFeatureButton").onclick();
            var outputTSV = rrv.getRankPlotData();
            chai.assert.equal(expectedTSV, outputTSV);
        });
    });
});
