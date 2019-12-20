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
                    'Unfollow' : 
                    $toggle.text().trim() === 'Unfollow' ? 
                    'Follow' : 
                    'Unfollow';                    
                $.ajax({
                    method: 'POST',
                    url: $followBtn.attr('href'),
                    data: {'csrfmiddlewaretoken': csrftoken},
                    success: function(data) {
                        $toggle.text(switchTextTo)
                        $followBtn.find('.count').text(data['followers_count'])
                        $followBtn.attr('disabled', false).css('cursor', 'pointer')
                    }
                });
            });  
        }
    }
    ThreadFollow.init();
});