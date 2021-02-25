//////////////////////////////////////////////////////
// Dom
//////////////////////////////////////////////////////
// textarea
const summaryArea = $('#summaryTextArea');
// 원본데이터
const originArea = $('#originArea');
// word count
const countArea = $('#wordCount');
// select word count
const selCountArea = $('#selectCount');
// iframe
const pdfFrame = $('#pdfFrame');
// currentJob page span
const currentJob = $('#currentJob');
// totalJob page span
const totalJob = $('#totalJob');

// 다음 버튼
const nextBtn = $('#nextBtn');
// 이전 버튼
const prevBtn = $('#prevBtn');
// 임시저장 버튼
const saveBtn = $('#saveBtn');
// 최종제출 버튼
const submitBtn = $('#submitBtn');
//건너뛰기 버튼
const skipBtn = $('#skipBtn');

// jobText
// 작업페이지 아이디 input
const jobTextId = $('#jobTextId');
// 작업페이지 아이디 input
const jobTextWorkerId = $('#jobTextWorkerId');
// 최종제출 여부 input
const jobTextStatus = $('#jobTextStatus');
// pdf url input
const jobTextPdfUrl = $('#jobTextPdfUrl');

// jobTextSummary
// summary id
const textSummaryId = $('#textSummaryId');
// summary page번호
const textSummaryPageNum = $('#textSummaryPageNum');
// summary 상태값
const textSummaryStatus = $('#textSummaryStatus');
//////////////////////////////////////////////////////
// variables
//////////////////////////////////////////////////////
const wordMinCount = 300;
const wordMaxCount = 500;

//////////////////////////////////////////////////////
// Ready function
//////////////////////////////////////////////////////
$(document).ready(function () {
    // iframe default 값 setting
    const pdfUrl = jobTextPdfUrl.val();
    if (pdfUrl) {
        pdfFrame.attr("src",  pdfUrl);
    }


    // jobtext status에 따라 제출버튼 disabled 설정
    fnJobStatusValidation(textSummaryStatus.val());

    if(jobTextStatus.val()==="AK02" || jobTextStatus.val()==="AK05" || jobTextStatus.val()==="AL03"){
        submitBtn.attr('disabled', true);
    }

    // 초기 text 글자수 count
    fnWordCounter();

    // 이전 다음버튼 상태에 따라 이전,다음버튼 disabled 설정
    fnPrevNextBtnProps(Number(textSummaryPageNum.val()), Number(totalJob.text()));

});


//////////////////////////////////////////////////////
// validation function
//////////////////////////////////////////////////////
//textarea에 입력된 문장 중 선택된 단어수 count


//textarea에 입력된 문장의 단어수 count
function fnWordCounter() {
    let wordCount = cfnWordValidator(summaryArea.val());
    countArea.text(wordCount);
}

// 이전버튼 다음버튼 validation
function fnPrevNextBtnProps(currentNum, totalCount) {
    const jtStatus = jobTextStatus.val();

    if (1 < currentNum) {
        prevBtn.attr('disabled', false);

        if (jtStatus == "AK02" || jtStatus == 'AK05' ||jtStatus == 'AL03') {// AK02 작업완료, AK05 회수, AL03 검수완료
            if (currentNum >= totalCount) {
                nextBtn.attr('disabled', true);
            } else {
                nextBtn.attr('disabled', false);
            }
        }
    } else {
        if (jtStatus == "AK02" || jtStatus == 'AK05' || jtStatus == 'AL03') {// AK02 작업완료, AK05 회수, AL03 검수완료
            if (currentNum >= totalCount) {
                nextBtn.attr('disabled', true);
            } else {
                nextBtn.attr('disabled', false);
            }
        }
        if (currentNum === 1) {
            prevBtn.attr('disabled', true);
        }
    }
}

//원본데이터가 존재할 시 현입력 데이터와 이전 입력데이터 비교
function fnTextCompare(originText, currentText) {
    if (originText === currentText) {
        saveBtn.attr('disabled', true);
        $('#saveBtnIcon').attr('class', 'fas fa-check');

    } else {
        saveBtn.attr('disabled', false);
        $('#saveBtnIcon').attr('class', 'fas fa-edit');

    }
}

