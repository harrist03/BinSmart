CREATE DATABASE IF NOT EXISTS BinSmart;
USE BinSmart;

DROP TABLE IF EXISTS BinReading;
DROP TABLE IF EXISTS Bin;
DROP TABLE IF EXISTS User;

CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    is_admin BOOLEAN DEFAULT FALSE
);

INSERT INTO User(username, email, google_id, is_admin) VALUES
('harrist03', 'harristeh85@gmail.com', '101472572053520235576', 1);

CREATE TABLE Bin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(8, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    address VARCHAR(255) NOT NULL,
    capacity FLOAT NOT NULL,
    is_full BOOLEAN DEFAULT FALSE
);

INSERT INTO Bin(name, latitude, longitude, address, capacity, is_full) VALUES 
('Bin 1', 54.0003, -6.3977, 'Marshes Shopping Centre', 100, FALSE),
('Bin 2', 53.9843, -6.3934, 'Dundalk Institute of Technology', 100, FALSE),
('Bin 3', 53.9877, -6.3752, 'DKIT Sport', 100, FALSE),
('Bin 4', 53.9884, -6.4009, 'Louth County Hospital', 80, FALSE);

CREATE TABLE BinReading (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id INT NOT NULL,
    distance FLOAT NOT NULL, -- distance from sensor
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bin_id) REFERENCES Bin(id) ON DELETE CASCADE
);

