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
      $li.append('<div><strong>Default:</strong> ' + defaultValue + '</div>');
      $li.append('<div><strong>Description:</strong> ' + description + '</div>');

      $list.append($li);
    }
  });

  $table.replaceWith($list);
});
