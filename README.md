# RangerNet Thermal Surveillance

## **Device Configuration Summary**

### **PTZ System Components**
1. **Pelco-D Controller**:
   - **IP Address**: `192.168.137.99`
   - Controls the movement (pan, tilt, zoom) of the PTZ system.

2. **Thermal Camera**:
   - **IP Address**: `192.168.137.102`
   - **Port**: `8000`
   - Provides thermal imaging as part of the PTZ system.

3. **Visible Camera**:
   - **IP Address**: `192.168.137.103`
   - **Port**: `8899`
   - Provides standard video with PTZ functionality.

4. **Relay Module**:
   - **IP Address**: `192.168.137.100`
   - Controls external peripherals like lights and IR lights.

### **Independent Front Thermal Camera**
- **IP Address**: `192.168.137.101`
- **Port**: `8000`
- Operates independently of the PTZ system, providing forward-facing thermal imaging.

---

## **Network Explanation**
### **PTZ System**
- Integrates the Pelco-D controller, thermal and visible cameras, and a relay module for enhanced control and imaging.
- Designed for dynamic monitoring with full pan-tilt-zoom capabilities.

### **Front Thermal Camera**
- Functions independently for static or focused thermal monitoring in the forward direction.

### **Server Communication**
- The Flask application connects to each device using their IP address and port.
- Real-time communication via Flask-SocketIO enables responsive control and streaming.


```
# Usage
python3 webstreaming.py --ip 0.0.0.0 --port 8000
```
