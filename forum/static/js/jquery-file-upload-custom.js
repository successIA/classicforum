$(document).ready(function () {
    var CustomFileUpload = {
        $realImageChooser: $("#realFileChooser"),
        $customImageChooser: $("#customFileChooser"),
        $progressBarWrapper: null,
        $attachmentMenu: null,
        
        init: function() {
            this.bindUploadEvent();
            this.bindUploadBtnEvent();
            this.bindInsertBtnEvent();
            this.bindRemoveBtnEvent();
        },

        bindUploadEvent: function() {
            var self = this;
            self.$realImageChooser.fileupload({
                dataType: 'json',
                sequentialUploads: true,  
                dropZone: $('#div_id_message'), 
                add: function(e, data) {
                    self.onAdd(e, data)
                },            
                start: function (e) {  
                    self.onStart(e);
                },            
                progressall: function (e, data) {
                    self.onProgressall(e, data)
                },
                stop: function (e) {
                    self.onStop(e)
                },
                done: function (e, data) { 
                    self.onDone(e, data)
                }
            })
        },

        bindUploadBtnEvent: function() {
            var self = this;
            self.$customImageChooser.click(function () {
                self.$realImageChooser.click();
            });          
        },

        bindInsertBtnEvent: function() {
            $('.insert-url-btn').on('click', function() {
                var src = $(this).attr('data-src');
                pos = easyMDE.codemirror.getCursor();
                easyMDE.codemirror.setSelection(pos, pos);
                easyMDE.codemirror.replaceSelection(src);
                $(this).next().show();
            })
        },

        bindRemoveBtnEvent: function() {
            $('.remove-url-btn').on('click', function() {
                var src = $(this).attr('data-src');
                var escapedSrc =  src.replace(/[-[\]{}()*+!<=:?.\/\\^$|#\s,]/g, '\\$&');
                var regex = new RegExp(escapedSrc, 'g')
                easyMDE.value(easyMDE.value().replace(regex, ''));
                $(this).hide();
            })
        },

        onAdd: function(e, data) {
            console.log(data);
            var acceptFileTypes = /^image\/(gif|jpe?g|png)$/i;
            var maxImageSize = 500 * 1024 // 500KB
            if (data.files[0] && !acceptFileTypes.test(data.files[0]['type'])) {
                alert("File is not an image");
            }
            else if (data.files[0] && data.files[0]['size'] > maxImageSize) {
                maxImageSizeHuman = maxImageSize / 1024 + " KB"
                alert("Image cannot be greater than " + maxImageSizeHuman)
            } else {
                data.submit();
            }
        },

        onStart: function(e) {
            var self = this;
            self.$progressBarWrapper = $("#progress-bar-wrapper")
            self.$progressBarWrapper.show();
            $('html,body').animate(
                { scrollTop: self.$progressBarWrapper.offset().top },
                'slow'
            );
        },

        onProgressall: function(e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            var strProgress = progress + "%";
            $('.progress-bar').css( {'width': strProgress} )
                              .text(strProgress)
                              .attr('aria-valuenow', String(progress))
        },

        onStop: function(e) {
            this.$progressBarWrapper.hide();
        },
        
        isImagePresent: function(url) {
            var isPresent = false;
            this.$attachmentMenu.find('img').each(function() {
                if ($(this).attr('src') === url) {
                    isPresent = true;
                }
            });
            return isPresent
        },

        populateAttachmentMenu: function(data) {
            var markdownImgTag = '![](' + data.result.url + ')';
            $firstItem = $('.attachment-menu-item:last-child')
            if (this.$attachmentMenu.css('display') === 'none') {
                this.$attachmentMenu.show();
                $firstItem.find('img').attr('src', data.result.url)
                $firstItem.find('button').attr('data-src', markdownImgTag)
            } else {
                $firstItem.clone(true).appendTo(this.$attachmentMenu)   
                $lastItem = $('.attachment-menu-item:last-child')             
                $lastItem.find('img').attr('src', data.result.url)
                $lastItem.find('button').attr('data-src', markdownImgTag)   
                $lastItem.find('.remove-url-btn').css('display', 'none')         
            }
        },

        onDone: function(e, data) {
            this.$attachmentMenu = $('.attachment-menu');
            if (data.result.is_valid) {
                if (this.isImagePresent(data.result.url)) {
                    alert("Image already exists");
                    return;
                }
                this.populateAttachmentMenu(data)
            } else {
                alert("Something went wrong");
            }   
        },

    }
    CustomFileUpload.init();
  });