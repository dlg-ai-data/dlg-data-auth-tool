const changed_record_idx_set = new Set();

// 하나의 tr의 변경을 감지함.
const detect_tr_change = (tr) => {
    const row_num = tr.find("td.row_num").text();
    if (row_num === "")
        return;
    const idx = row_num >= 16 ? row_num - 15 * (page - 1) - 1 : row_num - 1;
    const originGrade = tr.find("select.grade-selector").data('grade');
    const selectedGrade = tr.find("select.grade-selector").val();

    const originRole = tr.find("select.role-selector").data("role");
    const selectedRole = tr.find("select.role-selector").val();

    let is_changed = false;

    if (originGrade !== selectedGrade){
        is_changed = true
        if(selectedGrade === 'AA04') {
            $('.grade-selector').selectpicker('val', originGrade);
            is_changed = false
        }
    }

    if (originRole !== selectedRole) {
        is_changed = true
        if(selectedRole === 'MR04') {
            $('.role-selector').selectpicker('val', originRole);
            is_changed = false
        }
    }


    if (!is_changed) { // 수정 버튼 비활성
        tr.find('.actions-btn').attr('disabled', true);
        tr.find('.actions-btn').removeClass('btn-light-skype');
        tr.find('.actions-btn').addClass('btn-secondary');
        changed_record_idx_set.delete(idx)
    } else {
        tr.find('.actions-btn').attr('disabled', false);
        tr.find('.actions-btn').addClass('btn-light-skype');
        tr.find('.actions-btn').removeClass('btn-secondary');
        changed_record_idx_set.add(idx)
    }

    if (changed_record_idx_set.size > 0) {
        $(".all-user-grade-update-btn").attr('disabled', false);
        $(".all-user-grade-update-btn").addClass('btn-skype');
        $(".all-user-grade-update-btn").removeClass('btn-secondary');
    } else {
        $(".all-user-grade-update-btn").attr('disabled', true);
        $(".all-user-grade-update-btn").addClass('btn-secondary');
        $(".all-user-grade-update-btn").removeClass('btn-skype');
    }
}

// 한 번에 모든 tr의 변경을 감지
const detect_all_tr_change = () => {
    for (let count = 0; count < 15; count++) {
        const tr = $($('.record')[count]);
        if (tr.val() === undefined) {
            break;
        }
        detect_tr_change(tr);
    }
}

