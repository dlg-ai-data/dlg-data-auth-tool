// page move
function pageForm(index) {
    $("#page").val(index);
    $('#searchForm').submit();
}

// filter change function (jobStatus)
$('#job_status').on('change', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});

$('#job_date_picker').datepicker({
    todayBtn: "linked",
    todayHighlight: true,
    autoclose: true,
    clearBtn: true,
    dateFormat:'yy-mm-dd',
});


$('#job_date_picker').change(function () {
    $('#searchForm').submit();
})

// checkbox select all function
$('#selectAllChk').click(function () {
    const checked = this.checked;
    $('input:checkbox[name="checkboxRow"]').each(function () {
        this.checked = checked;
    });

    fnCheckValidation();
});

// checkbox validation 함수
function fnCheckValidation() {
    let valid = true;
    $('input:checkbox[name="checkboxRow"]:checked').each(function () {
        let status = $(this).siblings('[name="rowStatus"]').val();
        if (status !== 'AK02') {
            valid = false;
        }
    });
    return valid;

}


// 일괄 검수 function
function fnInspecSubmit(url) {
    if (!$('input:checkbox[name="checkboxRow"]:checked').length > 0) {
        swalFire("작업실패", "체크된 항목이 없습니다.", "error", "확인");
        return;
    }

    if (!fnCheckValidation()) {
        swalFire("작업실패", "작업완료 건에 대해서만 검수처리 가능합니다.", "error", "확인");
        return;
    }

    swalWithBootstrapButtons.fire({
        title: '검수 하기',
        text: "선택된 작업에 대하여 일괄 검수처리 하시겠습니까?",
        showCancelButton: true,
        confirmButtonText: '검수하기',
        cancelButtonText: '취소',

    }).then((result) => {
        if (result.isConfirmed) {
            let target = "";
            $('input:checkbox[name="checkboxRow"]:checked').each(function (index) {
                let value = $(this).siblings('[name="rowIdInpt"]').val();
                if (index !== 0) {
                    target += ","
                }
                target += value

            });


            $.ajax({
                url: url,
                method: 'post',
                data: {
                    target_data: target,
                },
                success: function (data) {
                    if (data.result == true) {
                        location.reload();
                    } else {
                        swalFire("일괄 검수 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    });

}