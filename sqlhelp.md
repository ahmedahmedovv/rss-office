make empty table

-- Option 1: TRUNCATE (faster, resets identity/auto-increment)
TRUNCATE TABLE rss_feeds;

-- Option 2: DELETE (slower but safer, maintains transaction log)
DELETE FROM rss_feeds;


-----