// JOBTEXT STATUS 상태에 따라 검수완료 버튼 DISABLED 설정
function fnJobStatusValidation(jobStatus) {
    if (jobStatus === "AK02") {
        submitBtn.attr('disabled', false);
    } else {
        submitBtn.attr('disabled', true);
    }
}

//textarea 커서지정시 작동
summaryArea.select(function () {
    if(!summaryArea.prop('disabled')){
        // window selection (커서지정) 된부분 count
        selCountArea.text(cfnSelectWordCounter() + "/");
    }
})

//textarea 커서지정 해제시 작동
summaryArea.on("blur mousedown", function (e) {
    selCountArea.text("");
});


// clipboard paste action bind
summaryArea.bind('paste', function (e) {
    // 복사시 Clipboard text replace
    cfnCustomBindPaste(e);

    // 복사 후 단어수 측정
    fnWordCounter();

    // 이전데이터 현데이터 비교해서 저장버튼 disabled 설정
    fnTextCompare(originArea.val(), summaryArea.val());

    // 선택단어수 초기화
    if (window.getSelection().toString() == '' || window.getSelection().toString() == ' ' || !window.getSelection().toString()) {
        selCountArea.text("");
    }
});

//textarea keyup event 키 입력시마다 글자수 체크
summaryArea.keyup(function () {
    // window selection (커서지정) 된부분 count
    summaryArea.val(cfnReplaceText(summaryArea.val()));
    // 이전데이터 현데이터 비교해서 저장버튼 disabled 설정
    fnTextCompare(originArea.val(), summaryArea.val());

    //fnWordCounter();
    fnWordCounter();

    // 선택단어수 초기화
    if (window.getSelection().toString() == '' || window.getSelection().toString() == ' ' || !window.getSelection().toString()) {
        selCountArea.text("");
    }
})

