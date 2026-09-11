% =========================================================================
% Cubesat Downlink Link Budget - AD9364 @ 2.4 GHz, OQPSK
% Ground station: Pilani, India (28.36 N, 75.60 E)
% Rain model: ITU-R P.837 (rain rate) + P.839 (rain height) + P.838 (specific attenuation)
% Transmitter specs from AD9364 datasheet (Analog Devices, Rev. C)
%
% CORRECTIONS APPLIED vs. original version:
%   1. PA_output_dBm is now derived from P_tx_dBm + PA_gain_dB instead of
%      a hardcoded value that matched neither the "no PA" nor "with PA"
%      case described in the original comments.
%   2. Output mismatch loss now switches between the AD9364's own S22
%      (no-PA case) and the external PA's output S22 (PA case) - these
%      are two different physical interfaces and were being conflated.
%   3. Added an explicit feeder/cable loss term (PA/AD9364 -> antenna).
%   4. ITU-R P.838 k/alpha are now computed by interpolating the actual
%      Recommendation table (log-log for k, linear for alpha vs log f)
%      instead of using hardcoded constants that didn't match 2.4 GHz.
%   5. Eb/N0 requirement is now tied to a named, documented FEC scheme
%      instead of a bare unexplained number.
% =========================================================================
clear; clc; close all;

%% ------------------------- USER INPUTS ---------------------------------
% Frequency and geometry
f_Hz     = 2.4e9;           % [Hz] Downlink frequency (S-band / ISM)
f_GHz    = f_Hz/1e9;        % [GHz] same, for rain-model lookups
c        = 3e8;             % [m/s] Speed of light
altitude = 450e3;           % [m] Orbit altitude (circular)
min_elev = 5;               % [deg] Minimum elevation angle

% Data volume
image_size_MB   = 270;                          % [MB] Compressed image size
image_size_bits = image_size_MB * 8 * 1e6;      % [bits]

% Pass duration
pass_time = 600;            % [s] 10 minutes

% ---- Transmit chain (AD9364 + optional external PA) ---------------------
P_tx_dBm          = 7.5;    % [dBm] AD9364 max output at 2.4 GHz (datasheet Table 1)
use_PA            = true;   % true = external PA present, false = AD9364 drives antenna directly
PA_gain_dB        = 12.5;   % [dB] External PA gain (ignored if use_PA = false)
PA_output_S22_dB  = -12;    % [dB] External PA OUTPUT match -- get this from YOUR PA's datasheet,
                             %      it has nothing to do with the AD9364's S22
AD9364_S22_dB     = -10;    % [dB] AD9364 output S22 (datasheet Table 1) - used only if no PA
cable_loss_dB     = 0.3;    % [dB] Feeder/connector loss between PA (or AD9364) and antenna
G_tx_dBi          = 5;      % [dBi] Cubesat antenna gain

if use_PA
    PA_output_dBm = P_tx_dBm + PA_gain_dB;   % derived, not hardcoded
    output_S22_dB = PA_output_S22_dB;        % mismatch now happens at the PA's output
    mismatch_src  = 'PA';
else
    PA_output_dBm = P_tx_dBm;
    output_S22_dB = AD9364_S22_dB;           % mismatch happens at the AD9364's output
    mismatch_src  = 'AD9364';
end

S22_lin          = 10^(output_S22_dB/10);
mismatch_loss_dB = -10*log10(1 - S22_lin);   % return-loss -> insertion-loss conversion

% ---- Receiver / Ground station -------------------------------------------
D_dish        = 3;          % [m] Ground dish diameter
eff           = 0.55;       % Antenna aperture efficiency
T_sys         = 150;        % [K] System noise temperature
atm_loss_dB   = 0.5;        % [dB] Clear-sky atmospheric (gaseous) loss
point_loss_dB = 0;          % [dB] Pointing loss

