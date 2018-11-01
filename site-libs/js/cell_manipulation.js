function toggle_source() {
  var btn = document.getElementById("show_source");
  if (btn.checked) {
    $('div.input').css('display', 'flex');
    $('.hidden_content').show();
    // this somehow does not work.
    $('div.cell').css('padding', '0pt').css('border-width', '0pt');
  } else {
    $('div.input').hide();
    $('.hidden_content').hide();
    $('div.cell').css('padding', '0pt').css('border-width', '0pt');
  }
}

function toggle_prompt() {
  var btn = document.getElementById("show_prompt");
  if (btn.checked) {
    $('.output_prompt').show();
    $('.input_prompt').show();
    $('.output_area .prompt').show();
  } else {
    $('.output_prompt').hide();
    $('.input_prompt').hide();
    $('.output_area .prompt').hide();
  }
}