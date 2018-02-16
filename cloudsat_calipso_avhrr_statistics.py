#Program cloudsat_calipso_avhrr_statistics.py
import config
import logging
logger = logging.getLogger(__name__)
import numpy as np
from get_flag_info import (
    get_calipso_low_medium_high_classification,
    get_cloudsat_low_medium_high_classification,
    get_semi_opaque_info_pps2014, 
    get_semi_opaque_info_pps2012,
    get_sunglint_info_pps2014,
    get_high_terrain_info_pps2014,
    get_mountin_info_pps2014,
    get_inversion_info_pps2014,
    get_land_coast_sea_info_pps2014,
    get_land_coast_sea_info_pps2012,
    get_land_coast_sea_info_cci2014,
    get_ice_info_pps2014,
    get_ice_info_pps2012,
    get_day_night_twilight_info_pps2014,
    get_day_night_twilight_info_pps2012,
    get_day_night_twilight_info_cci2014,
    get_day_night_twilight_info_maia,
    get_sunglint_info_pps2012,
    get_mountin_info_pps2012,
    get_inversion_info_pps2012)

def calculate_ctth_stats(val_subset, imager_ctth_m_above_seasurface, truth_sat_validation_height, imager_is_cloudy):

    imager_have_hight_for_selection = np.logical_and(
        val_subset,
        np.greater_equal(imager_ctth_m_above_seasurface,0))
    truth_have_hight_for_selection = np.logical_and(
        val_subset,
        np.greater_equal(truth_sat_validation_height,0)) 
    #validate where both have height:
    val_subset = np.logical_and(imager_have_hight_for_selection,
                                truth_have_hight_for_selection)
    #print "debug", np.sum(val_subset)
    #note how many true clouds (iss/cloudsat/caliop) had no hight for imager:
    only_truth_had_height = np.logical_and(~imager_have_hight_for_selection,
                                           truth_have_hight_for_selection)
    #print "debug", np.sum(only_truth_had_height)
    n_only_truth_had_height = np.sum(only_truth_had_height)
    n_only_truth_had_height_both_had_cloud = np.sum(np.logical_and(only_truth_had_height,
                                                                   imager_is_cloudy))
    #print "debug", np.sum(n_only_truth_had_height_both_had_cloud)
    avhrr_height_work = np.repeat(imager_ctth_m_above_seasurface[::],val_subset)
    truth_sat_validation_height_work = np.repeat(truth_sat_validation_height[::],val_subset)

    corr_caliop_avhrr = -9.0
    bias = -9.0
    RMS_difference = -9.0
    #        RMS_difference_biascorr = -9.0
    diff_squared_biascorr = np.array([-9.0])
    MAE = -9
    if len(truth_sat_validation_height_work) > 0:
        if len(avhrr_height_work) > 20:
            corr_caliop_avhrr = np.corrcoef(truth_sat_validation_height_work,
                                            avhrr_height_work)[0,1]
        else:
            corr_caliop_avhrr = -99.0
        diff = avhrr_height_work-truth_sat_validation_height_work
        bias = np.mean(diff)
        MAE = np.mean(np.abs(diff))
        diff_squared = diff*diff
        RMS_difference = np.sqrt(np.mean(diff_squared))
        diff_squared_biascorr = (diff-bias)*(diff-bias)
#        RMS_difference_biascorr = np.sqrt(np.mean(diff_squared_biascorr))

    #return (corr_caliop_avhrr,bias,RMS_difference,avhrr_height_work,diff_squared_biascorr)
    return "%3.2f %3.2f %3.2f %d %d %d %3.2f"%(corr_caliop_avhrr,
                                               bias,
                                               RMS_difference,
                                               len(avhrr_height_work), 
                                               n_only_truth_had_height,
                                               n_only_truth_had_height_both_had_cloud,
                                               MAE)

