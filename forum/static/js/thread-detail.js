$(document).ready(function() {
  var ThreadFollow = {
    init: function() {
        this.bindEvent();
    },

    bindEvent: function() {
      $('.thread-follow-btn').on('click', function(e){
          e.preventDefault();
          $followBtn = $(this);
          $followBtn.attr('disabled', true).css('cursor', 'not-allowed')
          $toggle = $followBtn.find('.toggle');
          var switchTextTo = $toggle.text().trim() === 'Follow' ? 
            'Following' : 
            $toggle.text().trim() === 'Following' ? 
            'Follow' : 
            'Following';                    
          $.ajax({
            method: 'POST',
            url: $followBtn.attr('href'),
            data: {'csrfmiddlewaretoken': csrftoken},
            success: function(data) {
              $toggle.find('.js-thread-follow-btn-text').text(switchTextTo)
              $followBtn.find('.count').text(data['followers_count'])
              $followBtn.attr('disabled', false).css('cursor', 'pointer')
            }
        });
      });  
    }
  }
  ThreadFollow.init();

  var CommentLike = {
    init: function() {
        this.bindEvent();
    },

    bindEvent: function() {
      $('.js-btn-like').on('click', function(e){
        e.preventDefault();
        $likeBtn = $(this);
        $likeBtn.attr('disabled', true).css('cursor', 'not-allowed')
                          
        $.ajax({
          method: 'POST',
          url: $likeBtn.data('action'),
          data: {'csrfmiddlewaretoken': csrftoken},
          success: function(data) {
            $likeBtn
              .find('.js-btn-like-text')
              .text(data.likers_count);
            if (data.is_liker) 
              $likeBtn.removeClass('text-muted').addClass('text-primary');
            else
              $likeBtn.removeClass('text-primary').addClass('text-muted');

            $likeBtn.attr('disabled', false).css('cursor', 'pointer')
          },
          error: function(data) {
            alert("Something went wrong")
            $likeBtn.attr('disabled', false).css('cursor', 'pointer')
          }
        });
      });  
    }
  }
  CommentLike.init();
});