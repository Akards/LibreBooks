DROP TABLE IF EXISTS payer CASCADE;
CREATE TABLE payer(
    id SERIAL,
    pass_hash CHAR(20) NOT NULL,
    email VARCHAR(40) NOT NULL,
    full_name VARCHAR(40) NOT NULL,
    company_name VARCHAR(30),
    PRIMARY KEY (id)
    );

DROP TABLE IF EXISTS accountant CASCADE;
CREATE TABLE accountant(
    id SERIAL,
    pass_hash CHAR(20) NOT NULL,
    email VARCHAR(40) NOT NULL,
    full_name VARCHAR(40) NOT NULL,
    security_level INT NOT NULL,
    PRIMARY KEY (id)
    );

DROP TABLE IF EXISTS company CASCADE;
CREATE TABLE company(
    id SERIAL,
    comp_name VARCHAR(30),
    PRIMARY KEY (id)
    );

DROP TABLE IF EXISTS can_access CASCADE;
CREATE TABLE can_access(
    user_id INT REFERENCES accountant(id),
    comp_id INT REFERENCES company(id),
    PRIMARY KEY(user_id, comp_id)
    );

DROP TABLE IF EXISTS account CASCADE;
CREATE TABLE account(
    id SERIAL,
    name VARCHAR(60) NOT NULL,
    type VARCHAR(20) NOT NULL,
    balance FLOAT(2),
    security_level INT,
    PRIMARY KEY(id)
    );

DROP TABLE IF EXISTS owns CASCADE;
CREATE TABLE owns(
    comp_id INT REFERENCES company(id),
    acc_id INT REFERENCES account(id),
    PRIMARY KEY(comp_id, acc_id)
    );

DROP TABLE IF EXISTS transact CASCADE;
CREATE TABLE transact(
    id SERIAL,
    time_created TIMESTAMP DEFAULT Now(),
    amount FLOAT(2) NOT NULL,
    name VARCHAR(60),
    PRIMARY KEY(id)
    );

DROP TABLE IF EXISTS inventory CASCADE;
CREATE TABLE inventory(
    id SERIAL,
    price FLOAT(2),
    quantity INT NOT NULL,
    PRIMARY KEY(id)
    );

DROP TABLE IF EXISTS invoice CASCADE;
CREATE TABLE invoice(
    id SERIAL,
    payer INT REFERENCES payer(id),
    account INT REFERENCES account(id),
    amount FLOAT(2) NOT NULL,
    date_created TIMESTAMP NOT NULL DEFAULT Now(),
    PRIMARY KEY(id)
    );

DROP TABLE IF EXISTS ledger CASCADE;
CREATE TABLE ledger(
    trans_id INT REFERENCES transact(id),
    acc_id INT REFERENCES account(id),
    amount FLOAT(2) NOT NULL,
    c_or_d CHAR(1) NOT NULL,
    CONSTRAINT check_allowed CHECK (c_or_d in ('C', 'D')),
    PRIMARY KEY(trans_id, acc_id)
    );

