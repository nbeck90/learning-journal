$(document).ready(function(){
$('.add_entry').on('submit', function(event){
    event.preventDefault();
    add_post();
  });

function add_post() {
    var title = $('#title').val();
    var text = $('#text').val();
    $.ajax({
      url: '/add',
      type: 'POST',
      dataType: 'json',
      data: {'title': title, 'text': text},
      success: success
    });
}

function success(entry){
     $('.add_entry').trigger('reset');
     var template = '<article class="entry" id="entry{{id}}">'+
                        '<a href ="/detail/{{id}}"><h3>{{title}}</h3></a>'+
                        '<div class="post">'+
                        '<a href ="/detail/{{id}}">'+
                        '<p class="dateline">{{created}}'+
                        '<div class="entry_body" id ="detail_post">'+
                        '{{{text}}}'+
                        '</div></a>'+
                        '</article>';


     var html = Mustache.to_html(template, entry);
     $('#all_posts').prepend(html);
}

    $(".edit_button").click(function(){
        $("#detail_post").hide( 'slow' );
        $(".edit_post").removeClass();
        $(".edit_button").hide();
    });

    $(".share_button").click(function(){
        $("#hidden_edit").addClass( 'edit_post' );
        $(".share_button").hide( 'slow' );
        $("#detail_post").show( 'slow' );
        $(".edit_button").show( 'slow' );
    });
});

