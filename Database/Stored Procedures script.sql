DELIMITER //

-- spGetAllIntervals: returns all the possible intervals (just for seeding)
DROP PROCEDURE IF EXISTS spPopulateIntervals //
CREATE PROCEDURE spPopulateIntervals (IN intervalDays INT, IN startDayOfWeek INT)
BEGIN
	DECLARE seedDate DATE;
	DECLARE maxDate DATE;
	DECLARE currDate DATE;
	DECLARE intervalId INT;

	SELECT min(d.doc_date), max(d.doc_date)
	INTO @seedDate, @maxDate
	FROM Document d;

	-- Set the seedDate to be on the earliest startDayOfWeek that doesnt loose data
	IF dayofweek(@seedDate) >= startDayOfWeek THEN -- Stay on this week and advance the difference in days
       SET @seedDate := date_add(@seedDate, INTERVAL startDayOfWeek - dayofweek(@seedDate) DAY);
    ELSE -- Go back to the previous week
	   SET @seedDate := date_add(@seedDate, INTERVAL -7 + startDayOfWeek - dayofweek(@seedDate) DAY);
	END IF;

	-- First insert seedDate
	SET @intervalId := 1;
	DROP TEMPORARY TABLE IF EXISTS tmpTable;
	CREATE TEMPORARY TABLE tmpTable
	SELECT @intervalId as Id, @seedDate as StartDate, date_add(@seedDate, INTERVAL intervalDays - 1 DAY) as EndDate, (SELECT count(doc_id) FROM Document WHERE doc_date BETWEEN @seedDate and date_add(@seedDate, INTERVAL intervalDays - 1 DAY)) as Doc_Count;
	-- Now add the rest of dates until maxDate (this is due to a lack of CTE in MySQL)
	SET @currDate := date_add(@seedDate, INTERVAL intervalDays DAY);
	WHILE (@currDate < @maxDate) DO
	    SET @intervalId := @intervalId + 1;

	    INSERT INTO tmpTable
	    SELECT @intervalId, @currDate, date_add(@currDate, INTERVAL intervalDays - 1 DAY), (SELECT count(doc_id) FROM Document WHERE doc_date BETWEEN @currDate and date_add(@currDate, INTERVAL intervalDays - 1 DAY));

		SET @currDate := date_add(@currDate, INTERVAL intervalDays DAY);
	END WHILE;

	INSERT INTO tfidf_interval
	SELECT * FROM tmpTable;
END //

-- spPopulateTFIDF: calculates and populates the tf idf for all words in all intervals to TERM_TF_INTERVAL
DROP PROCEDURE IF EXISTS spPopulateIntervalTFIDF //
CREATE PROCEDURE spPopulateIntervalTFIDF ()
BEGIN
	DECLARE nextIntervalId INT;
    DECLARE maxIntervalId INT;
    
    SELECT max(interval_id)
    INTO @maxIntervalId
    FROM tfidf_interval;
    
    SELECT coalesce(max(tfi.interval_id), 0) + 1
    INTO @nextIntervalId
    FROM term_tf_interval tfi;
    
    WHILE @nextIntervalId <= @maxIntervalId DO
		INSERT INTO term_tf_interval
		SELECT tfi.interval_id, t.term_id, sum(tf.tf) as tf, count(tf.doc_id) as term_doc_count, sum(tf.tf) * Log10(tfi.doc_count / count(tf.doc_id)) as tf_idf
		FROM document d
		JOIN term_tf tf on tf.doc_id = d.doc_id
		JOIN term t on tf.term_id = t.term_id
		JOIN tfidf_interval tfi on d.doc_date >= tfi.start_date and d.doc_date <= tfi.end_date
		WHERE tfi.interval_id = @nextIntervalId
		  -- and d.cat_id = 10
		GROUP BY tfi.interval_id, t.term_id
		ORDER BY 4 DESC
		LIMIT 0, 1000;
        
        SET @nextIntervalId := @nextIntervalId + 1;
    END WHILE;

    SELECT @nextIntervalId - 1;
END //

-- spPopulateIntervalCatTFIDF: calculates and populates the tf idf for all words in all intervals and categories to TERM_TF_INTERVAL
DROP PROCEDURE IF EXISTS spPopulateIntervalCatTFIDF //
CREATE PROCEDURE spPopulateIntervalCatTFIDF ()
BEGIN
	DECLARE IntervalId INT;
    DECLARE CatId INT;
	DECLARE done INT DEFAULT FALSE;
	DECLARE curCat CURSOR FOR SELECT DISTINCT interval_id, cat_id FROM tfidf_interval_cat;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN curCat;
    cat_loop: LOOP
		FETCH curCat INTO IntervalId, CatId;

		IF done THEN
			LEAVE cat_loop;
		END IF;    
        
        INSERT INTO term_tf_interval_cat
		SELECT tfi.interval_id, d.cat_id, t.term_id, sum(tf.tf) as tf, count(tf.doc_id) as term_doc_count, sum(tf.tf) * Log10(tfi.doc_count / count(tf.doc_id)) as tf_idf
		FROM document d
		JOIN term_tf tf on tf.doc_id = d.doc_id
		JOIN term t on tf.term_id = t.term_id
		JOIN tfidf_interval_cat tfi on d.cat_id = tfi.cat_id and d.doc_date >= tfi.start_date and d.doc_date <= tfi.end_date
		WHERE tfi.interval_id = IntervalId and tfi.cat_id = CatId
		GROUP BY tfi.interval_id, d.cat_id, t.term_id
		ORDER BY 6 DESC
		LIMIT 0, 1000;
	END LOOP;
 
	CLOSE curCat;
