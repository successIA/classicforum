var easyMDE = new EasyMDE({
    element: $("#id_message")[0],
    autoDownloadFontAwesome: false,
    // uploadImage: true,
    // imageUploadEndpoint: '/upload/',
    // imageCSRFToken: csrftoken,
    previewRender: function(plainText) {
      textWithRenderedMentions = MentionRenderer.render(plainText);
      return BBCodeQuoteRenderer.render(textWithRenderedMentions);
    },
    spellChecker: false,
    showIcons: ["code" /* , "upload-image" */]
  });
  
  var ConfirmEditor = {
    init: function() {
      this.bindConfirmPageEvent();
    },
  
    confirm: function() {
      return "Are you sure you want to leave?";
    },
  
    bindConfirmPageEvent: function() {
      // window.onbeforeunload = function() {
      //   if (easyMDE.value()) {
      //     return "Are you sure you want to leave?";
      //   }
      // };
    }
  };
  
  window.onload = ConfirmEditor.init();
  
  // Change image icon in the editor toolbar to upload icon
  // $('.upload-image').find('i').attr('class', 'fa fa-upload')
  
  var BBCodeQuoteRenderer = {
    // rOpenTagWithCapture: /\[quote(\s*)?=(\s*")?(?<username>[^\]\n]*?)(\s*,\s*)?(\w+?)?(\s*:\s*)?(?<id>\d+)?(\s*"\s*)?\][\s]*?[\n]/g,
    rOpenTagWithCapture: /\[quote(\s*)?=(\s*")?([^\]\n]*?)(\s*,\s*)?(\w+?)?(\s*:\s*)?(\d+)?(\s*"\s*)?\]/g,
  
    // rOpenAndCloseTag: /((\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n])(?![\s\S]*?\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n][\s\S]*?\[\/quote\][\s]*?[\n])([\s\S]*?)(\[\/quote\][\s]*?[\n]))/g,
    rOpenAndCloseTag: /((\[quote(?![A-Za-z\n])(?:[^\]]*?)?\])(?![\s\S]*?\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s\S]*?\[\/quote\])([\s\S]*?)(\[\/quote\]))/g,
  
    render: function(plainText) {
      plainText = this.replaceMatchWithHtmlBlockquote(plainText);
      var strippedPlainTextWithBlockquote = this.stripOutUnwantedNewLineChars(
        plainText
      );
      console.log(strippedPlainTextWithBlockquote);
      return easyMDE.markdown(strippedPlainTextWithBlockquote);
    },
  
    replaceMatchWithHtmlBlockquote: function(plainText) {
      if (!plainText) return plainText;
      var self = this,
        matchFound = false;
      var replacedText = plainText.replace(this.rOpenAndCloseTag, function(
        match,
        fullCapture,
        openTag,
        text,
        closeTag
      ) {
        matchFound = true;
        var result = self.rOpenTagWithCapture.exec(openTag);
  
        // Used to reset regex.exec.
        self.rOpenTagWithCapture.lastIndex = 0;
  
        if (result && result.length) {
          var username = result[3],
            id = result[7];
          var blockquote =
            '<span class="position-absolute">&nbsp;</span><aside class="quote mt-2 mb-2"><blockquote>' +
            '<div class="title">' +
            username +
            " said:</div>" +
            text.trim() +
            "</blockquote></aside>";
          return blockquote;
        } else {
          return (
            '<span class="position-absolute">&nbsp;</span><aside class="quote mt-2 mb-2"><blockquote>' +
            text.trim() +
            "</blockquote></aside>"
          );
        }
      });
  
      console.log(matchFound);
      if (matchFound) return self.replaceMatchWithHtmlBlockquote(replacedText);
      return replacedText;
    },
  
    stripOutUnwantedNewLineChars: function(plainText) {
      if (!plainText) return plainText;
      var rThreeNewLineChars = /(\n){3,}/g,
        rLeadingNewLineChars = /(\n){1,}<aside class="quote"><blockquote>/g,
        rTrailingNewLineChars = /<\/blockquote><\/aside>(\n){1,}/g;
  
      strippedText = plainText
        .replace(rThreeNewLineChars, "\n\n")
        .replace(rLeadingNewLineChars, '<aside class="quote"><blockquote>')
        .replace(rTrailingNewLineChars, "</blockquote></aside>");
      return strippedText;
    }
  };
  
  var MentionRenderer = {
    shouldFetchEnteredMentionObjList: false,
    allMentionsRegex: /@([\w]+)/g,
    atKeyCombo: null,
  
    init: function() {
      this.registerTextPasteEvent();
      this.registerAtKeyPressedEvent();
      this.registeChangeEvent();
    },
  
    render: function(plainText) {
      console.log("renderall");
  
      // The Preview grabs the raw text from the editor.
      // We still need to re-render the mentions here.
      var renderedMentionText = MentionRenderer.addLinkToAllValidMentions();
      return renderedMentionText;
    },
  
    renderPreviewWithLinkedMentions: function() {
      // This is used to forcefully change the text in the preview
      // any time mentions have been added to the MentionLab's
      // mentionObjList due to paste event or appending @ character
      // to a valid username.
      var linkedMentions = MentionRenderer.addLinkToAllValidMentions();
      // var markedTextWithLinkedMentions = editor.markdown(linkedMentions)
      var previewHtml = BBCodeQuoteRenderer.render(linkedMentions);
      $(".editor-preview").html(previewHtml);
    },
  
    registeChangeEvent: function() {
      var self = this;
      easyMDE.codemirror.on("change", function(instance, changeObj) {
        // console.log(instance)
        if (MentionRenderer.shouldFetchEnteredMentionObjList) {
          console.log("about to call fetchEnteredMentionObjList");
          MentionRenderer.setShouldFetchEnteredMentionObjList(false);
          usernameList = self.getUniqueAndNewMentionsInEditor();
          MentionObjLab.fetchMentionObjListInEditor(
            usernameList,
            self.onFetchSuccess
          );
        }
      });
    },
  
    onFetchSuccess: function(fetchedMentionObjList) {
      if (fetchedMentionObjList && fetchedMentionObjList.length) {
        MentionObjLab.addMentionObjList(fetchedMentionObjList);
        MentionRenderer.renderPreviewWithLinkedMentions();
      }
    },
  
    getUniqueAndNewMentionsInEditor: function() {
      mentionList = easyMDE.value().match(this.allMentionsRegex);
      if (!mentionList) return [];
      // remove duplicates.
      uniqueMentionList = mentionList.filter(function(item, pos, arr) {
        return arr.indexOf(item) === pos;
      });
      // support > IE9 but twice faster for array as small as five items.
      // uniqueMentionList = [... new Set(mentionList)]
      newUsernameList = this.getOnlyNewUsernameList(uniqueMentionList);
      return newUsernameList;
    },
  
    getOnlyNewUsernameList: function(mentionList) {
      var uniqueUsernameList = [];
      for (var i = 0; i < mentionList.length; i++) {
        var username = mentionList[i].replace("@", "");
        if (!MentionObjLab.isMentionObjPresent(username)) {
          uniqueUsernameList.push({ username: username });
        }
      }
      return uniqueUsernameList;
    },
  
    registerTextPasteEvent: function() {
      var self = this;
      easyMDE.codemirror.on("paste", function(instance, event) {
        // We can't initiate the fetching of mentions here because editor.value()
        // at this point will be empty. We can only set a variable that will be used
        // by the editor's codemirror onChange event which only gets called when editor.value()
        // is set to know when to fetch mentions
        self.setShouldFetchEnteredMentionObjList(true);
      });
    },
  
    registerAtKeyPressedEvent: function() {
      var self = this;
      easyMDE.codemirror.on("keydown", function(instance, event) {
        var code = event.keyCode || event.which;
        if (!self.atKeyCombo && code === 16) {
          self.atKeyCombo = code;
        } else if (self.atKeyCombo === 16 && code === 192) {
          // See comment in registerTextPasteEvent
          self.setShouldFetchEnteredMentionObjList(true);
          return false;
        } else {
          self.atKeyCombo = null;
        }
      });
    },
  
    setShouldFetchEnteredMentionObjList: function(flag) {
      this.shouldFetchEnteredMentionObjList = flag;
    },
  
    addLinkToAllValidMentions: function() {
      textWithLinkedMentons = easyMDE
        .value()
        .replace(this.allMentionsRegex, function(match) {
          var profileURL = MentionObjLab.getProfileURLByUsername(
            match.replace("@", "")
          );
          if (profileURL) {
            return (
              '<a class="mention" href="' + profileURL + '">' + match + "</a>"
            );
          }
          return match;
        });
  
      return textWithLinkedMentons;
    }
  };
  
  MentionRenderer.init();
  
  var MentionObjLab = {
    mentionObjList: [],
  
    addMentionObj: function(mentionObj) {
      if (mentionObj && mentionObj.username && mentionObj.profileURL) {
        this.mentionObjList.push(mentionObj);
      }
    },
  
    addMentionObjList: function(mentionObjList) {
      var self = this;
      mentionObjList.forEach(function(mentionObj) {
        var mentionObj = {
          username: mentionObj.username,
          profileURL: mentionObj.profile_url
        };
        if (
          mentionObj.username &&
          mentionObj.profileURL &&
          !self.isMentionObjPresent(mentionObj)
        ) {
          self.mentionObjList.push(mentionObj);
        }
      });
    },
  
    fetchMentionObjListInEditor: function(usernameList, onSuccess) {
      if (!usernameList.length) return;
      $.ajax({
        url: "/accounts/users/mention-list/",
        data: { username_list: JSON.stringify(usernameList) },
        dataType: "json",
        success: function(data, status) {
          onSuccess(data["user_list"]);
        }
      });
    },
  
    getMentionObjList: function() {
      return this.mentionObjList;
    },
  
    getProfileURLByUsername(username) {
      for (var i = 0; i < this.mentionObjList.length; i++) {
        if (username === this.mentionObjList[i].username) {
          return this.mentionObjList[i].profileURL;
        }
      }
      return null;
    },
  
    isMentionObjPresent: function(mentionObj) {
      for (var i = 0; i < this.mentionObjList.length; i++) {
        if (mentionObj.username === this.mentionObjList[i].username) {
          return true;
        }
      }
      return false;
    }
  };
  
  var MentionDropdown = {
    pattern: /@([\w]+)$/gm,
    startWith: "",
    codemirror: easyMDE.codemirror,
    atCharLeft: null,
    mentionList: [],
    $dropdown: $(".mention-dropdown"),
    // $dropdown: $('.mention-dropdown-wrapper'),
    dropdownItemSelector: ".username-item",
    activeDropdownItemSelector: ".item-active",
  
    init: function() {
      this.$dropdown.css("display", "none");
      this.registerMentionTrigger();
      this.registerFrameChangeEvent();
      this.registerKeyEvent();
      this.registerEditorBlurEvent();
    },
  
    registerFrameChangeEvent: function() {
      self = this;
      self.codemirror.on("refresh", function(instance) {
        self.updateDropDownParameters();
        self.postionDropDown();
      });
  
      $(window).resize(function() {
        self.updateDropDownParameters();
        self.postionDropDown();
      });
  
      $(window).scroll(function() {
        self.updateDropDownParameters();
        self.postionDropDown();
      });
    },
  
    registerKeyEvent: function() {
      var self = this;
      self.codemirror.on("keydown", function(instance, event) {
        var code = event.keyCode || event.which;
        var display = self.$dropdown.css("display");
        if (display !== "block") return;
  
        switch (code) {
          case 13:
            event.preventDefault();
            self.onEnterKeyPressed();
            break;
          case 38:
            event.preventDefault();
            self.onUpKeyPressed();
            break;
          case 40:
            event.preventDefault();
            self.onDownKeyPressed();
            break;
        }
      });
    },
  
    onEnterKeyPressed: function() {
      var $activeDropdownItem = $(this.activeDropdownItemSelector);
      if ($activeDropdownItem) {
        var username = $activeDropdownItem.text();
        var href = $activeDropdownItem.find("a").attr("href");
        if (username && href) this.onMentionItemClicked(username, href);
        return false;
      }
    },
  
    onUpKeyPressed: function() {
      var self = this;
      var $dropdownItem = $(self.dropdownItemSelector);
      var activeClass = self.activeDropdownItemSelector.replace(".", "");
      var $activeItem = self.$dropdown.find(self.activeDropdownItemSelector);
  
      if ($activeItem.index() > 0) {
        $activeItem.toggleClass(activeClass);
        $activeItem.prev().toggleClass(activeClass);
        return false;
      } else {
        $activeItem.toggleClass(activeClass);
        $dropdownItem.eq($dropdownItem.length - 1).toggleClass(activeClass);
        return false;
      }
    },
  
    onDownKeyPressed: function() {
      var self = this;
      var $dropdownItem = $(self.dropdownItemSelector);
      var activeClass = self.activeDropdownItemSelector.replace(".", "");
      var $activeItem = self.$dropdown.find(self.activeDropdownItemSelector);
  
      if ($activeItem.index() < $dropdownItem.length - 1) {
        $activeItem.toggleClass(activeClass);
        $activeItem.next().toggleClass(activeClass);
        return false;
      } else {
        $activeItem.toggleClass(activeClass);
        $dropdownItem.eq(0).toggleClass(activeClass);
        return false;
      }
    },
  
    registerMentionTrigger: function() {
      var self = this;
      self.codemirror.on("change", function(instance, changeObj) {
        console.log("change for mention trigger");
        self.updateDropDownParameters();
        if (self.startWith) {
          self.fetchMentionObjList(self.onFetchMentionObjListSuccess);
        } else {
          self.$dropdown.css("display", "none");
        }
      });
    },
  
    onFetchMentionObjListSuccess: function(mentionObjList) {
      if (mentionObjList && mentionObjList.length) {
        self.$dropdown.css("display", "block");
        self.setDropdown(mentionObjList);
      } else {
        self.$dropdown.css("display", "none");
      }
    },
  
    updateDropDownParameters: function() {
      text = this.getTextBeforeCurPos();
      result = this.getMentionMatch(text);
      if (result && result.groups.username) {
        this.setStartWith(result.groups.username);
        this.setAtCharLeft(result.index);
      } else {
        this.setStartWith("");
      }
    },
  
    registerEditorBlurEvent: function() {
      var self = this;
      $(document).click(function(e) {
        if (
          self.$dropdown.css("display") === "block" &&
          self.$dropdown.has(e.target).length === 0
        ) {
          self.$dropdown.css("display", "none");
        }
      });
    },
  
    getTextBeforeCurPos: function() {
      cursor = this.codemirror.getCursor();
      var currentLine = this.codemirror.getLine(cursor.line);
      var textBeforeCursorPos = currentLine.substring(0, cursor.ch);
      return textBeforeCursorPos;
    },
  
    getMentionMatch: function(textBeforeCursorPos) {
      // this.pattern.exec() may produce inconsitent results.
      // It is more suitable to always used newly declared local
      // variable get the match.
      var patt = /@([\w]+)$/gm;
      var result = patt.exec(textBeforeCursorPos);
      if (result && result.length) {
        result.groups = { username: result[1] };
        return result;
      }
      return null;
    },
  
    setStartWith: function(startWith) {
      this.startWith = startWith;
    },
  
    setAtCharLeft: function(index) {
      cursor = this.codemirror.getCursor();
      this.atCharLeft = this.codemirror.cursorCoords(
        { line: cursor.line, ch: index },
        "window"
      ).left;
    },
  
    fetchMentionObjList: function(onSuccess) {
      if (!this.startWith) return;
      $.ajax({
        url: "/accounts/users/mention/",
        data: { username: this.startWith },
        dataType: "json",
        success: function(data, status) {
          onSuccess(data["user_list"]);
        }
      });
    },
  
    setDropdown: function(newMentionList) {
      var self = this;
      self.mentionList = newMentionList;
      self.$dropdown.html("");
      newMentionList.forEach(function(mention) {
        self.appendDropdownItem(mention);
      });
  
      activeClass = self.activeDropdownItemSelector.replace(".", "");
      $(self.dropdownItemSelector)
        .eq(0)
        .addClass(activeClass);
      self.postionDropDown();
      self.registerDropdownItemClickEvent();
    },
  
    appendDropdownItem: function(mention) {
      var startWithRegex = new RegExp(String(this.startWith), "i"),
        strongStartWithHtml = "<strong>" + this.startWith + "</strong>",
        text = mention["username"].replace(startWithRegex, strongStartWithHtml);
  
      var dropdownItem =
        '<li class="username-item"><a href="' +
        mention["profile_url"] +
        '">' +
        '<img src="' +
        mention["avatar_url"] +
        '"><span>' +
        text +
        "</span></a></li>";
  
      this.$dropdown.append(dropdownItem);
    },
  
    registerDropdownItemClickEvent: function() {
      var self = this;
      $(self.dropdownItemSelector).on("click", function(e) {
        e.preventDefault();
        var username = $(this).text(),
          href = $(this)
            .find("a")
            .attr("href");
        self.onMentionItemClicked(username, href);
      });
    },
  
    postionDropDown: function() {
      if (!this.mentionList) return;
      // Dropdown should appear above the current cursor position.
      var top = this.codemirror.cursorCoords().top - this.$dropdown.height() - 3;
      var windowTop = this.codemirror.cursorCoords(true, "window").top;
  
      // If the dropdown has crossed the window re-adjust it
      // to appear below the curren position
      if (this.$dropdown.height() > windowTop) {
        top = this.codemirror.cursorCoords().top + 20;
      }
  
      this.$dropdown.css({
        left: this.atCharLeft + 10.5,
        top: top
      });
    },
  
    onMentionItemClicked: function(username, profileURL) {
      if (!username || !profileURL) return;
      cursor = this.codemirror.getCursor();
      var textBeforeCursorPos = this.getTextBeforeCurPos(),
        mention = "@" + username.toLowerCase(),
        mentionObj = { username: username, profileURL: profileURL };
      MentionObjLab.addMentionObj(mentionObj);
      var mentionPlusSpace = textBeforeCursorPos.replace(
        this.pattern,
        mention + " "
      );
      this.codemirror.setSelection({ line: cursor.line, ch: 0 }, cursor);
      this.codemirror.replaceSelection(mentionPlusSpace);
      this.codemirror.focus();
    }
  };
  
  MentionDropdown.init();
  
  // $('.btn-primary').on('click', function(e) {
  //     e.preventDefault()
  //     console.log('click')
  //     console.log(JSON.parse(JSON.stringify(editor.value())))
  //     // console.log(JSON.parse(editor.codemirror.getValue()))
  
  // })
  