// 개별적 사용자 등급 변경
const change_one_memberGrade = (e, action_url) => {
    const tr = $(e).parents("tr");
    const row_num = tr.find("td.row_num").text();
    const completed_idx = row_num >= 16 ? row_num - 15 * (page - 1) - 1 : row_num - 1;
    const id = $(e).data('id');
    const selects = Array.from(tr.find('select'));
    const selectedGrade = tr.find("select.grade-selector").val();
    const selectedRole = tr.find("select.role-selector").val();

    let parameter = "";

    const update_btn = $(e);
    swalWithBootstrapButtons.fire({
        title: '등급 및 역할 변경',
        text: "계속 진행하시겠습니까?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '확인',
        cancelButtonText: '취소',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: action_url + "?id=" + id + "&grade=" + selectedGrade + "&role=" + selectedRole + parameter,
                method: "GET",
                processData: false,
                contentType: false,
                success: function (data) {
                    if (data.result == true) {
                        swalFire("", "등급 및 역할이 변경되었습니다.", "success", "확인").then(() => {
                            let idx = 0;
                            selects.forEach(value => {
                                if (idx !== 6) {
                                    $(value).data("grade", data.new_data[idx]);
                                    $(value).attr("data-grade", data.new_data[idx]);
                                } else {
                                    $(value).data("role", data.new_data[idx]);
                                    $(value).attr("data-role", data.new_data[idx]);
                                }
                                idx++;
                            });
                            update_btn.addClass('btn-secondary');
                            update_btn.removeClass('btn-light-skype');
                            update_btn.prop("disabled", true);

                            changed_record_idx_set.delete(completed_idx)
                            if (changed_record_idx_set.size > 0) {
                                $(".all-user-grade-update-btn").attr('disabled', false);
                                $(".all-user-grade-update-btn").addClass('btn-skype');
                                $(".all-user-grade-update-btn").removeClass('btn-secondary');
                            } else {
                                $(".all-user-grade-update-btn").attr('disabled', true);
                                $(".all-user-grade-update-btn").addClass('btn-secondary');
                                $(".all-user-grade-update-btn").removeClass('btn-skype');
                            }
                        });
                    } else {
                        swalFire("변경 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    })
}

//일괄적 사용자 등급 변경
const change_multiple_memberGrade = (action_url) => {
    let to_be_changed_items = []
    for (let count of changed_record_idx_set) {
        const tr = $($(".record")[count]);
        const obj = new Object();
        obj['member_id'] = tr.find(".member_id").val();
        obj['grade_code'] = tr.find("select.grade-selector").val();
        obj['role_code'] = tr.find("select.role-selector").val();
        for (const key in project_type) {
            obj["AH0" + String(Number(key) + 1) + "_grade"] = tr.find("select.AH0" + String(Number(key) + 1) + "-grade-selector").val();
        }
        to_be_changed_items.push(obj)
    }
    const data = {"to_be_changed_items": to_be_changed_items}
    data['to_be_changed_items'] = JSON.stringify(data['to_be_changed_items'])
    swalWithBootstrapButtons.fire({
        title: '등급 및 역할 일괄 변경',
        text: "계속 진행하시겠습니까?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '확인',
        cancelButtonText: '취소',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: action_url,
                method: "POST",
                data: data,
                success: function (data) {
                    if (data.result == true) {
                        swalFire("", "등급 및 역할이 일괄 변경되었습니다.", "success", "확인").then(() => {
                            location.reload()
                        });
                    } else {
                        swalFire("변경 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    })
}

// 멤버 등급 일괄 변경 select의 선택값 변경감지
const detect_allGradeSelector_change = () => {
    if ($(".all-grade-selector option:selected").text() === "선택") {
        for (let count = 1; count < 30; count += 2) {
            $($('.grade-selector')[count]).selectpicker('val', $($('.grade-selector')[count]).data("grade"));
        }
    }
    for (const key in member_grade) {
        if ($(".all-grade-selector option:selected").text() === member_grade[key]) {
            $('.grade-selector').selectpicker('val', "AA0" + String(Number(key) + 1));
        }
    }
    detect_all_tr_change();
}

// 특정 프로젝트 등급 일괄 변경 select의 선택값 변경감지
const detect_allSpecificProjectGradeSelector_change = (type) => {
    const current_projectGrade_select_className = type + "-grade-selector";
    const current_all_projectGrade_select_className = "all-" + type + "-grade-selector";

    const current_select_text = $("." + current_all_projectGrade_select_className + " option:selected").text();

    if (current_select_text === "선택") {
        for (let count = 1; count < 30; count += 2) {
            $($('.' + current_projectGrade_select_className)[count]).selectpicker('val', $($('.' + current_projectGrade_select_className)[count]).data("grade"));
        }
    } else {

        for (const key2 in member_grade) {
            if (current_select_text === member_grade[key2]) {
                $('.' + current_projectGrade_select_className).selectpicker('val', "AA0" + String(Number(key2) + 1));
                break;
            }
        }
    }
    detect_all_tr_change();

}

// 멤버 역할 일괄 변경 select의 선택값 변경감지
const detect_allRoleSelector_change = () => {
    if ($(".all-role-selector option:selected").text() === "선택") {
        for (let count = 1; count < 30; count += 2) {
            $($('.role-selector')[count]).selectpicker('val', $($('.role-selector')[count]).data("role"));
        }
    }
    for (const key in member_role) {
        if ($(".all-role-selector option:selected").text() === member_role[key]) {
            $('.role-selector').selectpicker('val', "MR0" + String(Number(key) + 1));
        }
    }
    detect_all_tr_change();
}


function pageForm(index) {
    $("#page").val(index);
    $('#searchForm').submit();
}

$('#select_grade').on('change', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});

$('#select_join_source').on('change', function () {
    $("#page").val(1);
    $('#searchForm').submit();
});