# 🛰️ CubeSat Antenna Simulation Projects — CST Studio Suite

## 1. Overview
This directory contains CST Studio Suite projects for the design, simulation, and analysis of **CubeSat communication antennas**.  
Each project explores different antenna configurations intended for use in **UHF, VHF, S-band, or X-band CubeSat communication links**, focusing on compact, efficient, and space-qualified structures.

---

## 2. Objective
The goal of these simulations is to:
- Design and evaluate **antenna concepts** suitable for CubeSat missions.  
- Optimize for **gain, impedance matching (S11), bandwidth, and radiation efficiency**.  
- Characterize **radiation patterns** and **polarization** for ground link performance.  
- Support the **link budget analysis** and communication subsystem design.

---

## 3. Typical Simulation Workflow

1. **Model Setup**  
   - Define substrate, conductor materials, and CubeSat mounting geometry.  
   - Set operating frequency band and boundary conditions.  

2. **Meshing and Ports**  
   - Use waveguide or discrete ports as required.  
   - Check mesh cell limits and refine as needed.  

3. **Simulation**  
   - Run frequency-domain or time-domain solvers.  
   - Monitor convergence and energy balance.  

4. **Post-Processing**  
   - Analyze S11, VSWR, impedance, and radiation patterns.  
   - Export 3D far-field results for visualization.  
   - Extract gain, directivity, and efficiency values for link budget integration.

---

## 4. Design Parameters to Record

| Parameter | Description | Units |
|------------|-------------|--------|
| Frequency Band | Operating frequency range | MHz / GHz |
| Substrate Type | Material (e.g., FR-4, Rogers RT/duroid 5880) | — |
| Substrate Height | Thickness of substrate layer | mm |
| Feed Type | Coaxial, microstrip, or waveguide | — |
| Antenna Dimensions | Main geometric parameters | mm |
| Simulation Type | Time-domain / Frequency-domain | — |
| Solver Accuracy | Convergence criteria or mesh resolution | — |

---

## 5. Output Data

| Output | Description |
|---------|-------------|
| `S11` | Reflection coefficient vs frequency (return loss). |
| `VSWR` | Voltage Standing Wave Ratio. |
| `Gain Pattern` | Far-field radiation gain plots (3D and 2D cuts). |
| `Polarization` | Linear or circular polarization analysis. |
| `Efficiency` | Total radiation efficiency of the antenna. |