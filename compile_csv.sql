\connect axis;
COPY (
  SELECT title, url, pub_date, main_text
  FROM xinwenlianbo
  WHERE
    pub_date >= '2010-01-01'
    AND pub_date <= '2016-12-31'
  ORDER BY pub_date ASC, "order" ASC
) TO '~/Desktop/xinwenlianbo_dump.csv' WITH CSV HEADER DELIMITER '|';
