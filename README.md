# Team Anant  

Team Anant is a group of undergraduate students from BITS Pilani, currently developing a 3U Nanosatellite for multispectral imaging.  
Our technical team takes a first-principles approach to design the nanosatellite under the Cal Poly CubeSat standards. The project thrives under the guidance of the Institute and the Indian Space Research Organisation.  

---

## Telemetry, Tracking and Commands (TTC) Subsystem  

The Telemetry, Tracking and Commands (TTC) Subsystem, is responsible for setting up a reliable connection between the satellite and the ground station in the UHF and S-band for downlinking payload data, beacon signal and uplinking commands data.  

**“Never let a satellite go incommunicado”** is the motto around which the TTC team works.  

The subsystem is responsible for setting up a reliable connection between the satellite and the ground station in the UHF and VHF amateur bands. It consists of a beacon and a data telemetry system.  

- The **beacon** basically advertises its humble existence to the world and is used for transmitting some mission critical data (some of the housekeeping data).  
- The **data downlinking system** is tasked with transmitting the payload data and all the housekeeping data.  
- Along with this, the **telemetry system** receives commands and updates sent from the ground station.  

The ground station server will run a software for tracking the satellite and control a rotor accordingly, to orient the antennae. The client connected to the server will be able to remotely operate it.  

A good number of satellites have been launched which have successfully established connections with the ground station. Owing to the low earth orbit into which the satellite will be deployed, each satellite pass will last for about 6-9 minutes and there will be about 3 passes a day. This calls for a high data rate of transmission which in turn increases power consumption, increases the bandwidth occupancy and decreases the reliability of connection.  

Well, here's the rub in our case:  

1. The size of a hyperspectral image is unconventionally large to be transmitted from a nanosatellite.  
2. Owing to the low earth orbit into which the satellite will be deployed, each satellite pass will last for about 6-9 minutes and there will be about 3 passes a day.  

This calls for a high data rate of transmission which in turn increases power consumption, increases the bandwidth occupancy and decreases the reliability of connection.  

---

## Current Team  

- Dhrish Bhansali  
- Ashish ("do you know what a number is? No u dont")
- Shashank Saha  
- Harsh Lakshakar  
- Kanishk Jain  
- Rakshit Jain  
- Aarnav Sood  
- Raafey Aziz  
- Vatsal Goyal  
- Y. N. Shashank  
