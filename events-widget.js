/* SQLBites events widget. Single source: events.json.
   Drives the /events month calendar (#cal-grid) AND the homepage upcoming strip (#sb-upcoming).
   Hosted at https://speaking.sqlbites.net/events-widget.js, included via <script src> on sqlbites.net pages. */
(function () {
  var SRC = 'https://speaking.sqlbites.net/events.json';
  var MON = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var MON3 = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

  function esc(s) {
    return (s || '').replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function parse(s) { var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }

  var today = new Date(); today.setHours(0, 0, 0, 0);

  fetch(SRC).then(function (r) { return r.json(); }).then(function (data) {
    var EV = (data.events || []).map(function (e, i) { e.d = parse(e.date); e.idx = i; return e; });
    var calGrid = document.getElementById('cal-grid');
    if (calGrid) initCalendar(EV);
    var strip = document.getElementById('sb-upcoming');
    if (strip) renderUpcoming(EV, strip);
  }).catch(function () {
    var strip = document.getElementById('sb-upcoming');
    if (strip) strip.innerHTML = '<div style="color:#555;font-size:13px">Events unavailable right now.</div>';
    var list = document.getElementById('cal-list');
    if (list) list.innerHTML = '<div class="cal-empty">Could not load events right now.</div>';
  });

  /* Homepage upcoming strip: next 3 future events */
  function renderUpcoming(EV, strip) {
    var up = EV.filter(function (e) { return e.d >= today; }).sort(function (a, b) { return a.d - b.d; }).slice(0, 3);
    if (!up.length) { strip.innerHTML = '<div style="color:#555;font-size:13px">No upcoming talks scheduled. Check back soon.</div>'; return; }
    strip.innerHTML = up.map(function (e) {
      var inner =
        '<div class="event-date">' + MON3[e.d.getMonth()] + ' ' + e.d.getDate() + ', ' + e.d.getFullYear() + '</div>' +
        '<div class="event-conf">' + esc(e.conference) + '</div>' +
        '<div class="event-loc">&#128205; ' + esc(e.location || '') + '</div>' +
        '<div class="event-session">' + esc(e.title) + '</div>' +
        '<span class="event-tag upcoming">Upcoming</span>';
      var href = e.sessionUrl || e.conferenceUrl || 'https://sqlbites.net/events/';
      return '<a href="' + esc(href) + '" class="event-card">' + inner + '</a>';
    }).join('');
  }

  /* /events month calendar */
  function initCalendar(EV) {
    var grid = document.getElementById('cal-grid');
    var list = document.getElementById('cal-list');
    var lbl = document.getElementById('cal-month');
    var view = new Date(today.getFullYear(), today.getMonth(), 1);
    var up = EV.filter(function (e) { return e.d >= today; }).sort(function (a, b) { return a.d - b.d; });
    if (up.length) view = new Date(up[0].d.getFullYear(), up[0].d.getMonth(), 1);

    function sameMonth(d) { return d.getFullYear() === view.getFullYear() && d.getMonth() === view.getMonth(); }

    function render() {
      lbl.textContent = MON[view.getMonth()] + ' ' + view.getFullYear();
      grid.innerHTML = '';
      DOW.forEach(function (d) { var c = document.createElement('div'); c.className = 'cal-dow'; c.textContent = d; grid.appendChild(c); });
      var start = new Date(view.getFullYear(), view.getMonth(), 1).getDay();
      var dim = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
      var cells = Math.ceil((start + dim) / 7) * 7;
      for (var i = 0; i < cells; i++) {
        var dayNum = i - start + 1;
        var inMonth = dayNum >= 1 && dayNum <= dim;
        var cell = document.createElement('div');
        cell.className = 'cal-cell' + (inMonth ? '' : ' other');
        if (inMonth) {
          var cd = new Date(view.getFullYear(), view.getMonth(), dayNum);
          if (cd.getTime() === today.getTime()) cell.className += ' today';
          var num = document.createElement('div'); num.className = 'cal-num'; num.textContent = dayNum; cell.appendChild(num);
          EV.filter(function (e) { return e.d.getFullYear() === cd.getFullYear() && e.d.getMonth() === cd.getMonth() && e.d.getDate() === dayNum; })
            .forEach(function (e) {
              cell.classList.add('has');
              var chip = document.createElement('div');
              chip.className = 'cal-ev' + (e.d < today ? ' past' : '');
              chip.textContent = e.conference;
              chip.title = e.conference + ': ' + e.title;
              chip.addEventListener('click', function () {
                var t = document.getElementById('ev-' + e.idx);
                if (t) { t.scrollIntoView({ behavior: 'smooth', block: 'center' }); t.style.outline = '2px solid #F92342'; setTimeout(function () { t.style.outline = ''; }, 1600); }
              });
              cell.appendChild(chip);
            });
        }
        grid.appendChild(cell);
      }
      var month = EV.filter(function (e) { return sameMonth(e.d); }).sort(function (a, b) { return a.d - b.d; });
      list.innerHTML = '';
      if (!month.length) { list.innerHTML = '<div class="cal-empty">No talks this month. Use the arrows to browse.</div>'; return; }
      var h = document.createElement('h3'); h.textContent = MON[view.getMonth()] + ' ' + view.getFullYear(); list.appendChild(h);
      month.forEach(function (e) {
        var isUp = e.d >= today;
        var conf = e.conferenceUrl
          ? '<a href="' + esc(e.conferenceUrl) + '" target="_blank" rel="noopener">' + esc(e.conference) + '</a>'
          : esc(e.conference);
        var links = '';
        if (e.sessionUrl) links += '<a href="' + esc(e.sessionUrl) + '" target="_blank" rel="noopener">Slides &amp; materials &#8594;</a>';
        if (e.conferenceUrl) links += '<a href="' + esc(e.conferenceUrl) + '" target="_blank" rel="noopener">Conference &#8594;</a>';
        var row = document.createElement('div');
        row.className = 'ev-row' + (isUp ? ' up' : '');
        row.id = 'ev-' + e.idx;
        row.innerHTML =
          '<div class="ev-date"><div class="d">' + e.d.getDate() + '</div><div class="m">' + MON3[e.d.getMonth()] + '</div></div>' +
          '<div class="ev-body"><div class="ev-conf">' + conf + (isUp ? '<span class="ev-tag">Upcoming</span>' : '') + '</div>' +
          '<div class="ev-talk">' + esc(e.title) + '</div>' +
          '<div class="ev-meta">&#128205; ' + esc(e.location || '') + '</div>' +
          (links ? '<div class="ev-links">' + links + '</div>' : '') +
          '</div>';
        list.appendChild(row);
      });
    }

    document.getElementById('cal-prev').addEventListener('click', function () { view.setMonth(view.getMonth() - 1); render(); });
    document.getElementById('cal-next').addEventListener('click', function () { view.setMonth(view.getMonth() + 1); render(); });
    render();
  }
})();
