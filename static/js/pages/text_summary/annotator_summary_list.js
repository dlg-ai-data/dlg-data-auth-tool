//////////////////////////////////////////////////////
// Dom
//////////////////////////////////////////////////////
const searchForm = $('#searchForm');
const statusSelect = $('#jobText_status');


//////////////////////////////////////////////////////
// function
//////////////////////////////////////////////////////

// selectbox filter change function
statusSelect.change(function () {
    searchForm.submit();
});

$('#assign_date_picker').datepicker({
    todayBtn: "linked",
    todayHighlight: true,
    autoclose: true,
    clearBtn: true,
});


$('#assign_date_picker').change(function () {
    searchForm.submit();
})

// 작업 배정 가능 여부 체크 validation function
function fnJobValidation(valid_url, new_url) {
    $.ajax({
        url: valid_url,
        method: 'post',
        success: function (data) {
            if (data.result == true) {
                if (data.valid) {
                    fnNewJob(new_url)
                } else {
                    swalFire("작업배정 실패", "작업중이거나 미작업 데이터가 존재할땐 배정받을 수 없습니다.", "error", "확인");
                }
            } else {
                swalFire("작업배정 실패", data.error, "error", "확인");
            }
        }
    });

}

// 새로운 작업 배정 받는 function
function fnNewJob(url) {
    swalWithBootstrapButtons.fire({
        title: '작업배정',
        text: "새로운 작업을 배정받으시겠습니까?",
        showCancelButton: true,
        confirmButtonText: '확인',
        cancelButtonText: '취소',

    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: url,
                method: 'post',
                success: function (data) {
                    if (data.result == true) {
                        location.reload();
                    } else {
                        swalFire("작업배정 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    });
}