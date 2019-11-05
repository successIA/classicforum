BEGIN;
--
-- Create model UserProfile
--
CREATE TABLE IF NOT EXISTS "accounts_userprofile" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "created" datetime NOT NULL, "modified" datetime NOT NULL, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id"));
CREATE TABLE IF NOT EXISTS "accounts_userprofile_thread_following" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "userprofile_id" integer NOT NULL REFERENCES "accounts_userprofile" ("id"), "thread_id" integer NOT NULL REFERENCES "threads_thread" ("id"));
CREATE TABLE IF NOT EXISTS "accounts_userprofile_user_followers" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "userprofile_id" integer NOT NULL REFERENCES "accounts_userprofile" ("id"), "user_id" integer NOT NULL REFERENCES "auth_user" ("id"));
CREATE TABLE IF NOT EXISTS "accounts_userprofile_user_following" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "userprofile_id" integer NOT NULL REFERENCES "accounts_userprofile" ("id"), "user_id" integer NOT NULL REFERENCES "auth_user" ("id"));
CREATE UNIQUE INDEX "accounts_userprofile_thread_following_userprofile_id_thread_id_7345c910_uniq" ON "accounts_userprofile_thread_following" ("userprofile_id", "thread_id");
CREATE INDEX "accounts_userprofile_thread_following_userprofile_id_aee0b3fd" ON "accounts_userprofile_thread_following" ("userprofile_id");
CREATE INDEX "accounts_userprofile_thread_following_thread_id_0f6edde8" ON "accounts_userprofile_thread_following" ("thread_id");
CREATE UNIQUE INDEX "accounts_userprofile_user_followers_userprofile_id_user_id_26494607_uniq" ON "accounts_userprofile_user_followers" ("userprofile_id", "user_id");
CREATE INDEX "accounts_userprofile_user_followers_userprofile_id_30027837" ON "accounts_userprofile_user_followers" ("userprofile_id");
CREATE INDEX "accounts_userprofile_user_followers_user_id_a42df29d" ON "accounts_userprofile_user_followers" ("user_id");
CREATE UNIQUE INDEX "accounts_userprofile_user_following_userprofile_id_user_id_bd772c5c_uniq" ON "accounts_userprofile_user_following" ("userprofile_id", "user_id");
CREATE INDEX "accounts_userprofile_user_following_userprofile_id_10b7d144" ON "accounts_userprofile_user_following" ("userprofile_id");
CREATE INDEX "accounts_userprofile_user_following_user_id_3b7810d8" ON "accounts_userprofile_user_following" ("user_id");
COMMIT;


SELECT  "threads_thread"."slug",
 comments_comment.id AS comment_id, comments_comment.created AS comment_created,
 threads_threadfollowership.userprofile_id,  COUNT("comments_comment"."id") AS "num_comments",
 threads_threadfollowership.comment_time AS "comment_time",
 MAX(comments_comment.created) AS recent
  FROM "threads_thread"
  INNER JOIN "threads_threadfollowership" ON ("threads_thread"."id" = "threads_threadfollowership"."thread_id") 
  LEFT OUTER JOIN "comments_comment" ON ("threads_thread"."id" = "comments_comment"."thread_id")
  WHERE ("threads_thread"."visible" = True 
  AND "threads_threadfollowership"."userprofile_id" = 2 AND comment_id > 0) 
  GROUP BY "threads_thread"."id"  
  
  

  SELECT "threads_thread"."id", "threads_thread"."created", "threads_thread"."modified", "threads_thread"."title", "threads_thread"."slug",
 "threads_thread"."body", "threads_thread"."category_id", "threads_thread"."user_id", "threads_thread"."likes", "threads_thread"."views",
 "threads_thread"."visible", COUNT(DISTINCT "comments_comment"."id") AS "num_comments", MAX("comments_comment"."created") AS "recent" 
  FROM "threads_thread"
  INNER JOIN "threads_threadfollowership" ON ("threads_thread"."id" = "threads_threadfollowership"."thread_id") 
  LEFT OUTER JOIN "comments_comment" ON ("threads_thread"."id" = "comments_comment"."thread_id")
  WHERE ("threads_thread"."visible" = True AND "threads_threadfollowership"."userprofile_id" = 2) 
  GROUP BY "threads_thread"."id", "threads_thread"."created", "threads_thread"."modified", "threads_thread"."title", "threads_thread"."slug",
     "threads_thread"."body", "threads_thread"."category_id", "threads_thread"."user_id", "threads_thread"."likes", "threads_thread"."views",
      "threads_thread"."visible"
  HAVING COUNT(DISTINCT "comments_comment"."id") > 0 ORDER BY "recent" DESC

SELECT "threads_thread"."id", "threads_thread"."created", "threads_thread"."modified", "threads_thread"."title", "threads_thread"."slug", 
"threads_thread"."body", "threads_thread"."category_id", "threads_thread"."user_id", "threads_thread"."likes", "threads_thread"."views", 
"threads_thread"."visible",
MAX("comments_comment"."created") AS "recent" FROM "threads_thread"
INNER JOIN "threads_threadfollowership" ON ("threads_thread"."id" = "threads_threadfollowership"."thread_id")
INNER JOIN "comments_comment" ON ("threads_thread"."id" = "comments_comment"."thread_id")
INNER JOIN "threads_threadfollowership" T5 ON ("threads_thread"."id" = T5."thread_id") 
WHERE ("threads_thread"."visible" = True AND "threads_threadfollowership"."userprofile_id" = 2 AND "comments_comment"."id" > 0) 
GROUP BY "threads_thread"."id", "threads_thread"."created", "threads_thread"."modified", "threads_thread"."title",
"threads_thread"."slug", "threads_thread"."body", "threads_thread"."category_id", "threads_thread"."user_id",
"threads_thread"."likes", "threads_thread"."views", "threads_thread"."visible", T5."comment_time"
HAVING T5."comment_time" < (MAX("comments_comment"."created")) ORDER BY "recent" DESC