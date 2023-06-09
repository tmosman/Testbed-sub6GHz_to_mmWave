import numpy as np
import scipy.signal as scs

# 802.11 Stuff, like LTS values and pilot positions
lts = np.loadtxt('lts.txt').view(complex)
lts = np.real(np.fft.fft(lts,64))
pilot_sub_carriers = [-21,-7,7,21]

# Import data
x_p = np.fromfile('generated_ofdm_packet.dat',dtype=np.complex64)
pkt_len = x_p.shape[0]

# Globals
fs = int(20e6)
Ts = 1/fs
K = 64
Kon = 52
cp_len = 16
num_dat_sym = 127

# Generate Zadoff Chu Sequence
zc_len = 63
idx=np.arange(zc_len)
M_root=29
x_t=np.exp(-1j*np.pi*M_root/63*idx*(idx+1))

# Useful Function
def extract_used_carriers(S):
    return np.fft.fftshift(S)[6:-5]

def insert_subcarriers(S):
    S2 = np.zeros((64,),dtype=np.complex64)
    S2[6:-5] = S
    return np.fft.fftshift(S2)

def get_pilots(S):
    if (len(S) == 64):
        return S[pilot_sub_carriers]
    else:
        return insert_subcarriers(S)[pilot_sub_carriers]
    
def pilot_symbols(n):
    return np.roll(np.array([1,1,1,-1]),-n)

def get_packets(y):
    # Generate Zadoff Chu Sequence
    zc_len = 63
    idx=np.arange(zc_len)
    M_root=29
    x_t=np.exp(-1j*np.pi*M_root/63*idx*(idx+1))

    # Correlate with received signal
    corr = np.correlate(y,x_t)
    locs,temp = scs.find_peaks(np.abs(corr),distance = pkt_len,prominence = np.max(np.abs(corr)/4))

    if len(locs) <= 1:
        if locs <= y.shape[0]/2:
            y = y[int(locs+pkt_len):]
        else:
            y = y[:int(locs-pkt_len)]

        corr = np.correlate(y,x_t)
        locs,temp = scs.find_peaks(np.abs(corr),distance = pkt_len,prominence = np.max(np.abs(corr)/4))

    if len(locs) <= 20:
        y[np.abs(y) > 0.4] = 0

        corr = np.correlate(y,x_t)
        locs,temp = scs.find_peaks(np.abs(corr),distance = pkt_len,prominence = np.max(np.abs(corr)/4))

    # Break Up by the correlated peaks
    y_rx = []

    for i in range(10,len(locs) - 10):
        y_rx.append(y[locs[i]:locs[i] + pkt_len])
    
    return y_rx

# Construct transmited data symbols
x_d = np.sign(lts)
x_d[0] = 0
x_d[pilot_sub_carriers] = 0
x_dat = extract_used_carriers(x_d)

def process_channel(y_rx):
    # Coarse frequency correction
    cf_len = 10*cp_len
    N_sample = 16
    y_cf = y_rx[zc_len + cp_len:zc_len + cf_len]
    yc1 = y_cf[:-cp_len]
    yc2 = y_cf[cp_len:]

    cf_off = 1/(N_sample)*np.angle(np.sum(np.conj(yc1)*yc2))
#         print('Coarse Offset: ' + str(cf_off/(2*np.pi*Ts)) + ' Hz')

    xcr = x_p[zc_len + cf_len:]
    ycr = y_rx[zc_len + cf_len:]
    m = np.arange(0,len(ycr))
    ycr = ycr * np.exp(-1j * m * cf_off)

    # Initial Channel Estimation Using LTS
    lts_sign = np.sign(extract_used_carriers(lts))
    lts_sign[26] = 0
    ff_len = 2*K + 2*cp_len
    N_sample = K
    y_ff = ycr[2*cp_len:ff_len]
    y_ff2 = y_ff.reshape(2,K)
    Y1 = np.fft.fft(y_ff2[0])
    Y1 = extract_used_carriers(Y1)
    Y2 = np.fft.fft(y_ff2[1])
    Y2 = extract_used_carriers(Y2)
    H_e = (Y1 + Y2)/2 * lts_sign
    H_e[26] = (H_e[25] + H_e[24])/2
