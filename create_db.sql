DROP DATABASE IF EXISTS trust_pilot;
CREATE DATABASE trust_pilot;
USE trust_pilot;

CREATE TABLE Category (
    category_id int NOT NULL AUTO_INCREMENT,
    name VARCHAR(45), 
    url VARCHAR(2000),
    PRIMARY KEY (category_id)
);

CREATE TABLE Business (
    business_id int NOT NULL AUTO_INCREMENT,
    category_id int NOT NULL,
    name VARCHAR(255),
    score float,
    reviews int,
    url VARCHAR(2000),
    PRIMARY KEY (business_id),
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);

CREATE TABLE User_details (
    user_id int NOT NULL AUTO_INCREMENT,
    user_name VARCHAR(255),
    user_location VARCHAR(45),
    primary KEY (user_id)
);

CREATE TABLE Review (
    review_id int NOT NULL AUTO_INCREMENT,
    business_id int NOT NULL,
    user_id int, 
    score float,
    url VARCHAR(2000),
    timestamp timestamp,
    PRIMARY KEY (review_id),
    FOREIGN KEY (business_id) REFERENCES Business(business_id),
    FOREIGN KEY (user_id) REFERENCES User_details(user_id)

);

CREATE TABLE Review_text (
    review_id int NOT NULL AUTO_INCREMENT,
    title VARCHAR(255),
    text VARCHAR(500),
    primary KEY (review_id),
    FOREIGN KEY (review_id) REFERENCES Review(review_id)
);


