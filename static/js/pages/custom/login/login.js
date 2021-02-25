"use strict";

// Class Definition
const KTLogin = function() {
    let _login;

    const _showForm = function(form) {
        var cls = 'login-' + form + '-on';
        var form = 'kt_login_' + form + '_form';

        _login.removeClass('login-forgot-on');
        _login.removeClass('login-signin-on');
        _login.removeClass('login-signup-on');

        _login.addClass(cls);

        KTUtil.animateClass(KTUtil.getById(form), 'animate__animated animate__backInUp');
    }

    const _handleSignInForm = function() {
    	let validation;

        // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
        validation = FormValidation.formValidation(
			KTUtil.getById('kt_login_signin_form'),
			{
				fields: {
					email: {
						validators: {
							notEmpty: {
								message: '이메일은 필수입력입니다.'
							},
							emailAddress: {
								message: '이메일형식이 올바르지 않습니다.'
							}
						}
					},
					password: {
						validators: {
							notEmpty: {
								message: '패스워드는 필수입니다.'
							}
						}
					}
				},
				plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    submitButton: new FormValidation.plugins.SubmitButton(),
                    //defaultSubmit: new FormValidation.plugins.DefaultSubmit(), // Uncomment this line to enable normal button submit after form validation
					bootstrap: new FormValidation.plugins.Bootstrap()
				}
			}
		);

        $('#kt_login_signin_submit').on('click', function (e) {
            e.preventDefault();

            validation.validate().then(function(status) {
		        if (status == 'Valid') {
                    $('#kt_login_signin_form').submit();
				} else {
					swal.fire({
		                text: "Sorry, looks like there are some errors detected, please try again.",
		                icon: "error",
		                buttonsStyling: false,
		                confirmButtonText: "Ok, got it!",
                        customClass: {
    						confirmButton: "btn font-weight-bold btn-light-primary"
    					}
		            }).then(function() {
						KTUtil.scrollTop();
					});
				}
		    });
        });

        // Handle forgot button
        $('#kt_login_forgot').on('click', function (e) {
            e.preventDefault();
            _showForm('forgot');
        });

        // Handle signup
        $('#kt_login_signup').on('click', function (e) {
            e.preventDefault();
            _showForm('signup');
        });
    }

	const _handleSignUpForm = function (e) {
		let validation;
		const form = KTUtil.getById('kt_login_signup_form');

		// Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
		validation = FormValidation.formValidation(
			form,
			{
				fields: {
					name: {
						validators: {
							notEmpty: {
								message: '이름은 필수입력입니다.'
							}
						}
					},
					email: {
						validators: {
							notEmpty: {
								message: '이메일은 필수입력입니다.'
							},
							emailAddress: {
								message: '이메일형식이 올바르지 않습니다.'
							}
						}
					},
					password: {
						validators: {
							notEmpty: {
								message: '비밀번호는 필수입력입니다.'
							}
						}
					},
					cpassword: {
						validators: {
							notEmpty: {
								message: '비밀번호를 한번더 입력하세요.'
							},
							identical: {
								compare: function () {
									return form.querySelector('[name="password"]').value;
								},
								message: '비밀번호 입력이 일치하지 않습니다.'
							}
						}
					},
					agree: {
						validators: {
							notEmpty: {
								message: '가입 동의는 필수입니다.'
							}
						}
					},
				},
				plugins: {
					trigger: new FormValidation.plugins.Trigger(),
					bootstrap: new FormValidation.plugins.Bootstrap()
				}
			}
		);

		$('#kt_login_signup_submit').on('click', function (e) {
			e.preventDefault();

			validation.validate().then(function (status) {
				if (status == 'Valid') {
					ajax_join();
				} else {
					swal.fire({
						text: "입력값이 올바르지 않습니다.",
						icon: "error",
						buttonsStyling: false,
						confirmButtonText: "확인",
						customClass: {
							confirmButton: "btn font-weight-bold btn-light-primary"
						}
					}).then(function () {
						KTUtil.scrollTop();
					});
				}
			});
		});

		// Handle cancel button
		$('#kt_login_signup_cancel').on('click', function (e) {
			e.preventDefault();

			_showForm('signin');
		});
	};

	// Public Functions
    return {
        // public functions
        init: function() {
            _login = $('#kt_login');

            _handleSignInForm();
            _handleSignUpForm();
        }
    };
}();

// Class Initialization
jQuery(document).ready(function() {
    KTLogin.init();
});
