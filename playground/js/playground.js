// Copyright Vespa.ai. All rights reserved.

contexts = {
    VIEW: "view",
    EDIT: "edit",
    SETUP: "setup"
};

var show_setup = false;
var setup = { "f": [] };
var results = { "f": [] };
var variables = new Map();
var selected = null;
var converter = new showdown.Converter();
var context = contexts.VIEW;
var currentTheme = localStorage.getItem('theme') || null; // Will be set based on system preference
// unique id counter for frames so D3 can track DOM nodes across reorders
var frame_uid = 0;

///////////////////////////////////////////////////////////////////////////////
// Notifications
///////////////////////////////////////////////////////////////////////////////

function show_notification(message, type = 'info', duration = 3000) {
    // Remove any existing notifications
    d3.selectAll('.notification').remove();
    
    // Create notification element
    var notification = d3.select('body')
        .append('div')
        .attr('class', 'notification ' + type)
        .style('opacity', '0')
        .html(message);
    
    // Fade in
    notification
        .transition()
        .duration(300)
        .style('opacity', '1');
    
    // Automatically fade out after duration
    setTimeout(function() {
        notification
            .transition()
            .duration(300)
            .style('opacity', '0')
            .on('end', function() {
                notification.remove();
            });
    }, duration);
}

///////////////////////////////////////////////////////////////////////////////
// Operations and UI
///////////////////////////////////////////////////////////////////////////////

var operations = {

    ////////////////////////////////////////////////////////////
    // Comments
    "c" : {
        "params" : {
            "t" : ""  // text of comment
        },
        "setup_ui" : function(param, element, header, content, frame_index, controls) {
            // For comments: header is a side icon container; ensure aria-label for accessibility
            header.attr("aria-label", "Edit comment");
            // Use controls container for buttons when provided. Clear any existing controls to avoid duplicates.
            if (controls) {
                controls.html("");
                controls.append("div").attr("class", "block right");
            } else {
                clear(header);
                header.append("div").attr("class", "block header-empty").html("");
            }
            var buttonArea = controls ? controls.select(".block.right") : header.append("div").attr("class", "block right");
            add_setup_ui_buttons(buttonArea);

            clear(content);
            add_table(content);
            add_textarea_field(content, "Comment", "", 3, 100, param["t"], true);
            add_save_cancel_field(content);
        },
        "result_ui" : function(result, element, header, content, frame_index, controls) {
            // For comments: header is a side icon container; ensure aria-label for accessibility
            header.attr("aria-label", "Comment");
            // Use controls container for buttons when provided. Clear any existing controls to avoid duplicates.
            if (controls) {
                controls.html("");
                controls.append("div").attr("class", "block right");
            } else {
                // Ensure header is empty and available as fallback
                clear(header);
                header.append("div").attr("class", "block header-empty").html("");
            }

            // Render result buttons into the controls container if present, otherwise into header
            var buttonArea = controls ? controls.select(".block.right") : header.append("div").attr("class", "block right");
            add_result_ui_buttons(buttonArea, frame_index);

            clear(content);
            content.html(result.get("t"));
        },
        "save" : function(param, element) {
            if (element.select("textarea").node() != null) {
                param["t"] = element.select("textarea").property("value").trim();
            }
        },
    },

    ////////////////////////////////////////////////////////////
    // Expressions
    "e" : {
        "params" : {
            "n" : "",  // name
            "e" : ""   // expression
        },
        "setup_ui" : function(param, element, header, content, frame_index) {
            clear(header);
            header.append("div").attr("class", "block").html(icon_code() + '<span class="visually-hidden">Edit expression</span>');
            add_setup_ui_buttons(header.append("div").attr("class", "block right"));

            clear(content);
            add_table(content);
            add_input_field(content, "Name", "expression_name", param["n"], true, "Only required if using in other expressions");
            add_textarea_field(content, "Expression", "expression_expression", 3, 65, param["e"], false);
            add_save_cancel_field(content);
        },
        "result_ui" : function(result, element, header, content, frame_index) {
            // place icon + accessible label
            clear(header);
            header.append("div").attr("class", "block").html(icon_code() + '<span class="visually-hidden">Expression</span>');
            clear(content);
            if (result.size == 0) {
                content.html("Not executed yet...");
                return;
            }

            var headerLeft = "Expression";
            if (result.has("n") && result.get("n").length > 0) {
                headerLeft = "<b>" + result.get("n") + "</b>";
            }
            if (result.has("executing") && result.get("executing") == true) {
                headerLeft += " <i>(awaiting result)</i>";
            }

            clear(header);
            // headerLeft may contain short name and status; show name visibly next to icon
            var visibleName = headerLeft.replace(/<[^>]*>?/gm, '');
            header.append("div").attr("class", "block").html(icon_code() + '<span class="frame-name">' + visibleName + '</span>');
            var button_area = header.append("div").attr("class", "block right");
            add_expression_result_ui_buttons(button_area, frame_index);
            add_result_ui_buttons(button_area, frame_index);

            if (result.has("error")) {
                content.html("");
                var table = content.append("table");
                if (result.has("e") && result.get("e").length > 0) {
                    var row = table.append("tr")
                    row.append("td").attr("class", "label").html("Expression");
                    row.append("td").attr("class", "code").html(replace_html_code(result.get("e")));
                }
                var row = table.append("tr")
                row.append("td").attr("class", "label").html("Error");
                row.append("td").append("div").attr("class", "error").html(replace_html_code(result.get("error")));

            } else {
                var data = result.get("result");
                if (typeof data === "object") {
                    // Create a container for all tensor cards
                    var tensorContainer = content.append("div").attr("class", "tensor-section");
                    
                    // Get the values we need
                    var value = data["value"];
                    if (data["type"] !== null && data["type"].includes("tensor")) {
                        value = data["value"]["literal"];
                    }
                    
                    // Expression row
                    if (result.has("e") && result.get("e").length > 0) {
                        var expressionRow = tensorContainer.append("div").attr("class", "tensor-row");
                        expressionRow.append("div").attr("class", "tensor-label").html("Expression:");
                        var expressionValue = expressionRow.append("div").attr("class", "tensor-value");
                        expressionValue.html(replace_html_code(result.get("e")));
                        
                        // Add copy icon to the right of the field
                        expressionRow.append("span")
                            .attr("class", "tensor-clipboard copy-button-align")
                            .html(icon_replicate())
                            .on("click", function() { 
                                copy_to_clipboard(result.get("e")); 
                                event.stopPropagation(); 
                            });
                    }
                    
                    // Type row
                    if (result.has("type") && result.get("type").length > 0) {
                        var typeRow = tensorContainer.append("div").attr("class", "tensor-row");
                        typeRow.append("div").attr("class", "tensor-label").html("Type:");
                        var typeValue = typeRow.append("div").attr("class", "tensor-value");
                        typeValue.html(replace_html_code(result.get("type")));
                    }
                    
                    // Check if value should be shown based on the 'same' parameter in the response
                    const shouldShowValue = data["same"] !== true;
                    
                    if (shouldShowValue) {
                        // Value row - only show if different from expression
                        var valueRow = tensorContainer.append("div").attr("class", "tensor-row");
                        valueRow.append("div").attr("class", "tensor-label").html("Value:");
                        var valueContent = valueRow.append("div").attr("class", "tensor-value tensor-value-single-line");
                        
                        // Add input with value
                        valueContent.append("pre")
                            .attr("style", "margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;")
                            .text(value);
                        
                        // Add copy icon to the right of the field
                        valueRow.append("span")
                            .attr("class", "tensor-clipboard copy-button-align")
                            .html(icon_replicate())
                            .on("click", function(event) { 
                                copy_to_clipboard(value); 
                                event.stopPropagation(); 
                            });
                    }

                    // Table row - with empty space for label to align with other rows
                    var tableRow = tensorContainer.append("div").attr("class", "tensor-row");
                    tableRow.append("div").attr("class", "tensor-label").html("");
                    var tableContent = tableRow.append("div").attr("style", "margin-top: 4px; width: 100%;");
                    draw_table(tableContent, data);
                    
                    // Add execution trace section (previously steps)
                    const primitive = "Primitive representation:\n" + result.get("primitive");
                    const steps = "Steps:\n" + JSON.stringify(JSON.parse(result.get("steps")), null, 2);
                    var debugContainer = content.append("div").attr("class", "debug-info-container").attr("id", "steps_" + frame_index);
                    
                    if (!result.has("show_details") || result.get("show_details") == false) {
                        debugContainer.attr("hidden", true);
                    }
                    
                    var traceHeader = debugContainer.append("div").attr("class", "tensor-row");
                    traceHeader.append("div").attr("class", "tensor-label").html("Execution Trace:");
                    debugContainer.append("textarea")
                        .attr("rows", steps.split("\n").length + 2)
                        .attr("class", "debug-info-text")
                        .attr("style", "width: 100%; margin-top: 4px;")
                        .text(primitive + "\n\n" + steps);
                } else {
                    content.html(data);
                }
            }

        },
        "save" : function(param, element) {
            if (element.select(".expression_name").node() != null) {
                param["n"] = get_input_field_value(element, "expression_name");
                param["e"] = get_textarea_field_value(element, "expression_expression");
            }
        },
    }
}

