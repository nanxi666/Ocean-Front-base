CREATE DATABASE ocean_data;

USE ocean_data;

CREATE TABLE location (
    location INT AUTO_INCREMENT PRIMARY KEY,
    latitude DOUBLE,
    longitude DOUBLE
);

CREATE TABLE observation (
    observation_id INT AUTO_INCREMENT PRIMARY KEY,
    location INT,
    date DATE,
    depth DOUBLE,
    temperature DOUBLE,
    salinity DOUBLE,
    density DOUBLE,
    FOREIGN KEY (location) REFERENCES location (location)
);

CREATE TABLE gradients (
    gradient_id INT AUTO_INCREMENT PRIMARY KEY,
    observation_id INT,
    temperature_gradient DOUBLE,
    salinity_gradient DOUBLE,
    density_gradient DOUBLE,
    FOREIGN KEY (observation_id) REFERENCES observation (observation_id)
);