END //

-- spGetDocumentCount: returns the daily number of documents between the specified date interval
DROP PROCEDURE IF EXISTS spGetDailyDocumentCount //
CREATE PROCEDURE spGetDailyDocumentCount (IN startDate DATE, IN endDate DATE)
BEGIN
	select tfi.start_date, tfi.doc_count
    from tfidf_interval tfi
    where (startDate <= tfi.end_date) and (endDate >= tfi.start_date);
END //

-- spGetCategoryCount: returns the number of documents in a category between the specified date interval
DROP PROCEDURE IF EXISTS spGetCategoryCount //
CREATE PROCEDURE spGetCategoryCount (IN startDate DATE, IN endDate DATE)
BEGIN
	select c.cat_id, c.cat_name, sum(ti.doc_count) as doc_count
    from tfidf_interval_cat ti
    join category c on ti.cat_id = c.cat_id
    where (startDate <= ti.end_date) and (endDate >= ti.start_date)
    group by c.cat_id, c.cat_name
    having sum(ti.doc_count) > 0;
END //

-- spGetTermDailyCountPerCategory: returns the daily count of a term grouped by category between specified date interval
DROP PROCEDURE IF EXISTS spGetTermDailyCountPerCategory //
CREATE PROCEDURE spGetTermDailyCountPerCategory (IN term VARCHAR(100), IN startDate DATE, IN endDate DATE)
BEGIN
	drop temporary table if exists tmpTable;
    create temporary table tmpTable
	select d.cat_id, ti.interval_id, sum(tf.tf) as term_count
	from term t
	join term_tf tf on tf.term_id = t.term_id
	join document d on tf.doc_id = d.doc_id
	join tfidf_interval ti on d.doc_date between ti.start_date and ti.end_date
	where (startDate <= ti.end_date) and (endDate >= ti.start_date) and
		   t.term = term
	group by d.cat_id, ti.interval_id;
    
    drop temporary table if exists tmpTableCat;
    create temporary table tmpTableCat
    select distinct cat_id from tmpTable;

    select c.cat_name, tfi.start_date, coalesce(sum(t.term_count), 0) as term_count
    from tfidf_interval_cat tfi
    join category c on tfi.cat_id = c.cat_id
    left join tmpTable t on tfi.cat_id = t.cat_id and tfi.interval_id = t.interval_id
    where tfi.cat_id in (select * from tmpTableCat)
    group by c.cat_name, tfi.start_date
    order by c.cat_name, tfi.start_date;
END //

-- spGetWordCloud: returns the word cloud for the intervals
DROP PROCEDURE IF EXISTS spGetWordCloud //
CREATE PROCEDURE spGetWordCloud (IN startDate DATE, IN endDate DATE, IN maxRecords INT)
BEGIN
    DECLARE docCount INT;

	select sum(doc_count)
    into @docCount
    from tfidf_interval ti
	where (startDate <= ti.end_date) and (endDate >= ti.start_date);

	select t.term, sum(tfi.tf) as tf, sum(tfi.term_doc_count) as count_in_docs, @docCount as tot_docs, sum(tfi.tf) * Log10(@docCount / sum(tfi.term_doc_count)) as tf_idf
	from term_tf_interval tfi
	join tfidf_interval ti on tfi.interval_id = ti.interval_id
	join term t on tfi.term_id = t.term_id
	where ((startDate <= ti.end_date) and (endDate >= ti.start_date)) and
		  t.term_id not in (select term_id from banned_terms)
	group by t.term
	order by 5 desc
	limit 0,maxRecords;
END //

-- spGetWordCloud: returns the word cloud for the intervals
DROP PROCEDURE IF EXISTS spGetWordCloudCat //
CREATE PROCEDURE spGetWordCloudCat (IN startDate DATE, IN endDate DATE, IN categoryList VARCHAR(250), IN maxRecords INT)
BEGIN
	DECLARE queryStr VARCHAR(4096);
    DECLARE docCount INT;
    
	DROP TEMPORARY TABLE IF EXISTS tmpTable;
    SET @queryStr := CONCAT('CREATE TEMPORARY TABLE tmpTable SELECT cat_id FROM category WHERE cat_id in (',categoryList,')');

	PREPARE stmt FROM @queryStr;
	EXECUTE stmt;
	DEALLOCATE PREPARE stmt;
    
	select sum(doc_count)
    into @docCount
    from tfidf_interval_cat ti
	where ((startDate <= ti.end_date) and (endDate >= ti.start_date)) and
		  ti.cat_id in (select * from tmpTable);
    
	select t.term, sum(tfi.tf) as tf, sum(tfi.term_doc_count) as count_in_docs, @docCount as tot_docs, sum(tfi.tf) * Log10(@docCount / sum(tfi.term_doc_count)) as tf_idf
	from term_tf_interval_cat tfi
	join tfidf_interval_cat ti on tfi.interval_id = ti.interval_id and tfi.cat_id = ti.cat_id
	join term t on tfi.term_id = t.term_id
	where ((startDate <= ti.end_date) and (endDate >= ti.start_date)) and
		  t.term_id not in (select term_id from banned_terms) and
		  tfi.cat_id in (select * from tmpTable)
	group by t.term
	order by 5 desc
	limit 0,maxRecords;
END //

DELIMITER ;