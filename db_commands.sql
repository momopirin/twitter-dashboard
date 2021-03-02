CREATE DATABASE twitter_dashboard;

USE twitter_dashboard;

CREATE TABLE IF NOT EXISTS users (id VARCHAR(25) NOT NULL, created_at DATETIME, PRIMARY KEY (id));

CREATE TABLE IF NOT EXISTS user_stats (id VARCHAR(100) NOT NULL, user_id VARCHAR(25) NOT NULL, last_insert_date DATETIME, description VARCHAR(300), followers_count MEDIUMINT, friends_count MEDIUMINT, name VARCHAR(50), screen_name VARCHAR(25), statuses_count MEDIUMINT, protected BOOLEAN, PRIMARY KEY (id), UNIQUE KEY unique_id (id));

CREATE TABLE IF NOT EXISTS tweets (id VARCHAR(25) NOT NULL, created_at TIMESTAMP,
       favorite_count INT, favorited BOOLEAN, in_reply_to_status_id VARCHAR(25), 
       in_reply_to_user_id VARCHAR(25), in_reply_to_screen_name VARCHAR(35), lang CHAR(10),
       retweet_count INT, retweeted BOOLEAN, source VARCHAR(50), text VARCHAR(500), user_id VARCHAR(25), last_insert_date DATETIME,
       PRIMARY KEY (id),
       FOREIGN KEY (user_id) REFERENCES users(id)
       );
       
CREATE TABLE IF NOT EXISTS media (id VARCHAR(25) NOT NULL, media_type VARCHAR(30), filename VARCHAR(30), media_url BLOB, tweet_id VARCHAR(25), last_insert_date DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY (tweet_id) REFERENCES tweets(id));
    
/* Add support for unicode columns */
ALTER DATABASE twitter_dashboard COLLATE utf8mb4_general_ci;

ALTER TABLE user_stats CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

ALTER TABLE user_stats CHANGE description description VARCHAR(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE user_stats CHANGE name name VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE tweets CHANGE in_reply_to_screen_name in_reply_to_screen_name VARCHAR(35) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE tweets CHANGE text text VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE tweets CHANGE source source VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;