//......... utilitary functions............
function incr_lbl(ary, h_idx) { //increment heading label  w/ h_idx (zero based)
    ary[h_idx]++;
    for (var j = h_idx + 1; j < ary.length; j++) {
        ary[j] = 0;
    }
    return ary.slice(0, h_idx + 1);
}


function removeMathJaxPreview(elt) {
    elt.find("script[type='math/tex']").each(
        function (i, e) {
            $(e).replaceWith('$' + $(e).text() + '$');
        });
    elt.find("span.MathJax_Preview").remove();
    elt.find("span.MathJax").remove();
    return elt
}


var make_link = function (h, num_lbl) {
    var a = $("<a/>");
    a.attr("href", '#' + h.attr('id'));
    // get the text *excluding* the link text, whatever it may be
    var hclone = h.clone();
    hclone = removeMathJaxPreview(hclone);
    if (num_lbl) {
        hclone.prepend(num_lbl);
    }
    hclone.children().last().remove(); // remove the last child (that is the automatic anchor)
    hclone.find("a[name]").remove(); //remove all named anchors
    a.html(hclone.html());
    a.on('click', function () {
        setTimeout(function () {
            $.ajax()
        }, 100); //workaround for  https://github.com/jupyter/notebook/issues/699
    });
    return a;
};


// Table of Contents =================================================================
function table_of_contents(sidebar, cfg) {
    sidebar.append(
      $("<div/>")
        .attr("id", "toc")
        .addClass('toc')
    );

    var ul = $("<ul/>").addClass("toc-item").attr('id', 'toc-level0');

    // update toc element
    $("#toc").empty().append(ul);

    var depth = 1; //var depth = ol_depth(ol);
    var li = ul; //yes, initialize li with ul! 
    var all_headers = $("#notebook").find(":header");
    var min_lvl = 1,
        lbl_ary = [];
    for (; min_lvl <= 6; min_lvl++) {
        if (all_headers.is('h' + min_lvl)) {
            break;
        }
    }
    for (var i = min_lvl; i <= 6; i++) {
        lbl_ary[i - min_lvl] = 0;
    }

    //loop over all headers
    all_headers.each(function (i, h) {
        var level = parseInt(h.tagName.slice(1), 10) - min_lvl + 1;
        // skip below threshold
        if (level > cfg.threshold) {
            return;
        }
        // skip headings with no ID to link to
        if (!h.id) {
            return;
        }
        //If h had already a number, remove it
        $(h).find(".toc-item-num").remove();
        var num_str = incr_lbl(lbl_ary, level - 1).join('.'); // numbered heading labels
        var num_lbl = $("<span/>").addClass("toc-item-num")
            .text(num_str).append('&nbsp;').append('&nbsp;');

        // walk down levels
        for (var elm = li; depth < level; depth++) {
            var new_ul = $("<ul/>").addClass("toc-item");
            elm.append(new_ul);
            elm = ul = new_ul;
        }
        // walk up levels
        for (; depth > level; depth--) {
            // up twice: the enclosing <ol> and <li> it was inserted in
            ul = ul.parent();
            while (!ul.is('ul')) {
                ul = ul.parent();
            }
        }
        // Change link id -- append current num_str so as to get a kind of unique anchor
        // A drawback of this approach is that anchors are subject to change and thus external links can fail if toc changes
        // Anyway, one can always add a <a name="myanchor"></a> in the heading and refer to that anchor, eg [link](#myanchor)
        // This anchor is automatically removed when building toc links. The original id is also preserved and an anchor is created
        // using it.
        // Finally a heading line can be linked to by [link](#initialID), or [link](#initialID-num_str) or [link](#myanchor)
        h.id = h.id.replace(/\$/g, '').replace('\\', '');
        if (!$(h).attr("saveid")) {
            $(h).attr("saveid", h.id)
        } //save original id
        h.id = $(h).attr("saveid") + '-' + num_str.replace(/\./g, '');
        // change the id to be "unique" and toc links to it
        // (and replace '.' with '' in num_str since it poses some pb with jquery)
        var saveid = $(h).attr('saveid');
        //escape special chars: http://stackoverflow.com/questions/3115150/
        var saveid_search = saveid.replace(/[-[\]{}():\/!;&@=$£%§<>%"'*+?.,~\\^$|#\s]/g, "\\$&");
        if ($(h).find("a[name=" + saveid_search + "]").length == 0) { //add an anchor with original id (if it doesnt't already exists)
            $(h).prepend($("<a/>").attr("name", saveid));
        }


        // Create toc entry, append <li> tag to the current <ol>. Prepend numbered-labels to headings.
        li = $("<li/>").append(make_link($(h), num_lbl));

        ul.append(li);
        $(h).prepend(num_lbl);


    });

    // Show section numbers if enabled
    cfg.number_sections ? $('.toc-item-num').show() : $('.toc-item-num').hide()

}