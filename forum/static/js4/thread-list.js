$(document).ready(function() {   
    
    (function registerAddThreadBtnClick() {        
        // $('#comment-form').hide()
        $('.add-thread-btn').on('click', function(){
            $('.add-thread-btn-small').hide();
            $('#comment-form').show();
            $('html,body').animate(
                {
                    scrollTop: $('#comment-form').offset().top
                },
                'slow'
            );
        });     
    })();

    // (function registerFormSubmitBtnClick() {
    //     $('button[type="submit"]').on('click', function(e) {
    //         e.preventDefault();
    //         console.log(csrftoken)
    //         console.log('category: ' + $('select#id_category').val());
    //         console.log('thread:' + $('input#id_title').val());
    //         console.log('message:' + editor.value());

    //         // $.ajax({
    //         //     url: $('form').attr('action'),
    //         //     dataType: 'json',
    //         //     data: {
    //         //         'category': $('select#id_category').val(),
    //         //         'thread': $('input#id_title').val(),
    //         //         'message': editor.value()
    //         //     }
    //         // })
    //         console.log('click')
    //     });
    // });

})