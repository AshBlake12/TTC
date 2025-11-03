# 🛰️ MATLAB Link Budget Simulation for LEO Satellite Communication

## 1. Overview
This MATLAB script computes and visualizes the **link margin** of a satellite communication link between a **LEO spacecraft** and a **ground station** as a function of **elevation angle**.  

It evaluates two key metrics:
- **Link Margin via Receiver Sensitivity**  
- **Link Margin via Eb/No (Energy per bit to Noise density ratio)**  

These results determine whether the received signal power is sufficient for reliable demodulation at various satellite elevation angles.

---

## 2. Purpose
A **link budget** accounts for every gain and loss in a communication path — from the transmitter output to the receiver input — to determine if enough signal power reaches the receiver.  

This model helps to:
- Evaluate **coverage performance** versus elevation  
- Quantify **propagation and system losses**  
- Determine **link margin reserves** for reliability  
- Assess **system design feasibility** before hardware or simulation testing  

---

## 3. Key Parameters

| Parameter | Symbol | Description | Units |
|------------|---------|-------------|--------|
| Frequency | `f` | Carrier frequency | Hz |
| Earth Radius | `Re` | Mean Earth radius | m |
| Satellite Altitude | `h` | Height above Earth surface | m |
| Elevation Angles | `el` | Ground station elevation range | degrees |
| Tx Power | `P_t` | Transmitter output (including HPA) | dBW |
| Tx Antenna Gain | `G_t` | Transmit antenna gain | dBi |
| Rx Antenna Gain | `G_r` | Receive antenna gain | dBi |
| Tx System Loss | `L_txsystem` | Feedline, connector, filter, HPA losses | dB |
| Rx System Loss | `L_rxsystem` | Feedline, filter, LNA, demodulator losses | dB |
| Pointing Loss | `L_point` | Misalignment or tracking error loss | dB |
| Bandwidth | `B_datasheet` | Receiver IF bandwidth | Hz |
| Bitrate | `U_bitrate` | Data transmission rate | Mbps |
| Receiver Sensitivity | `S_datasheet` | Sensitivity threshold | dBm |
| Eb/No Threshold | `EbNo_threshold` | Minimum Eb/No required | dB |

---

## 4. Outputs

| Variable | Description | Units |
|-----------|-------------|-------|
| `LINKMARGINP_via_sensitivity` | Margin between received power and sensitivity | dB |
| `LINKMARGINP_via_ebno` | Margin between calculated Eb/No and threshold | dB |
| `Results` | Table summarizing link performance vs elevation | — |
| `Plot` | Graph showing link margin variation vs elevation | — |

---

## 5. Graph Interpretation
- **Link margin** typically increases with **elevation angle**, as path loss decreases.  
- At **low elevations**, atmospheric noise and longer path lengths reduce received power.  
- A **positive link margin** indicates a reliable link.  
- Margins above **10 dB** generally provide robust communication even under minor disturbances.

---

## 6. How to Run
1. Open the MATLAB script.  
2. Adjust the system parameters to match your satellite and ground station setup.  
3. Run the script.  
4. The output table and graph will show link margin variation across elevation angles.  

---

## 7. Notes
- The model assumes free-space propagation and simplified atmospheric losses.  
- Results are expressed in **dB** and **dBm** — ensure consistent unit use.  
- Adjust bitrate and bandwidth carefully; mismatched units affect Eb/No results.  