% ---- Modulation and coding (CCSDS-compatible OQPSK) -----------------------
% NOTE: CCSDS 133.0-B-2 (Space Packet Protocol) only defines packet framing
% (APID, sequence count, 6-byte primary header) and performs NO error
% correction of its own (see SPP Sec. 2.3.1). Channel coding is a
% DIFFERENT CCSDS standard: CCSDS 131.0-B-6 (TM Synchronization and
% Channel Coding). That document specifies the code structures below
% (generator polynomials, block lengths, rates) but does NOT publish
% Eb/N0-vs-BER performance curves - the dB figures here are general
% literature/textbook estimates for BER=1e-6, NOT numbers taken from
% CCSDS 131.0-B-6 itself. Replace them with your decoder's actual
% published performance curve if you have one.
%
%   'uncoded'       ~10.5 dB   (no FEC at all)
%   'conv_1_2'      ~4.5  dB   (CCSDS Sec 4.3: (7,1/2) convolutional, K=7)
%   'concatenated'  ~2.5  dB   (CCSDS Sec 6: conv + Reed-Solomon (255,223))
%   'turbo_1_2'     ~1.0  dB   (CCSDS Sec 7: Turbo code, rate 1/2)
%   'ldpc_1_2'      ~1.0  dB   (CCSDS Sec 8.4: LDPC family, rate 1/2, k=4096)
%
% CCSDS 131.0-B-6 Sec 13.3 explicitly recommends the LDPC family for
% high-data-rate, bandwidth-limited links using QPSK/OQPSK or higher
% (>=2 coded symbols per modulation symbol) -- which is exactly this
% link (LEO, OQPSK). Sec 13.2 says Turbo codes are better suited to
% power-constrained links "beyond low-Earth orbit." That's why LDPC,
% not Turbo or plain convolutional, is the default below.
FEC_scheme = 'ldpc_1_2';

switch FEC_scheme
    case 'uncoded',      EbN0_req_dB = 10.5;
    case 'conv_1_2',     EbN0_req_dB = 4.5;
    case 'concatenated', EbN0_req_dB = 2.5;
    case 'turbo_1_2',    EbN0_req_dB = 1.0;
    case 'ldpc_1_2',     EbN0_req_dB = 1.0;
    otherwise, error('Unknown FEC_scheme: %s', FEC_scheme);
end
impl_loss_dB = 2;           % [dB] Implementation loss (EVM, carrier leakage, filtering, etc.)

% ---- Rain attenuation (ITU-R P.837 + P.839 + P.838) ------------------------
use_itu_rain        = true;
rain_fade_dB_manual = 5;    % fallback value, not used if use_itu_rain = true

gs_lat = 28.36;             % Pilani, India
gs_lon = 75.60;
link_availability = 99.9;   % [%]
polarization = 'circular';
% ---------------------------------------------------------------------------

%% ------------------------- COMPUTATIONS ------------------------------------
lambda = c/f_Hz;

% --- Geometry: slant range ---
Re = 6371e3;
theta_c = acosd(Re/(Re+altitude) * cosd(min_elev)) - min_elev;
slant_range = sqrt((Re+altitude)^2 + Re^2 - 2*(Re+altitude)*Re*cosd(theta_c));
slant_range_km = slant_range/1e3;

% --- Free-space path loss ---
L_fs_dB = 20*log10(4*pi*slant_range/lambda);

% --- EIRP (now includes cable loss) ---
EIRP_dBm = PA_output_dBm + G_tx_dBi - cable_loss_dB;

% --- Ground antenna gain / G-over-T ---
G_rx_dBi = 10*log10(eff * (pi*D_dish/lambda)^2);
G_T_dB   = G_rx_dBi - 10*log10(T_sys);

% --- Rain attenuation: ITU-R P.838 k/alpha via table interpolation ---
if use_itu_rain
    % ITU-R P.838 Table 1 (1-8 GHz range; extend the table before trusting
    % results outside this range)
    f_table      = [1        2       4       6       7       8      ];
    kH_table     = [0.0000387 0.000154 0.000650 0.00175 0.00301 0.00454];
    kV_table     = [0.0000352 0.000138 0.000591 0.00155 0.00265 0.00395];
    alphaH_table = [0.912    0.963   1.121   1.308   1.332   1.327  ];
    alphaV_table = [0.880    0.923   1.075   1.265   1.312   1.310  ];

    if f_GHz < f_table(1) || f_GHz > f_table(end)
        warning('f_GHz = %.2f is outside the tabulated 1-8 GHz range; extend the table before trusting this result.', f_GHz);
    end

    log_f  = log10(f_GHz);
    log_ft = log10(f_table);
    kH_f     = 10^interp1(log_ft, log10(kH_table), log_f, 'linear', 'extrap');
    kV_f     = 10^interp1(log_ft, log10(kV_table), log_f, 'linear', 'extrap');
    alphaH_f = interp1(log_ft, alphaH_table, log_f, 'linear', 'extrap');
    alphaV_f = interp1(log_ft, alphaV_table, log_f, 'linear', 'extrap');

    % Polarization tilt angle tau (deg): 0 = horizontal, 90 = vertical, 45 = circular
    if strcmpi(polarization, 'circular')
        tau = 45;
    elseif strcmpi(polarization, 'horizontal')
        tau = 0;
    else
        tau = 90;
    end
    theta = min_elev; % path elevation angle used in the general P.838 combination formula

    k_rain     = (kH_f + kV_f + (kH_f - kV_f)*cosd(theta)^2*cosd(2*tau)) / 2;
    alpha_rain = (kH_f*alphaH_f + kV_f*alphaV_f + ...
                 (kH_f*alphaH_f - kV_f*alphaV_f)*cosd(theta)^2*cosd(2*tau)) / (2*k_rain);

    % Rain height (ITU-R P.839 approximation) and rain-affected path length
    h_R = 5.0 - 0.075*(gs_lat - 23);    % [km] valid for 23 <= lat < 60 (approximate model)
    h_0 = 0;
    L_s = (h_R - h_0) / sind(min_elev); % [km] slant path length through rain

    % Point rain rate exceeded for (100 - availability)% of the year.
    % NOTE: these are generic placeholder tiers, NOT looked up from the
    % actual ITU-R P.837 rain map for Pilani's coordinates. For a rigorous
    % design, query P.837 at gs_lat/gs_lon (e.g. via the ITU-Rpy package).
    if link_availability >= 99.9
        R = 25;   % mm/h
    elseif link_availability >= 99.5
        R = 15;
    elseif link_availability >= 99
        R = 8;
    else
        R = 0;
    end

    gamma_R      = k_rain * R^alpha_rain;  % [dB/km] specific attenuation
    rain_fade_dB = gamma_R * L_s;          % [dB] total rain fade
