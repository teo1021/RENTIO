COPY barrios (nombre, comuna, zona, tipo)
FROM '/docker-entrypoint-initdb.d/barrios_medellin_geomedellin.csv'
WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO alembic_version (version_num) VALUES ('20261102_01');
