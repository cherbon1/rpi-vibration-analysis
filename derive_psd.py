import numpy as np
from scipy import signal

def integrate_peaks(frequency, spectrum, analysis_windows):
    # integrate intensities
    idx_ranges = np.hsplit(np.searchsorted(frequency, [d for a in analysis_windows.values() for d in a]),
                           len(analysis_windows))
    idx_ranges = [slice(*idx_r) for idx_r in idx_ranges]
    integrated_peaks = {k:np.sqrt(np.mean(spectrum[idx_r] ** 2) * (v[1] - v[0]))
                                for idx_r, (k, v) in zip(idx_ranges, analysis_windows.items())}
    return integrated_peaks

def derive_psd(data, sampling_rate, method='welch',
               subdivision_factor=1, nfft_factor=None, pad_zeros_pow2=False, return_onesided=True, detrend=None):
    """Derive the power spectral density from a time trace.

    There are two methods available for deriving the PSD: standard FFT
    and the Welch method that offers windowing to avoid spectral
    leakage.

    Note
    ----
    The Welch method uses the function `scipy.signal.welch and does
    not include the DC component of the signal.

    Parameters
    ----------
    data : numpy.ndarray
        1D array of equally spaced time trace data.
    sampling_rate : float
        sampling rate of the equally spaced time trace data
    method : {'fft', 'welch'}, optional
        Method used for derivation of power spectral density. Either
        'fft' for using standard FFT, or 'welch' for Welch's
        windowing method.
    subdivision_factor : int, optional
        The subdivision factor used for deriving the size of the
        window for the 'welch' method. For the 'fft' method, the time
        trace will be devided into this number of segments.
    nfft_factor : float, optional
        Factor of how much longer the spectrum vector should be
        compared to the data vector. For values >1 the data vector
        is zero-padded. Defaults to None (no change in vector length).
    detrend : optional
        When using the 'welch' method, this argument is used there.

    Returns
    -------
    numpy.ndarray
        power spectral density for the time trace data
    numpy.ndarray
        frequency array of the PSD

    To see the effect of the method, try subdivision factor of 10
    and 16 for both methods ('fft' and 'welch'). For 'fft' you will
    see spectral leakage with a subdivision factor of 16, not so for
    'welch'. Thus 'welch' is usually the better option. But note
    that 'welch' does not include the DC component of the signal!
    """

    if pad_zeros_pow2 and subdivision_factor == 1:
        defifict = int(2 ** np.ceil(np.log2(len(data))) - len(data))
        data = np.pad(data, (defifict, 0), mode='constant')
    if method.lower() in 'fft':
        # subdivide time trace
        part_length = len(data)//subdivision_factor
        data = [data[i*part_length:(i+1)*part_length]
                for i in range(subdivision_factor)]
        psd = []

        # Derive Frequency Step
        if nfft_factor is not None:
            n = int(part_length*nfft_factor)
        else:
            n = part_length
        frequency_step = sampling_rate/n

        for i in range(subdivision_factor):
            if nfft_factor is not None:
                fft_data = np.fft.fftshift(np.abs(
                    np.fft.fft(data[i], n=n))/n)
            else:
                fft_data = np.fft.fftshift(np.abs(
                    np.fft.fft(data[i]))/len(data[i]))

            if return_onesided:
                # Drop negative Frequencies and correct at f=0, multiply by sqrt(2) since Sx = 2Sxx
                fft_data = np.sqrt(2)*fft_data[len(fft_data)//2:]
                fft_data[0] /= np.sqrt(2)


            # Derive Power Spectral Density
            psd.append((fft_data)**2 / frequency_step)

        psd = np.average(psd, axis=0)

        if return_onesided:
            frequency = np.linspace(0, frequency_step*(len(psd)-1),
                                   len(psd))
        else:
            frequency = np.linspace(- frequency_step*(len(psd)-1)/2, frequency_step*(len(psd)-1)/2, len(psd))


    elif method.lower() in 'welch':
        # Derive size of segments
        segment_size = int(len(data)/subdivision_factor)

        # Derive single-sided PSD using Welch's method
        if nfft_factor is not None:
            frequency, psd = signal.welch(
                data, sampling_rate,
                nperseg=segment_size, return_onesided=return_onesided,
                nfft=int(len(data)*nfft_factor))
        else:
            frequency, psd = signal.welch(
                data, sampling_rate,
                nperseg=segment_size, return_onesided=return_onesided, detrend = detrend)

        if not return_onesided:
            frequency = np.fft.fftshift(frequency)
            psd = np.fft.fftshift(psd)

    elif method.lower() in 'rfft':
        # Derive size of segments
        sample_size = len(data) // subdivision_factor
        if sample_size == 0:
            sample_size = 1
            subdivision_factor = len(data)
            print('Subdivision factor bigger than sample size. Reducing subdivision factor to maximal value.')

        # Make Sample Size compatible with division factor
        data = data[:sample_size * subdivision_factor]

        data_split = np.array(np.hsplit(data, subdivision_factor))

        if nfft_factor is not None:
            n = int(sample_size * nfft_factor)
        else:
            n = sample_size


        if pad_zeros_pow2 and subdivision_factor != 1:
            if nfft_factor is not None:
                n = int(2 ** np.ceil(np.log2(len(data_split[0]) * nfft_factor )))
            else:
                n = int(2 ** np.ceil(np.log2(len(data_split[0]))))
            psd = np.mean(abs(np.fft.rfft(data_split, n=n, axis=1)) ** 2, axis=0)
        else:
            psd = np.mean(abs(np.fft.rfft(data_split, n=n, axis=1)) ** 2, axis=0)
        psd *= 2 / (sampling_rate * n)
        psd[0] /= 2

        frequency = np.fft.rfftfreq(n, 1 / sampling_rate)

    else:
        raise ValueError('invalid method')

    return frequency, psd