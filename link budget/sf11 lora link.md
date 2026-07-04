
```matlab
clc; clearvars;

f = 433e6; % frequency in Hertz
Re = 6371e3; % Earth radius in metres
h  = 450e3; % satellite altitude above Earth's surface in metres
elevation_angles = 5:5:90; % elevation angle range in degrees

P_t = 20; % includes HPA, Power of the transmitter in dBm
G_t = 1; % gain of the antenna, in dBi 
L_txsystem = 1; %losses due to feeding lines, connectors, filters, HPA etc in dB
L_fspl = 0; %free space path loss (calculation below) in dB
L_atm = 0; %atmospheric, rain, clouds, fog, ionosphere attenuation + (Diffusion- due to obstacles- neglect) + (Multipath fading- only for terrestrial- neglect) in dB
L_plrz = 3; %polarization mismatch, effectively 0 for circularly polarised antennas in dB
L_point = 1.5; % pointing losses, add both reciever and transmitter pointing losses in dB

G_r = 9; % gain of ground station in dBi
G_lna_ext = 0; %gain of external lna, see below for effect on F in dBi
L_rxsystem = 1.5; %losses due to feeding lines, connectors, filters, LNA, demodulators etc in dB

S_datasheet = -132; %sensitivity on datasheet (already includes the internal LNA gain effect an noise spectrum density change) in dBm
T_cold = 200; %At zenith
T_hot  = 1000; %at horizon
T_ant = 0; %Thermal temperature, Tsky(atmospheric thermal temp) + Tgnd(due to sie and back lobes) in K, Calculation below
B_datasheet = 125e3; %Bandwidth of reciever in Hz
SNRrequired_datasheet = -17.5; %required signal to noise ratio for the reciever to be able to demod the signal in dB

U_bitrate = 980e-6; %bitrate that WE pass, megabits per second
EbNo_threshold = 7.1; %minimum Eb/No required by the reciever, in dB

% Preallocate arrays
LINKMARGINP_via_sensitivity = zeros(size(elevation_angles));
LINKMARGINP_via_ebno = zeros(size(elevation_angles));
r_all = zeros(size(elevation_angles));
L_fspl_all = zeros(size(elevation_angles));
Ts_actual_all = zeros(size(elevation_angles));
CNo_all = zeros(size(elevation_angles));
EbNo_all = zeros(size(elevation_angles));

for i = 1:length(elevation_angles)
    el = elevation_angles(i); % current elevation angle
    fprintf('\n=== Elevation Angle: %.1f° ===\n', el);

    r = sqrt((Re + h)^2 - (Re * cosd(el))^2) - Re * sind(el); % Compute slant range (distance from ground station to satellite)
    EIRP = P_t + G_t - L_txsystem; %effective output power in dBm
    L_fspl = 20*log10(4*pi*r*f/299792458);
    L_prop = L_fspl + L_atm; %propogation losses

    Pr = EIRP - L_prop - L_plrz - L_point + G_r + G_lna_ext - L_rxsystem;
    C = Pr; %recieved power to digital system at reciever end, in dBm
    T_ant = T_cold + (T_hot - T_cold) * (1 - sind(el)); %using Thot an Tcold to model elevation differences
    N = S_datasheet - SNRrequired_datasheet; %noise power
    NF = N + 174 - 10*log10(B_datasheet); %noise figure at datasheet
    F = 10^(NF/10); %noise factor at datasheet

    % if external lna connected - F = Flna + (Frx - 1)/G_lna_ext;

    Tr = (F-1)*290; %Thermal temp at reciever end
    Ts_actual = T_ant + Tr; %Thermal temp of system incluing Tatm and Tr (entire system)
    Ts_spec = F*290; %Thermal temp use by mnufacturer to calculate
    correction = 10*log10(Ts_actual/Ts_spec); %change due to Tatm

    S_actual = S_datasheet + correction; %actual sensitivity of reciever system
    Psensitivity = S_actual;
    LINKMARGINP_via_sensitivity(i) = Pr - Psensitivity;

    No = 1.380649e-23 * Ts_actual; %Noise spectral density in W/Hz
    No = 10*log10(No); %nsd in dBW/Hz

    C_ = C - 30; %C in dBW
    CNo = C_ - No; %received carrier power/noise spectral density in dB-Hz
    EbNo_calculated = CNo - 10*log10(U_bitrate) - 60; %received EbNo in dB, 60 subtracte to convert from Mbps to bps
    LINKMARGINP_via_ebno(i) = EbNo_calculated - EbNo_threshold;

    % Store results for table
    r_all(i) = r;
    L_fspl_all(i) = L_fspl;
    Ts_actual_all(i) = Ts_actual;
    CNo_all(i) = CNo;
    EbNo_all(i) = EbNo_calculated;

    % Print key values for this elevation
    fprintf('Slant range (r): %.2f km\n', r/1e3);
    fprintf('Free-space path loss (L_fspl): %.2f dB\n', L_fspl);
    fprintf('System temperature (Ts_actual): %.2f K\n', Ts_actual);
    fprintf('C/N0: %.2f dB-Hz\n', CNo);
    fprintf('Eb/No: %.2f dB\n', EbNo_calculated);
    fprintf('Link Margin (via Eb/No): %.2f dB\n', LINKMARGINP_via_ebno(i));
    fprintf('------------------------------------------\n');
end
```

