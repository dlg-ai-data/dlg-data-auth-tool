// pagination 이동
function pageForm(index) {
    $("#page").val(index);
    $('#searchForm').submit();
}

// 페이지 이동
function fnMovePage(path) {
    if (path) {
        location.href = path;
    }
}

// textarea에 입력된 문자가 단어인지 아닌지 검증 함수
function cfnIsWord(str) {

    let isWord = false;
    if (str) {
        for (let i = 0; i < str.length; i++) {
            let code = str.charCodeAt(i);

            if ((code > 47 && code < 58) || // 숫자 (0-9)
                (code > 64 && code < 91) || // 알파벳 대문자 (A-Z)
                (code > 96 && code < 123) || // 알파벳 소문자 (a-z)
                (code > 44032 && code < 55203) || //한글
                (code >= 33 && code <= 47) || //특수문자
                (code >= 58 && code <= 64) || //특수문자
                (code >= 91 && code <= 96) || //특수문자
                (code >= 123 && code <= 126)  //특수문자
            ) {
                isWord = true;
                return isWord;
            }
        }
    }
    return isWord;
}

// get wordcount function
function cfnWordValidator(text) {
    let wordCount = 0;
    text = text.replaceAll("\n", ' ');

    /*
    //단어 수 측정할 때 split
    let textArr = text.split(' ');

    for (let i = 0; i <= textArr.length; i++) {
        if (textArr[i] !== ' ' && cfnIsWord(textArr[i])) {
            wordCount++;
        }
    }
     */
    // 글자수 count 할 때 split
    let textArr = text.split("");

    textArr = textArr.filter(word => word !== " ");

    wordCount = textArr.length;

    return wordCount;
}

// 선택된 TEXT Count
function cfnSelectWordCounter() {
    if (window.getSelection) {
        let selCount = cfnWordValidator(window.getSelection().toString());
        return selCount;
    }

}

// clipboard 복사시 text replace
function cfnCustomBindPaste(e) {
    e.preventDefault();
    let pastedText;
    let clipboard = (e.originalEvent || e).clipboardData;
    if (clipboard === undefined || clipboard === null) {
        pastedText = window.clipboardData.getData("text") || "";
        if (pastedText !== "") {
            pastedText = cfnReplaceText(pastedText);
            if (window.getSelection) {
                let newNode = document.createElement("span");
                newNode.innerHTML = pastedText;
                window.getSelection().getRangeAt(0).insertNode(newNode);
            } else {
                document.selection.createRange().pasteHTML(pastedText);
            }
        }
    } else {
        pastedText = clipboard.getData('text/plain') || "";
        if (pastedText !== "") {
            pastedText = cfnReplaceText(pastedText);
            document.execCommand('insertText', false, pastedText);
        }
    }
}

// text 가공 function
function cfnReplaceText(text){
    if(text){
        text = text.replaceAll(/\s{2,}/g, ' ');
        text = text.replaceAll(/[\n\r]+/g, '');
    }
    return text;
}