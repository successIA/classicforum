$(document).ready(function() {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    $('.thread-follow-btn').on('click', function(e){
        e.preventDefault();

        $followBtn = $(this);
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
            }
        });
    });
});