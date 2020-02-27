$(document).ready(function() {
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
            var likers_count = parseInt(data.likers_count)
            if (isNaN(likers_count)) {
              alert('Something went wrong');              
            } else {
              var count = likers_count === 0 ? '' : likers_count;              
              $likeBtn.find('.js-btn-like-text').text(count);

              if (data.is_liker) 
                $likeBtn.removeClass('text-muted').addClass('text-primary');
              else
                $likeBtn.removeClass('text-primary').addClass('text-muted');
            }
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

  var CommentPermaLinkCopy = {
    $permalink: $('.js-permalink'),

    init: function() {
      this.bindLinkClickEvent();
    },

    bindLinkClickEvent: function() {
      this.$permalink.on('click', function(e) {
        e.preventDefault();
        var permalink = $(this).attr('href').trim()
        var $tempInput = $("<input>");
        $("body").append($tempInput);
        $tempInput.val(permalink).select();
        document.execCommand("copy");
        $tempInput.remove();
        alert("You copied " + permalink)
      })
    }
  }
  CommentPermaLinkCopy.init();
})