def get_subset_for_mode(cObj, mode):
    cObj_truth_sat = getattr(cObj, cObj.truth_sat)
    latitude_abs = np.abs(getattr(cObj_truth_sat, 'latitude'))
    if cObj.truth_sat.lower() in ['calipso']: 
        nsidc_st = getattr(cObj_truth_sat, 'nsidc_surface_type')
        igbp_st = getattr(cObj_truth_sat, 'igbp_surface_type')
    else :
        nsidc_st = None
        igbp_st = None
 
    # First prepare possible subsetting of CALIOP/CLOUDSAT/ISS without NSIDC
    # and IGBP surface types  
    if mode == 'BASIC':
        cal_subset = np.bool_(np.ones(latitude_abs.shape))
    elif mode == 'OPTICAL_DEPTH':
        cal_subset = np.bool_(np.ones(latitude_abs.shape))
    elif mode == 'STANDARD':
        cal_subset = np.bool_(np.ones(latitude_abs.shape))
    elif mode == 'OPTICAL_DEPTH_THIN_IS_CLEAR':
        cal_subset = np.bool_(np.ones(latitude_abs.shape))
    elif mode == 'TROPIC_ZONE':
        cal_subset = latitude_abs <= 10    
    elif mode == 'SUB_TROPIC_ZONE':
        cal_subset = np.logical_and((latitude_abs > 10), 
                                    (latitude_abs <= 45))     
    elif mode == 'HIGH-LATITUDES':
        cal_subset = np.logical_and((latitude_abs > 45), 
                                    (latitude_abs <= 75))
    elif mode == 'POLAR':
        cal_subset = latitude_abs > 75
    elif nsidc_st is None and igbp_st is None:
        cal_subset = np.bool_(np.zeros(latitude_abs.shape))
        logger.warning("Will not run igbp/nsidc dependent mode: %s for %s", 
                       mode, cObj.truth_sat)
        return None
    # Then prepare possible subsetting of CALIOP datasets according to NSIDC
    # and IGBP surface types  if we have them
    elif mode == 'ICE_COVER_SEA':
        cal_subset = np.logical_and(
            np.logical_and(np.less_equal(nsidc_st,100), np.greater(nsidc_st,10)),
            np.equal(igbp_st,17))
    elif mode == 'ICE_FREE_SEA':
        cal_subset = np.logical_and(np.equal(nsidc_st,0),np.equal(igbp_st,17))
    elif mode == 'SNOW_COVER_LAND':
        cal_subset = np.logical_and(
            np.logical_and(np.less(nsidc_st,104), np.greater(nsidc_st,10)),
            np.not_equal(igbp_st,17))
        #: Notice that some uncertainty remains about the meaning of IGBP 
        #: category 15 = "snow and ice". Can this possibly include also 
        #: the Arctic ice sheet? We hope that it is not! 
        #: However, if it is, the whole classification here might be wrong 
        #: since this will affect also the definition of IGBP category 17./KG 
    elif mode == 'SNOW_FREE_LAND':
        cal_subset = np.logical_and(np.equal(nsidc_st,0),
                                    np.not_equal(igbp_st,17))
    elif mode == 'COASTAL_ZONE':
        cal_subset = np.equal(nsidc_st,255)    
    elif mode == 'TROPIC_ZONE_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and(np.equal(nsidc_st,0),
                                        np.not_equal(igbp_st,17))
        cal_subset_area = latitude_abs <= 10
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'TROPIC_ZONE_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and(np.equal(nsidc_st,0),
                                        np.equal(igbp_st,17))
        cal_subset_area = latitude_abs <= 10
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)   
    elif mode == 'SUB_TROPIC_ZONE_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and((latitude_abs > 10), 
                                        (latitude_abs <= 45))
        cal_subset_area = np.logical_and(np.equal(nsidc_st,0),
                                         np.not_equal(igbp_st,17))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'SUB_TROPIC_ZONE_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and((latitude_abs > 10), 
                                        (latitude_abs <= 45))
        cal_subset_area = np.logical_and(np.equal(nsidc_st,0),
                                         np.equal(igbp_st,17))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)

    elif mode == 'HIGH-LATITUDES_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and(np.equal(nsidc_st,0),
                                        np.not_equal(igbp_st,17))
        cal_subset_area = np.logical_and((latitude_abs > 45), 
                                         (latitude_abs <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'HIGH-LATITUDES_SNOW_COVER_LAND':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less(nsidc_st,104),
                           np.greater(nsidc_st,10)),
            np.not_equal(igbp_st,17))
        cal_subset_area = np.logical_and((latitude_abs > 45), (latitude_abs <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'HIGH-LATITUDES_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and(np.equal(nsidc_st,0),
                                        np.equal(igbp_st,17))
        cal_subset_area = np.logical_and((latitude_abs > 45), 
                                         (latitude_abs <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'HIGH-LATITUDES_ICE_COVER_SEA':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less_equal(nsidc_st,100),
                           np.greater(nsidc_st,10)),
            np.equal(igbp_st,17))
        cal_subset_area = np.logical_and((latitude_abs > 45), 
                                         (latitude_abs <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)        
    elif mode == 'POLAR_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and(np.equal(nsidc_st,0),
                                        np.not_equal(igbp_st,17))
        cal_subset_area = latitude_abs > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'POLAR_SNOW_COVER_LAND':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less(nsidc_st,104),
                           np.greater(nsidc_st,10)),
            np.not_equal(igbp_st,17))
        cal_subset_area = latitude_abs > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'POLAR_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and(
            np.equal(nsidc_st,0),np.equal(igbp_st,17))
        cal_subset_area = latitude_abs > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'POLAR_ICE_COVER_SEA':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less_equal(nsidc_st,100),
                           np.greater(nsidc_st,10)),
            np.equal(igbp_st,17))
        cal_subset_area = latitude_abs > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)    
    else:
        raise ProcessingError('Unknown mode')

    return cal_subset     

def get_day_night_info(cObj):
    daynight_flags = None
    cObj_imager = getattr(cObj, 'avhrr') #Same as cObj.avhrr
    cObj_truth_sat= getattr(cObj, cObj.truth_sat) #cObj.calipso or cObj.iss
    if config.CCI_CLOUD_VALIDATION or config.MAIA_CLOUD_VALIDATION:
        daynight_flags = get_day_night_twilight_info_cci2014(
        cObj_imager.sunz)
    if config.PPS_VALIDATION and  hasattr(cObj_imager, 'cloudtype_qflag'):
        if cObj_imager.cloudtype_qflag is not None:
            daynight_flags = get_day_night_twilight_info_pps2012(
                cObj_imager.cloudtype_qflag)
    if config.PPS_VALIDATION and  hasattr(cObj_imager, 'cloudtype_conditions'):
        if cObj_imager.cloudtype_conditions is not None:
            daynight_flags = get_day_night_twilight_info_pps2014(
                cObj_imager.cloudtype_conditions)     
    if config.PPS_VALIDATION and daynight_flags is None:
        daynight_flags = get_day_night_twilight_info_cci2014(
        cObj_imager.sunz)
    (no_qflag, night_flag, twilight_flag, day_flag, all_dnt_flag) = daynight_flags
    if (no_qflag.sum() + night_flag.sum() + twilight_flag.sum() + 
        day_flag.sum()) != cObj_truth_sat.longitude.size:          
        raise ProcessingError("Something wrong with quality flags. It does not sum up.")
    return daynight_flags
    
