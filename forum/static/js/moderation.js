$(document).ready(function() {
  var KeyEvent = {
    KEY_BACK_SPACE: 8,
    KEY_RETURN: 13,
    KEY_ESCAPE: 27,
    KEY_UP: 38,
    KEY_DOWN: 40
  };

  var UserSelector = {
    $searchWrapper: $(".user-search-wrapper"),
    $input: $("#user-search-input"),
    value: "",
    prevValue: "",
    $dropdown: null,
    itemActiveCls: "bg-light-purple",
    isDropdownShown: false,
    justLoaded: true,

    init: function() {
      this.bindSearchUserEvent();
      this.bindKeyEvents();
      this.bindChangeUserDetail();
      this.bindDropdownBlurEvent();
    },

    bindSearchUserEvent: function() {
      var self = this;
      self.$input.on("keyup", function(e) {
        self.value = $(this).val();
        self.performSearch(e);
      });

      if (self.justLoaded && self.$input.val().length) {
        self.value = self.$input.val();
        self.performSearch();
      } else {
        self.justLoaded = false;
      }
    },

    performSearch: function(e) {
      var self = this;
      if (self.canSearch(e)) {
        self.hideUserDetail();
        self.fetchUsers(self.showDropdown);
        self.prevValue = self.value;
      } else {
        if (!self.value.length && self.isDropdownShown) {
          self.hideDropdown();
        }
      }
    },

    canSearch: function(event) {
      if (event) {
        var code = event.keyCode || event.which;
        if (
          code === KeyEvent.KEY_RETURN ||
          code === KeyEvent.ESCAPE ||
          code === KeyEvent.KEY_UP ||
          code === KeyEvent.KEY_DOWN
        ) {
          return false;
        }
      }
      if (!this.value.length) {
        // The previous value will be equal to current value when
        // the user types in a recently cleared last character.
        // To avoid we have to reset the prevValue.
        this.prevValue = "";
        return false;
      }
      if (this.value === this.prevValue) {
        return false;
      }
      return true;
    },

    hideUserDetail: function() {
      var $userDetail = $("#user-detail");
      if (
        $userDetail &&
        $userDetail.find(".username-wrapper").text() !== this.$input.val()
      ) {
        $userDetail.css("display", "none");
      }
    },

    fetchUsers: function(showDropdown) {
      var self = this;
      $.ajax({
        url: "/accounts/users/mention/",
        data: { username: self.value },
        dataType: "json",
        success: function(data, status) {
          showDropdown(data);
        }
      });
    },

    showDropdown: function(data) {
      // This is a callback function, the 'this'
      // keyword will not work here
      var self = UserSelector;
      self.$dropdown = $("#user-search-dropdown");

      var userList = self.buildUserList(data["user_list"]);

      if (userList.length) {
        self.$dropdown.show().html(userList);

        var $current = self.$dropdown.find("li").eq(0);
        $current.addClass(self.itemActiveCls);

        self.isDropdownShown = true;
        self.bindDropdownItemClickEvent();

        if (self.justLoaded) {
          self.onJustLoaded($current);
        }
      } else {
        self.hideDropdown();
      }
    },

    buildUserList: function(userList) {
      var self = this;
      var list = "";
      userList.forEach(function(user) {
        var startWithRegex = new RegExp(String(self.value), "i");
        var startWith = startWithRegex.exec(user.username)[0];
        var strongStartWith = "<strong>" + startWith + "</strong>",
          text = user.username.replace(startWithRegex, strongStartWith);
        list +=
          '<li style="cursor: pointer" class="list-group-item user-item" data-url="' +
          user.profile_url +
          '">' +
          '<img src="' +
          user.avatar_url +
          '" width="30" height="30" class="avatar mr-2"/>' +
          text +
          "</li>";
      });
      return list;
    },

    bindDropdownItemClickEvent: function() {
      var self = this;
      var $items = self.$dropdown.find(".user-item");
      $items.off().on("click", function() {
        if (!self.isDropdownShown) return;
        self.setUserDetail($(this));
        self.$input.blur();
        self.$searchWrapper.hide();
      });
    },

    onJustLoaded: function($current) {
      this.justLoaded = false;
      this.setUserDetail($current);
    },

    hideDropdown: function() {
      this.$dropdown.hide();
      self.isDropdownShown = false;
      this.$dropdown.html("");
      this.value = "";
    },

    setUserDetail: function($chosenItem, shouldHide) {
      if (!$chosenItem) return;
      var $userDetail = $("#user-detail");

      $userDetail.css("display", "flex");

      $userDetail
        .find(".user-profile-link")
        .attr("href", $chosenItem.data("url"));

      var src = $chosenItem.find("img").attr("src");

      $userDetail
        .find("img")
        .show()
        .attr("src", src);

      var username = $chosenItem.text();
      $userDetail.find(".username-wrapper").text(username);
      this.$input.val(username);

      shouldHide = shouldHide === undefined ? true : false;
      if (shouldHide) {
        this.hideDropdown();
        this.value = "";
      }
    },

    bindChangeUserDetail: function() {
      var self = this;
      $("#change-user-detail").click(function(e) {
        e.preventDefault();
        self.$searchWrapper.show();
        self.$input.focus();
      });
    },

    bindDropdownBlurEvent: function() {
      var self = this;
      $(document).click(function(e) {
        if (!self.isDropdownShown) return;
        if (
          self.$dropdown.has(e.target).length === 0 &&
          self.$input.has(e.target).length === 0
        ) {
          self.hideDropdown();
        }
      });
    },

    bindKeyEvents: function() {
      var self = this;
      self.$input.on("keydown", function(e) {
        if (!self.isDropdownShown) return;
        var code = e.keyCode || e.which;
        switch (code) {
          case KeyEvent.KEY_RETURN:
            e.preventDefault();
            self.onReturnKeyPressed();
            break;
          case KeyEvent.KEY_ESCAPE:
            e.preventDefault();
            self.onEscKeyPressed();
            break;
          case KeyEvent.KEY_UP:
            e.preventDefault();
            self.onUpKeyPressed();
            break;
          case KeyEvent.KEY_DOWN:
            e.preventDefault();
            self.onDownKeyPressed();
            break;
        }
      });
    },

    onReturnKeyPressed: function() {
      var activeSelector = "." + this.itemActiveCls;
      var $activeItem = this.$dropdown.find(activeSelector);
      if ($activeItem) {
        this.setUserDetail($activeItem);
        this.$input.blur();
        this.$searchWrapper.hide();
      }
    },

    onEscKeyPressed: function() {
      this.hideDropdown();
    },

    onUpKeyPressed: function() {
      var activeSelector = "." + this.itemActiveCls;
      var $activeItem = this.$dropdown.find(activeSelector);
      $dropdownItems = this.$dropdown.find(".user-item");

      if ($activeItem.index() > 0) {
        $activeItem.toggleClass(this.itemActiveCls);
        
        var $prev = $activeItem.prev();
        $prev.toggleClass(this.itemActiveCls);
        this.setUserDetail($prev, false);
      } else {
        $activeItem.toggleClass(this.itemActiveCls);
        $dropdownItems
          .eq($dropdownItems.length - 1)
          .toggleClass(this.itemActiveCls);

        var $last = $dropdownItems.eq($dropdownItems.length - 1);
        $last.toggleClass(this.itemActiveCls);
        this.setUserDetail($last, false);
      }
    },

    onDownKeyPressed: function() {
      var activeSelector = "." + this.itemActiveCls;
      var $activeItem = this.$dropdown.find(activeSelector);
      $dropdownItems = this.$dropdown.find(".user-item");

      if ($activeItem.index() < $dropdownItems.length - 1) {
        $activeItem.toggleClass(this.itemActiveCls);

        var $next = $activeItem.next();
        $next.toggleClass(this.itemActiveCls);
        this.setUserDetail($next, false);
      } else {
        $activeItem.toggleClass(this.itemActiveCls);

        var $first = $dropdownItems.eq(0);
        $first.toggleClass(this.itemActiveCls);
        this.setUserDetail($first, false);
      }
    }
  };

  UserSelector.init();
});
