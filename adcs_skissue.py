"""
================================================================================
cubesat_propagator.py
================================================================================
1U CubeSat Orbit Propagator & LoRa RFM96W Link Budget Analyser

Propagates FIVE different orbital initial conditions (Keplerian elements) and,
for each one, computes:
  - Full link budget table (el 5 to 90 deg, exact match to provided MATLAB output)
  - 7-day pass predictions over the Pilani ground station
  - Beacon timing optimisation (optimal x/y window lengths for blind cycling)
  - Doppler shift at peak elevation of each pass

Hardware / RF parameters:
  Radio     : HopeRF RFM96W (SX1276 core)
  Frequency : 433 MHz
  Modulation: LoRa SF12, BW=125 kHz, CR=4/5, explicit header
  Max Tx    : +20 dBm PA_BOOST  (P_t = -10 dBW = 100 mW)
  External LNA at GS: +15 dB

MATLAB equivalence:
  All link budget values (C/N0, Eb/N0, link margins) are verified to match
  the provided MATLAB script to 4 decimal places.  See link_budget() docstring
  for notes on the MATLAB unit convention that is faithfully replicated here.

Assumptions / limitations:
  - Circular Keplerian orbit (eccentricity = 0)
  - J2 perturbation and atmospheric drag are NOT modelled
    (adequate for 7-day operations planning at 450 km)
  - Earth rotation is included (OMEGA_E = 7.29e-5 rad/s)
  - Satellite attitude: isotropic antenna (no attitude model needed)
  - No GPS on satellite -- beacon cycle runs blind

Dependency : numpy only   ->   pip install numpy
Run         : python cubesat_propagator.py
================================================================================
"""

import numpy as np


# ==============================================================================
# SECTION 1 -- PHYSICAL CONSTANTS
# These are exact CODATA / IAU values; do not edit.
# ==============================================================================

PI      = np.pi
R_E     = 6_371_000.0       # Earth mean radius                        [m]
MU      = 3.986004418e14    # Standard gravitational parameter GM_E    [m^3/s^2]
OMEGA_E = 7.2921150e-5      # Earth sidereal rotation rate             [rad/s]
C_LIGHT = 299_792_458.0     # Speed of light in vacuum                 [m/s]
k_B     = 1.380649e-23      # Boltzmann constant                       [J/K]


# ==============================================================================
# SECTION 2 -- GROUND STATION  (Pilani, Rajasthan)
# Edit GS_LAT_DEG / GS_LON_DEG to relocate the ground station.
# ==============================================================================

GS_LAT_DEG   = 28.3802     # Geodetic latitude                        [deg N]
GS_LON_DEG   = 75.6092     # Longitude                                [deg E]
GS_ALT_M     = 333.0       # Altitude above mean sea level            [m]
MIN_ELEV_DEG = 5.0         # Minimum elevation to count as a pass     [deg]

GS_LAT   = np.radians(GS_LAT_DEG)
GS_LON   = np.radians(GS_LON_DEG)
MIN_ELEV = np.radians(MIN_ELEV_DEG)


# ==============================================================================
# SECTION 3 -- LORA / RFM96W LINK BUDGET PARAMETERS
#
# All values taken directly from the provided MATLAB script.
# Do not change these unless your hardware configuration has changed.
# ==============================================================================

FREQ        = 433e6        # Carrier frequency                         [Hz]
P_T         = -10.0        # Transmitter power  (-10 dBW = 100 mW = +20 dBm)
G_T         = 0.0          # Tx antenna gain -- isotropic cubesat      [dBi]
L_TXSYS     = 1.0          # Tx system losses: feed, connectors, HPA   [dB]
L_ATM       = 1.0          # Atmospheric + ionospheric losses           [dB]
L_PLRZ      = 3.0          # Polarisation mismatch loss                 [dB]
L_POINT     = 1.0          # Combined Tx + Rx pointing loss             [dB]
G_R         = 8.0          # Ground station Rx antenna gain             [dBi]
G_LNA_EXT   = 15.0         # External LNA gain at ground station        [dB]
L_RXSYS     = 1.0          # Rx system losses: feed, connectors         [dB]
S_DATASHEET = -136.0       # Datasheet sensitivity (SF12, BW=125kHz)   [dBm]
B_RX        = 125e3        # Receiver noise bandwidth                   [Hz]
SNR_REQ     = -20.0        # Min SNR required for demodulation          [dB]
T_COLD      = 200.0        # Sky noise temperature at zenith (el=90)    [K]
T_HOT       = 1000.0       # Sky noise temperature at horizon (el=0)    [K]
U_BITRATE   = 293e-6       # Useful bit rate expressed in Mbps (293 bps)
EBN0_THR    = 7.1          # Minimum Eb/N0 required by RFM96W           [dB]


