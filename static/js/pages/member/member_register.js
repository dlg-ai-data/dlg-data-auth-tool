$("#form").on('submit', (e) => {
    e.preventDefault();
    registerMember()
})
const registerMember = () => {
    const emailVal = $("#email").val();
    const pw1Val = $("#pw1").val();
    const pw2Val = $("#pw2").val();
    const nameVal = $("#user-name").val();
    const rrn1Val = $("#rrn1").val();
    const rrn2Val = $("#rrn2").val();
    const tel1Val = $("#tel1").val();
    const tel2Val = $("#tel2").val();
    const tel3Val = $("#tel3").val();
    const bankCodeVal = $("#bank-select option:selected").val();
    const bankNoVal = $(".input-bank_no").val();

    const pw1_check_result = chkPW(pw1Val);
    const pw2_check_result = chkPW(pw2Val);

    let rrn_validation = {result: true};
    let tel_validation = {result: true};
    let bank_validation = true;

    if (!(rrn1Val.trim() === "" && rrn2Val.trim() === "")) {
        rrn_validation = isValid_RRN(rrn1Val, rrn2Val);
    }

    if (!(tel1Val.trim() === "" && tel2Val.trim() === "" && tel3Val.trim() === "")) {
        tel_validation = isValid_TEL(tel1Val, tel2Val, tel3Val);
    }

    if (!(bankCodeVal.trim() === "" && bankNoVal.trim() === "")) {
        bank_validation = isValid_BANK(bankCodeVal, bankNoVal);
    }

    if (emailVal.match(regExp_ID) == null || emailVal.trim() === '') {
        swalFire("등록 에러", "이메일 미기입 또는 양식이 맞지 않습니다.", "error", "확인")
    } else if (nameVal === '') {
        swalFire("등록 에러", "이름을 입력해주세요.", "error", "확인")
    } else if (pw1Val === '' || pw2Val === '') {
        swalFire("등록 에러", "비밀번호를 입력해주세요.", "error", "확인")
    } else if (pw1_check_result !== '') {
        swalFire("등록 에러", pw1_check_result, "error", "확인")
    } else if (pw2_check_result !== '') {
        swalFire("등록 에러", pw2_check_result, "error", "확인")
    } else if (!rrn_validation.result) {
        swalFire("등록 에러", rrn_validation.message, "error", "확인")
    } else if (!tel_validation.result) {
        swalFire("등록 에러", tel_validation.message, "error", "확인")
    } else if (!bank_validation) {
        swalFire("등록 에러", "은행 정보를 화인해주세요.", "error", "확인")
    } else {
        $.ajax({
            url: url_registerMember,
            method: "POST",
            processData: false,
            contentType: false,
            data: new FormData($("#form")[0]),
            success: function (data) {
                if (data.result === true) {
                    swalFire("회원 등록 성공", "성공적으로 저장되었습니다.", "success", "확인").then(() => {
                        location.href = "/member/list/"; // 회원목록 페이지로 이동
                    });
                } else {
                    swalFire("회원 등록 실패", data.error, "error", "확인");
                }
            }
        });
    }
}

$(".phone-num").keyup(function () {
    var charLimit = $(this).attr("maxlength");
    if (this.value.length >= charLimit) {
        $(this).next('.phone-num').focus();
        return false;
    }
});

$("input:file").change(function () {
    const elementId = $(this).attr("id");
    const fileName = $(this).val().split("\\");
    $("label[for='" + elementId + "']").text(fileName[fileName.length - 1]);
});

$('.custom-file-input').on('change', function () {
    const fileName = $(this).val();
    const fileType = $(this).attr('id');
    $(this).next('.custom-file-label').addClass("selected").html(fileName);
    $("." + fileType + "-minus").css("visibility", "visible");
});

function file_reset(file_id) {
    $("#" + file_id).val("").trigger("change");
    $('.' + file_id + "-label").removeClass("selected").html("<span style=\"color: #a9a9a9 \">비어있음.</span>");
    $("." + file_id + "-minus").css("visibility", "hidden");
}