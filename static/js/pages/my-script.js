// 주소 검색
function execDaumPostcode() {
    const width = 500; //팝업의 너비
    const height = 600; //팝업의 높이

    new daum.Postcode({
        oncomplete: (data) => {
            // 팝업에서 검색결과 항목을 클릭했을때 실행할 코드를 작성하는 부분.

            // 각 주소의 노출 규칙에 따라 주소를 조합한다.
            // 내려오는 변수가 값이 없는 경우엔 공백('')값을 가지므로, 이를 참고하여 분기 한다.
            let addr = ''; // 주소 변수
            let extraAddr = ''; // 참고항목 변수

            //사용자가 선택한 주소 타입에 따라 해당 주소 값을 가져온다.
            if (data.userSelectedType === 'R') { // 사용자가 도로명 주소를 선택했을 경우
                addr = data.roadAddress;
            } else { // 사용자가 지번 주소를 선택했을 경우(J)
                addr = data.jibunAddress;
            }

            // 사용자가 선택한 주소가 도로명 타입일때 참고항목을 조합한다.
            if (data.userSelectedType === 'R') {
                // 법정동명이 있을 경우 추가한다. (법정리는 제외)
                // 법정동의 경우 마지막 문자가 "동/로/가"로 끝난다.
                if (data.bname !== '' && /[동|로|가]$/g.test(data.bname)) {
                    extraAddr += data.bname;
                }
                // 건물명이 있고, 공동주택일 경우 추가한다.
                if (data.buildingName !== '' && data.apartment === 'Y') {
                    extraAddr += (extraAddr !== '' ? ', ' + data.buildingName : data.buildingName);
                }
                // 표시할 참고항목이 있을 경우, 괄호까지 추가한 최종 문자열을 만든다.
                if (extraAddr !== '') {
                    extraAddr = ' (' + extraAddr + ')';
                }
                // 검색한 주소와 참고항목을 합친다.
                addr += extraAddr;

            }

            document.getElementById('postcode').value = data.zonecode;
            document.getElementById("address").value = addr;

            document.getElementById("detailAddress").focus(); // 상세 주소 입력란 포커스
        }
    }).open({
        /**
         * 팝업창 화면 중앙 배치
         */
        left: (window.screen.width / 2) - (width / 2),
        top: (window.screen.height / 2) - (height / 2),
        /*
         * 화면 여러개 띄워지는 현상 막아줌.
         */
        popupName: 'Search_address'
    });
}

function isValid_RRN(rrn1, rrn2) {

    const yy = rrn1.substr(0, 2);        // 년도
    const mm = rrn1.substr(2, 2);        // 월
    const dd = rrn1.substr(4, 2);        // 일
    const genda = rrn2.substr(0, 1);        // 성별
    let cc;

    // 길이가 6이 아닌 경우
    if (rrn1.length != 6) {
        return {message: "주민등록번호 앞자리를 다시 입력하세요.", result: false};
    }

    // 첫번째 자료에서 연월일(YYMMDD) 형식 중 기본 구성 검사
    if (yy < "00"
        || yy > "99"
        || mm < "01"
        || mm > "12"
        || dd < "01"
        || dd > "31") {
        return {message: "주민등록번호 앞자리를 다시 입력하세요.", result: false};
    }

    // 길이가 7이 아닌 경우
    if (rrn2.length != 7) {
        return {message: "주민등록번호 뒷자리를 다시 입력하세요.", result: false};
    }

    // 성별부분이 1 ~ 4 가 아닌 경우
    if (genda < "1" || genda > "4") {
        return {message: "주민등록번호 뒷자리를 다시 입력하세요.", result: false};
    }

    // 연도 계산 - 1 또는 2: 1900년대, 3 또는 4: 2000년대
    cc = (genda == "1" || genda == "2") ? "19" : "20";
    // 첫번째 자료에서 연월일(YYMMDD) 형식 중 날짜 형식 검사
    if (isValidDate(cc + yy + mm + dd) == false) {
        return {message: "주민등록번호 앞자리를 다시 입력하세요.", result: false};
    }

    // Check Digit 검사
    if (!isSSN(rrn1, rrn2)) {
        return {message: "입력한 주민등록번호를 검토한 후, 다시 입력하세요.", result: false};
    }
    return {result: true};
}

