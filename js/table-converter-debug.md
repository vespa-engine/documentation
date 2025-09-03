# Table Converter Script Debugging Guide

This guide explains how to check if the table-list-converter.js script is being loaded and working correctly when running the site locally.

## Visual Indicators

When the page loads, you should see two visual indicators:

1. **Script Loaded Indicator**: A green box will appear in the bottom-right corner of the page for 10 seconds, indicating that the script has been loaded.

2. **Table Conversion Status**: A panel will appear in the top-right corner showing the status of each table conversion:
   - Whether each table was found on the page
   - Whether each table was successfully converted
   - Buttons to retry conversion or close the status panel

## Console Debugging

If the visual indicators don't appear, you can check the browser's console for debugging information:

1. Open your browser's developer tools (F12 or right-click > Inspect)
2. Go to the Console tab
3. Look for messages starting with `[Table Converter]`
4. These messages will show if the script was loaded and any issues it encountered

## Manual Triggers

You can manually trigger various functions from the browser's console:

```javascript
// Check conversion status
TableConverter.checkStatus();

// Retry conversion of all tables
TableConverter.convertAll();

// Convert specific tables
TableConverter.convertRankFeatureTable();
TableConverter.convertNativeRankVariablesTable();
TableConverter.convertNativeRankParametersTable();

// Enable/disable debug logging
TableConverter.debug(true);  // Enable
TableConverter.debug(false); // Disable
```

## Troubleshooting

If the script is not loading or working correctly:

1. **Check the script path**: Make sure the script is being loaded from the correct path. The script should be loaded using `{{ site.baseurl }}/js/table-list-converter.js` in the HTML head.

2. **Rebuild without incremental flag**: The `--incremental` flag in Jekyll can sometimes cause issues with script loading. Try rebuilding without it:
   ```
   bundle exec jekyll serve --drafts --trace
   ```

3. **Force a full rebuild**:
   ```
   bundle exec jekyll clean
   bundle exec jekyll serve --incremental --drafts --trace
   ```

4. **Check for jQuery**: The script depends on jQuery. Make sure jQuery is loaded before the table converter script.

5. **Check for table markup**: The script looks for tables with specific IDs:
   - `#rank-feature-table`
   - `#nativerank-variables-table`
   - `#native-rank-parameters-table`

6. **Check for the trigger comment**: The script is only loaded if the page contains the comment `<!--table-to-list-->`.

## How It Works

The script is included in the HTML head with this conditional:

```html
{% if page.content contains '<!--table-to-list-->'%}
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="{{ site.baseurl }}/js/table-list-converter.js"></script>
{% endif %}
```

This means the script will only be loaded on pages that contain the `<!--table-to-list-->` comment in their content.