#     plt.plot(np.abs(H))


    y_ff2[0] = np.fft.ifft(insert_subcarriers(Y1/H_e))
    y_ff2[1] = np.fft.ifft(insert_subcarriers(Y2/H_e))

    # Fine Frequency Recovery
    ff_off = 1/(N_sample) * np.angle(np.sum(np.conj(y_ff2[0]) * y_ff2[1]))
#         print('Fine Offset: ' + str(ff_off/(2*np.pi*Ts)) + ' Hz')

    d_len = K + cp_len
    m = np.arange(0,len(ycr))
    ycr = ycr * np.exp(-1j * m * ff_off)
    x_dt = xcr[ff_len:]
    y_dt = ycr[ff_len:]
    x_dt = x_dt[:int(y_dt.shape[0]/d_len)*d_len].reshape(-1,d_len)
    y_dt = y_dt[:int(y_dt.shape[0]/d_len)*d_len].reshape(-1,d_len)

    # Data Phase Recovery with Pilots
    H_av = np.zeros((y_dt.shape[0],Kon+1),dtype=np.complex)
    Yd_re = np.zeros((y_dt.shape[0],Kon+1))
    BER = np.zeros(y_dt.shape[0])

    for j in np.arange(y_dt.shape[0]):
        y_d = y_dt[j,:]
        x_d = x_dt[j,:]
        y_d = y_d[cp_len:]
        x_d = x_d[cp_len:]
        Yd = extract_used_carriers(np.fft.fft(y_d))/H_e
        Yplt = get_pilots(Yd)
        Hplt = get_pilots(H_e)
        phase = np.angle(np.sum(np.conj(Yplt) * pilot_symbols(j) * np.abs(Hplt)))

        # Place Phase between -pi and pi
        if phase < -np.pi:
            phase = phase + 2*np.pi
        elif phase > np.pi:
            phase = phase - 2*np.pi

#             print("Residual Phase Offset: " + str(phase))
        Yd = Yd * np.exp(1j * phase)
        Yd = insert_subcarriers(Yd)
        Yd = np.sign(Yd.real)
        Yd[0] = 0
        Yd[pilot_sub_carriers] = 0
        Yd = extract_used_carriers(Yd)
        H_av[j] = H_e * np.exp(-1j * phase)
        Yd_re[j] = Yd
        BER[j] = np.sum((Yd != x_dat))
    
    return (np.average(np.abs(H_av),axis=0),BER)

def get_channel(y_rx):
    # Variables
    # 802.11 Stuff, like LTS values and pilot positions
    lts = np.loadtxt('lts.txt').view(complex)
    lts = np.real(np.fft.fft(lts,64))

    # Globals
    cp_len = 16

    # Coarse frequency correction
    cf_len = 10*cp_len
    N_sample = 16
    y_cf = y_rx[zc_len + cp_len:zc_len + cf_len]
    yc1 = y_cf[:-cp_len]
    yc2 = y_cf[cp_len:]

    cf_off = 1/(N_sample)*np.angle(np.sum(np.conj(yc1)*yc2))
#         print('Coarse Offset: ' + str(cf_off/(2*np.pi*Ts)) + ' Hz')

    ycr = y_rx[zc_len + cf_len:]
    m = np.arange(0,len(ycr))
    ycr = ycr * np.exp(-1j * m * cf_off)

    # Initial Channel Estimation Using LTS
    lts_sign = np.sign(extract_used_carriers(lts))
    lts_sign[26] = 0
    ff_len = 2*K + 2*cp_len
    N_sample = K
    y_ff = ycr[2*cp_len:ff_len]
    y_ff2 = y_ff.reshape(2,K)

    # Fine Frequency Recovery
    ff_off = 1/(N_sample) * np.angle(np.sum(np.conj(y_ff2[0]) * y_ff2[1]))
#         print('Fine Offset: ' + str(ff_off/(2*np.pi*Ts)) + ' Hz')

    m = np.arange(0,len(ycr))
    ycr = ycr * np.exp(-1j * m * ff_off)

    # Actual Channel Estimation Using LTS
    y_ff = ycr[2*cp_len:ff_len]
    y_ff2 = y_ff.reshape(2,K)
    Y1 = np.fft.fft(y_ff2[0])
    Y1 = extract_used_carriers(Y1)
    Y2 = np.fft.fft(y_ff2[1])
    Y2 = extract_used_carriers(Y2)
    H_e = (Y1 + Y2)/2 * lts_sign
    H_e[26] = (H_e[25] + H_e[24])/2

    return H_e