// 작업제외 action
function fnSkipJob(url) {
    swalWithBootstrapButtons.fire({
        title: '작업대상 제외',
        text: "해당 PDF를 작업대상에서 제외하시겠습니까?.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '확인',
        cancelButtonText: '취소',

    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: url,
                method: 'post',
                data: {
                    job_text_id: jobTextId.val(),
                },
                success: function (data) {
                    if (data.result == true) {
                        location.href = "/textsummary/annotator/list" // 목록 페이지로 이동
                    } else {
                        swalFire("작업제외 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    });
}

// text summary 목록 화면으로
function fnGoListPage(url) {
    if (originArea.val() === summaryArea.val()) {
        location.href = url
    } else {
        swalWithBootstrapButtons.fire({
            title: '목록으로 이동',
            text: "저장하지 않은 작업내용이 사라집니다.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: '목록으로',
            cancelButtonText: '취소',

        }).then((result) => {
            if (result.isConfirmed) {
                location.href = url
            }
        });
    }

}

// page 작업내용 저장여부 확인
function fnPageCheck(type, url) {
    if (originArea.val() === summaryArea.val()) {
        fnMovePage(type, url);
    } else {
        swalWithBootstrapButtons.fire({
            title: '페이지 이동',
            text: "해당 페이지의 작업내용이 저장되지 않았습니다.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: '이동하기',
            cancelButtonText: '취소',

        }).then((result) => {
            if (result.isConfirmed) {
                fnMovePage(type, url);
            }
        });
    }
}

// 페이지 이동
function fnMovePage(type, url) {

    if (type === "next" && textSummaryStatus.val() !== "AK02") {
        swalFire("이동 불가", "해당 페이지 작업을 완료하지 않으면 다음페이지로 이동할 수 없습니다.", "error", "확인")
        return;
    }

    let movePage = Number(textSummaryPageNum.val());
    if (type === "next") {
        movePage += 1;
    } else {
        movePage -= 1;
    }

    $.ajax({
        url: url,
        method: 'post',
        data: {
            job_text_id: jobTextId.val(),
            page_number: movePage,
        },
        success: function (data) {
            if (data.result == true) {
                // 현재 job 페이지
                currentJob.text(data.data.page_number);
                // 전체 job 페이지
                totalJob.text(data.max_page_number);
                // textarea에 값 삽입
                summaryArea.val(data.data.summary);
                // 원본 데이터 input에 값 삽입
                originArea.val(data.data.summary);

                //textSummary info setting
                textSummaryId.val(data.data.id)
                textSummaryStatus.val(data.data.job_summary_status);
                textSummaryPageNum.val(data.data.page_number);

                //커서 지정된 textcount initialize
                selCountArea.text('');

                //summary status validation
                fnJobStatusValidation(data.data.job_summary_status);

                if(jobTextStatus.val()==="AK02" || jobTextStatus.val()==="AK05" || jobTextStatus.val()==="AL03"){// AK02 작업완료, AK05 회수, AL03 검수완료
                    submitBtn.attr('disabled', true);
                }

                fnWordCounter();

                if (jobTextStatus.val() !== "AL03" && jobTextStatus.val() !== "AK05") {// AL03 검수완료ㅑ, AK05 회수
                    fnTextCompare(summaryArea.val(), originArea.val());
                }
                fnPrevNextBtnProps(data.data.page_number,Number(totalJob.text()))

            } else {
                swalFire("작업 페이지 이동 실패", data.error, "error", "확인");
            }
        }
    });

}

// 저장버튼 클릭시 분기 함수
function fnSaveValidation(url) {
    if (jobTextStatus.val() === "AK02" || jobTextStatus.val() === "AL03") {// AK02 작업완료, AL03 검수완료
        swalFire("등록 에러", "제출완료 되거나 검수완료된 자료는 변경 불가능합니다.", "error", "확인")
        return;
    } else {
        fnSummarySave(url);
    }
}

// // summary 임시 저장 함수
// function fnSummarySave(url) {
//     // 저장 시 단어 수 검증
//     let submitCount = cfnWordValidator(summaryArea.val());
//     if (submitCount < wordMinCount || submitCount > wordMaxCount) {
//         swalFire("등록 에러", "기준에 맞지 않습니다. (300글자 이상, 500글자 이하)", "error", "확인")
//         return;
//     }
//     // 저장되는동안 저장버튼 ICON SPINNER로 변경
//     saveBtn.addClass('spinner spinner-white spinner-left');
//     $('#saveBtnIcon').css('display', 'none');
//
//     $.ajax({
//         url: url,
//         method: 'post',
//         data: {
//             saveStatus: textSummaryStatus.val(),
//             page_number: textSummaryPageNum.val(),
//             job_text_id: jobTextId.val(),
//             summary_id: textSummaryId.val(),
//             summary: summaryArea.val(),
//             submit_status: jobTextStatus.val()
//         },
//         success: function (data) {
//             if (data.result == true) {
//                 // summary 내용 값 삽입
//                 summaryArea.val(data.text_summary_qs.summary);
//                 originArea.val(data.text_summary_qs.summary);
//
//                 // summary status 값 지정
//                 textSummaryStatus.val(data.text_summary_qs.job_summary_status)
//
//                 // validation
//                 fnTextCompare(summaryArea.val(), originArea.val());
//                 fnJobStatusValidation(textSummaryStatus.val());
//
//                 // 저장이 되면 작업완료 x
//                 skipBtn.attr('disabled', false);
//                 saveBtn.removeClass('spinner spinner-white spinner-left');
//                 $('#saveBtnIcon').css('display', 'inline-block');
//             } else {
//                 swalFire("저장 실패", data.error, "error", "확인");
//             }
//         }
//     });
// }

// 작업 최종 제출 fucntion
function fnFinalSubmit(url) {
    swalWithBootstrapButtons.fire({
        title: '최종 제출',
        text: "저장된 작업내용을 모두 제출합니다.",
        icon: 'info',
        showCancelButton: true,
        confirmButtonText: '확인',
        cancelButtonText: '취소',
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: url,
                method: 'post',
                data: {
                    status: textSummaryStatus.val(),
                    job_text_id: jobTextId.val()
                },
                success: function (data) {
                    if (data.result == true) {
                        swalFire("제출 성공", "성공적으로 제출되었습니다.", "success", "확인").then(() => {
                            location.href = "/textsummary/annotator/list"; // 목록 페이지로 이동
                        });

                    } else {
                        swalFire("제출 실패", data.error, "error", "확인");
                    }
                }
            });
        }
    });
}