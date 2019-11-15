
var plainTextLengthCache = 0;
var plainTextCache = "";
var simplemde = new SimpleMDE({
    // autofocus: true,
    // element: document.getElementById("NA"),

    previewRender: function(plainText) {
        if (plainText !== null && plainText !== "" && plainText.length === plainTextLengthCache) {
            return this.parent.markdown(plainTextCache);
        } 

        // User all_username_list_cache to validate all the mentions in the textarea
        // before rendering them as links.
        var username_regex = /@(?<username>[\w]+)/g
        plainText = plainText.replace(username_regex, function (match){
            for(var i = 0; i < all_username_list_cache.length; i++) {
                var mention = '@' + all_username_list_cache[i]['username'];
                if (match === mention) {
                    return '<a class="mention" href="' + all_username_list_cache[i]['profile_url'] +'">' + match + '</a>';
                }
            }
            return match;            
        });

        plainTextLengthCache = plainText.length;

        // Match [quote  only if charater A-Za-z and newline character does not follow
        // Match as many characters except ] (closing square bracket) if present  
        // Match ] and as many whitespace character if present and a compulsory new line character
        var quoteStartTagRegex = /(\[quote)(?![A-Za-z\n])([^\]]*?)?(\])[\s]*?[\n]/g;  
        var quotePlaceHolderStartTagRegex = /\[quote(\s*)?=(\s*")?(?<username>[^\]\n]*?)(\s*,\s*)?(\w+?)?(\s*:\s*)?(?<id>\d+)?(\s*"\s*)?\][\s]*?[\n]/g;
        var quoteEndTagRegex = /\[\/quote\][\s]*?[\n]*?/g
        var quoteSyntaxRegex = /((\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n])(?![\s\S]*?\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n][\s\S]*?\[\/quote\][\s]*?[\n])([\s\S]*?)(\[\/quote\][\s]*?[\n]))/g;
                            
        if (plainText !== null && plainText !== "") {
            var t0 = performance.now();
            var placeHolderStartTagCount = ((plainText || '').match(quotePlaceHolderStartTagRegex) || []).length;
            var startTagCount = ((plainText || '').match(quoteStartTagRegex) || []).length;
            var endTagCount = ((plainText || '').match(quoteEndTagRegex) || []).length;
            var startTagTotalCount = placeHolderStartTagCount + startTagCount;
            var tagLength = (startTagTotalCount <= endTagCount) ? startTagTotalCount : endTagCount;
            for (var count = 0; count < tagLength; count++) {
                var placeHolderStartTagTest = ((plainText || '').match(quotePlaceHolderStartTagRegex) || []).length > 0;
                var endTagTest = ((plainText || '').match(quoteEndTagRegex) || []).length > 0;
                var startTagTest = ((plainText || '').match(quoteStartTagRegex) || []).length > 0;
                if ((placeHolderStartTagTest && endTagTest) || (startTagTest && endTagTest)) {                
                    plainText = plainText.replace(quoteSyntaxRegex, function(match, fullCapture, startTag, text, endTag) { 
                        var result = quotePlaceHolderStartTagRegex.exec(startTag);
                        quotePlaceHolderStartTagRegex.lastIndex = 0;
                        if (result !== null && result !== "" && result.groups.username !== "") {
                            var username = result.groups.username;
                            var id = result.groups.id;
                            // console.log("COUNTER " + " USERNAME: " + username);
                            // console.log("COUNTER " +  " ID: " + id);
                            var blockquote = '<aside class="quote"><blockquote>'
                                    + '<div class="title">' + username + ' said:</div>'
                                    + text.trim()
                                    +'</blockquote></aside>';
                            return blockquote;
                        } 
                        else if (startTagTest && endTagTest) {
                            var blockquote = '<aside class="quote"><blockquote>'
                                             + '<p>' + text.trim() + '</p>'
                                             + '</blockquote></aside>';
                            return blockquote;
                        } else {
                            var html = startTag + text + endTag;
                            return html;
                        }
                        });                                                                        
                } else { 
                        break;
                }
            }
        } 
        var threeNewLineChars = /(\n){3,}/g;
        var blockquoteLeadingNewLineChars = /(\n){1,}<aside class="quote"><blockquote>/g;
        var blockquoteTrailingNewLineChars = /<\/blockquote><\/aside>(\n){1,}/g;
        var afterThreeNewLines = plainText.replace(threeNewLineChars, "\n\n");
        var afterLeadingNewLinesChars = 
                    afterThreeNewLines.replace(blockquoteLeadingNewLineChars, '<aside class="quote"><blockquote>');
        plainText = afterLeadingNewLinesChars.replace(blockquoteTrailingNewLineChars, '</blockquote></aside>');
        plainTextCache = plainText;
        var t1 = performance.now();
        
        // console.log("Call to doSomething took " + (t1 - t0) + " milliseconds.");
        return this.parent.markdown(plainText); // Returns HTML from a custom parser
    },

    showIcons: ["code"],

    spellChecker: false,
});