function replace_html_code(str) {
    return str.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function has_error(response, result) {
    result.delete("error");
    if (response == null) {
        result.set("error", "Did not receive a response.")
        return true;
    } else if ("error" in response) {
        result.set("error", response["error"])
        return true;
    }
    return false;
}

function clear(root) {
    root.html("");
}

function add_table(root) {
    root.append("table");
}

function add_label_field(root, label) {
    root = root.select("table");
    var field = root.append("tr");
    field.append("td")
        .attr("colspan", "3")
        .attr("class", "header")
        .html(label);
}

function add_input_field(root, label, classname, value, focus, helptext) {
    root = root.select("table");
    var field = root.append("tr");
    field.append("td").html(label);
    field.append("td")
        .attr("class", classname)
        .append("input")
            .attr("value", value)
            .attr("size", "50");
    field.append("td").html("<i>" + (helptext == null ? "" : helptext) + "</i>");
    if (focus) {
        field.select("input").node().select();
    }
}

function add_textarea_field(root, label, classname, rows, cols, value, focus, helptext) {
    root = root.select("table");
    var field = root.append("tr");
    field.append("td").html(label);
    field.append("td")
        .attr("class", classname)
        .append("textarea")
            .attr("rows", rows)
            .attr("cols", cols)
            .text(value);
    field.append("td").html("<i>" + (helptext == null ? "" : helptext) + "</i>");
    if (focus) {
        field.select("textarea").node().select();
    }
}

function add_save_cancel_field(root) {
    var row = root.select("table").append("tr");
    row.append("td").attr("class", "label");
    var cell = row.append("td");

    var saveButton = cell.append("a").attr("href", "#").attr("class","header tooltip save-button")
        .html(icon_check() + " Save and execute (ctrl + enter)" + '<span class="tooltip-text">Save changes and execute expression</span>')
        .on("click", function(event) { execute_selected(); event.preventDefault(); });
    var cancelButton = cell.append("a").attr("href", "#").attr("class","header tooltip cancel-button")
        .attr("style","margin-left: 80px").html(icon_exit() + " Cancel (escape)" + '<span class="tooltip-text">Cancel editing</span>')
        .on("click", function(event) { document.activeElement.blur(); exit_edit_selected(); event.preventDefault(); });

    // Check if we're in an expression context by looking for the expression textarea
    var expressionTextarea = root.select(".expression_expression textarea");
    if (!expressionTextarea.empty()) {
        // disable save button if expression is empty (causes ugly errors from backend)
        function updateButtonStates() {
            var value = get_textarea_field_value(root, "expression_expression");
            var isEmpty = value === "";

            saveButton.classed("disabled", isEmpty);
        }

        // Initial check
        updateButtonStates();

        // Add event listener to check for changes
        expressionTextarea.on("input", updateButtonStates);
    }
}

function add_setup_ui_buttons(root) {
    root.append("a").attr("href", "#").attr("class","header tooltip").html(icon_cancel() + '<span class="tooltip-text">Cancel editing</span>')
        .on("click", function(event) { document.activeElement.blur(); exit_edit_selected(); event.preventDefault(); });
}

function addActionButton(root, iconFn, actionFn, frameIndex, actionName, tooltipText) {
    root.append("a")
        .attr("href", "#")
        .attr("class", "header tooltip")
        .html(iconFn() + `<span class="tooltip-text">${tooltipText}</span>`)
        .on("click", function(event) {
            // Only allow actions if not in edit mode
            if (context !== contexts.EDIT) {
                actionFn(frameIndex);
            } else {
                show_notification(`Cannot ${actionName} while in edit mode. Finish editing first.`, "warning");
            }
            event.stopPropagation();
            event.preventDefault();
        });
}

function add_result_ui_buttons(root, frame_index) {
    addActionButton(root, icon_up, move_frame_up, frame_index, "move frames", "Move frame up");
    addActionButton(root, icon_down, move_frame_down, frame_index, "move frames", "Move frame down");
    addActionButton(root, icon_cross, remove_frame, frame_index, "remove frames", "Remove this frame");
}

function add_expression_result_ui_buttons(root, frame_index) {
    root.append("a").attr("href", "#").attr("class","header header-space tooltip").html(icon_hierarchy() + '<span class="tooltip-text">Show execution trace</span>')
        .on("click", function(event) { show_details(frame_index); event.stopPropagation(); event.preventDefault(); });
}

function get_input_field_value(root, classname) {
    return root.select("." + classname).select("input").property("value").trim();
}

function get_textarea_field_value(root, classname) {
    return root.select("." + classname).select("textarea").property("value").trim();
}

function get_select_field_value(root, classname) {
    return root.select("." + classname).select("select").property("value").trim();
}

function draw_table(element, variable) {
    if (variable === null || typeof variable !== "object") {
        return;
    }

    var type = variable["type"];
    var columns = new Set();
    columns.add("__value__");

    var data = [ { "__value__": variable["value"]} ]
    if (type.includes("tensor")) {
        data = variable["value"]["cells"].map(function(cell) {
            var entry = new Object();
            var address = cell["address"];
            for (var dim in address) {
                entry[dim] = address[dim];
                columns.add(dim);
            }
            entry["__value__"] = cell["value"];
            return entry;
        });
    }

    columns = [...columns]; // sort "value" to back
    columns.sort(function(a, b) {
        var _a = a.toLowerCase(); // ignore upper and lowercase
        var _b = b.toLowerCase(); // ignore upper and lowercase
        if (_a.startsWith("__value__") && !_b.startsWith("__value__")) {
            return 1;
        }
        if (_b.startsWith("__value__") && !_a.startsWith("__value__")) {
            return -1;
        }
        if (_a < _b) {
            return -1;
        }
        if (_a > _b) {
            return 1;
        }
        return 0;
    });

    if (data.length > 25) {
        empty_row = columns.reduce((accumulator,current)=>(accumulator[current]='',accumulator), {})
        empty_row.__value__ = "...";
        filtered_data = data.filter(function(d,i) { return i < 10; });
        filtered_data = filtered_data.concat([empty_row]);
        data = filtered_data.concat(data.filter(function(d,i) { return i > data.length - 10 - 1; }));
    }
    table_html(element, data, columns);
}

function table_html(element, data, columns) {
    var table = element.append("table")
        .attr("class", "tensor-table"),
        thead = table.append("thead"),
        tbody = table.append("tbody");

    thead.append("tr")
        .selectAll("th")
        .data(columns)
        .enter()
        .append("th")
        .text(function(column) { return column.startsWith("__value__") ? "value" : column; });

    var rows = tbody.selectAll("tr")
        .data(data)
        .enter()
        .append("tr");

    var cells = rows.selectAll("td")
        .data(function(row) {
            return columns.map(function(column) {
                return {column: column, value: row[column]};
            });
        })
        .enter()
        .append("td")
        .text(function(d) { return d.value; });

    return table;
}

// icons from https://systemuicons.com/
function icon_edit() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m7 1.5h-4.5c-1.1045695 0-2 .8954305-2 2v9.0003682c0 1.1045695.8954305 2 2 2h10c1.1045695 0 2-.8954305 2-2v-4.5003682"/><path d="m14.5.46667982c.5549155.5734054.5474396 1.48588056-.0167966 2.05011677l-6.9832034 6.98320341-3 1 1-3 6.9874295-7.04563515c.5136195-.5178979 1.3296676-.55351813 1.8848509-.1045243z"/><path d="m12.5 2.5.953 1"/></g></svg>';
}

