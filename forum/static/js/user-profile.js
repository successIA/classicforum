$(document).ready(function() {
  var HorizontalScrollNavigation = {
    $navScroller: $(".nav-scroller"),

    sidebarItems: {
      Information: "stats",
      Notifications: "user_notifs",
      Settings: "settings",
      Replies: "replies",
      New: "new",
      Following: "following",
      Threads: "me",
      "User Following": "user_following",
      Followers: "user_followers"
    },

    init: function() {
      this.bindEvent();
    },

    bindEvent: function() {
      var self = this;
      self.$navScroller.find("a").each(function() {
        var $item = $(this);
        text = self.sidebarItems[$item.text().trim()];
        if ($item.data("target") === text) {
          self.$navScroller.find("nav").scrollLeft($item.position().left - $item.width());
        }
      });
    }
  };
  HorizontalScrollNavigation.init();

  var ConfirmProfileSettings = {
    hasChanged: false, 

    init: function() {
      this.bindConfirmPageEvent();
    },

    confirm: function() {
      return "Are you sure you want to leave?";
    },

    bindConfirmPageEvent: function() {
      var self = ConfirmProfileSettings
      $(
        "#id_image,#id_gender,#id_signature,#id_location,#id_website"
      ).change(function() {
        self.hasChanged = true;
      });
      
      window.onbeforeunload = function() {
        var self = ConfirmProfileSettings
        var image = $("#id_image").val();
        var gender = $("#id_gender").val();
        var signature = $("#id_signature").val();
        var location = $("#id_location").val();
        var website = $("#id_website").val();
        isNonEmpty = !!(image || gender || signature || location || website);
        if (self.hasChanged && isNonEmpty) {
          return "Are you sure you want to leave?";
        }
      };
    }
  };

  window.onload = ConfirmProfileSettings.init();

  var ProfileImageChooser = {
    $realImageChooserWrapper: $("#div_id_image"),
    $realImageChooser: $("#id_image"),

    init: function() {
      this.$realImageChooserWrapper.css("display", "none");
      this.$realImageChooser.css("display", "none");
      this.bindImageChooserClickEvent();
      this.bindWindowResizeEvent();
      this.bindImageChooserChangeEvent();
      this.bindImageAlertError();
    },

    getImageChooser: function() {
      var $customImageChooser =
        $("#custom-image-chooser1").css("display") === "none"
          ? $("#custom-image-chooser2")
          : $("#custom-image-chooser1");
      return $customImageChooser;
    },

    bindImageChooserClickEvent: function() {
      var self = this,
        $customImageChooser = self.getImageChooser();
      $customImageChooser.on("click", function() {
        self.$realImageChooser.click();
      });
    },

    bindWindowResizeEvent: function() {
      var self = this;
      window.onresize = function(e) {
        self.bindImageChooserClickEvent();
      };
    },

    bindImageChooserChangeEvent: function() {
      var self = this;
      self.$realImageChooser.change(function(e) {
        var tagForMobile = document.getElementById("custom-image-chooser1");
        var tagForDesktop = document.getElementById("custom-image-chooser2");
        self.bindFileReaderEvent(e, tagForMobile, tagForDesktop);
      });
    },

    bindFileReaderEvent: function(e, tag1, tag2) {
      var reader = new FileReader();
      reader.onload = function(e) {
        tag1.src = e.target.result;
        tag2.src = e.target.result;
      };
      if (e.target.files[0]) {
        // window.validateImage can be found in js/script.js
        if (window.validateImage(e.target)) {
          reader.readAsDataURL(e.target.files[0]);
        }
      }
    },

    bindImageAlertError: function() {
      var $error = $("#error_1_id_image");
      if ($error && $error.length) {
        setTimeout(function() {
          alert($error.text());
          $error = null;
        }, 100);
      }
    }
  };
  ProfileImageChooser.init();
});