else
    rain_fade_dB = rain_fade_dB_manual;
    k_rain = NaN; alpha_rain = NaN;
end

% --- Total other losses ---
total_other_losses = atm_loss_dB + point_loss_dB + rain_fade_dB + mismatch_loss_dB;

% --- Received C/N0 ---
% C/N0 [dBHz] = EIRP[dBm] - FSPL[dB] + G/T[dB/K] + 198.6 - other_losses[dB]
% (198.6 = 228.6 - 30: Boltzmann's constant term (-10*log10(k)=228.6 dBW/K/Hz),
%  minus 30 dB to convert EIRP from dBW to dBm)
C_N0_dB = EIRP_dBm - L_fs_dB + G_T_dB + 198.6 - total_other_losses;

% --- Required data rate for one pass ---
R_req = image_size_bits / pass_time;
C_N0_req_dB = EbN0_req_dB + impl_loss_dB + 10*log10(R_req);

% --- Margin ---
margin_dB = C_N0_dB - C_N0_req_dB;

% --- Maximum data rate at 0 dB margin ---
R_max = 10^((C_N0_dB - (EbN0_req_dB + impl_loss_dB))/10);

%% ------------------------- DISPLAY RESULTS ----------------------------------
fprintf('================ LINK BUDGET RESULTS ================\n');
fprintf('Ground station: Pilani, India (%.2f N, %.2f E)\n', gs_lat, gs_lon);
fprintf('Frequency: %.2f GHz\n', f_GHz);
fprintf('Slant range: %.1f km\n', slant_range_km);
fprintf('Free-space path loss: %.2f dB\n', L_fs_dB);
fprintf('AD9364 output power: %.2f dBm\n', P_tx_dBm);
fprintf('PA in chain: %d (gain %.1f dB)\n', use_PA, PA_gain_dB);
fprintf('PA/Tx output power: %.2f dBm\n', PA_output_dBm);
fprintf('EIRP (after cable loss): %.2f dBm\n', EIRP_dBm);
fprintf('Output mismatch loss (%s S22 = %.1f dB): %.3f dB\n', mismatch_src, output_S22_dB, mismatch_loss_dB);
fprintf('Cable/feeder loss: %.2f dB\n', cable_loss_dB);
fprintf('Rain model: k = %.5g, alpha = %.3f (interpolated at %.2f GHz)\n', k_rain, alpha_rain, f_GHz);
fprintf('Rain fade: %.3f dB\n', rain_fade_dB);
fprintf('Total other losses: %.3f dB\n', total_other_losses);
fprintf('Received C/N0: %.2f dBHz\n', C_N0_dB);
fprintf('FEC scheme: %s  (Eb/N0 req = %.1f dB)\n', FEC_scheme, EbN0_req_dB);
fprintf('Required data rate for %d s pass: %.3f Mbps\n', pass_time, R_req/1e6);
fprintf('Required C/N0: %.2f dBHz\n', C_N0_req_dB);
fprintf('Link margin: %.2f dB\n', margin_dB);
if margin_dB >= 0
    fprintf('=> Link CLOSES with margin.\n');
else
    fprintf('=> Link DOES NOT close. Need more power/antenna gain/FEC, or a longer pass.\n');
end
fprintf('Maximum data rate (0 dB margin): %.3f Mbps\n', R_max/1e6);
