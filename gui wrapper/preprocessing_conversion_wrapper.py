import os
import time
import logging
import ev100_vector_preprocessing_multi_threading
import ev100_vector_conversion_waipio_std


class wrapper():
    def __init__(self, rev, chip_version, py_log_path, py_log_name, pattern_category, vector_type, updated_date_time):
        self.rev = rev
        self.chip_version = chip_version
        self.updated_date_time = updated_date_time
        self.py_log_name = py_log_name
        self.py_log_path = py_log_path
        self.pattern_category = pattern_category
        self.vector_type = vector_type
        self.logger = self.set_up_logger()

    def set_up_logger(self):
        # set up logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

        # py_log = os.path.join(py_log_path,'conversion_test.log')
        py_log = os.path.join(self.py_log_path, self.py_log_name)
        # py_log = os.path.join(py_log_path,'TDF_zip_transfer_log.log')
        file_handler = logging.FileHandler(py_log)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        # stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        return logger

    def copy_stil_zip_files(self, dest, map_path, par_vector_path_r1):
        preprocess = ev100_vector_preprocessing_multi_threading.Preprocess(self.rev, self.chip_version, self.py_log_path, self.py_log_name, self.pattern_category, self.vector_type,
                 self.updated_date_time, self.logger, dest, map_path, par_vector_path_r1)
        preprocess.store_all_zip_atpg(dest, self.pattern_category, self.vector_type)

    def velocity_conversion(self, dest, blocks, log_name, velocity_dft_cfg_path, patch_timesets_path,
                            patch_timesets_50mhz_path, enable_del_zip=False):

        conversion = ev100_vector_conversion_waipio_std.Conversion(self.rev, self.chip_version, self.py_log_path, self.py_log_name, self.pattern_category, self.vector_type,
                 self.updated_date_time, self.logger, dest, blocks, log_name, velocity_dft_cfg_path, patch_timesets_path, patch_timesets_50mhz_path, enable_del_zip)
        version_num = self.rev + "_sec5lpe"
        rev_path = os.path.join(dest, self.chip_version, version_num)

        for block in blocks:
            block_path = os.path.join(rev_path, block)
            pattern_categories = self.pattern_category.split("|")
            for pat_cat in pattern_categories:
                pat_path = os.path.join(block_path, pat_cat)
                vector_types = self.vector_type.split("|")
                for type in vector_types:
                    type_path = os.path.join(pat_path, type)
                    print(type_path)
                    conversion.traverse_levels(type_path, pat_cat, type, log_name, enable_del_zip)

    def generate_pats_txt(self, conversion_log_csv_path, dir_pat, log_name, lim, list_dirs_exclude = [], pin_group ='OUT', enable_cyc_cnt=1, block=None, freq_modes = ['NOM', 'SVS', 'TUR', 'SVSD1']):
        dir_exec = os.path.join(dir_pat, self.chip_version, 'pattern_execution', 'pattern_list')
        preprocess = ev100_vector_preprocessing_multi_threading.Generate_Pats(conversion_log_csv_path, self.logger)
        pattern_categories = self.pattern_category.split("|")
        for pat_cat in pattern_categories:
            vector_types = self.vector_type.split("|")
            for type in vector_types:
                preprocess.generate_pats_txt(pat_cat, type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude, pin_group, enable_cyc_cnt, block, freq_modes)


def main():

    updated_date_time = time.strftime("%Y%m%d-%H%M%S")

## to run any input needed
    rev = 'r1'
    chip_version = 'waipio'
    py_log_path = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop"
    py_log_name = 'py_conversion_' + updated_date_time + '_test.log'
    pattern_category = r"INT|SAF"
    vector_type = r"PROD"
    to_run = []

    preprocess_convert = wrapper(rev, chip_version, py_log_path, py_log_name, pattern_category, vector_type, updated_date_time)

# to run copy zip STIL files
    par_vector_path_r1 = r'\\qctdfsrt\prj\qct\chips' + "\\" + chip_version + r'\sandiego\test\vcd' + "\\" + rev + r'_sec5lpe\tester_vcd'

## to run copy zip STIL files and conversion velocity
    dest = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\test_multi"
    map_path = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\Automation csv\demo_int_saf.csv"

# to run conversion velocity and PATS.txt generation
    # make list based on dest
    blocks = ["ATPG"] # input

    #default
    conversion_log_csv_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + "\\" + r"\conversion_log"

    #input name for conversion
    #autofill options for pats.txt
    log_name = '061021_conv_test_log' #input

# to run conversion velocity
    #default
    velocity_dft_cfg_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\velocity_cfg\waipio\waipio_WY_dft_universal_v1.cfg"
    #default
    patch_timesets_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\waipio\patch_timesets.txt"
    #default
    patch_timesets_50mhz_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\lahaina\patch_timesets_50MHz.txt"  # TODO Roshni: need to update after waipio timesets methdology is avaialbe from TEV
    #default
    enable_del_zip = False

# to run PATS.txt generation
    #defaults
    lim = 1
    pin_group = 'ALL_PINS'
    freq_modes = ['SVS', 'NOM', 'TUR', 'SVSD1']
    enable_cyc_cnt = 1
    list_dirs_exclude = []
    block = None

    preprocess_convert.copy_stil_zip_files(dest, map_path, par_vector_path_r1)

    preprocess_convert.velocity_conversion(dest, blocks, log_name, velocity_dft_cfg_path, patch_timesets_path, patch_timesets_50mhz_path, enable_del_zip)

    preprocess_convert.generate_pats_txt(conversion_log_csv_path, dest, log_name, lim, list_dirs_exclude, pin_group, enable_cyc_cnt, block, freq_modes)


if __name__ == '__main__':
    main()