def get_semi_opaque_info(caObj):
    semi_flag = None    
    opaque_flag = None
    if hasattr(caObj.avhrr, 'cloudtype_qflag'):
        #print caObj.avhrr.ctth_opaque
        if caObj.avhrr.ctth_opaque is not None:
            semi_flag, opaque_flag = get_semi_opaque_info_pps2012(
                caObj.avhrr.ctth_opaque) 
    if hasattr(caObj.avhrr, 'cloudtype_conditions'):
        if caObj.avhrr.ctth_status is not None:
            #print caObj.avhrr.ctth_status
            semi_flag, opaque_flag = get_semi_opaque_info_pps2014(
                caObj.avhrr.ctth_status)
    return semi_flag, opaque_flag


def find_imager_clear_cloudy(cObj):
    imager_clear =np.logical_and(np.less_equal(cObj.avhrr.cloudtype,4),np.greater(cObj.avhrr.cloudtype,0))
    imager_cloudy = np.logical_and(np.greater(cObj.avhrr.cloudtype,4),np.less(cObj.avhrr.cloudtype,20))
    if config.USE_CMA_FOR_CFC_STATISTICS:
        imager_clear = np.logical_or(np.equal(cObj.avhrr.cloudmask,3),
                                     np.equal(cObj.avhrr.cloudmask,0))
        imager_cloudy = np.logical_or(np.equal(cObj.avhrr.cloudmask,1),
                                      np.equal(cObj.avhrr.cloudmask,2))
    return imager_clear, imager_cloudy

def find_truth_clear_cloudy(cObj, val_subset):

    # For the combined 1km + 5km dataset cloud_fraction can only have values (0.0, 0.2, 0.4, 0.6, 0.8, 1.0). So the threshold should
    # really be set to 0.4, i.e., at least two 1 km columns should be cloudy!. 
    # Imager cloudy clear
    cObj_truth_sat = getattr(cObj, cObj.truth_sat)
    if 'CALIPSO' in cObj.truth_sat.upper():
        truth_clear = np.logical_and(
            np.less(cObj_truth_sat.cloud_fraction,config.CALIPSO_CLEAR_MAX_CFC),val_subset)
        truth_cloudy = np.logical_and(
            np.greater_equal(cObj_truth_sat.cloud_fraction,config.CALIPSO_CLOUDY_MIN_CFC),val_subset)        
    else:
        truth_clear = np.logical_and(
            np.less_equal(cObj_truth_sat.cloud_fraction,0.5), val_subset)
        truth_cloudy = np.logical_and(
            np.greater(cObj_truth_sat.cloud_fraction,0.5), val_subset)       
    return truth_clear, truth_cloudy    

def print_cpp_stats(cObj, statfile, val_subset):
    # CLOUD PHASE EVALUATION
    #=======================    
    # CLOUD PHASE: CALIOP/ISS - IMAGER
    if cObj.avhrr.cpp_phase is None:
        logger.warning("There are no cpp data.")
        return
    from validate_cph import get_calipso_phase_inner, CALIPSO_PHASE_VALUES
    val_subset = np.logical_and(
        val_subset, 
        cObj.calipso.cloud_fraction >= config.CALIPSO_CLOUDY_MIN_CFC)
    cal_phase = get_calipso_phase_inner(
        cObj.calipso.feature_classification_flags, 
        max_layers=10,
        same_phase_in_top_three_lay=True)
    truth_water = np.equal(cal_phase, CALIPSO_PHASE_VALUES['water'])
    truth_ice = np.logical_or(
        np.equal(cal_phase, CALIPSO_PHASE_VALUES['ice']),
        np.equal(cal_phase, CALIPSO_PHASE_VALUES['horizontal_oriented_ice']))
    truth_water = np.logical_and(truth_water.data, ~cal_phase.mask)
    truth_ice = np.logical_and(truth_ice.data, ~cal_phase.mask)
    pps_water = np.equal(cObj.avhrr.cpp_phase,1)
    pps_ice = np.equal(cObj.avhrr.cpp_phase,2)
    pps_ice = np.logical_and(pps_ice, val_subset)
    pps_water = np.logical_and(pps_water,val_subset)

    n_ice_ice = np.sum(
        np.logical_and(truth_ice,pps_ice))
    n_water_water = np.sum(
        np.logical_and(truth_water,pps_water))
    n_ice_water = np.sum(
        np.logical_and(truth_ice,pps_water))
    n_water_ice = np.sum(
        np.logical_and(truth_water,pps_ice))

    nice = n_ice_ice + n_ice_water 
    nwater = n_water_water + n_water_ice
    #nwater_pps = n_water_water+n_ice_water
    #nice_pps = n_water_ice+n_ice_ice
  
    pod_water = -9.0
    pod_ice = -9.0
    hitrate = -9
    if nwater > 0:
        pod_water = 100*float(n_water_water)/nwater
    if nice > 0:
        pod_ice = 100*float(n_ice_ice)/nice
    if nice + nwater >0:    
        hitrate = (n_ice_ice + n_water_water)*1.0/(nice+nwater)
    statfile.write("CLOUD PHASE %s-IMAGER TABLE: %s %s %s %s \n" % (cObj.truth_sat.upper(), n_ice_ice,n_ice_water,n_water_ice,n_water_water))
    statfile.write("CLOUD PHASE %s-IMAGER POD-WATER: %3.2f \n" % (cObj.truth_sat.upper(), pod_water))
    statfile.write("CLOUD PHASE %s-IMAGER POD-ICE: %3.2f \n" % (cObj.truth_sat.upper(), pod_ice))
    statfile.write("CLOUD PHASE %s-IMAGER Hitrate: %3.2f \n" % (cObj.truth_sat.upper(), hitrate))  
            