function isValid_TEL(tel1, tel2, tel3) {

    // 길이가 6이 아닌 경우
    if (tel1.length < 2) {
        return {message: "연락처 앞 부분을 다시 입력하세요.", result: false};
    }
    // 길이가 6이 아닌 경우
    if (tel2.length < 3) {
        return {message: "연락처 중간 부분을 다시 입력하세요.", result: false};
    }
    // 길이가 6이 아닌 경우
    if (tel3.length < 4) {
        return {message: "연락처 끝 부분을 다시 입력하세요.", result: false};
    }

    return {result: true};
}

function isValid_BANK(code, no) {
    if (code !== '' && no !== '') {
        return true;
    } else
        return false;
}

function isValidDate(iDate) {
    if (iDate.length != 8) {
        return false;
    }

    oDate = new Date();
    oDate.setFullYear(iDate.substring(0, 4));
    oDate.setMonth(Number(iDate.substring(4, 6)) - 1);
    oDate.setDate(iDate.substring(6));
    if (Number(oDate.getFullYear()) != Number(iDate.substring(0, 4))
        || Number(oDate.getMonth() + 1) != Number(iDate.substring(4, 6))
        || Number(oDate.getDate()) != Number(iDate.substring(6))) {

        return false;
    }

    return true;
}

function isSSN(s1, s2) {
    let n = 2;
    let sum = 0;
    for (let i = 0; i < s1.length; i++)
        sum += Number(s1.substr(i, 1)) * n++;
    for (let i = 0; i < s2.length - 1; i++) {
        sum += Number(s2.substr(i, 1)) * n++;
        if (n == 10) n = 2;
    }

    c = 11 - sum % 11;
    if (c == 11) c = 1;
    if (c == 10) c = 0;
    if (c != Number(s2.substr(6, 1))) return false;
    else return true;
}

const swalFire = async (title, text, icon, confirmButtonText) => {
    await swal.fire({
        title: title,
        text: text,
        icon: icon,
        buttonsStyling: false,
        confirmButtonText: confirmButtonText,
        customClass: {
            confirmButton: "btn font-weight-bold btn-light-primary"
        }
    }).then(function () {
        KTUtil.scrollTop();
    });
}