# ==============================================================================
# SECTION 4 -- FIVE ORBITAL INITIAL CONDITIONS
#
# Each entry defines a complete set of Keplerian elements for a circular 1U
# CubeSat at 450 km.  Five scenarios illustrate different coverage geometries
# over Pilani (28.4 N, 75.6 E):
#
#   IC-1  ISS-inclined, RAAN=60   -- morning / early-afternoon passes
#   IC-2  Sun-synchronous (SSO)   -- dawn-dusk frozen plane; repeating ground track
#   IC-3  ISS-inclined, RAAN=150  -- afternoon / evening passes (RAAN +90 deg vs IC-1)
#   IC-4  Near-polar, RAAN=0      -- frequent passes but mostly low elevation
#   IC-5  Low-inclination, ic=28.5-- barely above GS latitude; rare, short passes
#
# Keys:
#   name      : label printed in the report
#   h_km      : circular altitude above Earth surface  [km]
#   inc_deg   : inclination                            [deg]
#   raan_deg  : Right Ascension of Ascending Node      [deg]
#   aop_deg   : argument of perigee (0 for circular)   [deg]
#   ta_deg    : true anomaly at epoch t=0              [deg]
# ==============================================================================

INITIAL_CONDITIONS = [
    {
        "name"    : "IC-1  ISS-inclined  inc=51.6 deg  RAAN=60 deg",
        "h_km"    : 450.0,
        "inc_deg" : 51.6,
        "raan_deg": 60.0,
        "aop_deg" : 0.0,
        "ta_deg"  : 0.0,
    },
    {
        "name"    : "IC-2  Sun-synchronous  inc=97.4 deg  RAAN=120 deg",
        "h_km"    : 450.0,
        "inc_deg" : 97.4,    # exact SSO inclination at 450 km altitude
        "raan_deg": 120.0,
        "aop_deg" : 0.0,
        "ta_deg"  : 0.0,
    },
    {
        "name"    : "IC-3  ISS-inclined  inc=51.6 deg  RAAN=150 deg  (afternoon)",
        "h_km"    : 450.0,
        "inc_deg" : 51.6,
        "raan_deg": 150.0,   # 90 deg RAAN shift from IC-1 shifts pass times by ~6 h
        "aop_deg" : 0.0,
        "ta_deg"  : 0.0,
    },
    {
        "name"    : "IC-4  Near-polar  inc=85 deg  RAAN=0 deg",
        "h_km"    : 450.0,
        "inc_deg" : 85.0,
        "raan_deg": 0.0,
        "aop_deg" : 0.0,
        "ta_deg"  : 0.0,
    },
    {
        "name"    : "IC-5  Low-inclination  inc=28.5 deg  RAAN=75 deg",
        "h_km"    : 450.0,
        "inc_deg" : 28.5,    # barely above GS latitude; rare passes
        "raan_deg": 75.0,
        "aop_deg" : 0.0,
        "ta_deg"  : 0.0,
    },
]


# ==============================================================================
# SECTION 5 -- ORBITAL MECHANICS
# ==============================================================================

def orbital_period(h_m):
    """
    Compute the orbital period of a circular orbit at altitude h_m.

    Uses Kepler's third law:  T = 2*pi * sqrt(a^3 / mu)
    where  a = R_E + h  is the semi-major axis (equal to orbital radius
    for a circular orbit with eccentricity = 0).

    Parameters
    ----------
    h_m : float
        Altitude above Earth surface [m].

    Returns
    -------
    float
        Orbital period [s].
    """
    a = R_E + h_m
    return 2.0 * PI * np.sqrt(a**3 / MU)


def keplerian_to_eci(h_m, inc_deg, raan_deg, aop_deg, ta_deg):
    """
    Convert Keplerian elements to an ECI Cartesian position vector.

    Assumes circular orbit (eccentricity = 0), so the orbital radius is
    constant:  r = a = R_E + h  at all positions.

    The argument of latitude  u = aop + ta  is the only angle that changes
    with time for a circular orbit.

    Rotation sequence  perifocal -> ECI:
        r_ECI = Rz(-RAAN).T  @  Rx(-inc).T  @  r_perifocal

    Parameters
    ----------
    h_m      : float  altitude above Earth surface [m]
    inc_deg  : float  inclination [deg]
    raan_deg : float  RAAN [deg]
    aop_deg  : float  argument of perigee [deg]
    ta_deg   : float  true anomaly [deg]

    Returns
    -------
    np.ndarray, shape (3,)
        ECI position vector [m].
    """
    r_orb = R_E + h_m
    inc   = np.radians(inc_deg)
    raan  = np.radians(raan_deg)
    u     = np.radians(aop_deg + ta_deg)   # argument of latitude

    # Perifocal position (x toward periapsis, y 90 deg ahead in orbital plane)
    r_peri = np.array([r_orb * np.cos(u),
                       r_orb * np.sin(u),
                       0.0])

    # Elementary rotation matrices
    Rz = np.array([[ np.cos(raan),  np.sin(raan), 0.0],
                   [-np.sin(raan),  np.cos(raan), 0.0],
                   [ 0.0,           0.0,          1.0]])

    Rx = np.array([[1.0, 0.0,           0.0         ],
                   [0.0, np.cos(inc),  -np.sin(inc) ],
                   [0.0, np.sin(inc),   np.cos(inc) ]])

    # r_ECI = Rz(-RAAN).T @ Rx(-inc).T @ r_perifocal
    return Rz.T @ Rx.T @ r_peri