var incomplete_name_cache = '';
var cursorPosCache = '';  // Cached current cursor position
var username_list_cache = [];
var all_username_list_cache = [] // List of valid mention entered so far

// Replace the chars entered excluding the @ with selected username
// and space when the enter or return key is pressed.
simplemde.codemirror.on('keydown', function (instance, event) {
    var code = event.keyCode || event.which;

    var display = $('.username-suggest').css('display')
    
    if (code === 13 && display === 'block') {  // Enter key
        // Prevent the cursor from moving to the next line
        event.preventDefault();   
        setUsername(incomplete_name_cache, $('.item-active').text(), cursorPosCache)
        updateAllUserNameListCache();
    }

    // Handle the up key event if the dropdown is visible.
    else if (code == 38 && display === 'block') {  // Up key
        // Prvent the cursor from moving to the beginning of the line
        event.preventDefault();
        $('.username-item').each(function (index) {
            var list_item = $(this)
            if( list_item.hasClass('item-active') ) {
                if (index === 0) {
                    var last_item_index = $('.username-item').length - 1
                    list_item.removeClass('item-active')
                    $('.username-item').eq(last_item_index).addClass('item-active')
                    return false;
                } else {
                    list_item.removeClass('item-active')
                    list_item.prev().addClass('item-active')
                    return false;
                }
            }
        })
    }    
});


// Handled up and down arrow key to move active username in the
// dropdown. This event may not handle the return or enter key pressed
// event properly
simplemde.codemirror.on('keyHandled', function (instance, name, event) {
    var code = event.keyCode || event.which;
    

    var display = $('.username-suggest').css('display')

    // Handle down arrow key event if the dropdown is visible.
    if (code == 40 && display === 'block') { 
        $('.username-item').each(function (index) {
            var list_item = $(this)
            if( list_item.hasClass('item-active') ) {
                if (index === ($('.username-item').length - 1)) {
                    list_item.removeClass('item-active')
                    $('.username-item').eq(0).addClass('item-active')
                    return false;
                } else {
                    list_item.removeClass('item-active')
                    list_item.next().addClass('item-active')                    
                    return false;
                }
            }
        })
    }
});


