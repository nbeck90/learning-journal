$(document).ready(function(){

function get_edit() {
  var id = $('.entry').attr('id').split("=")[1];
  $.ajax({
    url: '/edit',
    type: 'GET',
    dataType: 'json',
    data: {'id': id},
    success: get_edit_success,
  });

}

function get_edit_success(entry){
  var template = '<aside><form action="{{ request.route_url("edit", id=entry.id) }}" method="POST" class="edit_entry">'+
                 '<div class="edit_field"><label for="title" class="edit_title">Title</label><br>'+
                 '<textarea name="title" id="title" rows="1" cols="30">{{title}}</textarea>'+
                 '</div><div class="edit_field"><label for="text" class="edit_title">Text</label><br>'+
                 '<textarea name="text" id="text" rows="5" cols="80">{{text}}</textarea></div>'+
                 '<div class="control_row"><input type="submit" value="Share" name="Share"/></div></form></aside>';

  var html = Mustache.to_html(template, entry);
  $('.entry').hide()
  $('.twitter').remove()
  $('#editing').prepend(html);
  $(".edit_button").hide();
  $('.edit_entry').on('submit', function(event){
      event.preventDefault();
      make_edit();
  });
}

function make_edit() {
    var title = $('#title').val();
    var text = $('#text').val();
    var split_path = window.location.pathname.split("/");
    var id = split_path[split_path.length-1];
    $.ajax({
      url: '/edit',
      type: 'POST',
      dataType: 'json',
      data: {'title': title, 'text': text, 'id': id},
      success: make_edit_success,
    });

}

function make_edit_success(entry){
  var template = '<article class="entry" id="entry{{id}}">'+
                        '<h3>{{title}}</h3>'+
                        '<div class="post">'+
                        '<p class="dateline">{{created}}'+
                        '<div class="entry_body" id ="test">'+
                        '{{{text}}}'+
                        '</div>'+
                        '</article>'+
                        '<div style="text-align:center" class="twitter">'+
                        '<a href="https://twitter.com/share" class="twitter-share-button" data-text="New Blog Post: {{title}}" data-via="BeckerCommaNick" data-size="large" data-dnt="true">Tweet</a>'+
                        "<script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+'://platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document, 'script', 'twitter-wjs');</script>"+
                        '</div>';

  var html = Mustache.to_html(template, entry);
  $(".edit_entry").remove()
  $('#edited').prepend(html);
  $(".edit_button").show();
  twttr.widgets.load();
}

function remove_post() {
    var split_path = window.location.pathname.split("/");
    console.log(split_path)
    var id = split_path[split_path.length-1];
    console.log(id)
    $.ajax({
      url: '/remove',
      type: 'POST',
      dataType: 'json',
      data: {'id': id},
    });

}

function relocate() {
  window.location.replace("/journal");
}

function add_post() {
    var title = $('#title').val();
    var text = $('#text').val();
    $.ajax({
      url: '/add',
      type: 'POST',
      dataType: 'json',
      data: {'title': title, 'text': text},
      success: add_success
    });
}

function add_success(entry){
     $('.add_entry').trigger('reset');
     var template = '<article class="entry" id="entry{{id}}">'+
                        '<a href ="/detail/{{id}}"><h3>{{title}}</h3></a>'+
                        '<div class="post">'+
                        '<a href ="/detail/{{id}}">'+
                        '<p class="dateline">{{created}}'+
                        '<div class="entry_body" id ="detail_post">'+
                        '{{{text}}}'+
                        '</div></a>'+
                        '</article>'+
                        '<div style="text-align:center" class="twitter">'+
                        '<a href="https://twitter.com/share" class="twitter-share-button" data-text="New Blog Post: {{title}}" data-via="BeckerCommaNick" data-size="large" data-dnt="true">Tweet</a>'+
                        "<script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+'://platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document, 'script', 'twitter-wjs');</script>"+
                        '</div>';


     var html = Mustache.to_html(template, entry);
     $('#all_posts').prepend(html);
     twttr.widgets.load();
}


$('.edit_button').click(function(event){
    event.preventDefault();
    get_edit();
  });

$('.remove_button').click(function(event){
    event.preventDefault();
    remove_post();
  });

$('.add_entry').on('submit', function(event){
    event.preventDefault();
    add_post();
  });
});

