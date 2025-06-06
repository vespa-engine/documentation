/* Table to list converter wit JQuery */
$(window).on('load', function() {
  let $table = $('#rank-feature-table');
  let $list = $('<ul id="feature-list"></ul>');

  $table.find('tr').each(function() {
    let $row = $(this);

    // Check if it's a section heading (h3 inside td)
    if ($row.find('td[colspan="3"] h3').length > 0) {
      let headingText = $row.find('h3').text().trim();
      let headingId = $row.find('h3').attr('id') || '';

      let $headingLi = $('<li style="list-style: none; margin-top: 1em;"></li>');
      $headingLi.append('<h3' + (headingId ? ' id="' + headingId + '"' : '') + '>' + headingText + '</h3>');

      $list.append($headingLi);
      return;
    }

    // Skip column headers
    if ($row.hasClass('trx') || $row.find('th').length > 0) {
      return;
    }

    let $tds = $row.find('td');
    if ($tds.length >= 3) {
      let featureName = $tds.eq(0).text().trim();
      let defaultValue = $tds.eq(1).text().trim();
      let description = $tds.eq(2).html().trim(); // Keep inner HTML

      let $li = $('<li></li>');
      $li.append('<strong>' + featureName + '</strong>');
      $li.append('<div>Default: ' + defaultValue + '</div>');
      $li.append('<div> ' + description + '</div>');

      $list.append($li);
    }
  });

  $table.replaceWith($list);
});

/* Natve Ranking Tables */
$(window).on('load', function() {
    let $table = $('#nativerank-variables-table');
    let $list = $('<ul id="variable-list"></ul>');
  
    $table.find('tbody tr').each(function() {
      let $row = $(this);
      let $tds = $row.find('td');
  
      if ($tds.length >= 2) {
        let variable = $tds.eq(0).html().trim(); // Keep HTML (e.g., <em>, <sub>)
        let description = $tds.eq(1).html().trim(); // Keep inner HTML
  
        let $li = $('<li style="margin-bottom: 1em;"></li>');
        $li.append('<strong>' + variable + '</strong>');
        $li.append('<div>' + description + '</div>');
  
        $list.append($li);
      }
    });
  
    $table.replaceWith($list);
  });
  
  $(window).on('load', function() {
    let $table = $('#native-rank-parameters-table');
    let $list = $('<ul id="native-rank-parameters-list"></ul>');
  
    $table.find('tbody tr').each(function() {
      let $row = $(this);
      let $tds = $row.find('td');
  
      // Skip rows that span all columns (e.g., deprecated notice)
      if ($tds.length === 1 && $tds.attr('colspan') === '4') {
        let noticeHtml = $tds.html().trim();
        let $li = $('<li style="list-style: none; margin: 1em 0; color: red;"></li>');
        $li.html(noticeHtml);
        $list.append($li);
        return;
      }
  
      if ($tds.length >= 4) {
        let feature = $tds.eq(0).html().trim();       // Feature name (keep HTML)
        let parameter = $tds.eq(1).html().trim();     // Parameter (keep HTML)
        let defaultValue = $tds.eq(2).text().trim();  // Default (plain text)
        let description = $tds.eq(3).html().trim();   // Description (keep HTML)
  
        let $li = $('<li style="margin-bottom: 1em;"></li>');
        $li.append('<strong>' + feature + ' → ' + parameter + '</strong>');
        $li.append('<div><em>Default:</em> ' + defaultValue + '</div>');
        $li.append('<div>' + description + '</div>');
  
        $list.append($li);
      }
    });
  
    $table.replaceWith($list);
  });
  