```matlabTextOutput
=== Elevation Angle: 5.0° ===
Slant range (r): 1943.68 km
Free-space path loss (L_fspl): 150.95 dB
System temperature (Ts_actual): 2707.98 K
C/N0: 36.32 dB-Hz
Eb/No: 6.41 dB
Link Margin (via Eb/No): -0.69 dB
------------------------------------------
=== Elevation Angle: 10.0° ===
Slant range (r): 1569.57 km
Free-space path loss (L_fspl): 149.09 dB
System temperature (Ts_actual): 2638.78 K
C/N0: 38.29 dB-Hz
Eb/No: 8.38 dB
Link Margin (via Eb/No): 1.28 dB
------------------------------------------
=== Elevation Angle: 15.0° ===
Slant range (r): 1293.07 km
Free-space path loss (L_fspl): 147.41 dB
System temperature (Ts_actual): 2570.65 K
C/N0: 40.09 dB-Hz
Eb/No: 10.18 dB
Link Margin (via Eb/No): 3.08 dB
------------------------------------------
=== Elevation Angle: 20.0° ===
Slant range (r): 1089.70 km
Free-space path loss (L_fspl): 145.92 dB
System temperature (Ts_actual): 2504.09 K
C/N0: 41.69 dB-Hz
Eb/No: 11.78 dB
Link Margin (via Eb/No): 4.68 dB
------------------------------------------
=== Elevation Angle: 25.0° ===
Slant range (r): 938.75 km
Free-space path loss (L_fspl): 144.63 dB
System temperature (Ts_actual): 2439.61 K
C/N0: 43.10 dB-Hz
Eb/No: 13.19 dB
Link Margin (via Eb/No): 6.09 dB
------------------------------------------
=== Elevation Angle: 30.0° ===
Slant range (r): 824.96 km
Free-space path loss (L_fspl): 143.51 dB
System temperature (Ts_actual): 2377.70 K
C/N0: 44.33 dB-Hz
Eb/No: 14.42 dB
Link Margin (via Eb/No): 7.32 dB
------------------------------------------
=== Elevation Angle: 35.0° ===
Slant range (r): 737.78 km
Free-space path loss (L_fspl): 142.54 dB
System temperature (Ts_actual): 2318.84 K
C/N0: 45.41 dB-Hz
Eb/No: 15.50 dB
Link Margin (via Eb/No): 8.40 dB
------------------------------------------
=== Elevation Angle: 40.0° ===
Slant range (r): 669.99 km
Free-space path loss (L_fspl): 141.70 dB
System temperature (Ts_actual): 2263.47 K
C/N0: 46.35 dB-Hz
Eb/No: 16.44 dB
Link Margin (via Eb/No): 9.34 dB
------------------------------------------
=== Elevation Angle: 45.0° ===
Slant range (r): 616.67 km
Free-space path loss (L_fspl): 140.98 dB
System temperature (Ts_actual): 2212.02 K
C/N0: 47.17 dB-Hz
Eb/No: 17.26 dB
Link Margin (via Eb/No): 10.16 dB
------------------------------------------
=== Elevation Angle: 50.0° ===
Slant range (r): 574.38 km
Free-space path loss (L_fspl): 140.36 dB
System temperature (Ts_actual): 2164.87 K
C/N0: 47.88 dB-Hz
Eb/No: 17.97 dB
Link Margin (via Eb/No): 10.87 dB
------------------------------------------
=== Elevation Angle: 55.0° ===
Slant range (r): 540.74 km
Free-space path loss (L_fspl): 139.84 dB
System temperature (Ts_actual): 2122.38 K
C/N0: 48.49 dB-Hz
Eb/No: 18.58 dB
Link Margin (via Eb/No): 11.48 dB
------------------------------------------
=== Elevation Angle: 60.0° ===
Slant range (r): 514.02 km
Free-space path loss (L_fspl): 139.40 dB
System temperature (Ts_actual): 2084.88 K
C/N0: 49.01 dB-Hz
Eb/No: 19.10 dB
Link Margin (via Eb/No): 12.00 dB
------------------------------------------
=== Elevation Angle: 65.0° ===
Slant range (r): 493.01 km
Free-space path loss (L_fspl): 139.03 dB
System temperature (Ts_actual): 2052.66 K
C/N0: 49.44 dB-Hz
Eb/No: 19.53 dB
Link Margin (via Eb/No): 12.43 dB
------------------------------------------
=== Elevation Angle: 70.0° ===
Slant range (r): 476.81 km
Free-space path loss (L_fspl): 138.74 dB
System temperature (Ts_actual): 2025.95 K
C/N0: 49.79 dB-Hz
Eb/No: 19.88 dB
Link Margin (via Eb/No): 12.78 dB
------------------------------------------
=== Elevation Angle: 75.0° ===
Slant range (r): 464.78 km
Free-space path loss (L_fspl): 138.52 dB
System temperature (Ts_actual): 2004.96 K
C/N0: 50.06 dB-Hz
Eb/No: 20.14 dB
Link Margin (via Eb/No): 13.04 dB
------------------------------------------
=== Elevation Angle: 80.0° ===
Slant range (r): 456.47 km
Free-space path loss (L_fspl): 138.37 dB
System temperature (Ts_actual): 1989.86 K
C/N0: 50.25 dB-Hz
Eb/No: 20.33 dB
Link Margin (via Eb/No): 13.23 dB
------------------------------------------
=== Elevation Angle: 85.0° ===
Slant range (r): 451.60 km
Free-space path loss (L_fspl): 138.27 dB
System temperature (Ts_actual): 1980.75 K
C/N0: 50.36 dB-Hz
Eb/No: 20.45 dB
Link Margin (via Eb/No): 13.35 dB
------------------------------------------
=== Elevation Angle: 90.0° ===
Slant range (r): 450.00 km
Free-space path loss (L_fspl): 138.24 dB
System temperature (Ts_actual): 1977.70 K
C/N0: 50.40 dB-Hz
Eb/No: 20.48 dB
Link Margin (via Eb/No): 13.38 dB
------------------------------------------
```

