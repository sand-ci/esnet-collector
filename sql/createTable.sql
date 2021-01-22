create table interfaces(
id INT NOT NULL AUTO_INCREMENT,
name VARCHAR(100) NOT NULL,
status BOOLEAN NOT NULL,
active_from BIGINT(13) NOT NULL,
active_until BIGINT(13),
errors_until BIGINT(13),
discards_until BIGINT(13),
traffic_until BIGINT(13),
PRIMARY KEY ( id, name, active_from)
);