// 이메일 정규식
const regExp_ID = /^[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}$/i;
// 패스워드 정규식
const regExp_PW_NUM = /[0-9]/g;
const regExp_PW_ENG = /[a-z]/ig;
const regExp_PW_SPECIAL = /[`~!@@#$%^&*|₩₩₩'₩";:₩/?]/gi;

function chkPW(pw) {
    const num = pw.search(regExp_PW_NUM);
    const eng = pw.search(regExp_PW_ENG);
    const spe = pw.search(regExp_PW_SPECIAL);
    if (pw.length < 8 || pw.length > 20) {
        return "8자리 ~ 20자리 이내로 입력해주세요.";
    } else if (pw.search(/\s/) != -1) {
        return "비밀번호는 공백 없이 입력해주세요.";
    } else if (num < 0 || eng < 0 || spe < 0) {
        return "영문,숫자,특수문자 혼합하여 입력해주세요.";
    }
    return "";
}

const swalWithBootstrapButtons = Swal.mixin({
    customClass: {
        confirmButton: 'btn btn-light-success',
        cancelButton: 'btn btn-light-danger'
    },
    buttonsStyling: false
})

$(document).ajaxError(function (event, jqxhr, settings, exception) {	// jquery Ajax Error 시 호출
//	console.log("jqxhr.status : " + jqxhr.status);
    //jqxhr, exception
    var cont = "";
    //AnnotationExceptionHandler에서 생성된 에러처리(10000, 10001, 10009)
    if (jqxhr.status == 10000) {
        cont = 'System Exception. (' + jqxhr.responseText.message + ')';
    } else if (jqxhr.status == 10001) {
        cont = 'Data Access Exception. (' + jqxhr.responseText.message + ')';
    } else if (jqxhr.status == 10009) {
//		console.log("jqxhr : " + JSON.stringify(jqxhr));
//		console.log("jqxhr.responseText : " + jqxhr.responseText);
        cont = 'Exception. (' + jqxhr.responseText.message + ')';
    } else if (jqxhr.status === 0) {
        //더블클릭 등에서 오작동..단순 취소에서도 예외 발생하여 메시지 방지시킴
        cont = 'Not connect. Verify Network.(' + exception + ')';
    } else if (jqxhr.status == 404) {
        cont = 'Requested page not found. [404].(' + exception + ')';
    } else if (jqxhr.status == 500) {
        cont = 'Internal Server Error [500].(' + exception + ')';
    } else if (exception === 'parsererror') {
        cont = 'Requested JSON parse failed.';
    } else if (exception === 'timeout') {
        cont = 'Time out error.';
    } else if (exception === 'abort') {
        cont = 'Ajax request aborted.';
    } else {
        cont = 'Uncaught Error. (' + exception + ')';
        //cont = 'Uncaught Error.<br/>' + $.parseJSON(jqxhr.responseText).message;
    }
    //settings
    var err = '- url : ' + settings.url + '<br/>';
    err += '- data : ' + settings.data + '<br/>';
    err += '- dataType : ' + settings.dataType + '<br/>';
    err += '- type : ' + settings.type + '<br/>';
    err += '- async : ' + settings.async + '<br/>';
    err += '- exception : ' + cont;

    //팝업창 타이틀
    var $title = $("<div style='color:#fff;background:#ff6600;padding:8px 3px 6px 8px;'>예외사항발생</div>");
    //팝업창 내용
    var $contents = $("<div style='background:#fff;border:solid 1px #d0d0d0;padding:10px;margin:10px;height:175px;overflow:auto;'>" + err + "</div>");
    //팝업창
    var $div = $("<div style='position:absolute;top:200px;left:200px;border:solid 1px #ff6600;background:#e8e8e8;font-size:12px;width:400px;height:250px;z-index:1000;'></div>");
    //닫기 버튼
    var $button = $("<div style='position:absolute;top:8px;right:8px;cursor:pointer;color:#fff;font-weight:bold;'>X</div>");
    $button.bind('click', function () {
        $div.remove();
    });//$div.remove()
    //조립하고 Body에 붙임
    $title.append($button);
    $div.append($title);
    $div.append($contents);

    if (jqxhr.status !== 0) $div.appendTo("body");
}).ajaxStart(function () { 							// 1. jquery Ajax 첫번째 요청이 시작될때 호출
    $("input[type='submit'], button[type='submit']").addClass("spinner").addClass("spinner-left");
}).ajaxSend(function (event, jqxhr, settings) {		// 2. jquery Ajax 데이터 요청전 호출
}).ajaxComplete(function (event, jqxhr, settings) { 	// 3. jquery Ajax 성공 여부와 상관없이 완료시 호출
}).ajaxStop(function () { 	// 4. jquery Ajax 모든 요청이 완료되면 호출
    $("input[type='submit'], button[type='submit']").removeClass("spinner").removeClass("spinner-left");
});

$(function () {
    $('[data-toggle="tooltip"]').tooltip()
})

let arrows;
if (KTUtil.isRTL()) {
    arrows = {
        leftArrow: '<i class="la la-angle-right"></i>',
        rightArrow: '<i class="la la-angle-left"></i>'
    }
} else {
    arrows = {
        leftArrow: '<i class="la la-angle-left"></i>',
        rightArrow: '<i class="la la-angle-right"></i>'
    }
}

const set_daterangepicker = (selector, options = {}) => {
    $(selector).daterangepicker(options, function (start, end, label) {
        $(selector + ' .form-control').val(start.format('YYYY-MM-DD') + ' ~ ' + end.format('YYYY-MM-DD'));
    });
}

// 입력받은 값이 공백문자인지 체크
const isBlank = (value) => {
    if (value.length === 0 || value === null)
        return true;
    else
        return false;
}

// 입력받은 값이 숫자인지 체크
const isNumeric = (value) => {
    const regExp = /^[0-9]+$/g;
    return regExp.test(value);
}

// 입력받은 금액에 콤마 표시
const currencyFormatter = (money) => {
    return money.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

jQuery(document).ready(function () {
    $('.table_function').keypress((e) => {
        if(e.which === 13) {
            return false;
        }
    })
    $(document).keyup(function (e) {
        if (e.keyCode == 27) {
            $('.modal').modal('hide');
        }
        if (e.keyCode == 13) {
            // modal이 show 상태라면 enter 키를 눌렀을 때 필터링 적용 실행
            if ($(".modal:not(#user_search_Modal)").hasClass('show')) {
                $('#apply_bth').click();
            }
            $('#login_btn').click();
        }
    });

    $('.ki-close').parent().attr('title', '단축키: [ESC]')
    $('.ki-close').parent().tooltip()

    $('.img_go').on('click', (e) => {
        const img_url = $(e.currentTarget).children().attr('src')
        window.open(img_url, 'img_window')
    })


    $('.accordion_title').each((index, item) => {
        if ($(item).children(":first").hasClass('collapsed')) {
            $(item).css('border-radius', '0.42rem');
        } else {
            $(item).css('border-radius', '0.42rem 0.42rem 0 0');
        }
    });

    // 테이블 검색어 입력 후 엔터키로 submit 가능케 함.
    $("#table-data-search").keypress((e) => {
        if (e.which === 13) {
            $("#page").val(1);
            $('#searchForm').submit();
        }
    })

    // 모든 page에 있는 subheader의 너비는 그 페이지 컨텐츠의 너비와 같게.
    $(".subheader").css('width', $('.page-content').width() - 26)
    $(".subheader").children(":first").css("padding", 0)

    // 금액을 입력받은 input 태그에 focus되면 콤마사라짐.
    $('.inputPrice').on('focus', () => {
        let number = $('.inputPrice').val();
        if (!isBlank(number)) {
            number = number.replace(/,/g, '');
            $('.inputPrice').val(number);
        }
    });

    // 금액을 입력받은 input 태그가 focus를 잃으면 콤마 들어감.
    $('.inputPrice').on('blur', () => {
        let number = $('.inputPrice').val();
        if (!isBlank(number) && isNumeric(number)) {
            number = currencyFormatter(number);
            $('.inputPrice').val(number);
        }
    })

    // Y-m-d + ' ' + (H:i)으로 나타나는 데이터를 ' '대신 <br> 넣기
    $.each($('.two_line_date'), function (index, item) {
        $(item).html($(item).text().trim().replace(' ', '<br>'))
    });

    // START: 테이블 컬럼 클릭 시 정렬해주는 기능과 관련된 JS 코드
    // 정렬이 기준이 되는 컬럼이 무엇인지 눈에 띄게 해줌.
    $.each($('.sort'), function (index, item) {
        if ($(item).data('sort-criterion') === $('#sort_criterion').val()) {
            $(item).data('upDown', $('#upDown').val())
            $(item).css('color', '#63cdda');
            if ($('#upDown').val() === '-') {
                $(item).removeClass('sort_default');
                $(item).addClass('sort_desc');
            } else {
                $(item).removeClass('sort_default');
                $(item).addClass('sort_asc');
            }
        }
    });
    $('.sort').on('click', (e) => {
        $('#sort_criterion').val($(e.currentTarget).data('sort-criterion'));
        if ($(e.currentTarget).data('upDown') === '') {
            $('#upDown').val('-');
        } else if ($(e.currentTarget).data('upDown') === '-') {
            $('#upDown').val('+');
        } else {
            $('#upDown').val('-');
        }
        $("#page").val(1);
        $('#searchForm').submit();
    })
    // END: 테이블 컬럼 클릭 시 정렬해주는 기능과 관련된 JS 코드

    multiple_select_dataset('#select_dataset_name')
    // select 가 hide 될 때 선택되어 있는 값 submit
    $('#select_dataset_name').on('hide.bs.select', function (e) {
        // 원래 선택했던 데이터세트들인지 판단 후 페이지 새로 불러옴.
        if (!compareArray(previous_selected_list, temp_list)) {
            $("#page").val(1);
            $("#searchForm").submit();
        }
    });

    // modal hide 될 때 초기화
    $('.modal:not(.user_search_Modal, .table_filter_modal)').on('hidden.bs.modal', function (e) {
        $(e.currentTarget).find('form')[0].reset()
        $('.valid-feedback').empty();
        $('.invalid-feedback').empty();
        $('#save_date').datepicker('setDate', null);
    });
    $('.modal').draggable({
        handle: ".modal-header"
    });
});

// selectBox show 할 때 이미 선택했던 value 들을 받음.
let previous_selected_list = null;
let temp_list = null;

// START: 데이터세트 다중 선택 select 관련 코드
const multiple_select_dataset = (selector) => {
    $(selector).on('show.bs.select', function () {
        previous_selected_list = $(this).val();
        temp_list = [...previous_selected_list];
    })
    // show 상태에서 값이 선택될 때 마다 event
    $(selector).on('change', function () {
            // 선택한 value 들이 모여있는 list
            const items = $(this).val();

            // case 1: all 선택시 나머지 선택 모두 취소
            if (!temp_list.includes('all') && items.includes('all')) {
                // 먼저 모든 option 의 selected 를 false 로 만들고 all 을 선택.
                $(selector + ' option').prop('selected', false);
                $(selector + 'option:eq(0)').prop('selected', true);
                $(selector).parent().find('.dropdown-menu.inner').children().removeClass('selected');
                $(selector).parent().find('.dropdown-menu.inner').children().children().removeClass('selected');
                $(selector).parent().find('.dropdown-menu.inner').children().first().addClass('selected');
                temp_list = ['all']
            }

            // case 2: all 이 선택되어 있을 때 다른 데이터세트 선택시 all 선택 취소
            else if (temp_list.includes('all') && items.length >= 2) {
                $(selector + ' option:eq(0)').prop('selected', false);
                $(selector + ' option:eq(0)').removeAttr('selected')
                $(selector).parent().find('.dropdown-menu.inner').children().first().removeClass('selected')
                $(selector).parent().find('.dropdown-menu.inner').children().first().children('a').removeClass('selected')
                temp_list = $(this).val();
            }

            // case 3: all 이 선택되어있지 않았고 새로운 데이터세트 항목 선택 시
            else if (!temp_list.includes('all') && items.length >= 1) {
                temp_list = [...items];
            }

            // case 4: all 을 선택하지 않고 선택되어있던 데이터세트 항목을 취소
            else {
                temp_list = $(this).val();
            }

            if ($(this).val().length === 0) {
                temp_list = ['all']
                $(selector + ' option:eq(0)').prop('selected', true);
                $(selector).parent().find('.dropdown-menu.inner').children().first().addClass('selected');
            }
        }
    );
}
// END: 데이터세트 다중 선택 select 관련 코드

// readonly 인 input 태그는 value 가 change 돼도 jquery change()로 인식이 안되기 때문에 밑 함수를 사용.
(function ($) {
    var originalVal = $.fn.val;
    $.fn.val = function (value) {
        var res = originalVal.apply(this, arguments);

        if (this.is('input:text') && arguments.length >= 1) {
            this.trigger("input");
        }
        return res;
    };
})(jQuery);


Date.prototype.format = function (f) {
    if (!this.valueOf()) return " ";
    var weekName = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];
    var d = this;
    return f.replace(/(yyyy|yy|MM|dd|E|hh|mm|ss|a\/p)/gi, function ($1) {
        switch ($1) {
            case "yyyy":
                return d.getFullYear();
            case "yy":
                return (d.getFullYear() % 1000).zf(2);
            case "MM":
                return (d.getMonth() + 1).zf(2);
            case "dd":
                return d.getDate().zf(2);
            case "E":
                return weekName[d.getDay()];
            case "HH":
                return d.getHours().zf(2);
            case "hh":
                return ((h = d.getHours() % 12) ? h : 12).zf(2);
            case "mm":
                return d.getMinutes().zf(2);
            case "ss":
                return d.getSeconds().zf(2);
            case "a/p":
                return d.getHours() < 12 ? "오전" : "오후";
            default:
                return $1;
        }
    });
};
String.prototype.string = function (len) {
    var s = '', i = 0;
    while (i++ < len) {
        s += this;
    }
    return s;
};
String.prototype.zf = function (len) {
    return "0".string(len - this.length) + this;
};
Number.prototype.zf = function (len) {
    return this.toString().zf(len);
};


function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// 두 개의 배열을 인자로 받아 원소가 모두 같은지 확인.
function compareArray(arr1, arr2) {

    // 결과값
    var rst = false;

    // 길이가 다르면 다른 배열이라고 판단
    if (arr1.length != arr2.length) {
        return rst;
    }

    // arr1 배열의 크기만큼 반복
    arr1.forEach(function (item) {

        // arr1 배열 아이템이, arr2 배열에 있는지 확인
        // 있으면, arr2에 item이 존재하는 index 리턴
        // 없으면, -1 리턴
        var i = arr2.indexOf(item);

        // 존재하면, splice함수를 이용해서 arr2 배열에서 item 삭제
        if (i > -1) arr2.splice(i, 1);
    });

    // compare2의 길이가 0이면 동일하다고 판단.
    rst = arr2.length == 0;

    return rst;
}


function textLengthOverCut(txt, len, lastTxt) {
    if (len == "" || len == null) { // 기본값
        len = 20;
    }
    if (lastTxt == "" || lastTxt == null) { // 기본값
        lastTxt = "...";
    }
    if (txt.length > len) {
        txt = txt.substr(0, len) + lastTxt;
    }
    return txt;
}