function icon_up() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m3.5 7.5 4-4 4 4"/><path d="m7.5 3.5v11"/><path d="m.5.5h14"/></g></svg>';
}

function icon_down() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m3.5 7.5 4 4 4-4"/><path d="m7.5.5v11"/><path d="m.5 14.5h14"/></g></svg>';
}

function icon_cross() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(5 5)"><path d="m10.5 10.5-10-10z"/><path d="m10.5.5-10 10"/></g></svg>';
}

function icon_cancel() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="matrix(-1 0 0 1 18 3)"><path d="m10.595 10.5 2.905-3-2.905-3"/><path d="m13.5 7.5h-9"/><path d="m10.5.5-8 .00224609c-1.1043501.00087167-1.9994384.89621131-2 2.00056153v9.99438478c.0005616 1.1043502.8956499 1.9996898 2 2.0005615l8 .0022461"/></g></svg>';
}

function icon_replicate() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(3 3)"><path d="m11.5 9.5v-7c0-1.1045695-.8954305-2-2-2h-7c-1.1045695 0-2 .8954305-2 2v7c0 1.1045695.8954305 2 2 2h7c1.1045695 0 2-.8954305 2-2z"/><path d="m3.5 11.5v1c0 1.1045695.8954305 2 2 2h7c1.1045695 0 2-.8954305 2-2v-7c0-1.1045695-.8954305-2-2-2h-1"/></g></svg>';
}

function icon_check() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><path d="m.5 5.5 3 3 8.028-8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(5 6)"/></svg>';
}

function icon_exit() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="matrix(-1 0 0 1 18 3)"><path d="m10.595 10.5 2.905-3-2.905-3"/><path d="m13.5 7.5h-9"/><path d="m10.5.5-8 .00224609c-1.1043501.00087167-1.9994384.89621131-2 2.00056153v9.99438478c.0005616 1.1043502.8956499 1.9996898 2 2.0005615l8 .0022461"/></g></svg>';
}

function icon_comment() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" transform="translate(2 3)"><path d="m14.5.5c1.1045695 0 2 .8954305 2 2v10c0 1.1045695-.8954305 2-2 2l-2.999-.001-2.29389322 2.2938932c-.36048396.360484-.92771502.3882135-1.32000622.0831886l-.09420734-.0831886-2.29389322-2.2938932-2.999.001c-1.1045695 0-2-.8954305-2-2v-10c0-1.1045695.8954305-2 2-2z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"/><path d="m13.5 5.5h-6" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"/><path d="m4.49884033 6.5c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1zm0 4c.5 0 1-.5 1-1s-.5-1-1-1-.99884033.5-.99884033 1 .49884033 1 .99884033 1z" fill="currentColor"/><path d="m13.5 9.5h-6" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"/></g></svg>';
}