def print_cmask_stats(cObj, statfile, val_subset):
    # CLOUD MASK EVALUATION
    #=======================    
    # CORRELATION CLOUD MASK: CALIOP/ISS - IMAGER
    truth_clear, truth_cloudy = find_truth_clear_cloudy(cObj, val_subset)
    pps_clear, pps_cloudy = find_imager_clear_cloudy(cObj)
    pps_clear = np.logical_and(pps_clear, val_subset)
    pps_cloudy = np.logical_and(pps_cloudy,val_subset)
    n_clear_clear = np.repeat(
        pps_clear,np.logical_and(truth_clear,pps_clear)).shape[0]
    n_cloudy_cloudy = np.repeat(
        pps_cloudy,np.logical_and(truth_cloudy,pps_cloudy)).shape[0]
    n_clear_cloudy = np.repeat(
        pps_cloudy,np.logical_and(truth_clear,pps_cloudy)).shape[0]
    n_cloudy_clear = np.repeat(
        pps_clear,np.logical_and(truth_cloudy,pps_clear)).shape[0]
    nclear = n_clear_clear+n_clear_cloudy #np.repeat(truth_clear,truth_clear).shape[0]
    ncloudy = n_cloudy_cloudy+n_cloudy_clear#np.repeat(truth_cloudy,truth_cloudy).shape[0]
    ncloudy_pps = n_cloudy_cloudy+n_clear_cloudy
    nclear_pps = n_cloudy_clear+n_clear_clear
    
    pod_cloudy = -9.0*0.01
    far_cloudy = -9.0*0.01
    pod_clear = -9.0*0.01
    far_clear = -9.0*0.01
    if ncloudy > 0:
        pod_cloudy = float(n_cloudy_cloudy)/ncloudy
    if ncloudy_pps > 0:
        far_cloudy = float(n_clear_cloudy)/ncloudy_pps       
    if nclear > 0:
        pod_clear = float(n_clear_clear)/nclear
    if nclear_pps > 0:
        far_clear = float(n_cloudy_clear)/nclear_pps
        
    
    if (n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy) > 0:
        mean_caliop=((n_clear_clear+n_clear_cloudy)*0.0 + (n_cloudy_clear+n_cloudy_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
        mean_pps=((n_clear_clear+n_cloudy_clear)*0.0 + (n_cloudy_cloudy+n_clear_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
        bias=mean_pps-mean_caliop
    else:
        bias = -9.0*0.01

    statfile.write("CLOUD MASK %s-IMAGER TABLE: %s %s %s %s \n" % (cObj.truth_sat.upper(), n_clear_clear,n_clear_cloudy,n_cloudy_clear,n_cloudy_cloudy))
    #statfile.write("CLOUD MASK %s-IMAGER PROB:%3.2f \n" % (cObj.truth_sat.upper(), pod_cloudy,pod_clear,far_cloudy,far_clear,bias))
    statfile.write("CLOUD MASK %s-IMAGER POD-CLOUDY: %3.2f \n" % (cObj.truth_sat.upper(), pod_cloudy*100))
    statfile.write("CLOUD MASK %s-IMAGER POD-CLEAR:  %3.2f \n" %  (cObj.truth_sat.upper(), pod_clear*100))
    statfile.write("CLOUD MASK %s-IMAGER FAR-CLOUDY: %3.2f \n" % (cObj.truth_sat.upper(), far_cloudy*100))
    statfile.write("CLOUD MASK %s-IMAGER FAR-CLEAR:  %3.2f \n" %  (cObj.truth_sat.upper(), far_clear*100))
    statfile.write("CLOUD MASK %s-IMAGER BIAS percent: %3.2f \n" %  (cObj.truth_sat.upper(), bias*100))

def print_modis_stats(cObj, statfile, val_subset, cal_MODIS_cflag):    
    # CORRELATION CLOUD MASK: CALIOP - MODIS
    truth_clear, truth_cloudy = find_truth_clear_cloudy(cObj, val_subset)
    if cal_MODIS_cflag is None:
        return
    if len(val_subset) != len(cal_MODIS_cflag):
        logger.error("Lenght mismatch error for cal_MODIS_cflag")
        return
 
    modis_clear = np.logical_and(
        np.logical_or(np.equal(cal_MODIS_cflag,1),
                      np.equal(cal_MODIS_cflag,0)),val_subset)
    modis_cloudy = np.logical_and(
        np.logical_or(np.equal(cal_MODIS_cflag,3),
                      np.equal(cal_MODIS_cflag,2)),val_subset)

    n_clear_clear = np.repeat(
        modis_clear,
        np.logical_and(truth_clear,modis_clear)).shape[0]
    n_cloudy_cloudy = np.repeat(
        modis_cloudy,
        np.logical_and(truth_cloudy,modis_cloudy)).shape[0]
    n_clear_cloudy = np.repeat(
        modis_cloudy,
        np.logical_and(truth_clear,modis_cloudy)).shape[0]
    n_cloudy_clear = np.repeat(
        modis_clear,
        np.logical_and(truth_cloudy,modis_clear)).shape[0]
    nclear = np.repeat(truth_clear,truth_clear).shape[0]
    ncloudy = np.repeat(truth_cloudy,truth_cloudy).shape[0]
    ncloudy_modis = n_cloudy_cloudy+n_clear_cloudy
    nclear_modis = n_cloudy_clear+n_clear_clear
            
    if ncloudy > 0:
        pod_cloudy = float(n_cloudy_cloudy)/ncloudy
    else:
        pod_cloudy = -9.0
    if ncloudy_modis > 0:
        far_cloudy = float(n_clear_cloudy)/ncloudy_modis
    else:
        far_cloudy = -9.0
    if nclear > 0:
        pod_clear = float(n_clear_clear)/nclear
    else:
        pod_clear = -9.0
    if nclear_modis > 0:
        far_clear = float(n_cloudy_clear)/nclear_modis
    else:
        far_clear = -9.0

    if (n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy) > 0:
        mean_caliop=((n_clear_clear+n_clear_cloudy)*0.0 + (n_cloudy_clear+n_cloudy_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
        mean_modis=((n_clear_clear+n_cloudy_clear)*0.0 + (n_cloudy_cloudy+n_clear_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
        bias=mean_modis-mean_caliop
    else:
        bias=-9.0
    statfile.write("CLOUD MASK %s-MODIS TABLE: %s %s %s %s \n" % (cObj.truth_sat.upper(), n_clear_clear,n_clear_cloudy,n_cloudy_clear,n_cloudy_cloudy))
    #statfile.write("CLOUD MASK %s-MODIS FROM CLOUDSAT FLAG PROB: %f %f %f %f %f \n" % (pod_cloudy,pod_clear,far_cloudy,far_clear,bias))
    statfile.write("CLOUD MASK %s-MODIS FROM CLOUDSAT FLAG POD-CLOUDY:  %3.2f \n" % (cObj.truth_sat.upper(), pod_cloudy*100))
    statfile.write("CLOUD MASK %s-MODIS FROM CLOUDSAT FLAG POD-CLEAR:   %3.2f \n" % (cObj.truth_sat.upper(), pod_clear*100))
    statfile.write("CLOUD MASK %s-MODIS FROM CLOUDSAT FLAG FAR-CLOUDY:  %3.2f \n" % (cObj.truth_sat.upper(), far_cloudy*100))
    statfile.write("CLOUD MASK %s-MODIS FROM CLOUDSAT FLAG FAR-CLEAR:   %3.2f \n" % (cObj.truth_sat.upper(), far_clear*100))
    statfile.write("CLOUD MASK %s-MODIS FROM CLOUDSAT FLAG BIAS percent: %3.2f \n" % (cObj.truth_sat.upper(),  bias*100))    
    
    
def print_calipso_stats_ctype(caObj, statfile, val_subset, low_medium_high_class):
    if config.CCI_CLOUD_VALIDATION :
        logger.info("Cloudtype validation not useful for CCI validation")
        return
    if caObj.avhrr.cloudtype is None:
        logger.warning("There are no cloudtype data.")
        return
    # CLOUD TYPE EVALUATION - Based exclusively on CALIPSO data (Vertical Feature Mask)
    # =======================
    calipso_low = np.logical_and(low_medium_high_class['low_clouds'],
                                 val_subset)
    calipso_medium = np.logical_and(low_medium_high_class['medium_clouds'],
                                    val_subset)
    calipso_high = np.logical_and(low_medium_high_class['high_clouds'],
                                 val_subset)

    if  caObj.avhrr.cloudtype_conditions is not None: 
        logger.debug("Assuming cloudtype structure from pps v2014")
        avhrr_low = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,5),
                           np.less_equal(caObj.avhrr.cloudtype,6)),
            val_subset)
        avhrr_medium = np.logical_and(
            np.equal(caObj.avhrr.cloudtype,7), val_subset)
        avhrr_high_op = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,8),
                           np.less_equal(caObj.avhrr.cloudtype,9)),
            val_subset)
        avhrr_cirrus = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,11),
                           np.less_equal(caObj.avhrr.cloudtype,15)),
            val_subset)
        avhrr_high = avhrr_high_op #np.logical_or(avhrr_high_op,avhrr_high_semi)
        avhrr_frac = np.logical_and(np.equal(caObj.avhrr.cloudtype,10), 
                                    val_subset)

    else:
        logger.warning("Assuming cloudtype structure from pps v2012")
        avhrr_low = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,5),
                           np.less_equal(caObj.avhrr.cloudtype,8)),
            val_subset)
        avhrr_medium = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,9),
                           np.less_equal(caObj.avhrr.cloudtype,10)),
            val_subset)
        avhrr_high = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,11),
                           np.less_equal(caObj.avhrr.cloudtype,18)),
            val_subset)
        avhrr_frac = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,19),
                           np.less_equal(caObj.avhrr.cloudtype,19)),
            val_subset)

    calipso_clear = np.logical_and(
        np.less(caObj.calipso.cloud_fraction,config.CALIPSO_CLEAR_MAX_CFC),val_subset)
    calipso_cloudy = np.logical_and(
        np.greater_equal(caObj.calipso.cloud_fraction,config.CALIPSO_CLOUDY_MIN_CFC),val_subset)
    avhrr_clear = np.logical_and(
        np.logical_and(np.less_equal(caObj.avhrr.cloudtype,4),
                       np.greater(caObj.avhrr.cloudtype,0)),
        val_subset)
    
    
    # Notice that we have unfortunately changed order in notation compared to cloud mask
    # Here the PPS category is mentioned first and then the CALIOP category 

    n_low_low = np.repeat(
        avhrr_low,
        np.logical_and(calipso_low,avhrr_low)).shape[0]
    n_low_medium = np.repeat(
        avhrr_low,
        np.logical_and(calipso_medium,avhrr_low)).shape[0]
    n_low_high = np.repeat(
        avhrr_low,
        np.logical_and(calipso_high,avhrr_low)).shape[0]
    n_medium_low = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_low,avhrr_medium)).shape[0]
    n_medium_medium = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_medium,avhrr_medium)).shape[0]
    n_medium_high = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_high,avhrr_medium)).shape[0]
    n_high_low = np.repeat(
        avhrr_high, 
        np.logical_and(calipso_low,avhrr_high)).shape[0]
    n_high_medium = np.repeat(
        avhrr_high,
        np.logical_and(calipso_medium,avhrr_high)).shape[0]
    n_high_high = np.repeat(
        avhrr_high,
        np.logical_and(calipso_high,avhrr_high)).shape[0]
    n_frac_low = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_low,avhrr_frac)).shape[0]
    n_frac_medium = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_medium,avhrr_frac)).shape[0]
    n_frac_high = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_high,avhrr_frac)).shape[0]
    n_cirrus_low = np.repeat(
        avhrr_cirrus,
        np.logical_and(calipso_low,avhrr_cirrus)).shape[0]
    n_cirrus_medium = np.repeat(
        avhrr_cirrus,
        np.logical_and(calipso_medium,avhrr_cirrus)).shape[0]
    n_cirrus_high = np.repeat(
        avhrr_cirrus,
        np.logical_and(calipso_high,avhrr_cirrus)).shape[0]

    n_clear_low = np.repeat(
        avhrr_clear,
        np.logical_and(calipso_low,avhrr_clear)).shape[0]
    n_clear_medium = np.repeat(
        avhrr_clear,
        np.logical_and(calipso_medium,avhrr_clear)).shape[0]
    n_clear_high = np.repeat(
        avhrr_clear,
        np.logical_and(calipso_high,avhrr_clear)).shape[0]
    n_low_clear = np.repeat(
        avhrr_low,
        np.logical_and(calipso_clear,avhrr_low)).shape[0]
    n_medium_clear = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_clear,avhrr_medium)).shape[0]
    n_high_clear = np.repeat(
        avhrr_high,
        np.logical_and(calipso_clear,avhrr_high)).shape[0]
    n_frac_clear = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_clear,avhrr_frac)).shape[0]
    n_cirrus_clear = np.repeat(
        avhrr_cirrus,
        np.logical_and(calipso_clear,avhrr_cirrus)).shape[0]

    if (n_low_low+n_medium_low+n_high_low+n_frac_low + n_cirrus_low) > 0:
        pod_low = float(n_low_low + n_frac_low) / (
            n_low_low + n_medium_low+n_high_low+n_frac_low + n_cirrus_low)
        far_low = float(n_low_medium+n_low_high)/(
            n_low_low + n_low_medium+n_low_high  +
            n_frac_low + n_frac_medium+n_frac_high )
    else:
        pod_low = -9.0
        far_low = -9.0
    if (n_low_medium+n_medium_medium+n_high_medium+n_frac_medium + n_cirrus_medium) > 0:
        pod_medium = float(n_medium_medium + n_cirrus_medium)/(
            n_low_medium + n_medium_medium + n_high_medium + 
            n_frac_medium + n_cirrus_medium)
        far_medium = float(n_medium_low+n_medium_high)/(
            n_medium_low + n_medium_medium+n_medium_high + n_cirrus_medium)
    else:
        pod_medium =-9.0
        far_medium =-9.0
    if (n_low_high+n_medium_high+n_high_high+n_frac_high + n_cirrus_high) > 0:
        pod_high = float(n_high_high+n_cirrus_high)/(n_low_high+n_medium_high+n_high_high+n_frac_high + n_cirrus_high)
        far_high = float(n_high_low+n_high_medium +n_cirrus_low)/(n_high_low + n_high_medium +n_high_high 
                                                                  + n_cirrus_high +n_cirrus_low)
    else:
        pod_high =-9.0
        far_high =-9.0

    statfile.write("CLOUD TYPE %s-IMAGER TABLE: %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s\n" % (
        caObj.truth_sat.upper(), 
        n_low_low, n_low_medium, n_low_high,
        n_medium_low, n_medium_medium, n_medium_high, 
        n_high_low, n_high_medium, n_high_high,
        n_frac_low, n_frac_medium, n_frac_high,
        n_cirrus_low, n_cirrus_medium, n_cirrus_high))
    statfile.write("CLOUD TYPE %s-IMAGER PROB: %f %f %f %f %f %f \n" % (
        caObj.truth_sat.upper(), 
        pod_low, pod_medium, pod_high, far_low, far_medium, far_high))
    statfile.write("CLOUD TYPE %s-IMAGER TABLE MISSED: %s %s %s %s %s %s %s %s \n" % (
        caObj.truth_sat.upper(),
        n_clear_low, n_clear_medium, n_clear_high, 
        n_low_clear, n_medium_clear, n_high_clear, n_frac_clear, n_cirrus_clear))
            

