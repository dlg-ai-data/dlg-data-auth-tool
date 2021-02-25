create
    definer = vaiv@`%` procedure member_calc()
BEGIN
    DECLARE done INTEGER DEFAULT FALSE;
    DECLARE v_rowcount      INT DEFAULT 0;
    DECLARE v_start_date    DATETIME;
    DECLARE v_end_date      DATETIME;
    DECLARE v_calc_month    INT;
    DECLARE v_calc_id       INT;
    DECLARE v_pay_price     INT;
    DECLARE v_bank_no       VARCHAR(50);
    DECLARE v_bank_code     VARCHAR(4);
    DECLARE v_member        INT;
    DECLARE v_source_type   VARCHAR(4);

    SET v_start_date = (SELECT MAX(calc_date) FROM calc);
    IF v_start_date IS NULL OR v_start_date = '' THEN
        SET v_start_date = (SELECT DATE_ADD(NOW(), INTERVAL -1 YEAR));
    END IF;
    SET v_end_date = NOW();

    BEGIN
        DECLARE cur_calc_header CURSOR FOR
            SELECT
                p.member_id,
                'BB01' as source_type,
                SUM(d.price + dg.grade_price) as pay_price,
                ma.bank_code,
                ma.bank_no
            FROM
            job_talk_source s
            JOIN dataset d on s.dataset_id = d.id
            JOIN provider p on p.id = s.provider_id AND p.dataset_id = d.id
            JOIN member_grade mg on p.member_id = mg.member_id
            JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
            JOIN member_addition ma on p.member_id = ma.member_id
            LEFT OUTER JOIN calc_detail cd on cd.job_id = s.id AND cd.job_source_type = 'BB01'
            WHERE s.inspection_status = 'AL03'
            AND p.valid_yn = 'Y'
            AND mg.valid_yn = 'Y'
            AND cd.id is null
            AND s.inspection_date BETWEEN v_start_date AND v_end_date
            group by p.member_id
            union
            SELECT
                p.member_id,
                'BB03' as source_type,
                SUM(d.price + dg.grade_price) as pay_price,
                ma.bank_code,
                ma.bank_no
            FROM
            job_talk_source s
            JOIN dataset d on s.dataset_id = d.id
            JOIN reviewer p on p.id = s.reviewer_id AND p.dataset_id = d.id
            JOIN member_grade mg on p.member_id = mg.member_id
            JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
            JOIN member_addition ma on p.member_id = ma.member_id
            LEFT OUTER JOIN calc_detail cd on cd.job_id = s.id AND cd.job_source_type = 'BB03'
            WHERE s.inspection_status = 'AL03'
            AND p.valid_yn = 'Y'
            AND mg.valid_yn = 'Y'
            AND cd.id is null
            AND s.inspection_date BETWEEN v_start_date AND v_end_date
            group by p.member_id
            union
            SELECT
                p.member_id,
                'BB04' as source_type,
                SUM(d.price + dg.grade_price) as pay_price,
                ma.bank_code,
                ma.bank_no
            FROM
            job_talk s
            JOIN dataset d on s.dataset_id = d.id
            JOIN reviewer p on p.id = s.reviewer_id AND p.dataset_id = d.id
            JOIN member_grade mg on p.member_id = mg.member_id
            JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
            JOIN member_addition ma on p.member_id = ma.member_id
            LEFT OUTER JOIN calc_detail cd on cd.job_id = s.id AND cd.job_source_type = 'BB04'
            WHERE s.inspection_status = 'AL03'
            AND p.valid_yn = 'Y'
            AND mg.valid_yn = 'Y'
            AND cd.id is null
            AND s.inspection_date BETWEEN v_start_date AND v_end_date
            group by p.member_id
            union
            SELECT
                p.member_id,
                'BB02' as source_type,
                SUM(d.price + dg.grade_price) as pay_price,
                ma.bank_code,
                ma.bank_no
            FROM
            job_talk s
            JOIN dataset d on s.dataset_id = d.id
            JOIN annotator p on p.id = s.annotator_id AND p.dataset_id = d.id
            JOIN member_grade mg on p.member_id = mg.member_id
            JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
            JOIN member_addition ma on p.member_id = ma.member_id
            LEFT OUTER JOIN calc_detail cd on cd.job_id = s.id AND cd.job_source_type = 'BB02'
            WHERE s.inspection_status = 'AL03'
            AND p.valid_yn = 'Y'
            AND mg.valid_yn = 'Y'
            AND cd.id is null
            AND s.inspection_date BETWEEN v_start_date AND v_end_date
            group by p.member_id;

        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = true;
        SET v_calc_month = CAST(DATE_FORMAT(NOW(), "%Y%m") AS INTEGER );
        OPEN cur_calc_header;
            calc_loop: LOOP
                FETCH cur_calc_header INTO v_member, v_source_type, v_pay_price,v_bank_code, v_bank_no;

                    IF done THEN
                        LEAVE calc_loop;
                    END IF;
                    SET v_rowcount = v_rowcount + 1;
                    #INSERT HEADER DATA
                    INSERT INTO calc
                    (member_id,calc_month, pay_price, pay_bank_code, pay_bank_no, calc_status,calc_date, vat_price, tax_price)
                    VALUES
                    (v_member, v_calc_month, v_pay_price, v_bank_code, v_bank_no, 'AN01', NOW(), 0, 0);

                    SET v_calc_id = (SELECT LAST_INSERT_ID());

                    IF v_source_type = 'BB01' THEN
                        INSERT INTO calc_detail
                        (dataset_id, calc_id, job_source_type, job_id, calc_type, pay_type, job_price, price, grade_price, grade_code)
                        SELECT
                            s.dataset_id,
                            v_calc_id,
                            v_source_type,
                            s.id,
                            'AI01',
                            d.provider_pay_type,
                            d.price + dg.grade_price as job_price,
                            d.price,
                            dg.grade_price,
                            mg.grade_code
                        FROM
                        job_talk_source s
                        JOIN dataset d on s.dataset_id = d.id
                        JOIN provider p on p.id = s.provider_id AND p.dataset_id = d.id
                        JOIN member_grade mg on p.member_id = mg.member_id
                        JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
                        JOIN member_addition ma on p.member_id = ma.member_id
                        WHERE s.inspection_status = 'AL03'
                        AND p.valid_yn = 'Y'
                        AND mg.valid_yn = 'Y'
                        AND p.member_id = v_member
                        AND s.inspection_date BETWEEN v_start_date AND v_end_date
                        group by p.member_id, s.id;
                    ELSEIF v_source_type = 'BB02' THEN
                        INSERT INTO calc_detail
                        (dataset_id, calc_id, job_source_type, job_id, calc_type, pay_type, job_price, price, grade_price, grade_code)
                        SELECT
                            s.dataset_id,
                            v_calc_id,
                            v_source_type,
                            s.id,
                            'AI01',
                            d.provider_pay_type,
                            d.price + dg.grade_price as job_price,
                            d.price,
                            dg.grade_price,
                            mg.grade_code
                        FROM
                        job_talk s
                        JOIN dataset d on s.dataset_id = d.id
                        JOIN annotator p on p.id = s.annotator_id AND p.dataset_id = d.id
                        JOIN member_grade mg on p.member_id = mg.member_id
                        JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
                        JOIN member_addition ma on p.member_id = ma.member_id
                        WHERE s.inspection_status = 'AL03'
                        AND p.valid_yn = 'Y'
                        AND mg.valid_yn = 'Y'
                        AND p.member_id = v_member
                        AND s.inspection_date BETWEEN v_start_date AND v_end_date
                        group by p.member_id, s.id;
                    ELSEIF v_source_type = 'BB03' THEN
                        INSERT INTO calc_detail
                        (dataset_id, calc_id, job_source_type, job_id, calc_type, pay_type, job_price, price, grade_price, grade_code)
                        SELECT
                            s.dataset_id,
                            v_calc_id,
                            v_source_type,
                            s.id,
                            'AI01',
                            d.provider_pay_type,
                            d.price + dg.grade_price as job_price,
                            d.price,
                            dg.grade_price,
                            mg.grade_code
                        FROM
                        job_talk_source s
                        JOIN dataset d on s.dataset_id = d.id
                        JOIN reviewer p on p.id = s.reviewer_id AND p.dataset_id = d.id
                        JOIN member_grade mg on p.member_id = mg.member_id
                        JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
                        JOIN member_addition ma on p.member_id = ma.member_id
                        WHERE s.inspection_status = 'AL03'
                        AND p.valid_yn = 'Y'
                        AND mg.valid_yn = 'Y'
                        AND p.member_id = v_member
                        AND s.inspection_date BETWEEN v_start_date AND v_end_date
                        group by p.member_id, s.id;
                    ELSEIF v_source_type = 'BB04' THEN
                        INSERT INTO calc_detail
                        (dataset_id, calc_id, job_source_type, job_id, calc_type, pay_type, job_price, price, grade_price, grade_code)
                        SELECT
                            s.dataset_id,
                            v_calc_id,
                            v_source_type,
                            s.id,
                            'AI01',
                            d.provider_pay_type,
                            d.price + dg.grade_price as job_price,
                            d.price,
                            dg.grade_price,
                            mg.grade_code
                        FROM
                        job_talk s
                        JOIN dataset d on s.dataset_id = d.id
                        JOIN reviewer p on p.id = s.reviewer_id AND p.dataset_id = d.id
                        JOIN member_grade mg on p.member_id = mg.member_id
                        JOIN dataset_grade dg on d.id = dg.dataset_id AND dg.grade_code = mg.grade_code
                        JOIN member_addition ma on p.member_id = ma.member_id
                        WHERE s.inspection_status = 'AL03'
                        AND p.valid_yn = 'Y'
                        AND mg.valid_yn = 'Y'
                        AND p.member_id = v_member
                        AND s.inspection_date BETWEEN v_start_date AND v_end_date
                        group by p.member_id, s.id;
                    END IF;
            END LOOP;
        CLOSE cur_calc_header;
    END;
END;