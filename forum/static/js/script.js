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

  csrftoken = getCookie('csrftoken');

  
  var NotificationIconBackgroudSwitcher  = {
    init: function() {
      this.bindEvent();
    },

    bindEvent: function() {      
      $('.notif-icon').on('click', function(e) {
        e.preventDefault();
        var self = $(this);
        window.setTimeout(function() {
          self.css('background-color', current_bg_color);
        }, 400)
        var current_bg_color = $(this).css('background-color')
        self.css('background-color', 'hsla(219, 59%, 80%, 0.78)');    
      });   
    }
  }
  NotificationIconBackgroudSwitcher.init();

  var ShowPostFormScroll = {
    $commentForm: $('#comment-form'),

    init: function() {
      this.bindAddThreadBtnClick();  
    },

    bindAddThreadBtnClick() {        
        var self = this;
        $('.add-thread-btn').on('click', function(){
            $('.add-thread-btn-small').hide();
            self.$commentForm.show();
            $('html,body').animate(
                { scrollTop: self.$commentForm.offset().top },
                'slow'
            );
        });   
    }
  }
  ShowPostFormScroll.init();

  var SideBarToggler = {
    $menuToggle: $('#menu-toggle'),
    $sidebarOverlay: $(".sidebar-overlay"),
    $wrapper: $("#wrapper"),
    $closeSidebarIcon: $("#close-sidebar"),
    $sidebarWrapper: $("#sidebar-wrapper"),

    init: function () {
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
          e.originalEvent && e.originalEvent.touches && e.originalEvent.touches[0];
        var validTouch = touch || e;
        if (validTouch.clientX > self.$sidebarWrapper.width()) {
          self.$sidebarOverlay.toggleClass("overlay-show");
          self.$wrapper.toggleClass("toggled");
          e.preventDefault();
        }
      });
    }
  }
  SideBarToggler.init();

  var AddThreadMobileBtnToggler = {

    init: function() {      
      // To prevent flashing button when the browser is refreshed
      // at a point the button is meant to be invisible
      setTimeout(this.toggleAddThreadMobileBtn, 200)

      this.toggleAddThreadMobileBtn();
      this.bindWindowScrollEvent();
    },

    bindWindowScrollEvent: function() {     
      var self = this;
      $(window).on('scroll', function() {
        self.toggleAddThreadMobileBtn();
      }) 
    },

    toggleAddThreadMobileBtn: function() {
      var $fixedBtn = $('.add-thread-btn-small');
      var fixedBtnBottom = $fixedBtn.offset().top + $fixedBtn.height();
      var $textWrapper = $('#div_id_message');
      var textWrapperBottom = $textWrapper.offset().top + $textWrapper.height();
      fixedBtnBottom >= textWrapperBottom ? $fixedBtn.css('opacity', 0)
                                          : $fixedBtn.css('opacity', 1); 
    }
  }
  AddThreadMobileBtnToggler.init();
});