def print_height_all_low_medium_high(NAME, val_subset,  statfile, 
                                     low_medium_high_class, imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height, imager_is_cloudy):
    out_stats = calculate_ctth_stats(val_subset,imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height, imager_is_cloudy)
    statfile.write("CLOUD HEIGHT %s ALL: %s\n" %(NAME, out_stats))
    if low_medium_high_class is None:
        #Nothing more can be done!
        return
    cal_low_ok = np.logical_and(low_medium_high_class['low_clouds'],
                                 val_subset)
    out_stats = calculate_ctth_stats(cal_low_ok,imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height, imager_is_cloudy)   
    statfile.write("CLOUD HEIGHT %s LOW: %s \n" % (NAME, out_stats))
    cal_mid_ok = np.logical_and(low_medium_high_class['medium_clouds'],
                                 val_subset)
    out_stats = calculate_ctth_stats(cal_mid_ok, imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height, imager_is_cloudy)   
    statfile.write("CLOUD HEIGHT %s MEDIUM: %s \n" % (NAME, out_stats))
    cal_high_ok = np.logical_and(low_medium_high_class['high_clouds'],
                                 val_subset)
    out_stats = calculate_ctth_stats(cal_high_ok, imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height, imager_is_cloudy) 
    statfile.write("CLOUD HEIGHT %s HIGH: %s \n" % (NAME, out_stats))