```matlab
% Produce table of results
Results = table(elevation_angles.', r_all.'/1e3, L_fspl_all.', Ts_actual_all.', ...
    CNo_all.', EbNo_all.', LINKMARGINP_via_sensitivity.', LINKMARGINP_via_ebno.', ...
    'VariableNames', {'Elevation_deg', 'SlantRange_km', 'L_fspl_dB', 'Ts_K', ...
    'CNo_dBHz', 'EbNo_dB', 'LinkMargin_Sens_dB', 'LinkMargin_EbNo_dB'});

disp(Results);
```

```matlabTextOutput
    Elevation_deg    SlantRange_km    L_fspl_dB     Ts_K     CNo_dBHz    EbNo_dB    LinkMargin_Sens_dB    LinkMargin_EbNo_dB
    _____________    _____________    _________    ______    ________    _______    __________________    __________________

          5             1943.7         150.95        2708     36.323     6.4104           2.8784               -0.68956     
         10             1569.6         149.09      2638.8     38.292     8.3797           4.8477                 1.2797     
         15             1293.1         147.41      2570.6     40.089     10.177           6.6445                 3.0765     
         20             1089.7         145.92      2504.1     41.689     11.777           8.2447                 4.6767     
         25             938.75         144.63      2439.6     43.097     13.185           9.6532                 6.0852     
         30             824.96         143.51      2377.7     44.331     14.419           10.887                 7.3191     
         35             737.78         142.54      2318.8      45.41     15.498           11.966                 8.3981     
         40             669.99          141.7      2263.5     46.352      16.44           12.908                 9.3402     
         45             616.67         140.98        2212     47.173      17.26           13.728                  10.16     
         50             574.38         140.36      2164.9     47.883     17.971           14.439                 10.871     
         55             540.74         139.84      2122.4     48.494     18.581           15.049                 11.481     
         60             514.02          139.4      2084.9     49.011     19.099           15.567                 11.999     
         65             493.01         139.03      2052.7     49.441     19.529           15.997                 12.429     
         70             476.81         138.74      2025.9     49.789     19.876           16.344                 12.776     
         75             464.78         138.52        2005     50.056     20.143           16.611                 13.043     
         80             456.47         138.37      1989.9     50.245     20.333           16.801                 13.233     
         85              451.6         138.27      1980.7     50.358     20.446           16.914                 13.346     
         90                450         138.24      1977.7     50.396     20.484           16.951                 13.384     
```

```matlab
% Plot link margins vs elevation angle
figure;
plot(elevation_angles, LINKMARGINP_via_sensitivity, '-o', 'LineWidth', 1.5); hold on;
plot(elevation_angles, LINKMARGINP_via_ebno, '-s', 'LineWidth', 1.5);
grid on;
xlabel('Elevation Angle (°)');
ylabel('Link Margin (dB)');
title('Link Margin vs Elevation Angle');
legend('Via Sensitivity', 'Via Eb/No', 'Location', 'best');
```

![figure_0.png](./nealinkb_loop_media/figure_0.png)