// This listens for mentioned username by simply checking the server
// when the user start typing the username with @ and presents a
// dropdown containing list of matching usernames
simplemde.codemirror.on("change", function(instance, changeObj) {
    console.log(changeObj.origin)
    // current cursor position
    const cursorPos = this.simplemde.codemirror.getCursor(); 

    // To be used in key event listeners and in helper 
    // functions
    cursorPosCache = cursorPos  
   
    // Set the dropdown to none. This will ensure that the dropdown
    // remains invisible when there is no matching string.
    $('.username-suggest').css('display', 'none')

    var username_list_to_send = get_username_list_to_send()

    updateAllUserNameListCache();

    // Pattern that matches the last occurence of '@username' in a string
    var m_regex = /@(?<username>[\w]+)$/gm   

    // Use getLine method to retrieve the current line string in the
    // current cursor position.
    var current_line = this.simplemde.codemirror.getLine(cursorPos.line)

    // Extract the text from the beginning of the line to the current cursor
    // position using the ch position (character).
    var extractedText = current_line.substring(0, cursorPos.ch)    

    // Check for '@username' pattern in the extracted text.
    var m_res = m_regex.exec(extractedText)
      
    if (m_res !== null && m_res !== "" && m_res.groups.username !== "") {
        var username = m_res.groups.username

        // To be used when the return key is pressed
        incomplete_name_cache = username; 
        
        // Get the left offset of the '@'character in current line 
        // using index of the matched pattern as ch position to
        // ensure that the dropdown always stay at the bottom of
        // the @username text entered.
        var cursorLeft = this.simplemde
                             .codemirror
                             .cursorCoords({
                                line: cursorPos.line,
                                ch: m_res.index
                             }, 'window').left

        var cursorTop = this.simplemde.codemirror.cursorCoords().top    

        var matched_username_list = []

        // Search for the text in the cache first and assign the results
        // to matched_username_list array if there is any.
        for (var i = 0; i < username_list_cache.length; i++) {
            if(username_list_cache[i]['username'].startsWith(username)) {
                matched_username_list.push(username_list_cache[i])
            } 
        }

        // If there is an matched username populate the dropdown.
        if (matched_username_list.length > 0) {    
            setAllUserNameListCache(matched_username_list)
            setSuggestionDropdown(matched_username_list, cursorLeft, cursorTop)
        }

        // If there is no any matched username, Check the server. 
        // populate the dropdown if there is any result and also 
        // populate the username_list_cache.
        if (matched_username_list.length === 0) {
            $.ajax({
                url: "/accounts/users/mention/",
                data: { 'username':  username },
                dataType: 'json',
                success: function(data, status) {
                    var username_list = data['user_list']
                    username_list_cache = username_list
                    setAllUserNameListCache(username_list)
                    if (username_list.length > 0) {
                        setSuggestionDropdown(username_list, cursorLeft, cursorTop)
                    } 
                }
            });
        }   
    } 
    else if ( username_list_to_send.length > 0 && 
        (changeObj.origin === 'paste' || changeObj.origin === '+input' || changeObj.origin === '+delete') ) {
        renderValidNamesInText(username_list_to_send, cursorPos)
    }
});


simplemde.codemirror.on("refresh", function(instance) {
    $('.username-suggest').css('display', 'none')
});

// simplemde.codemirror.on("viewportChange", function(instance, from, to) {
//     this.simplemde.codemirror.focus();
// });

$( window ).resize(function() {
  $('.username-suggest').css('display', 'none')
});

function get_username_list_to_send() {
    var m_regex = /@(?<username>[\w]+)/g;
    return get_useful_name_list(
        [... new Set(simplemde.value().match(m_regex))]
    )
}

// Populate, position and positon the dropdown with the given
// parameters.
function setSuggestionDropdown(username_list, cursorLeft, cursorTop) {
    var li = ''
    for (var i = 0; i < username_list.length; i++) {   
            var profile_url = username_list[i]['profile_url']
            var avatar_url = username_list[i]['avatar_url']        
            var reg = new RegExp(String(incomplete_name_cache), 'i')
            var t = '<strong>' + incomplete_name_cache + '</strong>'
            var strong_text = username_list[i]['username'].replace(reg, t)
            var img = '<img src="' + avatar_url + '">'
            li += '<li class="username-item"><a href="' + profile_url + '">' + 
                      img + '<span>' + strong_text + '</span>' + 
                  '</a></li>'
    }

    var username_suggest = $('.username-suggest')
    username_suggest.css('display', 'block')
    username_suggest.html('')
    username_suggest.html('<ul>' + li + '</ul>')
    var username_item = $('.username-item');
    username_item.eq(0).addClass('item-active');

    var count = username_list.length === 1 ? 0 : username_list.length

    // Position the dropdown containing list of users
    username_suggest.css({
        left: cursorLeft + 17,
        top: cursorTop - 30 - (count * 23),
    });

    username_item.on('click', function (e) {
        e.preventDefault()
        setUsername(incomplete_name_cache, $(this).text(), cursorPosCache)
    });
}

