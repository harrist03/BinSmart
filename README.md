# BinSmart

BinSmart is a smart waste management system that monitors trash bin fill levels and visualizes them on an interactive map, allowing users to view bin status in real time and optimize collection routes, reducing unnecessary trips, fuel consumption, and operational costs.

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

### Hardware Layer
**Hardware components:**
- Raspberry Pi
- HC-SR04 ultrasonic sensor
- LEDs for physical bin status indication

## 🧩 Fritzing Diagram
![Fritzing Diagram Image](/Hardware/Fritzing_diagram.png)






