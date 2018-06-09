# -*- coding: utf-8 -*-
"""
Created on Tue May 22 09:34:07 2018

@author: Peter
"""
import numpy as np

def region_blocked(data_wave, data_flux, temp_wave, temp_flux):
    
    ###############################################################################################
    #                                                                                             #
    #   this sets limits based on start and end points and it also finds the overlap value lap.   #
    #   The function rebins this into a new array and also cuts out any zeros at either end       #
    #                                                                                             #
    ###############################################################################################
    
    ##############################setting limits and initialising arrays########################### 
    
    N = int(len(data_wave))
    Nt = int(len(temp_wave))
    
    data_wave_reg = np.zeros(N) 
    temp_wave_reg = np.zeros(Nt)
    data_flux_reg = np.zeros(N)
    temp_flux_reg = np.zeros(Nt)
    index_m = np.zeros(Nt)
    index_n = np.zeros(N)
    
    ##############################assign the start and end points##################################
    
    if temp_wave[0] >= data_wave[0]:
        start = temp_wave[0]
    else:
        start = data_wave[0]
    if temp_wave[-1] >= data_wave[-1]:
        end = data_wave[-1]
    else:
        end = temp_wave[-1]
        
    ####################################find lap###################################################
    
    start_n = np.exp(start)
    end_n = np.exp(end)
    lap=abs(np.log(end_n/start_n))
    
    ######################################rebinning################################################
    
    for i in range(0,N):
        if data_wave[i] >= start:
            data_wave_reg[i] = data_wave[i]
            data_flux_reg[i] = data_flux[i]
            
    for j in range(0,Nt):
        if np.any(temp_wave[j] >=start) and np.any(temp_wave[j] <= end):
            temp_wave_reg[j] = temp_wave[j]
            temp_flux_reg[j] = temp_flux[j]
    
    for k in range(0,Nt):
        if temp_wave_reg[k] != 0 :
            temp_flux_reg[k] = temp_flux[k]
    
    for l in range(0,N):
        if data_wave_reg[l] != 0:
            data_flux_reg[l] = data_flux[l]

    #########################deleting zeros at the ends of the new arrays##########################

    for n in range(0,N):
        if data_wave_reg[n] == 0:
            index_n[n]=n        
    
    for m in range(0,Nt):
        if temp_wave_reg[m] == 0:
            index_m[m]=m   

    data_flux_reg = np.delete(data_flux_reg, index_n)
    data_wave_reg = np.delete(data_wave_reg, index_n)
    temp_flux_reg = np.delete(temp_flux_reg, index_m)
    temp_wave_reg = np.delete(temp_wave_reg, index_m)

    return data_wave_reg, data_flux_reg, temp_wave_reg, temp_flux_reg, lap

def interp_spec(wave_data, flux_data):
    
    ###################################################################
    #   interpolates any 2 arrays into a new array of length 1024*7   #
    #           because that was found to maximise r                  #
    ###################################################################
    
    from scipy import interpolate
    f = interpolate.interp1d(wave_data, flux_data)
    n = wave_data[0]
    m = wave_data[-1]
    x = np.linspace(n, m, 1024*7)
    f_d = f(x)
    
    return f_d

def get_r_value(wave_data, flux_data, temp_wave, temp_flux, h):
    
    #####################################################################################
    #                                                                                   #
    #             a function that takes the spectrum. determines the peak               #
    #           and the rms antisymetrical function of the correlation curve            #
    #                  uses these to find r the correlation coefficient                 #
    #                                                                                   #    
    #####################################################################################
    
    from cross_corr import interp_spec
    
    f_d = interp_spec(wave_data, flux_data)
    f_t = interp_spec(temp_wave, temp_flux)
    
    autocorr1 = np.correlate(f_t , f_t , "full")
    rmsTemp = np.std(autocorr1)
    autocorr1 = (1/len(autocorr1)*rmsTemp*rmsTemp)*autocorr1

    Corr1 = np.correlate(f_d, f_t, "full")
    rmsInput = np.std(Corr1)
    Corr1 = (1. / len(Corr1) * rmsInput * rmsTemp) * Corr1
    
    arandom = Corr1- autocorr1
    rmsa = np.std(arandom)

    if rmsa == 0:
        import math
        r = math.inf
    else:
        r = abs((h)/(np.sqrt(2)*rmsa))
    
    return r


def get_correlate(data_wave, filteredflux_data, temp_wave, filteredflux_temp):
    
    #############################################################
    #                                                           #
    #   finds the correlation beteern two spectra, fins their   # 
    #   correlation coefficients, calls get_r_value to do so    #
    #   calls region_blocked aswell to find lap                 #
    #                                                           #
    #############################################################
    
    import scipy.fftpack as fft
    
    '''
    SORT OUT THE R COEFFICIENT, STILL TOO LOW. LOOK INTO THE NORMALISATION
    '''
   
    wave_data, flux_data, temp_wave, temp_flux, lap = region_blocked(data_wave, filteredflux_data, temp_wave, filteredflux_temp)
    try:
        dft_data = fft.fft(flux_data)
        dft_temp = fft.fft(temp_flux)
        
        rmsInput = np.std(dft_data)
        rmsTemp = np.std(dft_temp)
        
        Corr = np.correlate(flux_data, temp_flux, "full")
        Corr = (1. / len(Corr) * rmsInput * rmsTemp) * Corr
        h = max(Corr)
        r = get_r_value(wave_data, flux_data, temp_wave, temp_flux, h)
        rlap=r*lap

    except ValueError:
        r = 0
        rlap = 0
        
    return lap

def correlate(data_wave, filteredflux_data, temp_wave, filteredflux_temp):
    
    ################################################################################################    
    #                                                                                              #
    #   This function loops through many redshifts, calls rbl from redshift.py and get_correlate   #
    #                                                                                              #
    ################################################################################################

    from redshift import red_boi_loop as rbl
    
    r_list = []
      
    for i in range(0,300):
        wave_shift = rbl(temp_wave,i)
        r = get_correlate(data_wave, filteredflux_data, wave_shift, filteredflux_temp)
        r_list = np.append(r_list, r)

    return r_list