// Replace the chars entered excluding the @ with selected username
// and space.
function setUsername(incomplete_name, selected_name, cursorPos) {
    var m_regex = /@(?<username>[\w]+)$/gm
    var current_line = this.simplemde.codemirror
                                     .getLine(cursorPos.line)
    var extractedText = current_line.substring(0, cursorPos.ch)
    var mention_text = '@' + selected_name.toLowerCase();
    var newExtractedText = extractedText.replace(m_regex,  mention_text + ' ')
    simplemde.codemirror.setSelection({line: cursorPos.line, ch: 0}, cursorPos);
    simplemde.codemirror.replaceSelection(newExtractedText);
    simplemde.codemirror.focus();
}


// Initialize the cache that will be used for to determine what mentions
// should be retrieved from the server after a text is pasted. And used
// by the previewRender in validating all the mentions.
function setAllUserNameListCache(username_list) {
    if (all_username_list_cache.length > 0) {
        for (var i = 0; i < username_list.length; i++) {    
            var can_add = true                    
            for (var j = 0; j < all_username_list_cache.length; j++) {
                if (username_list[i]['username'] === all_username_list_cache[j]['username']) {
                   can_add = false;
                   break
                }                                
            }
            if (can_add) all_username_list_cache.push(username_list[i])
        }
    } else {
        all_username_list_cache = username_list
    }
}


// Remove any unused mentions from the user_name_list_cahe.
// This may improve performance if the user system is running
// out of memory.
function updateAllUserNameListCache() {
    m_regex2 = /@(?<username>[\w]+)/g;
    var useful_name_list = simplemde.value().match(m_regex2);
    if (all_username_list_cache.length > 0 && 
        useful_name_list !== null && useful_name_list !== '' ) {
        for (var i = 0; i < all_username_list_cache.length; i++) {
            var can_remove = true;
            for (var j = 0; j < useful_name_list.length; j++) {
                var mention = '@' + all_username_list_cache[i]['username']
                if  ( mention === useful_name_list[j] ) {
                    can_remove = false;
                    break;
                }
            }
            if (can_remove) all_username_list_cache.splice(i, 1);
        }
    }
}

function get_useful_name_list(useful_name_list) {
    var username_list_to_send = []        
    for (var i = 0; i < useful_name_list.length; i++) {
        var can_add = true
        var username = useful_name_list[i].replace('@', '')
        for (var j = 0; j < all_username_list_cache.length; j++) {
            if (username === all_username_list_cache[j]['username']) {
                can_add = false;
                break;
            }
        }

        if (can_add) username_list_to_send.push({username: username})
    }
    return username_list_to_send
}


// When a text containing valid mentions is pasted or @ is added to an 
// existing valid username the preview will render the text without 
// formating the mentions despite this line is called before
// the previewRender gets called. This is because ajax is asynchronous. We
// have set textarea manually once the process is done and after the 
// all_user_name_list_cache has been set.
function renderValidNamesInText(username_list_to_send, cursorPos){
    $.ajax({
        url: "/accounts/users/mention-list/",
        data: { 'username_list': JSON.stringify(username_list_to_send) },
        dataType: 'json',
        success: function(data, status) {
            setAllUserNameListCache(data['user_list'])
            // Reset the plaintextCache so that the preview can render
            // the all valid names.
            plainTextLengthCache = 0;
            plainTextCache = "";
            simplemde.value(simplemde.value())
            // Set the cursor at the ending of the text.
            simplemde.codemirror.setCursor(cursorPos);                    
        }
    });
}   