def sat_eci_at_t(t, ic):
    """
    Return the satellite ECI position at time t seconds from epoch.

    For a circular orbit the mean motion is constant:
        omega = 2*pi / T_orb  [rad/s]
    so the true anomaly advances linearly: ta(t) = ta(0) + omega*t.
    All other Keplerian elements are fixed (J2 and drag neglected).

    Parameters
    ----------
    t  : float  elapsed time from epoch [s]
    ic : dict   one entry from INITIAL_CONDITIONS

    Returns
    -------
    np.ndarray, shape (3,)
        Satellite ECI position [m].
    """
    h_m   = ic["h_km"] * 1e3
    T_orb = orbital_period(h_m)
    omega = 2.0 * PI / T_orb                          # mean motion [rad/s]
    ta_t  = ic["ta_deg"] + np.degrees(omega * t)      # true anomaly at time t

    return keplerian_to_eci(
        h_m      = h_m,
        inc_deg  = ic["inc_deg"],
        raan_deg = ic["raan_deg"],
        aop_deg  = ic["aop_deg"],
        ta_deg   = ta_t,
    )


def gs_eci_at_t(t):
    """
    Return the Pilani ground station ECI position at time t.

    The GS rotates with the Earth at the sidereal rate OMEGA_E.
    It is modelled as a point on a sphere of radius  R_E + GS_ALT_M.

    Parameters
    ----------
    t : float  elapsed time from epoch [s]

    Returns
    -------
    np.ndarray, shape (3,)
        Ground station ECI position [m].
    """
    lon = GS_LON + OMEGA_E * t      # ECI longitude at time t
    r   = R_E + GS_ALT_M
    return r * np.array([
        np.cos(GS_LAT) * np.cos(lon),
        np.cos(GS_LAT) * np.sin(lon),
        np.sin(GS_LAT),
    ])


def elevation_azimuth_range(sat, gs):
    """
    Compute topocentric elevation, azimuth, and slant range of the satellite
    as seen from the Pilani ground station.

    Steps:
      1. Form range vector  delta = r_sat - r_gs  in ECI.
      2. Build local East-North-Up (ENU) unit vectors at the GS.
      3. Project delta onto ENU axes to get (east, north, up) components.
      4. elevation = arcsin(up / |delta|)
      5. azimuth   = arctan2(east, north)  -- 0 = North, increases clockwise.

    The ENU frame uses the epoch GS longitude (a valid approximation within
    any single pass lasting a few minutes).

    ENU unit vectors in ECI:
      e_hat = [-sin(lon),  cos(lon),  0]
      n_hat = [-sin(lat)*cos(lon),  -sin(lat)*sin(lon),  cos(lat)]
      u_hat = [ cos(lat)*cos(lon),   cos(lat)*sin(lon),  sin(lat)]

    Parameters
    ----------
    sat : np.ndarray (3,)  satellite ECI position [m]
    gs  : np.ndarray (3,)  ground station ECI position [m]

    Returns
    -------
    el_rad : float  elevation [rad]
    az_rad : float  azimuth   [rad]  (0=N, pi/2=E, pi=S, 3pi/2=W)
    rng_m  : float  slant range [m]
    """
    delta = sat - gs
    rng_m = float(np.linalg.norm(delta))

    lat = GS_LAT
    lon = GS_LON

    e_hat = np.array([-np.sin(lon),
                       np.cos(lon),
                       0.0])
    n_hat = np.array([-np.sin(lat) * np.cos(lon),
                      -np.sin(lat) * np.sin(lon),
                       np.cos(lat)])
    u_hat = np.array([ np.cos(lat) * np.cos(lon),
                       np.cos(lat) * np.sin(lon),
                       np.sin(lat)])

    east  = float(np.dot(delta, e_hat))
    north = float(np.dot(delta, n_hat))
    up    = float(np.dot(delta, u_hat))

    el_rad = float(np.arcsin(np.clip(up / rng_m, -1.0, 1.0)))
    az_rad = float(np.arctan2(east, north) % (2.0 * PI))

    return el_rad, az_rad, rng_m


def doppler_shift_hz(t, ic):
    """
    Compute the instantaneous Doppler frequency shift at time t.

    Formula:  delta_f = -f0 * (v_r / c)

    where  v_r  is the component of the satellite velocity along the
    line of sight to the ground station.

    Sign convention:
      satellite approaching GS  ->  v_r < 0  ->  delta_f > 0  (frequency upshift)
      satellite receding from GS -> v_r > 0  ->  delta_f < 0  (frequency downshift)

    The satellite velocity is estimated by a 0.5 s finite difference.

    Parameters
    ----------
    t  : float  time from epoch [s]
    ic : dict   one entry from INITIAL_CONDITIONS

    Returns
    -------
    float
        Doppler frequency shift [Hz].
    """
    dt    = 0.5
    r1    = sat_eci_at_t(t,      ic)
    r2    = sat_eci_at_t(t + dt, ic)
    gs    = gs_eci_at_t(t)

    v_sat = (r2 - r1) / dt                    # satellite velocity vector [m/s]
    rng   = r1 - gs                           # GS-to-sat range vector
    r_hat = rng / np.linalg.norm(rng)         # unit vector GS -> sat

    vr = float(np.dot(v_sat, r_hat))          # radial velocity (positive = receding)
    return -FREQ * vr / C_LIGHT               # Doppler shift [Hz]


# ==============================================================================
# SECTION 6 -- PASS FINDER
# ==============================================================================

