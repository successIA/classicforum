$(document).ready(function () {
    $('#modal-progress').hide();
    var editor = $('.editor-preview-side');
    // editor.on('change', function(){
    //     console.log('x');
    // })
    // editor.on('DOMSubtreeModified', function() {
    //     var message = $(this).html()
        
    //     console.log($(this).html());
    // });
    
    // var thumbnailHolder = $('.img-thumbnail-holder')
    // thumbnailHolder.show();
    // src= 'http://127.0.0.1:8000/media/post_images/Desert.jpg'
    // html = '<div class="img-thumbnails"><img style="margin-left: 10px; " src="' + src + '" width="70" height="80" class="img-thumbnail"><div class="thumbnail-btn-ctrl"> <button class="btn btn-default insert-btn" src="' + src + '"onclick="appendText()">Insert</button>&nbsp;&nbsp;<button  class="btn btn-default remove-btn">Remove</button></div></div>';
    // html2 = '<div class="img-thumbnails"><img style="margin-left: 10px; " src="' + src + '" width="70" height="80" class="img-thumbnail"><div class="thumbnail-btn-ctrl"> <button class="btn btn-default insert-btn" src="' + src + '"onclick="appendText()">Insert</button>&nbsp;&nbsp;<button  class="btn btn-default remove-btn">Remove2</button></div></div>';

    // thumbnailHolder.append(html);
    // thumbnailHolder.append(html2);

    
    /* 1. OPEN THE FILE EXPLORER WINDOW */
  $(".js-upload-photos").click(function () {
    $('.img-thumbnail-holder-image-size').hide();
    $("#fileupload").click();
  });

  /* 2. INITIALIZE THE FILE UPLOAD COMPONENT */
  $("#fileupload").fileupload({ // BEGINNING OF FILE UPLOAD
    dataType: 'json',

    sequentialUploads: true,  /* 1. SEND THE FILES ONE BY ONE */

    send: function (e, data) {
        var imageSizeLimit = parseFloat(2048 * 1024);  // 2 MegaBytes 2048 KiloBytes 2097152 Bytes
        var imageSize = parseFloat(data.files[0].size)
        console.log(data.files[0].size)
        if ( imageSize > imageSizeLimit) {
            var thumbnailHolderImageSize = $('.img-thumbnail-holder-image-size');
            thumbnailHolderImageSize.show();
            var html = '<div class="alert alert-danger">'
                       + 'Image size  cannot be greater than <strong>' + imageSizeLimit / 1024 + ' KB</strong>.'
                       + ' Please Resize the image and try again.' 
                     + '</div>';
            
            if (thumbnailHolderImageSize.text() === "") {
                $('.img-thumbnail-holder-image-size').append(html);
            }
            return false;
        } 
        return true;
    },

    start: function (e) {  /* 2. WHEN THE UPLOADING PROCESS STARTS, SHOW THE MODAL */
      // console.log(e)
      // return;
      $("#modal-progress").show();
    },

    stop: function (e) {  /* 3. WHEN THE UPLOADING PROCESS FINALIZE, HIDE THE MODAL */
      $("#modal-progress").hide();
    },

    progressall: function (e, data) {  /* 4. UPDATE THE PROGRESS BAR */
      var progress = parseInt(data.loaded / data.total * 100, 10);
      var strProgress = progress + "%";
      $(".progress-bar").css({"width": strProgress});
      $(".progress-bar").text(strProgress);
    },

    done: function (e, data) {  /* 3. PROCESS THE RESPONSE FROM THE SERVER */
      if (!data.result.is_valid) {
            var imageSizeLimit = parseFloat(500 * 1024);
            var thumbnailHolderImageSize = $('.img-thumbnail-holder-image-size');
            thumbnailHolderImageSize.show();
            var html = '<div class="alert alert-danger">'
                       + data.result.message 
                     + '</div>';
            console.log('QW');       
            if (thumbnailHolderImageSize.text() === "") {
                $('.img-thumbnail-holder-image-size').append(html);
            }
      }
      if (data.result.is_valid) {
            var t0 = performance.now();
            var src = data.result.url;
            var fullSrc = '![](http://127.0.0.1:8000' + src + ')';
            // pos = simplemde.codemirror.getCursor();
            // simplemde.codemirror.setSelection(pos, pos);
            // simplemde.codemirror.replaceSelection(fullSrc);
            
            var thumbnailHolder = $('.img-thumbnail-holder');
            thumbnailHolder.show();
            
            var html = '<div id="no-btn-click" class="img-thumbnails">'
                    + '<img style="margin-left: 10px; " src="' + src + '" width="70" height="80" class="img-thumbnail">' 
                    + '<div class="thumbnail-btn-ctrl">'
                      + '<button class="btn btn-default insert-btn" src="' + fullSrc + '">Insert</button>&nbsp;&nbsp;'
                      + '<button style="display: none;" class="btn btn-default remove-btn" src="' + fullSrc + '">Remove</button>'
                    + '</div>'
                 + '</div>';
            thumbnailHolder.append(html);

            $('#no-btn-click').each(function(i) {
                var img_thumbnail = $(this)
                img_thumbnail.attr("id", "has-btn-click")
                // console.log(img_thumbnail.find('.insert-btn'))
                var insert_btn =  img_thumbnail.find('.insert-btn')
                var remove_btn =  img_thumbnail.find('.remove-btn')

                    insert_btn.on('click', function(){
                        var fullSrc = $(this).attr('src');
                        // var fullSrc = '![](' + src + ')'
                        pos = simplemde.codemirror.getCursor();
                        simplemde.codemirror.setSelection(pos, pos);
                        simplemde.codemirror.replaceSelection(fullSrc);
                        remove_btn.show();
                        // var textarea = $("textarea"),
                        // val = textarea.val();              
                        // textarea.focus()
                        // simplemde.value("")
                        // textarea.val(val);   
                    });
                    remove_btn.on('click', function(){
                        // $(this).parent().parent().css("display", "none" );
                        var fullSrc = $(this).attr('src');
                        var fullSrcEscaped =  fullSrc.replace(/[-[\]{}()*+!<=:?.\/\\^$|#\s,]/g, '\\$&');
                        var text = simplemde.value();
                        var regex = new RegExp(fullSrcEscaped, 'g')
                        var plainText = text.replace(regex, '')
                        console.log('plainText: ' + plainText)
                        simplemde.value(plainText);
                        remove_btn.hide();
                    });
                // }
            });
            


            // $("#gallery tbody").prepend(
            //   "<tr><td><a href='" + data.result.url + "'>" + data.result.name + "</a></td></tr>"
            // )
            var t1 = performance.now();
            console.log("Call to doSomething took " + (t1 - t0) + " milliseconds.");
      } 
    }
  }); // END OF FILE UPLOAD

  
});