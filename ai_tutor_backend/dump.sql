PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version VALUES('40118a0bf56c');
CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(128) NOT NULL, 
	subscription_status VARCHAR(50), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO users VALUES(1,'test@example.com','scrypt:32768:8:1$V6MUmS5yQ26K7gxG$ef4f51ff077e3c9d34a0e51a2bde9335a257598d5ce52c970dbaa3901201532b394f8d78376a25d202a8b5d8d48d855184a0f6da2fb9a3910a7712d750415f0d','free','2025-09-28 22:24:11.313934','2025-09-28 22:24:11.313938');
INSERT INTO users VALUES(2,'comprehensive@example.com','scrypt:32768:8:1$s4U8seaB08WyuJ4V$4ff913032904c1a2661b2d73e625309909ba068751e795caba2612173390d768cd04b95f2c7cc5c5cf6a1ec5bad5db760b78d0a15502d5ed7a93c79aad72d97f','free','2025-09-28 22:26:41.148860','2025-09-28 22:26:41.148864');
INSERT INTO users VALUES(3,'john@example.com','scrypt:32768:8:1$uIV6Mf4qpjU1PIGE$b98df9ca0e1cf955ac0b31688f23b86e26b52c605d61d42fee5c21d81893bddec1a13171c3f84e34b7e59a212af449b330efba3966f46b2ca8c51ff5cad05e98','free','2025-09-29 20:32:54.042630','2025-09-29 20:32:54.042635');
INSERT INTO users VALUES(4,'jane@example.com','scrypt:32768:8:1$vWHi4fGM0VXEKU8T$082d26a687e7689ba683b69d696ab85b99045180bb40c7e4f2f6b0238714273eced0044d6760ed008e770047e48dce3291beb428c895c65b52bf8c2bb11bc825','free','2025-09-29 20:42:26.189862','2025-09-29 20:42:26.189867');
INSERT INTO users VALUES(5,'fulltest@example.com','scrypt:32768:8:1$uOF3KtXgjtRyukoY$f5c027868892dfb45079ed12fd35f63b2f0633dfa23e52ed43ec39075ec12e0d15b3893bca72a6bc1f193cf3680d51b5a616ebb5e4b869f8330f505cd55d31ff','premium','2025-10-03 19:23:30.197336','2025-10-12 21:31:32.414091');
CREATE TABLE progress (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	topic VARCHAR(255) NOT NULL, 
	total_sessions INTEGER, 
	average_score FLOAT, 
	last_session_at DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO progress VALUES(1,2,'Software Testing',1,0.84999999999999997779,'2025-09-28 22:26:41.235129','2025-09-28 22:26:41.235133','2025-09-28 22:26:41.235134');
INSERT INTO progress VALUES(2,5,'Gravity',1,0.75,'2025-10-03 19:39:18.806829','2025-10-03 19:39:18.806834','2025-10-03 19:39:18.806836');
INSERT INTO progress VALUES(3,5,'Photosynthesis',1,0.75,'2025-10-03 19:40:19.620754','2025-10-03 19:40:19.620763','2025-10-03 19:40:19.620765');
INSERT INTO progress VALUES(4,5,'Python Functions',1,0.69999999999999995559,'2025-10-04 16:12:51.335492','2025-10-04 16:12:51.335497','2025-10-04 16:12:51.335499');
CREATE TABLE responses (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	concept VARCHAR(255) NOT NULL, 
	learner_input TEXT NOT NULL, 
	ai_feedback TEXT, 
	understanding_score FLOAT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO responses VALUES(1,2,'Database Testing','Testing involves checking if code works correctly','Good! Also mention edge cases and error handling.',0.84999999999999997779,'2025-09-28 22:26:41.203328');
INSERT INTO responses VALUES(2,5,'Gravity','Gravity is a fundamental force that attracts objects with mass toward each other. The more massive an object, the stronger its gravitational pull. This is why we stay on Earth and why planets orbit the Sun.','Thank you for your explanation about Gravity. You''ve made a good attempt. Keep practicing and try to add more specific details!',0.75,'2025-10-03 19:39:18.639533');
INSERT INTO responses VALUES(3,5,'Photosynthesis','Photosynthesis is the process where plants convert sunlight into chemical energy. They use carbon dioxide from air and water from soil, with chlorophyll capturing light energy to produce glucose and oxygen.','Thank you for your explanation about Photosynthesis. You''ve made a good attempt. Keep practicing and try to add more specific details!',0.75,'2025-10-03 19:40:19.577063');
INSERT INTO responses VALUES(4,5,'Python Functions','Functions are reusable blocks of code that perform specific tasks. They can take inputs called parameters and return outputs. Functions help make code more organized and reduce repetition.','Thanks for your explanation about Python Functions. You’ve made a great start! Try adding key terms and examples to reinforce your understanding.',0.69999999999999995559,'2025-10-04 16:12:51.225994');
CREATE TABLE subscriptions (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	plan_type VARCHAR(20) NOT NULL, 
	start_date DATETIME, 
	end_date DATETIME, 
	payment_status VARCHAR(20), 
	stripe_customer_id VARCHAR(100), 
	stripe_subscription_id VARCHAR(100), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (user_id)
);
INSERT INTO subscriptions VALUES(1,2,'free','2025-09-28 22:26:41.265337',NULL,'active',NULL,NULL,'2025-09-28 22:26:41.265343','2025-09-28 22:26:41.265345');
INSERT INTO subscriptions VALUES(2,3,'free','2025-09-29 20:32:54.090727',NULL,'active',NULL,NULL,'2025-09-29 20:32:54.090730','2025-09-29 20:32:54.090731');
INSERT INTO subscriptions VALUES(3,4,'free','2025-09-29 20:42:26.233982',NULL,'active',NULL,NULL,'2025-09-29 20:42:26.233985','2025-09-29 20:42:26.233986');
INSERT INTO subscriptions VALUES(4,5,'premium','2025-10-12 21:31:32.411228','2025-11-11 21:31:32.411243','cancelled',NULL,NULL,'2025-10-03 19:23:30.584255','2025-10-12 21:32:51.857003');
CREATE UNIQUE INDEX ix_users_email ON users (email);
COMMIT;