function icon_code() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 3)"><line x1="10.5" x2="6.5" y1=".5" y2="14.5"/><polyline points="7.328 2.672 7.328 8.328 1.672 8.328" transform="rotate(135 4.5 5.5)"/><polyline points="15.328 6.672 15.328 12.328 9.672 12.328" transform="scale(1 -1) rotate(-45 -10.435 0)"/></g></svg>';
}

function icon_hierarchy() {
    return '<svg height="21" viewBox="0 0 21 21" width="21" xmlns="http://www.w3.org/2000/svg"><g fill="none" fill-rule="evenodd" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" transform="translate(2 2)"><path d="m5.5.5h6v5h-6z"/><path d="m10.5 11.5h6v5h-6z"/><path d="m.5 11.5h6v5h-6z"/><path d="m3.498 11.5v-3h10v3"/><path d="m8.5 8.5v-3"/></g></svg>';
}

function setup_commands() {
    d3.select("#view-setup-cmd").on("click", function(event) { toggle_show_setup(); event.preventDefault(); });
    d3.select("#clear-cmd").on("click", function(event) { clear_all(); event.preventDefault(); });
    d3.select("#copy-url-cmd").on("click", function(event) { copy_to_clipboard(window.location); event.preventDefault(); });
    d3.select("#new-comment-cmd").html(icon_comment() + " " + d3.select("#new-comment-cmd").html())
        .on("click", function(event) {
            // Prevent the global document click handler from seeing this click as an
            // outside click (which would immediately save/close the newly created frame).
            if (event.stopPropagation) event.stopPropagation();
            event.preventDefault();
            // If currently editing, save the current edit first so user text isn't lost
            if (context === contexts.EDIT) {
                try {
                    // If the current edit is empty, discard it. Otherwise execute (save) it.
                    if (is_current_edit_empty()) {
                        exit_edit_selected();
                    } else {
                        execute_selected();
                    }
                } catch (e) { /* ignore errors and continue */ }
            }
            select_frame_by_index(num_frames() - 1);
            new_frame("c");
            return false;
        });
    d3.select("#new-expression-cmd").html(icon_code() + " " + d3.select("#new-expression-cmd").html())
        .on("click", function(event) {
            // Prevent the global document click handler from treating this as an outside click
            if (event.stopPropagation) event.stopPropagation();
            event.preventDefault();
            // If currently editing, save the current edit first so user text isn't lost
            if (context === contexts.EDIT) {
                try {
                    if (is_current_edit_empty()) {
                        exit_edit_selected();
                    } else {
                        execute_selected();
                    }
                } catch (e) { /* ignore errors and continue */ }
            }
            select_frame_by_index(num_frames() - 1);
            new_frame("e");
            return false;
        });
    d3.select("#apply-setup-cmd").html(icon_check() + " " + d3.select("#apply-setup-cmd").html())
        .on("click", function(event) { apply_setup(); event.preventDefault(); });
    d3.select("#close-setup-cmd").html(icon_exit() + " " + d3.select("#close-setup-cmd").html())
        .on("click", function(event) { toggle_show_setup(); event.preventDefault(); });
}

///////////////////////////////////////////////////////////////////////////////
// Setup handling
///////////////////////////////////////////////////////////////////////////////

function load_setup() {
    if (window.location.hash) {
        var compressed = window.location.hash.substring(1);
        var decompressed = LZString.decompressFromEncodedURIComponent(compressed);
        setup = JSON.parse(decompressed);
        d3.select("#setup-content").text(JSON.stringify(setup, null, 2));
        d3.select("#setup-input").attr("value", compressed);
        // ensure each frame has a stable __id for D3 data joining
        if (setup && Array.isArray(setup.f)) {
            setup.f.forEach(function(fr) {
                if (fr && typeof fr === 'object' && !('__id' in fr)) {
                    fr.__id = frame_uid++;
                }
            });
        }
    }
}

function apply_setup() {
    var setup_string = d3.select("#setup-content").property("value");
    setup = JSON.parse(setup_string);
    save_setup();
    clear_results();
    execute_all();
    toggle_show_setup();
}

function save_setup() {
    var setup_string = JSON.stringify(setup, null, 2);
    d3.select("#setup-content").text(setup_string);
    var compressed = LZString.compressToEncodedURIComponent(setup_string);
    window.location.hash = compressed;
    d3.select("#setup-input").attr("value", compressed);
}

function save_changes() {
    d3.selectAll(".setup").each(function (d,i) {
        var element = d3.select(this);
        var op = d["op"];
        var param = d["p"];
        operations[op]["save"](param, element);
    });
    save_setup();
}

function clear_results() {
    results["f"] = [];
    for (var i = 0; i < setup["f"].length; ++i) {
        results["f"][i] = new Map();
    }
}

function clear_all() {
    setup = { "f": [] };
    save_setup();
    clear_results();
    clear_examples();
    update();
}

// Command handler for the welcome "Start from scratch" button.
function start_from_scratch() {
    // Clear all state, then show the playground UI
    clear_all();
    showPlayground();
}

function get_started() {
    // Redirect to the static getting-started guide. Clear state first for a clean playground when returning.
    try { clear_all(); } catch (e) {}
    window.location.href = '/playground/getting-started.html';
}

function toggle_show_setup() {
    show_setup = !show_setup;
    d3.select("#setup-container").classed("hidden", !show_setup);
    d3.select("#frames").classed("hidden", show_setup);
    d3.select("#add_frames").classed("hidden", show_setup);
    if (show_setup) {
        d3.select("#setup-content").node().focus();
        context = contexts.SETUP;
    } else {
        context = contexts.VIEW;
    }
}

function num_frames() {
    return setup["f"].length;
}

function swap(frame1, frame2) {
    var setup_frame_1 = setup["f"][frame1];
    setup["f"][frame1] = setup["f"][frame2];
    setup["f"][frame2] = setup_frame_1;

    var result_frame_1 = results["f"][frame1];
    results["f"][frame1] = results["f"][frame2];
    results["f"][frame2] = result_frame_1;
}

function remove(frame) {
    setup["f"].splice(frame, 1);
    results["f"].splice(frame, 1);
}


///////////////////////////////////////////////////////////////////////////////
// UI handling
///////////////////////////////////////////////////////////////////////////////

