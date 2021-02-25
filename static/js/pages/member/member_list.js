// 회원 삭제
const deleteMember = (e, action_url) => {
    const id = $(e).data('id');  // 삭제 버튼을 누른 row의 id 값
    swalWithBootstrapButtons.fire({
        title: '회원 삭제',
        text: "계속 진행하시겠습니까?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '확인',
        cancelButtonText: '취소',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: action_url + "?id=" + id,
                method: "GET",
                success: function (data) {
                    if (data.result === true) {
                        swalFire("", "해당 사용자 정보가 삭제되었습니다.", "success", "확인").then(() => {
                            location.reload()
                        });
                    } else {
                        swalFire("회원 삭제 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    })
}
// 회원 승인
const approveMember = (e, action_url) => {
    const id = $(e).data('id');
    swalWithBootstrapButtons.fire({
        title: '회원 정보 승인',
        text: "계속 진행하시겠습니까?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '확인',
        cancelButtonText: '취소',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: action_url + "?id=" + id,
                method: "GET",
                success: function (data) {
                    if (data.result === true) {
                        swalFire("", "해당 사용자의 정보가 승인되었습니다.", "success", "확인").then(() => {
                            location.reload();
                        });
                    } else {
                        swalFire("사용자 정보 승인 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    })
}

const downloadExcel_memberList = (action_url) => {
    const join_source = $("#select_join_source option:selected").val();
    const join_date = $("#set_join_date").val();
    const admyn = $("#select_admyn option:selected").val();
    const project_type = $("#select_projectType option:selected").val();
    const sms_rect_yn = $("#select_sms_rect_yn option:selected").val();
    const searched_word = $("#table-data-search").val();

    // 엑셀 쿼리스트링 만드는 곳
    const params = {join_source, join_date, admyn, project_type, sms_rect_yn, searched_word};
    const qs = jQuery.param(params, true);

    window.open(action_url + '?' + qs)
}

function pageForm(index) {
    $("#page").val(index);
    $('#searchForm').submit();
}

$('#select_admyn').on('change', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});

$('#select_sms_rect_yn').on('change', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});

$('#select_join_source').on('change', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});

$('#select_projectType').on('change', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});

$("#set_join_date").on('input', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});

set_daterangepicker('#dateRangePicker_join_date', {title: '가입일자 필터', maxDate: new Date()});