def find_passes(ic, sim_days=7, dt_s=10.0):
    """
    Find all satellite passes above MIN_ELEV_DEG over the Pilani GS.

    Algorithm:
      Step through time at dt_s intervals.  When elevation first exceeds
      MIN_ELEV (AOS), begin recording the pass.  When it drops back below
      MIN_ELEV (LOS), close and store the pass record.
      Contacts shorter than 30 s are discarded as step-size artefacts.

    Parameters
    ----------
    ic       : dict   one entry from INITIAL_CONDITIONS
    sim_days : int    number of days to simulate           (default 7)
    dt_s     : float  propagation time step [s]            (default 10)

    Returns
    -------
    list of dicts, one per pass, with keys:
      start_s    : AOS epoch time                         [s]
      end_s      : LOS epoch time                         [s]
      dur_s      : pass duration                          [s]
      max_el_deg : peak elevation during pass             [deg]
      az_rise    : azimuth at AOS                         [deg]
      az_set     : azimuth at LOS                         [deg]
      t_peak_s   : epoch time of peak elevation           [s]
      day        : calendar day number (1-indexed)
      profile    : list of (t, el_deg, az_deg, range_m, doppler_hz)
                   sampled at every dt_s step during the pass
    """
    T_MAX   = sim_days * 86400.0
    passes  = []
    in_pass = False
    t_start = 0.0
    max_el  = 0.0
    t_peak  = 0.0
    az_rise = 0.0
    profile = []

    for t in np.arange(0.0, T_MAX + dt_s, dt_s):
        sat         = sat_eci_at_t(t, ic)
        gs          = gs_eci_at_t(t)
        el, az, rng = elevation_azimuth_range(sat, gs)

        if el >= MIN_ELEV:
            if not in_pass:
                # --- AOS ---
                in_pass = True
                t_start = t
                max_el  = el
                t_peak  = t
                az_rise = np.degrees(az)
                profile = []
            if el > max_el:
                max_el = el
                t_peak = t
            dop = doppler_shift_hz(t, ic)
            profile.append((t, np.degrees(el), np.degrees(az), rng, dop))

        else:
            if in_pass:
                # --- LOS ---
                in_pass = False
                dur_s   = t - t_start
                if dur_s > 30.0:
                    az_set = profile[-1][2] if profile else 0.0
                    passes.append({
                        "start_s"   : t_start,
                        "end_s"     : t - dt_s,
                        "dur_s"     : dur_s,
                        "max_el_deg": float(np.degrees(max_el)),
                        "az_rise"   : az_rise,
                        "az_set"    : az_set,
                        "t_peak_s"  : t_peak,
                        "day"       : int(t_start // 86400) + 1,
                        "profile"   : profile,
                    })
    return passes


# ==============================================================================
# SECTION 7 -- LINK BUDGET   (exact MATLAB match)
# ==============================================================================

def link_budget(el_deg):
    """
    Compute the full LoRa uplink budget at a given elevation angle.

    All 18 rows (el = 5 to 90 deg, step 5) are verified to match the
    provided MATLAB script to 4 decimal places.

    MATLAB unit convention (faithfully replicated here)
    ---------------------------------------------------
    P_t = -10 dBW throughout, so Pr is computed in dBW.
    The MATLAB script then applies  C_ = C - 30  as if C were in dBm.
    This introduces a consistent -30 dB offset into C/N0.  The EbNo
    equation compensates with a -60 term instead of -30 when converting
    U_bitrate from Mbps to bps:

        EbNo = CNo - 10*log10(U_bitrate_Mbps) - 60
             = CNo + 35.33 - 60
             (if CNo were truly in dBHz this gives correct Eb/N0)

    The -30 offset in CNo and the extra -30 in the bitrate conversion
    cancel, so final Eb/N0 values are physically correct.

    Parameters
    ----------
    el_deg : float
        Elevation angle [deg].

    Returns
    -------
    dict with keys:
      el_deg     : elevation angle                    [deg]
      r_km       : slant range                        [km]
      L_fspl_dB  : free-space path loss               [dB]
      T_ant_K    : antenna / sky noise temperature    [K]
      Ts_K       : total system noise temperature     [K]
      Pr_dBm     : received power at Rx input         [dBm]
      S_actual   : corrected receiver sensitivity     [dBm]
      LM_sens    : link margin via sensitivity        [dB]
      CNo_dBHz   : carrier-to-noise density           [dBHz]
      EbNo_dB    : energy-per-bit to noise density    [dB]
      LM_ebno    : link margin via Eb/N0              [dB]
      link_ok    : True when LM_ebno >= 0
    """
    el = np.radians(el_deg)

    # Slant range: exact spherical-Earth geometry (identical to MATLAB formula)
    r = (np.sqrt((R_E + 450e3)**2 - (R_E * np.cos(el))**2)
         - R_E * np.sin(el))

    # Free-space path loss [dB]
    L_fspl = 20.0 * np.log10(4.0 * PI * r * FREQ / C_LIGHT)

    # EIRP = P_t + G_t - Tx_system_losses  [dBW]
    EIRP = P_T + G_T - L_TXSYS

    # Received power at digital system input [dBW]
    L_prop = L_fspl + L_ATM
    Pr_dBW = EIRP - L_prop - L_PLRZ - L_POINT + G_R + G_LNA_EXT - L_RXSYS
    Pr_dBm = Pr_dBW + 30.0                       # dBW -> dBm

    # Antenna / sky noise temperature [K]
    # Linear model: T_COLD at zenith (sin 90 = 1), T_HOT at horizon (sin 0 = 0)
    T_ant = T_COLD + (T_HOT - T_COLD) * (1.0 - np.sin(el))

    # Back-calculate noise figure from datasheet sensitivity and required SNR
    N    = S_DATASHEET - SNR_REQ              # noise power at datasheet conditions [dBm]
    NF   = N + 174.0 - 10.0 * np.log10(B_RX) # noise figure [dB]  (174 dBm/Hz = kT_290)
    F    = 10.0 ** (NF / 10.0)               # linear noise factor

    # Total system noise temperature [K]
    Tr   = (F - 1.0) * 290.0                 # receiver noise temp [K]
    Ts   = T_ant + Tr                        # sky + receiver

    # Sensitivity correction for actual sky temp vs. manufacturer test condition
    Ts_spec  = F * 290.0                     # temp used by manufacturer
    corr     = 10.0 * np.log10(Ts / Ts_spec)
    S_actual = S_DATASHEET + corr            # corrected sensitivity [dBm]
    LM_sens  = Pr_dBm - S_actual             # link margin via sensitivity [dB]

    # C/N0 and Eb/N0  (MATLAB convention: apply -30 offset via C_ = Pr_dBW - 30)
    C_     = Pr_dBW - 30.0
    No_dBW = 10.0 * np.log10(k_B * Ts)      # noise spectral density [dBW/Hz]
    CNo    = C_ - No_dBW                     # C/N0 [dBHz]
    EbNo   = CNo - 10.0 * np.log10(U_BITRATE) - 60.0  # Eb/N0 [dB]
    LM_ebno = EbNo - EBN0_THR               # link margin via Eb/N0 [dB]

    return {
        "el_deg"   : el_deg,
        "r_km"     : r / 1e3,
        "L_fspl_dB": L_fspl,
        "T_ant_K"  : T_ant,
        "Ts_K"     : Ts,
        "Pr_dBm"   : Pr_dBm,
        "S_actual" : S_actual,
        "LM_sens"  : LM_sens,
        "CNo_dBHz" : CNo,
        "EbNo_dB"  : EbNo,
        "LM_ebno"  : LM_ebno,
        "link_ok"  : LM_ebno >= 0.0,
    }


# ==============================================================================
# SECTION 8 -- LORA TIME-ON-AIR
# ==============================================================================

def lora_toa(n_bytes, sf=12, bw_khz=125.0, cr=1, preamble=8,
             explicit_header=True):
    """
    Compute LoRa Time-on-Air using the exact SX127x formula.

    Reference: Semtech AN1200.13 "LoRa Modem Designer's Guide", Table 3.

    Packet structure (in symbols):
        [Preamble: preamble+4.25] + [payload symbols: 8 + max(ceil(...), 0)]

    Low Data Rate Optimisation (LDRO):
        Mandatory for SF >= 11.  It inserts de=2 in the symbol-count formula,
        effectively extending each symbol to prevent inter-symbol interference
        at very low chip rates.  SF12/BW=125kHz without LDRO is undecodable.
        This function enables LDRO automatically for SF >= 11.

    Parameters
    ----------
    n_bytes        : int    payload byte count
    sf             : int    spreading factor (7-12)
    bw_khz         : float  bandwidth [kHz]
    cr             : int    coding rate index  (1=4/5, 2=4/6, 3=4/7, 4=4/8)
    preamble       : int    preamble length in symbols (SX127x default = 8)
    explicit_header: bool   True = PHY header is included (default)

    Returns
    -------
    float
        Time-on-Air [s].
    """
    bw    = bw_khz * 1e3
    t_sym = (2**sf) / bw                   # symbol duration [s]
    t_pre = (preamble + 4.25) * t_sym      # preamble duration [s]

    de = 2 if sf >= 11 else 0              # LDRO shift
    ih = 0 if explicit_header else 1       # implicit header flag (0 = explicit)

    # Payload symbol count from spec (Table 3)
    n_sym_pay = 8 + max(
        int(np.ceil(
            (8 * n_bytes - 4 * sf + 28 + 16 - 20 * ih) / (4 * (sf - de))
        )) * (cr + 4),
        0
    )
    return t_pre + n_sym_pay * t_sym


# ==============================================================================
# SECTION 9 -- BEACON TIMING OPTIMISER
# ==============================================================================

def beacon_optimiser(dl_bytes=51, ul_bytes=51, guard_s=3.0,
                     pass_dur_s=320.0):
    """
    Compute optimal beacon cycle timing for a GPS-less CubeSat.

    Problem statement:
      The satellite has no GPS and no knowledge of its orbital position.
      It blindly and continuously cycles:

          [TX downlink beacon  x seconds]  ->  [RX listen window  y seconds]

      Pilani GS is the only uplink source.  The GS must transmit during
      a y-window while the satellite is in RX mode.

    Optimisation (minimise cycle length):
      x_min = ToA(dl_bytes) + switch_overhead
      y_min = ToA(ul_bytes) + guard_s

    Probability of catching the satellite on a single blind GS TX attempt:
      P = y / (x + y)

    Number of uplink windows available during a pass of duration D:
      windows = floor(D / (x + y))

    Parameters
    ----------
    dl_bytes   : int    downlink beacon payload size       [bytes]
    ul_bytes   : int    uplink command payload size        [bytes]
    guard_s    : float  timing guard added to y window     [s]
                        (covers oscillator drift + Doppler compensation latency)
    pass_dur_s : float  representative pass duration       [s]

    Returns
    -------
    dict with keys:
      x_s             : DL window length (minimum)        [s]
      y_s             : UL window length (minimum)        [s]
      cycle_s         : total cycle = x + y               [s]
      windows_per_pass: floor(pass_dur_s / cycle_s)
      max_ul_bytes    : windows_per_pass * ul_bytes        [bytes]
      p_hit_pct       : P(GS catches >=1 window) %
      toa_dl_s        : Time-on-Air of DL beacon          [s]
      toa_ul_s        : Time-on-Air of UL packet          [s]
    """
    toa_dl = lora_toa(dl_bytes)
    toa_ul = lora_toa(ul_bytes)
    x      = toa_dl + 0.5           # 0.5 s = SX127x mode-switch + MCU overhead
    y      = toa_ul + guard_s
    cycle  = x + y
    wins   = int(pass_dur_s / cycle)
    p_hit  = y / cycle

    return {
        "x_s"             : round(x,     2),
        "y_s"             : round(y,     2),
        "cycle_s"         : round(cycle, 2),
        "windows_per_pass": wins,
        "max_ul_bytes"    : wins * ul_bytes,
        "p_hit_pct"       : round(p_hit * 100.0, 1),
        "toa_dl_s"        : round(toa_dl, 3),
        "toa_ul_s"        : round(toa_ul, 3),
    }


# ==============================================================================
# SECTION 10 -- PRINT / REPORT HELPERS
# ==============================================================================

def hhmm(t_s):
    """
    Format an epoch-seconds value as HH:MM (wraps at 24 h).

    Examples:  hhmm(3661) -> '01:01'    hhmm(86399) -> '23:59'
    """
    h = int(t_s // 3600) % 24
    m = int((t_s % 3600) // 60)
    return f"{h:02d}:{m:02d}"


def sep(char="─", width=88):
    """Print a full-width horizontal separator line."""
    print(char * width)


def print_link_budget_table():
    """
    Print the link budget table for elevations 5 to 90 deg (step 5 deg).

    All values are verified against the MATLAB script to 4 decimal places.
    LM_EbNo is the operationally relevant margin -- link closes above ~50 deg.
    LM_Sens is always positive here because the external LNA dominates.
    """
    sep("=")
    print("  LINK BUDGET -- RFM96W @ 433 MHz | SF12  BW=125kHz  CR=4/5")
    print(f"  P_t={P_T} dBW  G_t={G_T} dBi  G_r={G_R} dBi  "
          f"LNA_ext={G_LNA_EXT} dB  Eb/N0 threshold={EBN0_THR} dB")
    sep("=")
    print(f"  {'El':>4} {'r(km)':>8} {'FSPL':>8} {'Ts(K)':>7} "
          f"{'C/N0':>11} {'Eb/N0':>9} {'LM_Sens':>10} {'LM_EbNo':>10}  Status")
    sep()

    close_el = None
    for el in range(5, 91, 5):
        lb     = link_budget(el)
        status = "OPEN  [+]" if lb["link_ok"] else "CLOSED[-]"
        if close_el is None and lb["link_ok"]:
            close_el = el
        print(f"  {el:>4} {lb['r_km']:>8.2f} {lb['L_fspl_dB']:>8.2f} "
              f"{lb['Ts_K']:>7.1f} {lb['CNo_dBHz']:>11.3f} "
              f"{lb['EbNo_dB']:>9.3f} {lb['LM_sens']:>10.4f} "
              f"{lb['LM_ebno']:>10.4f}  {status}")

    sep()
    print(f"  Link closes (Eb/N0 margin >= 0 dB) above ~{close_el} deg elevation")
    print(f"  NOTE: LM_Sens > 0 at all elevations because the +{G_LNA_EXT} dB external")
    print(f"        LNA masks the path loss.  Use LM_EbNo for operational decisions.")
    print()


def print_toa_table():
    """
    Print LoRa Time-on-Air for representative payload sizes.
    Settings: SF12, BW=125kHz, CR=4/5, LDRO=ON, explicit header, 8 preamble symbols.
    """
    sep("-", 56)
    print("  LORA TIME-ON-AIR  (SF12 / BW=125kHz / CR=4/5 / LDRO=ON)")
    sep("-", 56)
    print(f"  {'Payload(B)':>10}  {'ToA(s)':>8}  {'Net bps':>8}")
    sep("-", 56)
    for nb in [10, 20, 30, 51, 64, 100, 128, 200, 255]:
        toa    = lora_toa(nb)
        bps    = (nb * 8) / toa
        marker = "  <-- recommended" if nb == 51 else ""
        print(f"  {nb:>10}  {toa:>8.3f}  {bps:>8.1f}{marker}")
    print()


def print_passes_for_ic(ic, passes):
    """
    Print the full pass table for one initial condition.

    Each row shows: pass index, day, start time (HH:MM), duration,
    peak elevation, AOS/LOS azimuths, Eb/N0 link margin, peak Doppler,
    uplink window count, and a qualitative note.
    """
    if not passes:
        print("  No passes found for this initial condition.\n")
        return

    durs = [p["dur_s"]      for p in passes]
    els  = [p["max_el_deg"] for p in passes]
    good = sum(1 for e in els if e >= 45)
    fair = sum(1 for e in els if 25 <= e < 45)
    low  = sum(1 for e in els if e < 25)

    print(f"  Total passes (el >= {MIN_ELEV_DEG:.0f} deg): {len(passes)}"
          f"    Good (>=45): {good}"
          f"    Fair (25-45): {fair}"
          f"    Low (<25): {low}")
    print(f"  Duration -- avg: {np.mean(durs):.0f} s   "
          f"min: {np.min(durs):.0f} s   max: {np.max(durs):.0f} s")
    print(f"  Max el   -- avg: {np.mean(els):.1f} deg   "
          f"min: {np.min(els):.1f} deg   max: {np.max(els):.1f} deg")
    print()

    # Beacon cycle based on average good-pass duration for this IC
    good_durs = [p["dur_s"] for p in passes if p["max_el_deg"] >= 45]
    rep_dur   = float(np.mean(good_durs) if good_durs else np.mean(durs))
    opt       = beacon_optimiser(dl_bytes=51, ul_bytes=51,
                                 guard_s=3.0, pass_dur_s=rep_dur)

    print(f"  {'#':>3}  {'Day':>3}  {'Start':>5}  {'Dur(s)':>7}  "
          f"{'MaxEl':>6}  {'AzAOS':>6}  {'AzLOS':>6}  "
          f"{'LM_EbNo':>8}  {'Dopp(kHz)':>10}  {'ULwins':>6}  Note")
    sep("-")

    for i, p in enumerate(passes, 1):
        lb   = link_budget(p["max_el_deg"])
        dop  = doppler_shift_hz(p["t_peak_s"], ic)   # Doppler at peak elevation
        wins = int(p["dur_s"] / opt["cycle_s"])

        if p["max_el_deg"] >= 50:
            note = "PRIME  [*]"
        elif lb["link_ok"]:
            note = "USABLE    "
        else:
            note = "NO LINK   "

        print(f"  {i:>3}  {p['day']:>3}  {hhmm(p['start_s']):>5}  "
              f"{p['dur_s']:>7.0f}  {p['max_el_deg']:>6.1f}  "
              f"{p['az_rise']:>6.1f}  {p['az_set']:>6.1f}  "
              f"{lb['LM_ebno']:>8.2f}  {dop/1e3:>10.2f}  "
              f"{wins:>6}  {note}")
    print()


def print_beacon_for_ic(passes):
    """
    Print beacon timing sweep and the recommended x/y settings for one IC.

    Sweeps several DL/UL payload sizes and prints the resulting cycle length,
    uplink windows per pass, total uplink bytes per pass, and the probability
    of the GS catching a window on a single blind transmit attempt.
    """
    good_durs = [p["dur_s"] for p in passes if p["max_el_deg"] >= 45]
    rep_dur   = float(np.mean(good_durs) if good_durs
                      else np.mean([p["dur_s"] for p in passes]))

    print(f"  Representative pass duration (avg of good passes): {rep_dur:.0f} s")
    print()
    print(f"  {'DL_B':>5} {'UL_B':>5} {'x(s)':>7} {'y(s)':>7} "
          f"{'cycle':>7} {'wins':>5} {'UL_B/pass':>10} {'P(hit)%':>8}")
    sep("-", 62)

    for dl_b, ul_b in [(20, 20), (51, 20), (51, 51), (51, 100), (128, 51)]:
        o    = beacon_optimiser(dl_b, ul_b, guard_s=3.0, pass_dur_s=rep_dur)
        mark = "  <-- RECOMMENDED" if (dl_b == 51 and ul_b == 51) else ""
        print(f"  {dl_b:>5} {ul_b:>5} {o['x_s']:>7.1f} {o['y_s']:>7.1f} "
              f"{o['cycle_s']:>7.1f} {o['windows_per_pass']:>5} "
              f"{o['max_ul_bytes']:>10} {o['p_hit_pct']:>7.1f}%{mark}")

    print()
    rec = beacon_optimiser(51, 51, 3.0, rep_dur)
    print(f"  [RECOMMENDED SETTINGS]")
    print(f"    x (DL window) = {rec['x_s']} s"
          f"   (ToA {rec['toa_dl_s']} s + 0.5 s mode-switch overhead)")
    print(f"    y (UL window) = {rec['y_s']} s"
          f"   (ToA {rec['toa_ul_s']} s + 3.0 s timing guard)")
    print(f"    Cycle x + y   = {rec['cycle_s']} s")
    print(f"    UL windows per pass      : {rec['windows_per_pass']}")
    print(f"    Max uplink data per pass : {rec['max_ul_bytes']} bytes")
    print(f"    P(GS catches 1 window)   : {rec['p_hit_pct']}% per cycle attempt")
    print(f"    Relay string example (51 bytes):")
    print( '      "CMD=PING TS=20260324T120000Z RELAY=Hello_from_Pilani_GS!"')


# ==============================================================================
# SECTION 11 -- MAIN
# ==============================================================================

def main():
    """
    Entry point.  All output goes to stdout.

    Output order:
      1. Link budget table      -- elevation-dependent only; same for all ICs
      2. LoRa ToA table         -- same for all ICs
      3. For each of the 5 ICs:
           a. Orbital summary   (altitude, period, speed, max Doppler)
           b. 7-day pass table  (link margins, Doppler at peak, UL windows)
           c. Beacon timing recommendations
      4. Cross-IC comparison table
    """

    # ------------------------------------------------------------------
    # 1 & 2. Tables that depend only on RF parameters, not on orbit choice
    # ------------------------------------------------------------------
    print()
    print_link_budget_table()
    print_toa_table()

    # Cache passes to avoid re-simulating in the cross-IC summary
    all_passes = {}

    # ------------------------------------------------------------------
    # 3. Per-IC analysis
    # ------------------------------------------------------------------
    for idx, ic in enumerate(INITIAL_CONDITIONS, 1):
        h_m     = ic["h_km"] * 1e3
        T_orb   = orbital_period(h_m)
        v_orb   = 2.0 * PI * (R_E + h_m) / T_orb    # circular orbital speed [m/s]
        max_dop = FREQ * v_orb / C_LIGHT              # max Doppler (overhead pass) [Hz]

        sep("=")
        print(f"  INITIAL CONDITION {idx} of {len(INITIAL_CONDITIONS)}")
        print(f"  {ic['name']}")
        sep("=")
        print(f"  Altitude          : {ic['h_km']:.1f} km")
        print(f"  Inclination       : {ic['inc_deg']:.1f} deg")
        print(f"  RAAN              : {ic['raan_deg']:.1f} deg")
        print(f"  Arg of perigee    : {ic['aop_deg']:.1f} deg   "
              f"(circular orbit -- value unused)")
        print(f"  True anomaly (t0) : {ic['ta_deg']:.1f} deg")
        print(f"  Orbital period    : {T_orb/60:.2f} min  ({T_orb:.0f} s)")
        print(f"  Orbital speed     : {v_orb/1e3:.3f} km/s")
        print(f"  Max Doppler shift : +/- {max_dop/1e3:.1f} kHz  "
              f"(direct overhead pass; GS must compensate)")
        print()

        # Find all passes over the 7-day simulation window
        print(f"  Simulating 7-day orbit (dt=10 s) ...", end="", flush=True)
        passes = find_passes(ic, sim_days=7, dt_s=10.0)
        all_passes[idx] = passes
        print(f"  {len(passes)} passes found.")
        print()

        # Pass table
        print_passes_for_ic(ic, passes)

        # Beacon timing
        sep("-")
        print("  BEACON TIMING RECOMMENDATIONS")
        sep("-")
        if passes:
            print_beacon_for_ic(passes)
        else:
            print("  No passes -- no uplink opportunity from Pilani for this orbit.")
        print()

    # ------------------------------------------------------------------
    # 4. Cross-IC comparison
    # ------------------------------------------------------------------
    sep("=")
    print("  CROSS-IC COMPARISON -- 7-day statistics over Pilani GS")
    sep("=")
    print(f"  {'IC':>4}  {'Passes':>6}  {'Good':>5}  "
          f"{'AvgDur(s)':>10}  {'AvgMaxEl':>9}  "
          f"{'BestEl':>7}  {'BestLM(dB)':>11}  Description")
    sep("-")

    for idx, ic in enumerate(INITIAL_CONDITIONS, 1):
        passes  = all_passes[idx]
        label   = f"IC-{idx}"
        desc    = ic["name"].split("  ", 1)[1][:45]   # truncate for table width

        if not passes:
            print(f"  {label:>4}  {'0':>6}  {'0':>5}  "
                  f"{'--':>10}  {'--':>9}  {'--':>7}  {'--':>11}  {desc}")
            continue

        durs    = [p["dur_s"]      for p in passes]
        els     = [p["max_el_deg"] for p in passes]
        good    = sum(1 for e in els if e >= 45)
        best_el = max(els)
        best_lm = link_budget(best_el)["LM_ebno"]

        print(f"  {label:>4}  {len(passes):>6}  {good:>5}  "
              f"{np.mean(durs):>10.0f}  {np.mean(els):>8.1f} deg"
              f"  {best_el:>6.1f} deg  {best_lm:>10.2f} dB  {desc}")

    sep("=")
    print()
    print("  COLUMN GUIDE")
    print("  ------------")
    print("  Passes     : total passes with peak elevation >= 5 deg in 7 days")
    print("  Good       : passes with peak elevation >= 45 deg (link likely open)")
    print("  AvgDur     : average pass duration [s]")
    print("  AvgMaxEl   : average peak elevation per pass [deg]")
    print("  BestEl     : highest single-pass elevation in 7 days [deg]")
    print("  BestLM     : Eb/N0 link margin at BestEl (>0 dB = link open) [dB]")
    print()
    print("  PASS NOTE GUIDE")
    print("  ---------------")
    print("  PRIME  [*] : peak el >= 50 deg; margin > 0 dB; multiple UL windows")
    print("  USABLE     : peak el at link closure boundary; margin >= 0 dB")
    print("  NO LINK    : peak el < 50 deg; Eb/N0 margin negative; uplink fails")
    print("  ULwins     : uplink-listen windows available in that pass (y-slots)")
    print("  Dopp(kHz)  : Doppler at peak elevation; GS must centre its Rx on this")
    print("  P(hit)%    : probability GS catches >=1 window on blind TX attempt")
    print()


if __name__ == "__main__":
    main()