function new_frame(operation) {
    var default_params = JSON.stringify(operations[operation]["params"]);
    setup["f"].push({
        "op" : operation,
        "p" : JSON.parse(default_params),
        "__id": frame_uid++
    });
    results["f"].push(new Map());

    var insert_as_index = find_selected_frame_index() + 1;
    var current_index = num_frames() - 1;
    if (current_index > 0) {
        while (current_index > insert_as_index) {
            swap(current_index, current_index - 1);
            current_index -= 1;
        }
    }

    save_setup();
    update();
    select_frame_by_index(insert_as_index);
    document.activeElement.blur();
    edit_selected();
}

function update() {
    var all_data = d3.zip(setup["f"], results["f"]);

    // Bind using stable key so DOM nodes follow data items across reorders
    var rows = d3.select("#frames").selectAll(".frame").data(all_data, function(d) {
        // d is [setupFrame, resultMap]
        return d && d[0] && d[0].__id !== undefined ? d[0].__id : null;
    });
    rows.exit().remove();
    var frames = rows.enter()
        .append("div")
            .on("click", function() { 
                // Only allow frame selection when not in edit mode
                if (context !== contexts.EDIT) {
                    select_frame(this); 
                }
            })
            .on("dblclick", function(event) {
                // Double-click to edit the frame (also covers double-tap on some devices)
                if (context !== contexts.EDIT) {
                    // Select this frame and enter edit mode
                    select_frame(this);
                    // Use edit_selected which operates on the currently selected frame
                    edit_selected();
                }
                // Prevent further propagation so dblclick doesn't trigger other handlers
                if (event && event.stopPropagation) event.stopPropagation();
                if (event && event.preventDefault) event.preventDefault();
            })
            .attr("class", "frame");

    // For each entered frame, append header only for expressions; comments get a side icon and controls
    frames.each(function(d, i) {
        var el = d3.select(this);
        var op = d[0]["op"];
        el.attr('style', 'position: relative;');
        if (op === 'e') {
            el.append("div").attr("class", "frame-header").html("header");
        } else if (op === 'c') {
            // place a side icon container (left) and a controls container (top-right)
            el.append("div").attr("class", "frame-side-icon").html("");
            el.append("div").attr("class", "frame-controls");
        }
        el.append("div").attr("class", "frame-content").html("content");
    });

    // Add type-specific classes to all frames (enter + update) so they can be styled
    d3.selectAll('#frames .frame').each(function(d, i) {
        var el = d3.select(this);
        var data = el.data();
        if (!data || data.length === 0) return;
        var op = data[0][0]["op"];
        el.classed('frame-expression', op === 'e');
        el.classed('frame-comment', op === 'c');
    });

    // Use keyed data join here as well so the update pass uses stable keys
    d3.select("#frames").selectAll(".frame").data(all_data, function(d) {
        return d && d[0] && d[0].__id !== undefined ? d[0].__id : null;
    }).each(function (d, i) {
        var element = d3.select(this);
        var op = d[0]["op"];
        var param = d[0]["p"];
        var result = d[1];

        var content = element.select(".frame-content");
        if (op === 'e') {
            var header = element.select(".frame-header");
            operations[op]["result_ui"](result, element, header, content, i);
        } else if (op === 'c') {
            var side = element.select(".frame-side-icon");
            var controls = element.select(".frame-controls");
            // Pass side as header and controls as extra param
            operations[op]["result_ui"](result, element, side, content, i, controls);
        }
     }).order();

    // Ensure DOM order matches data order so elements move with their bound data
    d3.select('#frames').selectAll('.frame').order();
    // Debugging output and force reflow to prompt immediate repaint
    try {
        var dataOrder = all_data.map(function(d){ return d && d[0] ? d[0].__id : null; });
        var domOrder = d3.selectAll('#frames .frame').nodes().map(function(n){ return n.getAttribute('data-frame-id'); });
        console.debug('playground:update dataOrder=', dataOrder, 'domOrder=', domOrder);
    } catch (e) { /* ignore */ }
    try {
        var framesNode = d3.select('#frames').node();
        // reading offsetHeight forces layout/reflow
        var _ = framesNode ? framesNode.offsetHeight : null;
        console.debug('playground:update forced reflow');
    } catch (e) { /* ignore */ }
}

function remove_frame(frame_index) {
    select_frame_by_index(frame_index);
    remove_selected();
}

function remove_selected() {
    var frame = find_selected_frame_index();
    remove(frame);
    save_setup();
    update();
    select_frame_by_index(frame);
}

function move_frame_up(frame_index) {
    select_frame_by_index(frame_index);
    move_selected_up();
}

function move_selected_up() {
    var frame_index = find_selected_frame_index();
    if (frame_index == 0) {
        return;
    }
    swap(frame_index, frame_index-1);
    save_setup();
    update();
    select_frame_by_index(frame_index-1);
}

function move_frame_down(frame_index) {
    select_frame_by_index(frame_index);
    move_selected_down();
}

function move_selected_down() {
    var frame_index = find_selected_frame_index();
    if (frame_index == setup["f"].length - 1) {
        return;
    }
    swap(frame_index, frame_index+1);
    save_setup();
    update();
    select_frame_by_index(frame_index+1);
}

// Check if an expression is empty (only contains whitespace)
function is_expression_empty() {
    var edit = get_current_edit();
    return edit !== null && edit.op === 'e' && edit.text === '';
}

// Check if the current edit (comment or expression) is empty
function is_current_edit_empty() {
    var edit = get_current_edit();
    return edit !== null && edit.text === '';
}

// Returns current edit info or null: { op: 'e'|'c', text: string }
function get_current_edit() {
    if (context !== contexts.EDIT) return null;
    var frame = d3.select(selected);
    if (frame.empty()) return null;
    try {
        var data = frame.data();
        var setup = data[0][0]; // because of zip in update
        var op = setup["op"];
        if (op === 'e') {
            var value = get_textarea_field_value(frame, 'expression_expression');
            return { op: 'e', text: value };
        } else if (op === 'c') {
            var ta = frame.select('textarea');
            if (ta.empty()) return { op: 'c', text: '' };
            return { op: 'c', text: ta.property('value').trim() };
        }
    } catch (e) {
        return null;
    }
    return null;
}

