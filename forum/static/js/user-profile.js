$(document).ready(function() {    
    function scrollHorizontalNavigation() {
        // console.log(
        //   $(".nav-scroller")
        //     .find("a")
        //     .data("target")
        // );
        var profileSidebarActiveLinkKeys = [
          "stats",
          "user_notifs",
          "profile",
          "replies",
          "new",
          "following",
          "me",
          "user_following",
          "user_followers"
        ];
    
        $(".nav-scroller")
          .find("a")
          .each(function() {
            console.log($(this).data("target"));
          });
        var left = $(document).outerWidth() - $(window).width();
        $(".nav-scroller").scrollLeft(left);
      }
      // scrollHorizontalNavigation();
    
      var ProfileImageController = {
        $realImageChooserWrapper: $('#div_id_image'),
        $realImageChooser: $("#id_image"),
    
        init: function() {
          this.$realImageChooserWrapper.css('display', 'none');
          this.$realImageChooser.css("display", "none");
          this.bindImageChooserClickEvent();
          this.bindWindowResizeEvent();
          this.bindImageChooserChangeEvent();
        },
        
        getImageChooser: function() {
          var $fakeImageChooser =
            $("#fake-image-chooser1").css("display") === "none"
              ? $("#fake-image-chooser2")
              : $("#fake-image-chooser1");
          return $fakeImageChooser;
        },
    
        bindImageChooserClickEvent: function() {
          var self = this;
          var $fakeImageChooser = self.getImageChooser();
          $fakeImageChooser.on("click", function() {
            self.$realImageChooser.click();
          });
        },
    
        bindWindowResizeEvent: function() {
          var self = this;
          window.onresize = function(e) {
            console.log("resize");
            self.bindImageChooserClickEvent();
          };
        },
    
        bindImageChooserChangeEvent: function() {
          var self = this;
          self.$realImageChooser.change(function(e) {
            var tagForMobile = document.getElementById(
              "fake-image-chooser1"
            );
            var tagForDesktop = document.getElementById(
              "fake-image-chooser2"
            );
            self.bindFileReaderEvent(e, tagForMobile, tagForDesktop)
          });  
        },
    
        bindFileReaderEvent: function(e, tag1, tag2) {     
          var reader = new FileReader();
          reader.onload = function(e) {
            tag1.src = e.target.result;
            tag2.src = e.target.result;
          };
          if (e.target.files[0]) {
            reader.readAsDataURL(e.target.files[0]);
          }
        }
      }
    
    ProfileImageController.init();
})