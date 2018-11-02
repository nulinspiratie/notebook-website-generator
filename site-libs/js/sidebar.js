function attach_sidebar(sidebar){
  // $('#sidebar').resizable({
  //     handles: 'e',
  //     resize: function (event, ui) {
  //         setNotebookWidth(cfg, st)
  //         $(this).css('height', '100%');
  //     },
  //     start: function (event, ui) {
  //         $(this).width($(this).width());
  //         //$(this).css('position', 'fixed');
  //     },
  //     stop: function (event, ui) {
  //         // Ensure position is fixed (again)
  //         //$(this).css('position', 'fixed');
  //         $(this).css('height', '100%');
  //         $('#toc').css('height', $('#sidebar').height() - $("#sidebar-header").height());
  //     }
  // })

  $("body").append(sidebar);

  // if sidebar is undefined (first run(?), then hide it)
  if (sidebar.css('display') === undefined) sidebar.css('display', "none") //block

  // Bind sitebar height to site height
  $('#site').bind('siteHeight', function () {
    sidebar.css('height', $('#site').height());
  });
  $('#site').trigger('siteHeight');

  // Set sidebar height after a short delay
  setTimeout(function() {sidebar.css('top', 0)}, 500)

  // Set notebook container left margin
  $('#notebook').css('margin-left', '230px');
  // Also optionally set breadcrumb left margin
  if ($('.breadcrumb').length) {
    $('.breadcrumb').css('margin-left', '230px')
  }

  // Specify resize behaviour of notebook container
  $( window ).resize(function() {
    $('#notebook-container').width($( window ).width() - $('#sidebar').width()-100)
  });
}

function generate_sidebar(logo_source, homepage){
  var sidebar = $('<div id="sidebar"/>')
    .addClass('sidebar-wrapper')
    .append(
      $('<div id="sidebar-header"/>')
        .addClass("header")
        .append($("<form/>")
          .append($("<div/>")
            .addClass("tipue_search_group")
            .append($("<input/>")
              .attr("type", "text")
              .attr("name", "q")
              .attr("id", "tipue_search_input")
              .attr("pattern", ".{3,}")
              .attr("placeholder", "Search")
            ).append($("<button/>")
              .attr("type", "submit")
              .addClass("tipue_search_button")
              .append($("<div/>")
                .addClass("tipue_search_icon")
                .append("&#9906;")
              )
            )
          )
        )
        // .append($("<form/>")
        //   .attr('class', 'search-form')
        //   .attr('action', '../search.html')
        //   .append($("<input/>")
        //     .attr("type", "text")
        //     .attr('name', 'q')
        //     .attr('id', 'tipue_search_input')
        //     .attr('style', 'width:95%;margin-top:9px').
        //     attr('placeholder', 'search')
        //     .attr('pattern', '.{3,}')))
    ).append(
      $("<div/>")
        .attr("id", "toc")
        .addClass('toc')
    );

  if (homepage) {
    $('#sidebar-header')
      .prepend(
        $("<a/>")
          .attr("href", "../index.html")
          .attr('style', "color:#c4939c")
          .text(homepage)
      )
  }

  if (logo_source) {
    $('#sidebar-header').append(
      $("<img/>")
        .attr('id', 'home-image')
        .attr("href", "../index.html")
        .attr('height', '32')
        .attr('width', '32')
        .attr('style', "border:0px;margin-right:5px;vertical-align:bottom")
    ).append(
      $("<span/>")
        .html("&nbsp;&nbsp")
    )
  }
  return sidebar
}

function add_display_control_panel(sidebar) {
  sidebar.find("#sidebar-header")
    .append(
      $("<div/>")
        .addClass('display_control_panel')
        .append(
          $("<div/>")
            .addClass("display_checkboxes")
            .append(
              $("<input>")
                .attr('id', 'show_source')
                .attr('name', 'show_source')
                .attr("type", "checkbox")
                .attr("onclick", "toggle_source()")
            ).append(
            $("<label/>")
              .append("Source code")
          // ).append(
          //   $("<br/>")
          // ).append(
          //   $("<input>")
          //     .attr('id', 'show_prompt')
          //     .attr('name', 'show_prompt')
          //     .attr("type", "checkbox")
          //     .attr("onclick", "toggle_prompt()")
          // ).append(
          //   $("<label/>")
          //     .append("Execution prompt")
          )
        )
    )
}
