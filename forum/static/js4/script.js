$(document).ready(function() {
  //   $(window).resize(function() {
  //     $("#sidebar-wrapper").css({
  //       transition: "margin 0s ease-in"
  //     });
  //   });
  $('.notif-icon').on('click', function(e) {
    e.preventDefault();
    var self = $(this);
    window.setTimeout(function() {
      self.css('background-color', current_bg_color);
    }, 400)
    var current_bg_color = $(this).css('background-color')
    self.css('background-color', 'hsla(219, 59%, 80%, 0.78)');    
  });
  
  $("#menu-toggle").click(function(e) {
    e.preventDefault();
    $(".sidebar-overlay").toggleClass("overlay-show");
    $("#wrapper").toggleClass("toggled");
  });

  $("#close-sidebar").click(function(e) {
    e.preventDefault();
    $(".sidebar-overlay").toggleClass("overlay-show");
    $("#wrapper").toggleClass("toggled");
  });

  $(".sidebar-overlay").on("touchstart click", function(e) {
    console.log("hide");
    var touch =
      e.originalEvent && e.originalEvent.touches && e.originalEvent.touches[0];
    console.log(touch || e);
    var validTouch = touch || e;
    console.log("Sidebar width: ");
    console.log($("#sidebar-wrapper").width());

    if (validTouch.clientX > $("#sidebar-wrapper").width()) {
      $(".sidebar-overlay").toggleClass("overlay-show");
      $("#wrapper").toggleClass("toggled");

      e.preventDefault();
    }
  });

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

  function getImageChooser() {
    var $fakeImageChooser =
      $("#fake-image-chooser1").css("display") === "none"
        ? $("#fake-image-chooser2")
        : $("#fake-image-chooser1");
    return $fakeImageChooser;
  }

  window.onresize = function(e) {
    console.log("resize");
    setImageChooser();
  };

  function registerImageChooserChange() {
    // var $realImageChooser = $("#real-image-chooser");
    var $realImageChooser = $("#id_image");
    var $realImageChooser = $("#id_image");
    $realImageChooser.css("display", "none");
    $("#div_id_image").css("display", "none");

    $realImageChooser.change(function(e) {
      var fakeImageChooser2ImgTag1 = document.getElementById(
        "fake-image-chooser1"
      );
      var fakeImageChooser2ImgTag2 = document.getElementById(
        "fake-image-chooser2"
      );

      var reader = new FileReader();
      reader.onload = function(e) {
        fakeImageChooser2ImgTag1.src = e.target.result;
        fakeImageChooser2ImgTag2.src = e.target.result;
      };
      if (e.target.files[0]) {
        reader.readAsDataURL(e.target.files[0]);
      }
    });
  }

  function setImageChooser() {
    var $fakeImageChooser = getImageChooser();

    // var $realImageChooser = $("#real-image-chooser");
    console.log("real image chooser");

    var $realImageChooser = $("#id_image");
    console.log($realImageChooser);
    $realImageChooser.css("display", "none");
    $("#div_id_image").css("display", "none");
    $fakeImageChooser.on("click", function() {
      $realImageChooser.click();
      registerImageChooserChange();
    });
  }

  console.log("load");
  setImageChooser();

  // $('.message-test').fadeIn(1000).delay(2500).fadeOut(1000)

  // $('#id_image').css('display', 'none');

  /* Trigger the hidden file input button click */
  // $('#falseinput').on('click', function () {
  //   $("#id_image").click();
  // });

  /* Change the current image to the selected image */
  // $('#id_image').change(function (event) {
  //   var selectedFile = event.target.files[0];
  //   var reader = new FileReader();

  //   var imgtag = document.getElementById("profile-image-holder");
  //   imgtag.title = selectedFile.name;

  //   reader.onload = function (event) {
  //     imgtag.src = event.target.result;
  //   };

  //   reader.readAsDataURL(selectedFile);
  // });
});
