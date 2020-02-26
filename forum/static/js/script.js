$(document).ready(function() {
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  csrftoken = getCookie("csrftoken");

  function validateImage(data) {
    var acceptFileTypes = /^image\/(gif|jpe?g|png)$/i,
      maxImageSize = 500 * 1024; // 500KB
    if (data.files[0] && !acceptFileTypes.test(data.files[0]["type"])) {
      alert("File is not an image");
      return false;
    } else if (data.files[0] && data.files[0]["size"] > maxImageSize) {
      maxImageSizeHuman = maxImageSize / 1024 + " KB";
      alert("Image cannot be greater than " + maxImageSizeHuman);
      return false;
    } else {
      return true;
    }
  }
  window.validateImage = function(data) {
    return validateImage(data);
  };

  $(".nav-container")
    .last()
    .attr(
      "style", 
      "box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);"
    )

  var SideBarToggler = {
    $menuToggle: $("#menu-toggle"),
    $sidebarOverlay: $(".sidebar-overlay"),
    $wrapper: $("#wrapper"),
    $closeSidebarIcon: $("#close-sidebar"),
    $sidebarWrapper: $("#sidebar-wrapper"),

    init: function() {
      this.bindMenuToggleEvent();
      this.bindSidebarCloseBtnEvent();
      this.bindSidebarOverlayEvent();
    },

    bindMenuToggleEvent: function() {
      var self = this;
      self.$menuToggle.click(function(e) {
        e.preventDefault();
        self.$sidebarOverlay.toggleClass("overlay-show");
        self.$wrapper.toggleClass("toggled");
      });
    },

    bindSidebarCloseBtnEvent: function() {
      var self = this;
      self.$closeSidebarIcon.click(function(e) {
        e.preventDefault();
        self.$sidebarOverlay.toggleClass("overlay-show");
        self.$wrapper.toggleClass("toggled");
      });
    },

    bindSidebarOverlayEvent: function() {
      var self = this;
      self.$sidebarOverlay.on("touchstart click", function(e) {
        var touch =
          e.originalEvent &&
          e.originalEvent.touches &&
          e.originalEvent.touches[0];
        var validTouch = touch || e;
        if (validTouch.clientX > self.$sidebarWrapper.width()) {
          self.$sidebarOverlay.toggleClass("overlay-show");
          self.$wrapper.toggleClass("toggled");
          e.preventDefault();
        }
      });
    }
  };
  SideBarToggler.init();

  var SearchBarToggler = {
    // $icon: $('#search-icon'),
    $icon: $('.search-icon'),
    $aroundSearchBar: null,
    $searchBar: null,
    $searchInput: null,

    init: function() {
      this.bindOpenEvent();
    },

    hideSideSearchBar: function() {
      this.$aroundSearchBar.removeClass('search-bar-hide')
      if (this.$searchBar.is(':focus')) {
        this.$searchInput.focus();
      }
      this.$searchBar.removeClass('search-bar-show')
    },
    
    showSideSearchBar: function() {
      this.$aroundSearchBar.addClass('search-bar-hide')
      this.$searchBar.addClass('search-bar-show')
      this.$searchInput.focus();
    },

    bindResizeEvent: function() {
      var self = this;
      $(window).resize(function() {
        console.log('resize searchbar')
        self.hideSideSearchBar();
      });
    },

    bindOpenEvent: function() {
      var self = this;
      self.$icon.on('click', function() {
        console.log('clicked search icon')
        self.$aroundSearchBar = $('.around-search-bar');
        self.$searchBar = $('.search-bar');
        self.$searchInput = self.$searchBar.find('input');
        self.showSideSearchBar();  
        self.bindCloseEvent();
        self.bindResizeEvent();
      })
    },

    bindCloseEvent: function() {
      var self = this;
      $('#close-search-bar').on('click', function() {
        self.hideSideSearchBar();
      })
    }
  }
  SearchBarToggler.init();

  var NotificationIconBackgroundSwitcher = {
    init: function() {
      this.bindEvent();
    },

    bindEvent: function() {
      $(".js-main-nav__notif-link").on("click", function(e) {
        // e.preventDefault();
        var self = $(this);
        window.setTimeout(function() {
          self.css("background-color", current_bg_color);
        }, 200);
        var current_bg_color = $(this).css("background-color");
        self.css("background-color", "hsla(219, 59%, 80%, 0.78)");
      });
    }
  };
  NotificationIconBackgroundSwitcher.init();

  var ShowPostFormScroll = {
    $commentForm: $("#post-form"),
    $commentFormWrapper: $('.js-post-form-wrapper'),

    init: function() {
      // If there is no post-form, it means that the user is a
      // guest
      if (!this.$commentFormWrapper[0]) return;
      this.$commentForm.hide();

      this.bindAddThreadBtnClick();
    },

    bindAddThreadBtnClick() {
      var self = this;
      $(".add-thread-btn").on("click", function(e) {
        e.preventDefault();
        self.$commentForm.show();
        FloatingActionBtnToggler.init();
        $("html,body").animate(
          { scrollTop: self.$commentForm.offset().top },
          "slow"
        );
      });
    }
  };
  ShowPostFormScroll.init();

  var FloatingActionBtnToggler = {
    init: function() {
      // To prevent flashing button when the browser is refreshed
      // at a point the button is meant to be invisible
      setTimeout(this.toggle, 200);

      this.toggle();
      this.bindWindowScrollEvent();
    },

    bindWindowScrollEvent: function() {
      var self = this;
      $(window).on("scroll", function() {
        self.toggle();
      });
    },

    toggle: function() {
      var $actionBtn = $(".floating-action-btn");
      var actionBtnBottom = $actionBtn.offset().top + $actionBtn.height();
      var $textWrapper = $("#div_id_message");
      var textWrapperBottom = $textWrapper.offset().top + $textWrapper.height();
      actionBtnBottom >= textWrapperBottom
        ? $actionBtn.css("opacity", 0)
        : $actionBtn.css("opacity", 1);
    }
  };
});