function execute_selected() {
    // Don't execute if the expression is empty
    if (is_expression_empty()) {
        show_notification("Expression is empty. Please enter an expression first.", "warning");
        return;
    }

    var frame_index = find_selected_frame_index();
    var frame = d3.select(selected);
    var data = frame.data();
    var setup = data[0][0]; // because of zip in update
    var op = setup["op"];
    var param = setup["p"];

    operations[op]["save"](param, frame);
    save_setup();
    exit_edit_selected();

    // If frame is a comment, update directly. Else execute all
    if (op == "c") {
        var comment = replace_html_code(param["t"]);
        results["f"][frame_index].set("t", converter.makeHtml(comment));
        update();
    } else {
        execute_all();
    }
}

function execute_all() {
    var expressions = [];
    for (var i=0; i < setup["f"].length; ++i) {
        var op = setup["f"][i]["op"];
        var param = setup["f"][i]["p"];
        var result = results["f"][i];

        if (op == "e") {
            expressions.push({ "cell": i, "name": param["n"], "expr": param["e"], "verbose":true });  // later: add option
            if ( ! result.has("result")) {
                result.set("result", "Executing...");
            }
            result.set("executing", true)
            result.set("n", replace_html_code(param["n"]))
            result.set("e", replace_html_code(param["e"]))
        } else if (op == "c") {
            var comment = replace_html_code(param["t"]);
            result.set("t", converter.makeHtml(comment));
        }
    }
    update();

    d3.text("https://api.search.vespa.ai/playground/eval", {
            method: "POST",
            body: "json=" + encodeURIComponent(JSON.stringify(expressions)),
            headers: { "Content-Type": "application/x-www-form-urlencoded" }
        })
        .then(function(response) {
            response = JSON.parse(response);

            if ( ! Array.isArray(response) ) {
                var error = "Unknown error";
                if ("error" in response) {
                    error = response["error"];
                }
                for (var i=0; i < setup["f"].length; ++i) {
                    results["f"][i].set("executing", false);
                    results["f"][i].set("error", response["error"]);
                }
                update();
                return;
            }

            for(var i=0; i < response.length; ++i) {
                var cell = response[i]["cell"];
                var param = setup["f"][cell]["p"];
                var result = results["f"][cell];

                result.set("n", replace_html_code(param["n"]));
                result.set("e", param["e"]);
                result.set("executing", false);

                if ( ! has_error(response[i], result) ) {
                    if (param["n"].length > 0) {
                        variables.set(param["n"], {
                            "name" : param["n"],
                            "type" : response[i]["type"],
                            "value": response[i]["type"].includes("tensor") ? response[i]["value"]["literal"] : response["value"]
                        });
                    }
                    result.set("result", response[i]);
                    result.set("type", response[i]["type"]);
                    result.set("steps", response[i]["steps"]);
                    result.set("primitive", response[i]["primitive"]);
                }
            }
            update();
        })
        .catch(function(err) {
            // Network or CORS error — record per-frame error and update UI instead of throwing
            console.error('playground:execute_all network error', err);
            for (var i=0; i < setup["f"].length; ++i) {
                results["f"][i].set("executing", false);
                results["f"][i].set("error", String(err));
            }
            update();
        });
}

function find_selected_frame_index() {
    var result = -1;
    d3.select("#frames").selectAll(".frame")
        .each(function (d, i) {
            if (this.classList.contains("selected")) {
                result = i;
            }
        });
    return result;
}

function find_frame_index(frame) {
    var result = null;
    // If frame is a D3 selection, get the DOM element
    var frameNode = frame.node ? frame.node() : frame;

    d3.select("#frames").selectAll(".frame")
        .each(function (d, i) {
            if (this == frameNode) {
                result = i;
            }
        });
    return result;
}

function is_element_entirely_visible(el) {
    var rect = el.getBoundingClientRect();
    var height = window.innerHeight || doc.documentElement.clientHeight;
    return !(rect.top < 50 || rect.bottom > height);
}

function select_frame(frame) {
    // Don't allow selecting a different frame while in edit mode
    if (context === contexts.EDIT) {
        show_notification("Cannot select a different frame while in edit mode. Finish editing first.", "warning");
        return;
    }
    
    if (selected == frame) {
        return;
    }
    
    if (selected != null) {
        selected.classList.remove("selected");
    }
    selected = frame;
    selected.classList.add("selected");
    if (!is_element_entirely_visible(selected)) {
        selected.scrollIntoView();
        document.scrollingElement.scrollTop -= 60;
    }
    selected_frame_index = find_selected_frame_index();
}

function select_frame_by_index(i) {
    // Don't allow selecting a different frame while in edit mode
    if (context === contexts.EDIT) {
        show_notification("Cannot select a different frame while in edit mode. Finish editing first.", "warning");
        return;
    }
    
    if (i >= num_frames()) {
        i = num_frames() - 1;
    }
    if (i < 0) {
        i = 0;
    }
    d3.select("#frames").selectAll(".frame")
        .each(function (datum, index) {
            if (i == index) {
                select_frame(this);
            }
        });
}

function edit_frame(frame_index) {
    select_frame_by_index(frame_index);
    edit_selected();
}

function edit_selected() {
    if (context === contexts.EDIT) {
        exit_edit_selected();
        return;
    }
    var frame = d3.select(selected);
    var data = frame.data();
    var setup = data[0][0]; // because of zip in update
    var result = data[0][1];

    var op = setup["op"];
    var param = setup["p"];

    var content = frame.select(".frame-content");
    if (op === 'e') {
        var header = frame.select(".frame-header");
        operations[op]["setup_ui"](param, frame, header, content, find_frame_index(frame));
    } else if (op === 'c') {
        var side = frame.select(".frame-side-icon");
        var controls = frame.select(".frame-controls");
        operations[op]["setup_ui"](param, frame, side, content, find_frame_index(frame), controls);
    }
    
    // Add visual indicator for edit mode
    frame.classed("edit-mode-active", true);
    
    context = contexts.EDIT;
}

function show_details(frame_index) {
    var result = results["f"][frame_index];
    var element = document.getElementById("steps_" + frame_index);
    if (element != null) {
        element.hidden = ! element.hidden;
        result.set("show_details", result.has("show_details") ? ! result.get("show_details") : true);
    }
}

