$(document).ready(function() {
  var ThreadFollow = {
    init: function() {
        this.bindEvent();
    },

    bindEvent: function() {
      $('.js-thread-follow-btn').on('click', function(e){
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
            var followersCount = parseInt(data.followers_count)
            if (isNaN(followersCount)) {
              alert('Something went wrong');              
            } else {              
              $toggle.find('.js-thread-follow-btn-text').text(switchTextTo)
              var count = followersCount === 0 ? '' : followersCount;
              $followBtn.find('.count').text(count);              
            }
            $followBtn.attr('disabled', false).css('cursor', 'pointer');
          },

          error: function() {
            alert("Something went wrong")
            $followBtn.attr('disabled', false).css('cursor', 'pointer')
          }
        });
      });  
    }
  }
  ThreadFollow.init();
});