# BinSmart

BinSmart is a smart waste management system that monitors trash bin fill levels and visualizes them on an interactive map, allowing users to view bin status in real time and optimize collection routes, reducing unnecessary trips, fuel consumption, and operational costs. Visit it [here](https://binsmart.live).

## 🛠️ Technologies Used

- **Hardware**: Raspberry Pi, HC-SR04 Ultrasonic Sensors, Red and Green LEDs  
- **Backend**: Python, Flask  
- **Database**: MySQL, SQLAlchemy  
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS  
- **Real-Time Messaging**: PubNub  
- **APIs**: Google Places API, Google Maps JavaScript API, Google Directions API, Google OAuth 2.0  
- **Cloud & Deployment**: AWS EC2, Nginx, Gunicorn  

## 🌟 Key Features
- Real-time monitoring of trash bin fill levels  
- LED-based visual indicators (red/green) for bin status  
- Google OAuth 2.0 authentication for user sign ins
- Optimized route calculation based on full bins only  
- Role-based admin access with PubNub read/write controls  
- Interactive map displaying labeled bin locations

## 🏗️ System Architecture
![System Architecture image](/Hardware/System_Architecture.png)

---
### Device Layer
**Hardware components:**
- Raspberry Pi
- HC-SR04 ultrasonic sensor: measure the bin's fill level
- Red and Green LEDs: physical bin status indication (red = full, green = not full)

**Note:**
- A 220Ohm resistor is used to prevent damage to the LEDs
- A 1kOhm and a 2kOhm resistor to used to allow the ECHO pin in the ultrasonic sensor to have 3.3V power.

---
### Communication Layer
**PubNub Real-Time Messaging:**
- Acts as the message broker between devices and web clients
- Devices publish sensor readings to `bin_data` channel
- Flask app subscribes to receive real-time updates

**Message Format:**
```json
{
  "bin_id": "1",
  "distance": 20
}
```
---
### Backend / Web Server Layer
- **Nginx** acts as a reverse proxy and handles incoming HTTP requests.
- **Gunicorn** serves as the WSGI server, interfacing between Nginx and the Flask app.
- **Flask**: Application server that processes business logic, authentication, and API endpoints

---
### Database Layer / Design
The database schema is defined using a SQL schema file `schema.sql` located in the **Database** folder , which specifies the structure of tables, relationships, and constraints used by the application.

A MySQL database is used to store:
- Bin metadata
- Sensor readings
- User and role information

---



## 🧩 Fritzing Diagram
![Fritzing Diagram Image](/Hardware/Fritzing_diagram.png)