function exit_edit_selected() {
    if (context !== contexts.EDIT) {
        return;
    }

    var frame = d3.select(selected);
    var data = frame.data();
    var setup = data[0][0]; // because of zip in update
    var result = data[0][1];

    var op = setup["op"];
    var param = setup["p"];

    // Check if this is a new frame that hasn't been executed yet
    var isNewFrame = result.size === 0;
    var isEmptyExpression = op === "e" && param["e"] === "";
    var isEmptyComment = op === "c" && param["t"] === "";

    if (isNewFrame && (isEmptyExpression || isEmptyComment)) {
        // Nothing was entered, remove the frame
        var frameIndex = find_frame_index(frame);
        remove(frameIndex);
        save_setup();
        update();
        // Remove visual indicator for edit mode
        frame.classed("edit-mode-active", false);
        context = contexts.VIEW;
        select_frame_by_index(frameIndex-1);
        return;
    }

    var content = frame.select(".frame-content");
    if (op === 'c') {
        var side = frame.select(".frame-side-icon");
        var controls = frame.select(".frame-controls");
        operations[op]["result_ui"](result, frame, side, content, find_frame_index(frame), controls);
    } else {
        var header = frame.select(".frame-header");
        operations[op]["result_ui"](result, frame, header, content, find_frame_index(frame));
    }
    
    // Remove visual indicator for edit mode
    frame.classed("edit-mode-active", false);
    
    context = contexts.VIEW;
}

function event_in_input(event) {
    var tag_name = d3.select(event.target).node().tagName;
    return (tag_name == 'INPUT' || tag_name == 'SELECT' || tag_name == 'TEXTAREA' || tag_name == 'BUTTON');
}

function event_in_frame(event) {
    var node = d3.select(event.target).node();
    while (node != null) {
        if (d3.select(node).attr("class") != null) {
            if (d3.select(node).attr("class").includes("frame")) {
                return true
            }
        }
        node = node.parentElement;
    }
    return false;
}

function copy_to_clipboard(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    
    // Show notification when copied to clipboard
    show_notification("Copied to clipboard", "success", 2000);
}



function setup_keybinds() {
    var previous_keydown = { "key" : null, "ts" : 0 };

    key_binds = {}
    key_binds[contexts.VIEW] = {}
    key_binds[contexts.EDIT] = {}
    key_binds[contexts.SETUP] = {}

    key_binds[contexts.VIEW]["up"] =
    key_binds[contexts.VIEW]["k"]  = function() { select_frame_by_index(find_selected_frame_index() - 1); };
    key_binds[contexts.VIEW]["down"] =
    key_binds[contexts.VIEW]["j"]    = function() { select_frame_by_index(find_selected_frame_index() + 1); };

    key_binds[contexts.VIEW]["shift + up"] =
    key_binds[contexts.VIEW]["shift + k"]  = function() { move_selected_up(); };
    key_binds[contexts.VIEW]["shift + down"] =
    key_binds[contexts.VIEW]["shift + j"]  = function() { move_selected_down(); };

    key_binds[contexts.VIEW]["x"] =
    key_binds[contexts.VIEW]["d,d"] = function() { remove_selected(); };

    key_binds[contexts.VIEW]["e"]  =
    key_binds[contexts.VIEW]["enter"]   = function() { edit_selected(); };
    key_binds[contexts.VIEW]["ctrl + enter"]   = function() { execute_selected(); };

    key_binds[contexts.VIEW]["n,c"] = function() { new_frame("c"); };
    key_binds[contexts.VIEW]["n,e"] = function() { new_frame("e"); };
    key_binds[contexts.VIEW]["a"]   = function() { new_frame(null); };

    key_binds[contexts.VIEW]["esc"] = function() { document.activeElement.blur(); };
    key_binds[contexts.SETUP]["esc"] = function() { document.activeElement.blur(); };

    key_binds[contexts.EDIT]["esc"] = function() { document.activeElement.blur(); exit_edit_selected(); };
    key_binds[contexts.EDIT]["ctrl + enter"] = function() { execute_selected(); };


    d3.select('body').on('keydown', function(event) {
        var combo = [];

        if (event.shiftKey) combo.push("shift");
        if (event.ctrlKey) combo.push("ctrl");
        if (event.altKey) combo.push("alt");
        if (event.metaKey) combo.push("meta");

        var key_code = event.keyCode;

        if (key_code == 8) combo.push("backspace");
        if (key_code == 13) combo.push("enter");
        if (key_code == 27) combo.push("esc");
        if (key_code == 32) combo.push("space");
        if (key_code == 46) combo.push("del");

        if (key_code == 37) combo.push("left");
        if (key_code == 38) combo.push("up");
        if (key_code == 39) combo.push("right");
        if (key_code == 40) combo.push("down");

        // a-z
        if (key_code >= 64 && key_code < 91) combo.push(String.fromCharCode(key_code).toLowerCase());

        var key = combo.join(" + ");
        if (event_in_input(event) && !event_in_frame(event) && key !== "esc") {
            return;
        }

        // Check if combo combined with previous key is bound
        if (Date.now() - previous_keydown["ts"] < 400) {
            var two_key = previous_keydown["key"] + "," + key;
            if (two_key in key_binds[context]) {
                key_binds[context][two_key]();
                event.preventDefault();
                previous_keydown = { "key":null, "ts": 0 };  // reset
                return;
            }
        }

        if (key in key_binds[context]) {
            key_binds[context][key]();
            event.preventDefault();
        }

        previous_keydown = { "key":key, "ts": Date.now() };
    });
}

function setup_examples() {
    d3.select("#examples-select").on("change", function (_) { go_to_example(); });

    if (window.location.hash) {
        var hash = window.location.hash.substring(1);
        var select = d3.select("#examples-select");
        var option = select.select(`option[value="${hash}"]`);

        if (!option.empty()) {
            select.property("value", hash);
        } else {
            select.property("value", "");
        }
    }
}

// If examples are rendered as a list of links (.example-item), bind clicks to navigate
function setup_examples_list() {
    // delegate handler: bind to container and capture clicks
    var container = d3.select('.examples-list');
    if (container.empty()) return;

    container.selectAll('.example-item').on('click', function(event) {
        // Use d3 to get the clicked element's data-value attribute
        var el = d3.select(this);
        var val = el.attr('data-value');
        if (val) {
            try { localStorage.setItem('seen_playground_welcome', 'true'); } catch (e) {}
            // Navigate to the normalized playground base (strip everything after '/playground/')
            try {
                var path = window.location.pathname;
                var marker = '/playground/';
                var idx = path.indexOf(marker);
                var base = '/playground/';
                if (idx !== -1) {
                    // keep everything up to and including '/playground/' (so any trailing filename is removed)
                    base = path.substring(0, idx + marker.length);
                } else {
                    // fallback to the known base
                    base = marker;
                }
                // Build the new URL using the same origin
                var newUrl = window.location.origin + base + '#' + val;
                // If we're already on the normalized base path, changing href to the same
                // origin+path may not reload. In that case update just the hash and force reload.
                try {
                    var currentBaseUrl = window.location.origin + window.location.pathname;
                    var targetBaseUrl = window.location.origin + base;
                    if (currentBaseUrl === targetBaseUrl) {
                        try { window.location.hash = val; } catch (e3) {}
                        window.location.reload();
                    } else {
                        // Navigate to the new URL (changes path and hash)
                        window.location.href = newUrl;
                    }
                } catch (e3) {
                    // Best-effort fallback
                    window.location.href = newUrl;
                }
            } catch (e) {
                // Fallback: set hash and reload
                try { window.location.hash = ''; } catch (e2) {}
                window.location.hash = val;
                window.location.reload();
            }
        }
        event.preventDefault();
    });
}

