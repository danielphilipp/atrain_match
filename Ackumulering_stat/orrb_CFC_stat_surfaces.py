# Program orrb_CFC_stat_surfaces

# This program calculates basic statistics for the cloud amount (CFC) product for
# each month

import string
import math

from orrb_stat_class import OrrbStats

# -----------------------------------------------------
class CloudFractionSurfacesStats(OrrbStats):
    
    def do_stats(self):
        from numpy import NaN
        n_clear_clear_csa = 0
        n_clear_cloudy_csa = 0
        n_cloudy_clear_csa = 0
        n_cloudy_cloudy_csa = 0
        n_clear_clear_cal = 0
        n_clear_cloudy_cal = 0
        n_cloudy_clear_cal = 0
        n_cloudy_cloudy_cal = 0
        n_clear_clear_cal_MODIS = 0
        n_clear_cloudy_cal_MODIS = 0
        n_cloudy_clear_cal_MODIS = 0
        n_cloudy_cloudy_cal_MODIS = 0
    
        scenes = len(self.results_files)
        
        for datafile in self.results_files:
            current_datafile = open(datafile, "r")
            datalist = current_datafile.readlines()
            current_datafile.close()
            
            #print "Datafile: ", datafile
            csa_data = string.split(datalist[4])
            cal_data = string.split(datalist[8])
            modis_data = string.split(datalist[10])
    
            # Accumulate CloudSat statistics
        
            n_clear_clear_csa = n_clear_clear_csa + int(csa_data[4])
            n_clear_cloudy_csa = n_clear_cloudy_csa + int(csa_data[5])
            n_cloudy_clear_csa = n_cloudy_clear_csa + int(csa_data[6])
            n_cloudy_cloudy_csa = n_cloudy_cloudy_csa + int(csa_data[7])
        
            # Accumulate CALIOP statistics
        
            n_clear_clear_cal = n_clear_clear_cal + int(cal_data[4])
            n_clear_cloudy_cal = n_clear_cloudy_cal + int(cal_data[5])
            n_cloudy_clear_cal = n_cloudy_clear_cal + int(cal_data[6])
            n_cloudy_cloudy_cal = n_cloudy_cloudy_cal + int(cal_data[7])
    
            # Accumulate CALIOP-MODIS statistics
        
            n_clear_clear_cal_MODIS = n_clear_clear_cal_MODIS + int(modis_data[4])
            n_clear_cloudy_cal_MODIS = n_clear_cloudy_cal_MODIS + int(modis_data[5])
            n_cloudy_clear_cal_MODIS = n_cloudy_clear_cal_MODIS + int(modis_data[6])
            n_cloudy_cloudy_cal_MODIS = n_cloudy_cloudy_cal_MODIS + int(modis_data[7])
    
        samples_csa = n_clear_clear_csa + n_clear_cloudy_csa + n_cloudy_clear_csa +\
                      n_cloudy_cloudy_csa
        samples_cal = n_clear_clear_cal + n_clear_cloudy_cal + n_cloudy_clear_cal +\
                      n_cloudy_cloudy_cal
        if samples_csa > 0:
            bias_csa = float(n_clear_cloudy_csa - n_cloudy_clear_csa)/float(samples_csa)
            bias_csa_perc = 100.0*float(n_clear_cloudy_csa - n_cloudy_clear_csa)/float(samples_csa)
            mean_CFC_csa = 100.0*(n_cloudy_cloudy_csa+n_cloudy_clear_csa)/samples_csa
        else:
            bias_csa = NaN
            bias_csa_perc = NaN
            mean_CFC_csa = NaN
        if samples_cal > 0:
            mean_CFC_cal = 100.0*(n_cloudy_cloudy_cal+n_cloudy_clear_cal)/samples_cal
            bias_cal = float(n_clear_cloudy_cal - n_cloudy_clear_cal)/float(samples_cal)
            bias_modis = float(n_clear_cloudy_cal_MODIS - n_cloudy_clear_cal_MODIS)/float(samples_cal-1)
            bias_cal_perc = 100.0*float(n_clear_cloudy_cal - n_cloudy_clear_cal)/float(samples_cal)
            bias_modis_perc = 100.0*float(n_clear_cloudy_cal_MODIS - n_cloudy_clear_cal_MODIS)/float(samples_cal-1)
        else:
            mean_CFC_cal = NaN
            bias_cal = NaN
            bias_modis = NaN
            bias_cal_perc = NaN
            bias_modis_perc = NaN
        
        square_sum_csa =  float(n_clear_clear_csa+n_cloudy_cloudy_csa)*bias_csa*bias_csa + \
                         n_cloudy_clear_csa*(-1.0-bias_csa)*(-1.0-bias_csa) + \
                         n_clear_cloudy_csa*(1.0-bias_csa)*(1.0-bias_csa)
        if samples_csa > 0:
            rms_csa = 100.0*math.sqrt(square_sum_csa/(samples_csa-1))
        else:
            rms_csa = NaN
        square_sum_cal =  float(n_clear_clear_cal+n_cloudy_cloudy_cal)*bias_cal*bias_cal + \
                         n_cloudy_clear_cal*(-1.0-bias_cal)*(-1.0-bias_cal) + \
                         n_clear_cloudy_cal*(1.0-bias_cal)*(1.0-bias_cal)
        if samples_cal > 0:
            rms_cal = 100.0*math.sqrt(square_sum_cal/(samples_cal-1))
        else:
            rms_cal = NaN
        square_sum_modis =  float(n_clear_clear_cal+n_cloudy_cloudy_cal)*bias_modis*bias_modis + \
                           n_cloudy_clear_cal*(-1.0-bias_modis)*(-1.0-bias_modis) + \
                           n_clear_cloudy_cal*(1.0-bias_modis)*(1.0-bias_modis)
        if samples_cal > 0:
            rms_modis = 100.0*math.sqrt(square_sum_modis/(samples_cal-1))
        else:
            rms_modis = NaN
        
        self.scenes = scenes
        #self.samples_csa = samples_csa
        #self.bias_csa_perc = bias_csa_perc
        #self.rms_csa = rms_csa
        self.samples_cal = samples_cal
        self.mean_CFC_cal = mean_CFC_cal
        self.bias_cal_perc = bias_cal_perc
        self.rms_cal = rms_cal
        self.bias_modis_perc = bias_modis_perc
        self.rms_modis = rms_modis
    
    
    def printout(self):
        lines = []
        try:
            lines.append("Month is:  %s" % self.month)
        except KeyError:
            pass
        lines.append("Total number of matched scenes is: %s" % self.scenes)
        lines.append("")
        lines.append("Total number of CALIOP matched FOVs: %d" % self.samples_cal)
        lines.append("Mean CFC CALIOP: %f" % self.mean_CFC_cal)
        lines.append("Mean error: %f" % self.bias_cal_perc)
        lines.append("RMS error: %f" % self.rms_cal)
        lines.append("Mean error MODIS: %f" % self.bias_modis_perc)
        lines.append("RMS error MODIS: %f" % self.rms_modis)
        lines.append("")
        
        for l in lines:
            print(l)
        
        return lines


if __name__ == "__main__":
    import setup
    stats = CloudFractionSurfacesStats()
    stats.old_interface(modes=setup.SURFACES, output_file_desc="cfc_results_surfaces_summary")