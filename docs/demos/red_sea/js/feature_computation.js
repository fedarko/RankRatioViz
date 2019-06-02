define(function() {
    /* Converts a feature metadata field to a text-searchable type, if
     * possible.
     *
     * If the input is a string, returns the input unchanged.
     * If the input is a number, returns the input as a string.
     *     (This is useful if users want to search numbers as text -- when we
     *     add more sophisticated search methods in the future, this
     *     functionality should probably be removed.)
     * If the input is neither of those types, returns null to indicate that we
     * can't "search" the input.
     */
    function trySearchable(fmVal) {
        if (typeof fmVal === "string") {
            return fmVal;
        } else if (typeof fmVal === "number") {
            return String(fmVal);
        } else {
            return null;
        }
    }

    /* Given a list of feature "rows", a string of input text, and a feature
     * metadata field, returns a list of all features that contain that text in
     * the specified feature metadata field.
     *
     * Note that this can lead to some weird results if you're not careful --
     * e.g. just searching on "Staphylococcus" will include Staph phages in the
     * filtering (since their names contain the text "Staphylococcus").
     */
    function textFilterFeatures(
        featureRowList,
        inputText,
        featureMetadataField
    ) {
        var filteredFeatures = [];
        var currVal;
        for (var ti = 0; ti < featureRowList.length; ti++) {
            currVal = trySearchable(featureRowList[ti][featureMetadataField]);
            if (currVal === null) {
                continue;
            } else if (currVal.includes(inputText)) {
                filteredFeatures.push(featureRowList[ti]);
            }
        }
        return filteredFeatures;
    }

    /* Prepares an array of ranks, either from the input text or from a feature
     * metadata field.
     *
     * In rank searching, users can search for multiple ranks at once if they
     * separate them with a comma, a semicolon, or a space; and we rely on
     * these characters not being present within a taxonomic rank (as far as I
     * can tell, all standard formats use semicolons or commas as separators).
     *
     * The choice to consider spaces as a "separator" within taxonomic ranks
     * might be a bit idiosyncratic. We can change this in the future if
     * needed.
     */
    function textToRankArray(text) {
        if (typeof text !== "string") {
            return [];
        }
        var initialRankArray = text
            .trim()
            .replace(/[,;\s]/g, " ")
            .split(" ");
        // Filter out ""s caused by repeated commas or whitespace in the input.
        // Why we need this: "a b   c".split(" ") produces
        // ["a", "b", "", "", "c"] and we just want ["a", "b", "c"]
        return initialRankArray.filter(function(r) {
            return r !== "";
        });
    }

    /* Returns true if arrayA and arrayB share at least one element.
     *
     * The check is done via === ("strict equality" in JS).
     *
     * Since this returns as soon as a match is found, this should be pretty
     * efficient.
     */
    function existsIntersection(arrayA, arrayB) {
        for (var a = 0; a < arrayA.length; a++) {
            for (var b = 0; b < arrayB.length; b++) {
                if (arrayA[a] === arrayB[b]) {
                    // If we found a match, no need to keep checking.
                    return true;
                }
            }
        }
        return false;
    }

    /* Given a list of feature "rows", a string of input "ranks," and a feature
     * metadata field, returns a list of all features that contain a taxonomic
     * rank that matches a rank in the input.
     *
     * First, we throw the input text through textToRankArray() above to
     * get a list of taxonomic ranks in the input.
     *
     * Next, we go through the features one-by-one. Each feature's value for
     * the specified feature metadata field will be split up by semicolons
     * into an array. We then search for exact matches (not just
     * "does this contain the input text," like in textFilterFeatures(), but
     * "is this exactly equal to the input text?"), and return a list of
     * all features where at least one taxonomic rank matched the input
     * rank(s).
     */
    function rankFilterFeatures(
        featureRowList,
        inputText,
        featureMetadataField
    ) {
        var inputRankArray = textToRankArray(inputText);
        if (inputRankArray.length <= 0) {
            return [];
        }
        var ranksOfFeatureMetadata;
        var filteredFeatures = [];
        for (var ti = 0; ti < featureRowList.length; ti++) {
            // If the current feature metadata value is null / otherwise not
            // text-searchable, trySearchable() returns null (which will cause
            // textToRankArray() to return [], which will cause
            // existsIntersection() to return false quickly).
            ranksOfFeatureMetadata = textToRankArray(
                trySearchable(featureRowList[ti][featureMetadataField])
            );
            if (existsIntersection(ranksOfFeatureMetadata, inputRankArray)) {
                filteredFeatures.push(featureRowList[ti]);
            }
        }
        return filteredFeatures;
    }

    /* Returns list of feature data objects (in the rank plot JSON) based
     * on a match of a given feature metadata field (including Feature ID)
     * with the input text.
     *
     * If inputText is empty (i.e. its length is 0), this returns an empty
     * array.
     */
    function filterFeatures(
        rankPlotJSON,
        inputText,
        featureMetadataField,
        searchType
    ) {
        if (
            featureMetadataField !== "Feature ID" &&
            rankPlotJSON.datasets.qurro_feature_metadata_ordering.indexOf(
                featureMetadataField
            ) < 0
        ) {
            throw new Error("featureMetadataField not found in data");
        } else if (searchType !== "text" && searchType !== "rank") {
            throw new Error('searchType must be either "text" or "rank"');
        } else if (inputText.trim().length === 0) {
            return [];
        }

        var potentialFeatures = rankPlotJSON.datasets[rankPlotJSON.data.name];
        // We know search type has to be either "rank" or "text" since we
        // checked above
        if (searchType === "rank") {
            return rankFilterFeatures(
                potentialFeatures,
                inputText,
                featureMetadataField
            );
        } else {
            return textFilterFeatures(
                potentialFeatures,
                inputText,
                featureMetadataField
            );
        }
    }

    /* Vega-Lite doesn't filter out infinities (caused by taking log(0)
     * or of log(0)/log(0), etc.) by default. If left unchecked, this leads to
     * weird and not-useful charts due to the presence of infinities.
     *
     * To get around this, we preemptively set the balance for samples with an
     * abundance of <= 0 in either the top or bottom of the log ratio as NaN.
     *
     * (Vega-Lite does filter out NaNs and nulls if the invalidValues config
     * property is true [which is default]).
     */
    function computeBalance(topValue, botValue) {
        if (typeof topValue !== "number" || typeof botValue !== "number") {
            throw new Error(
                "computeBalance() called with non-numerical input(s)"
            );
        }
        if (topValue <= 0 || botValue <= 0) {
            return NaN;
        }
        return Math.log(topValue) - Math.log(botValue);
    }
    return {
        filterFeatures: filterFeatures,
        computeBalance: computeBalance,
        textToRankArray: textToRankArray,
        existsIntersection: existsIntersection,
        trySearchable: trySearchable
    };
});