// Mark welcome as seen when header links are used so navigating away/around
// doesn't unexpectedly show the welcome on reload. Exclude the logo link (it
// intentionally shows welcome).
function setup_header_link_tracking() {
    var header = document.getElementById('header-global-commands');
    if (!header) return;
    var anchors = header.querySelectorAll('a');
    anchors.forEach(function(a) {
        // skip logo anchor
        if (a.querySelector && a.querySelector('img.logo')) return;
        a.addEventListener('click', function() {
            try { localStorage.setItem('seen_playground_welcome', 'true'); } catch (e) {}
        });
    });
}

// Improve hover behavior: add a small delay before closing the dropdown so
// fast pointer moves from the toggle into the dropdown don't cause it to disappear.
function setup_examples_hover() {
    var menu = document.querySelector('.examples-menu');
    if (!menu) return;
    var timeout = null;

    function open() {
        clearTimeout(timeout);
        menu.classList.add('open');
    }

    function close() {
        clearTimeout(timeout);
        timeout = setTimeout(function() { menu.classList.remove('open'); }, 150);
    }

    menu.addEventListener('mouseenter', open);
    menu.addEventListener('focusin', open);
    menu.addEventListener('mouseleave', close);
    menu.addEventListener('focusout', close);
}

function go_to_example() {
    var hash = d3.select("#examples-select").property("value");
    if (!hash) return;
    // Navigate to the normalized playground base (strip everything after '/playground/')
    try {
        var path = window.location.pathname;
        var marker = '/playground/';
        var idx = path.indexOf(marker);
        var base = '/playground/';
        if (idx !== -1) {
            base = path.substring(0, idx + marker.length);
        }
        var newUrl = window.location.origin + base + '#' + hash;
        // If we're already on the normalized base path, updating href to the same
        // origin+path may not reload. Update hash and force reload in that case.
        var currentBaseUrl = window.location.origin + window.location.pathname;
        var targetBaseUrl = window.location.origin + base;
        if (currentBaseUrl === targetBaseUrl) {
            try { window.location.hash = hash; } catch (e2) {}
            window.location.reload();
        } else {
            window.location.href = newUrl;
        }
    } catch (e) {
        // Fallback
        try { window.location.hash = ''; } catch (e2) {}
        window.location.hash = hash;
        window.location.reload();
    }
}

function clear_examples() {
    d3.select("#examples-select").property("value", "");
}

///////////////////////////////////////////////////////////////////////////////
// Theme Toggle Functionality
///////////////////////////////////////////////////////////////////////////////

function setTheme(theme, saveToStorage = true) {
    currentTheme = theme;
    if (saveToStorage) {
        localStorage.setItem('theme', theme);
    }
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update the theme toggle icon
    const themeToggle = document.getElementById('toggle-theme-cmd');
    if (themeToggle) {
        if (theme === 'dark') {
            themeToggle.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="5"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
                <span class="tooltip-text">Toggle light mode</span>
            `;
        } else {
            themeToggle.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path>
                </svg>
                <span class="tooltip-text">Toggle dark mode</span>
            `;
        }
    }
}

function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme, true); // Save to storage when manually toggled
    show_notification(`Switched to ${newTheme} mode`, 'info', 2000);
}

function setupThemeToggle() {
    const themeToggle = document.getElementById('toggle-theme-cmd');
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            toggleTheme();
        });
    }
    
    // Check if theme is saved in localStorage
    const savedTheme = localStorage.getItem('theme');
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
        // Use saved preference if it exists
        currentTheme = savedTheme;
    } else {
        // Otherwise use system preference
        currentTheme = prefersDarkMode ? 'dark' : 'light';
    }
    
    // Apply the theme without saving to localStorage if using system preference
    setTheme(currentTheme, savedTheme !== null);
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        // Only change if user hasn't set a preference
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light', false); // Don't save to storage when following system
        }
    });
}

function main() {
    setup_commands();
    load_setup();
    clear_results();
    execute_all();
    select_frame_by_index(0);
    setup_keybinds();
    setup_examples();
    setup_examples_list();
    setup_examples_hover();
    setup_header_link_tracking();
    setupThemeToggle();

    // Global click handler: when editing a frame, clicking outside should save and exit edit mode
    // However, if the current edit is empty (comment or expression), warn the user instead
    // of silently discarding/saving it. Allow clicks on the new-frame buttons to proceed.
    document.addEventListener('click', function(event) {
        if (context !== contexts.EDIT) return;

        // If there's no selected frame, ignore
        if (!selected) return;

        // Determine if the click target is inside the selected frame
        var node = event.target;
        var inside = false;
        while (node) {
            if (node === selected) { inside = true; break; }
            node = node.parentElement;
        }

        // If click was outside the selected frame
        if (!inside) {
            // If the current edit is empty, show a warning instead of exiting.
            // Allow clicks on the new comment/expression buttons to proceed.
            var clickedNewButton = false;
            try {
                if (event.target && event.target.closest) {
                    clickedNewButton = event.target.closest('#new-comment-cmd, #new-expression-cmd') != null;
                }
            } catch (e) { /* ignore */ }

            if (is_current_edit_empty() && !clickedNewButton) {
                show_notification("You're editing an empty frame. Enter text or press Cancel/Escape to discard.", "warning", 3000);
                event.stopPropagation();
                event.preventDefault();
                return;
            }

            // execute_selected saves and exits edit mode (or shows warning if expression empty)
            try {
                execute_selected();
            } catch (e) {
                // Fallback: just exit edit mode if execute fails
                try { exit_edit_selected(); } catch (e2) {}
            }
        }
    });
}
