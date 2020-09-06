define(["vega", "dom_utils", "mocha", "chai", "testing_utilities"], function (
    vega,
    dom_utils,
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

    describe("The RRVDisplay destructor (destroy())", function () {
        var rrv;
        beforeEach(async function () {
            rrv = testing_utilities.getNewRRVDisplay(
                rankPlotJSON,
                samplePlotJSON,
                countJSON
            );
            await rrv.makePlots();
        });

        // TODO: add tests that leaving certain args as false still lets
        // destroy() work partially?
        it("Properly clears DOM element bindings", function () {
            rrv.destroy(true, true, true);
            for (var i = 0; i < rrv.elementsWithOnClickBindings.length; i++) {
                chai.assert.isNull(
                    document.getElementById(rrv.elementsWithOnClickBindings[i])
                        .onclick
                );
            }
            for (var j = 0; j < rrv.elementsWithOnChangeBindings.length; j++) {
                chai.assert.isNull(
                    document.getElementById(rrv.elementsWithOnChangeBindings[j])
                        .onchange
                );
            }
        });
        it("Properly clears the #rankPlot and #samplePlot divs", function () {
            rrv.destroy(true, true, true);
            chai.assert.isEmpty(document.getElementById("rankPlot").innerHTML);
            chai.assert.isEmpty(
                document.getElementById("samplePlot").innerHTML
            );
        });
        it("Properly clears the ranking/metadata field <select>s", function () {
            rrv.destroy(true, true, true);
            chai.assert.isEmpty(document.getElementById("rankField").innerHTML);
            chai.assert.isEmpty(document.getElementById("topSearch").innerHTML);
            chai.assert.isEmpty(document.getElementById("botSearch").innerHTML);
            chai.assert.isEmpty(
                document.getElementById("xAxisField").innerHTML
            );
            chai.assert.isEmpty(
                document.getElementById("colorField").innerHTML
            );
        });
        it("Removes the 'qiimediscrete' (Classic QIIME Colors) color scheme", function () {
            rrv.destroy(true, true, true);
            chai.assert.isUndefined(vega.scheme("qiimediscrete"));
        });
        /* Warning: here be ugly, bulky code that I wrote in a hurry */
        it("Properly resets other UI elements to their defaults", async function () {
            // before calling rrv.destroy(), change a few other things
            // this way we can check that these modifications are reverted on
            // calling destroy()
            await document.getElementById("borderCheckbox").click();
            await document.getElementById("boxplotCheckbox").click();
            await document
                .getElementById("exclSMFieldsInExportCheckbox")
                .click();
            document.getElementById("topSearchType").value = "rank";
            document.getElementById("botSearchType").value = "rank";
            document.getElementById("topText").value = "Test top search text";
            document.getElementById("botText").value =
                "Test bottom search text";
            for (var i = 0; i < dom_utils.statDivs.length; i++) {
                document.getElementById(dom_utils.statDivs[i]).textContent =
                    "test lol";
                document
                    .getElementById(dom_utils.statDivs[i])
                    .classList.add("invisible");
            }
            document.getElementById("xAxisScale").value = "quantitative";
            await document.getElementById("xAxisScale").onchange();

            document.getElementById("colorScale").value = "quantitative";
            await document.getElementById("colorScale").onchange();

            document.getElementById("barSizeSlider").value = "3";
            await document.getElementById("barSizeSlider").onchange();

            await document.getElementById("fitBarSizeCheckbox").click();

            document
                .getElementById("commonFeatureWarning")
                .classList.remove("invisible");
            document
                .getElementById("barSizeWarning")
                .classList.remove("invisible");

            rrv.destroy(true, true, true);

            chai.assert.isFalse(
                document.getElementById("borderCheckbox").checked
            );
            chai.assert.isFalse(
                document.getElementById("boxplotCheckbox").checked
            );
            chai.assert.isFalse(
                document.getElementById("exclSMFieldsInExportCheckbox").checked
            );
            // Check that boxplot mode "disabled" elements were enabled
            chai.assert.isFalse(document.getElementById("colorField").disabled);
            chai.assert.isFalse(document.getElementById("colorScale").disabled);
            chai.assert.isFalse(
                document.getElementById("borderCheckbox").disabled
            );
            chai.assert.equal(
                "text",
                document.getElementById("topSearchType").value
            );
            chai.assert.equal(
                "text",
                document.getElementById("botSearchType").value
            );
            chai.assert.isEmpty(document.getElementById("topText").value);
            chai.assert.isEmpty(document.getElementById("botText").value);
            chai.assert.equal(
                "nominal",
                document.getElementById("xAxisScale").value
            );
            chai.assert.equal(
                "nominal",
                document.getElementById("colorScale").value
            );
            chai.assert.equal(
                "tableau10",
                document.getElementById("catColorScheme").value
            );
            chai.assert.equal(
                "blues",
                document.getElementById("quantColorScheme").value
            );
            chai.assert.equal(
                "1",
                document.getElementById("barSizeSlider").value
            );
            chai.assert.isFalse(
                document.getElementById("barSizeSlider").disabled
            );
            chai.assert.isFalse(
                document.getElementById("fitBarSizeCheckbox").checked
            );

            chai.assert.isTrue(
                document
                    .getElementById("barSizeWarning")
                    .classList.contains("invisible")
            );
            chai.assert.isTrue(
                document
                    .getElementById("commonFeatureWarning")
                    .classList.contains("invisible")
            );

            for (var s = 0; s < dom_utils.statDivs.length; s++) {
                chai.assert.isEmpty(
                    document.getElementById(dom_utils.statDivs[s]).textContent
                );
                chai.assert.isTrue(
                    document
                        .getElementById(dom_utils.statDivs[s])
                        .classList.contains("invisible")
                );
            }
            chai.assert.isEmpty(
                document.getElementById("rankFieldLabel").textContent
            );

            /* Check that tables are properly cleared -- otherwise this causes
             * some nasty errors from DataTables (see #235 for sordid context).
             * Solution based on https://stackoverflow.com/a/2161646/10730311.
             */
            chai.assert.isFalse(
                document.getElementById("topFeaturesDisplay").hasChildNodes()
            );
            chai.assert.isFalse(
                document.getElementById("botFeaturesDisplay").hasChildNodes()
            );
        });
    });
});