def print_stats_ctop(cObj, statfile, val_subset, low_medium_high_class):
    if cObj.avhrr.ctth_height is None:
        logger.warning("There are no ctth height data.")
        return

    # CORRELATION: CALIOP - IMAGER HEIGHT
    # FIRST TOTAL FIGURES


    cObj_imager = getattr(cObj, 'avhrr') #Same as cObj.avhrr
    cObj_truth_sat= getattr(cObj, cObj.truth_sat) #cObj.calipso or cObj.iss
    imager_ctth_m_above_seasurface = cObj_imager.imager_ctth_m_above_seasurface  
    truth_sat_validation_height = cObj_truth_sat.validation_height
    (dummy, imager_is_cloudy) = find_imager_clear_cloudy(cObj)
                        
    val_subset = np.logical_and(
        val_subset, 
        cObj_truth_sat.cloud_fraction >= config.CALIPSO_CLOUDY_MIN_CFC)

 
    #print "ALL CLOUDS:" 
    print_height_all_low_medium_high(cObj.truth_sat.upper(),
                                     val_subset, 
                                     statfile, low_medium_high_class, 
                                     imager_ctth_m_above_seasurface, 
                                     truth_sat_validation_height, 
                                     imager_is_cloudy)
    
    if cObj.truth_sat.upper() not in ["CALIPSO"]:
        if cObj.truth_sat.upper() in ["ISS"]:
            logger.warning("WARNING WARNING WARNING only printing over all statistics "
                           "for cloudtop for ISS")
        return
    if  (config.COMPILE_RESULTS_SEPARATELY_FOR_SINGLE_LAYERS_ETC and 
         cObj.avhrr.cloudtype is not None):
        statfile.write("CLOUD HEIGHT GEO-STYLE\n")
        from scipy import  ndimage
        # GEO uses pixels with homogene CT in 9x9 pixels 
        # Let us use 9 homogene CT pixels. Not fully the same, but similar.
        # And variation (definition?) caliop pressure <200hPa
        # And variation CPR height less than 3km
        # And CALIPO clouds thinner than 0.2 removed. however pixel kept
        # For 1km data we have to either keep or fully remove the pixel
        maxct = ndimage.filters.maximum_filter1d(cObj.avhrr.cloudtype, size=9)
        minct = ndimage.filters.minimum_filter1d(cObj.avhrr.cloudtype, size=9)
        val_geo = np.logical_and(
            val_subset, 
            np.equal(maxct,minct)) 
        if hasattr(cObj,'calipso'):
            var_pressure = (ndimage.filters.maximum_filter1d(cObj.calipso.layer_top_pressure[:,0], size=9) - 
                            ndimage.filters.minimum_filter1d(cObj.calipso.layer_top_pressure[:,0], size=9))
            val_geo = np.logical_and(
                val_geo, 
                var_pressure<200) #Pressure variation less than 200hPa
        if hasattr(cObj,'cloudsat'):
            var_height = (ndimage.filters.maximum_filter1d(truth_sat_validation_height, size=9) - 
                            ndimage.filters.minimum_filter1d(truth_sat_validation_height, size=9))
            val_geo = np.logical_and(
                val_geo, 
                var_height<3000) # Height variation less than 3km
        average_height_truth = ndimage.filters.uniform_filter1d(truth_sat_validation_height*1.0, size=9)
        average_height_truth[truth_sat_validation_height<0] = -9
        average_height_imager = ndimage.filters.uniform_filter1d(imager_ctth_m_above_seasurface*1.0, size=9)
        average_height_imager[imager_ctth_m_above_seasurface<0] = -9
        print_height_all_low_medium_high("CALIOP-GEO-STYLE", 
                                         val_geo,
                                         statfile, low_medium_high_class, 
                                         average_height_imager,
                                         average_height_truth,
                                         imager_is_cloudy)
        val_geo = np.logical_and(
            val_geo, 
            np.greater_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,0.2))
        statfile.write("CLOUD HEIGHT GEO-STYLE-EXCLUDE-THIN-PIXELS\n")
        print_height_all_low_medium_high("CALIOP-GEO-STYLE-EXCLUDE-THIN-PIXELS", 
                                         val_geo,
                                         statfile, low_medium_high_class, 
                                         average_height_imager,
                                         average_height_truth,
                                         imager_is_cloudy)
 
    if config.COMPILE_RESULTS_SEPARATELY_FOR_SINGLE_LAYERS_ETC:
        statfile.write("CLOUD HEIGHT SINGLE-LAYER\n")
        val_subset_single = np.logical_and(
            val_subset, 
            np.equal(cObj.calipso.number_layers_found,1)) 
        print_height_all_low_medium_high("CALIOP-SINGLE-LAYER", 
                                         val_subset_single,
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, 
                                         truth_sat_validation_height, 
                                         imager_is_cloudy)

    if (config.COMPILE_RESULTS_SEPARATELY_FOR_SINGLE_LAYERS_ETC and
        (config.ALSO_USE_5KM_FILES or config.RESOLUTION==5)): 
        statfile.write("CLOUD HEIGHT SINGLE-LAYER, NOT THIN\n")
        lim=2*config.OPTICAL_DETECTION_LIMIT
        val_subset_single_not_thinnest = np.logical_and(
            val_subset_single, 
            np.greater_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-SINGLE-LAYER>%f"%(lim), 
                                         val_subset_single_not_thinnest,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, 
                                         truth_sat_validation_height, 
                                         imager_is_cloudy)
        
        statfile.write("CLOUD HEIGHT NOT VERY THIN TOP LAYER\n")
        lim=config.OPTICAL_DETECTION_LIMIT
        val_subset_not_thinnest_top_layer = np.logical_and(
            val_subset, 
            np.greater_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-TOP-LAYER>%f"%(lim), 
                                         val_subset_not_thinnest_top_layer,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, 
                                         truth_sat_validation_height, 
                                         imager_is_cloudy)

        lim=config.OPTICAL_DETECTION_LIMIT
        statfile.write("CLOUD HEIGHT VERY THIN TOP LAYER\n")
        val_subset_thinnest_top_layer = np.logical_and(
            val_subset, 
            np.less_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-TOP-LAYER<=%f"%(lim), 
                                         val_subset_thinnest_top_layer,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, 
                                         truth_sat_validation_height, 
                                         imager_is_cloudy)
           
   
def print_main_stats(cObj, statfile):
    val_object = getattr(cObj,cObj.truth_sat)
    num_val_data_ok = len(getattr(val_object,'elevation'))
    statfile.write("%s min and max time diff: %3.2f %3.2f \n" %(
        cObj.truth_sat.upper(),
        cObj.diff_sec_1970.min(),
        cObj.diff_sec_1970.max()))

    statfile.write("%s start and stop Latitude: %3.2f %3.2f \n" %(
        cObj.truth_sat.upper(),
        val_object.latitude[0],
        val_object.latitude[-1]))

    statfile.write("%s start and stop Longitude: %3.2f %3.2f \n" %(
        cObj.truth_sat.upper(),                            
        val_object.longitude[0],
        val_object.longitude[-1]))

    statfile.write("%s-IMAGER number of matches: %d\n"%(
        cObj.truth_sat.upper(), 
        num_val_data_ok))


def CalculateStatistics(mode, statfilename, caObj, clsatObj, issObj,
                        dnt_flag=None):

    def get_day_night_subset(cObj, val_subset):
        (no_qflag, night_flag, twilight_flag, day_flag, all_dnt_flag) = get_day_night_info(cObj)
        
        if dnt_flag is None:
            logger.debug('dnt_flag = %s', 'ALL PIXELS')
            dnt_subset = np.logical_and(val_subset, all_dnt_flag)
        elif dnt_flag.upper() == 'DAY':
            logger.debug('dnt_flag = %s', dnt_flag.upper())
            dnt_subset = np.logical_and(val_subset, day_flag)
        elif dnt_flag.upper() == 'NIGHT':
            logger.debug('dnt_flag = %s', dnt_flag.upper())
            dnt_subset = np.logical_and(val_subset, night_flag)
        elif dnt_flag.upper() == 'TWILIGHT':
            logger.debug('dnt_flag = %s', dnt_flag.upper())
            dnt_subset = np.logical_and(val_subset, twilight_flag)
        else:
            raise ProcessingError("Unknown DNT-flag %s"%(dnt_flag.upper()))
        return dnt_subset  
 
    if clsatObj is not None:
        logger.info("Cloudsat Statistics")
        val_subset = get_subset_for_mode(clsatObj, mode)
        if val_subset is not None:
            val_subset = get_day_night_subset(clsatObj, val_subset)
            #curretnly only mode BASIC
            low_medium_high_class = get_cloudsat_low_medium_high_classification(clsatObj)
            statfile = open(statfilename.replace('xxx','cloudsat'),"w")
            print_main_stats(clsatObj, statfile)
            print_cmask_stats(clsatObj, statfile, val_subset)
            print_modis_stats(clsatObj, statfile, val_subset, clsatObj.cloudsat.MODIS_cloud_flag)
            print_stats_ctop(clsatObj,  statfile, val_subset, low_medium_high_class)
            statfile.close()
    
    if caObj is not None:
        logger.info("Calipo Statistics")
        val_subset = get_subset_for_mode(caObj, mode)
        if val_subset is not None:
            statfile = open(statfilename.replace('xxx','calipso'),"w")
            low_medium_high_class = get_calipso_low_medium_high_classification(caObj)
            #semi_flag, opaque_flag = get_semi_opaque_info(caObj)
            val_subset = get_day_night_subset(caObj, val_subset)
            print_main_stats(caObj, statfile)
            print_cmask_stats(caObj, statfile, val_subset)
            print_modis_stats(caObj, statfile, val_subset,   caObj.calipso.cal_MODIS_cflag)
            print_calipso_stats_ctype(caObj, statfile, val_subset, low_medium_high_class)
            print_stats_ctop(caObj,  statfile, val_subset, low_medium_high_class) 
            print_cpp_stats(caObj, statfile, val_subset)
            statfile.close()
    
    if issObj is not None:
        val_subset = get_subset_for_mode(issObj, mode)
        if val_subset is not None:
            statfile = open(statfilename.replace('xxx','iss'),"w")
            val_subset = get_day_night_subset(issObj, val_subset)
            print_main_stats(issObj, statfile)
            print_cmask_stats(issObj, statfile, val_subset)
            #print_calipso_stats_ctype(issObj, statfile, val_subset, cal_vert_feature)
            print_stats_ctop(issObj, statfile, val_subset, None)
            statfile.close()
