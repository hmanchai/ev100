import os
import time
import json
import ev100_vector_preprocessing_multi_threading
import ev100_vector_conversion_waipio_std
import ev100_pats_txt_generation
from preprocess_init import Logger
import generate_json


class wrapper():
    """
    wrapper runs preprocessing scripts/subset of preprocessing scripts based on json input file that correctly sets variables and which scripts to run
    will then execute entire preprocessing flow
    """
    def __init__(self, rev, chip_version, py_log_path, py_log_name, pattern_category, vector_type, updated_date_time):
        self.rev = rev
        self.chip_version = chip_version
        self.updated_date_time = updated_date_time
        self.py_log_name = py_log_name
        self.py_log_path = py_log_path
        self.pattern_category = pattern_category
        self.vector_type = vector_type
        self.log_ob = Logger()
        self.logger = self.log_ob.set_up_logger(py_log_path, py_log_name)

    def copy_stil_zip_files(self, dest, map_path, par_vector_path_r1):
        """
        Method called to copy STIL files to SVE workspace
        :param dest: base destination folder for all zip files to be copied and organized into
        :type dest: str
        :param map_path: file path for mapping csv file containing vector info used in folder naming/organization and zip file retrieval
        :type map_path: str
        :param par_vector_path_r1: source for all stil vectors to be copied
        :type par_vector_path_r1: str
        """
        preprocess = ev100_vector_preprocessing_multi_threading.Preprocess(self.rev, self.chip_version,
                                                                           self.py_log_path, self.py_log_name,
                                                                           self.pattern_category, self.vector_type,
                                                                           self.updated_date_time, self.logger, dest,
                                                                           map_path, par_vector_path_r1)
        preprocess.store_all_zip_atpg()

    def velocity_conversion(self, conversion_log_csv_path, dest, blocks, log_name, velocity_dft_cfg_path,
                            patch_timesets_path,
                            patch_timesets_50mhz_path, map_path, enable_del_zip=False):
        """
        Method called to convert STIL files to .do and .dp using velocity tool
        :param conversion_log_csv_path: path to conversion log to keep track of data for converted header/payloads to .do
        (actual file log name not included), used in pats.txt generation
        :type conversion_log_csv_path: str
        :param dest: base destination folder for all zip files - root directory
        :type dest: str
        :param blocks: block names of files to be converted with velocity (used to filter filepaths)
        :type blocks: list
        :param log_name: conversion log file name (no file extension)
        :type log_name: str
        :param velocity_dft_cfg_path: configuration file path
        :type velocity_dft_cfg_path: str
        :param patch_timesets_path: timesets file path
        :type patch_timesets_path: str
        :param patch_timesets_50mhz_path: timesets file path
        :type patch_timesets_50mhz_path: str
        :param map_path: file path for mapping csv file containing vector info used in folder naming/organization and zip file retrieval
        :type map_path: str
        :param enable_del_zip: enable deleting zip
        :type enable_del_zip: Boolean
        """
        conversion = ev100_vector_conversion_waipio_std.Conversion(self.rev, self.chip_version, self.py_log_path,
                                                                   self.py_log_name, self.pattern_category,
                                                                   self.vector_type,
                                                                   self.updated_date_time, self.logger,
                                                                   conversion_log_csv_path, dest, blocks, log_name,
                                                                   velocity_dft_cfg_path, patch_timesets_path,
                                                                   patch_timesets_50mhz_path, map_path, enable_del_zip)
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

    def generate_pats_txt(self, conversion_log_csv_path, dir_pat, log_name, lim, list_dirs_exclude=[], pin_group='OUT',
                          enable_cyc_cnt=1, blocks=[], freq_modes=['NOM', 'SVS', 'TUR', 'SVSD1']):
        """
        Method called to generate pat.txt files for each
        :param conversion_log_csv_path: path to conversion log to keep track of data for converted header/payloads to .do
        (actual file log name not included), used in pats.txt generation
        :type conversion_log_csv_path: str
        :param dir_pat: base destination folder for all zip files to be copied and organized into
        :type dir_pat: str
        :param log_name: conversion log file name (no file extension)
        :type log_name: str
        :param lim: limit of max number of patterns to be included in each pats.txt file
        :type lim: int
        :param list_dirs_exclude: list of directories to exclude when looking for .do files to generate pats.txt
        :type list_dirs_exclude: list str
        :param pin_group: pin group label ex ALL_PINS
        :type pin_group: str
        :param enable_cyc_cnt: Enable cycle count 1 or 0
        :type enable_cyc_cnt: intN
        :param blocks: blocks that you want to generate pats.txt
        (if want to filter must uncomment dir_pat = os.path.join(dir_pat, block))
        :type blocks: list
        :param freq_modes: frequency modes that you want to generate pats.txt for
        :type freq_modes: list
        """
        dir_exec = os.path.join(dir_pat, 'pattern_execution', 'pattern_list')
        version_num = self.rev + "_sec5lpe"
        # dir_pat = os.path.join(dir_pat, self.chip_version, version_num)
        preprocess = ev100_pats_txt_generation.Generate_Pats(conversion_log_csv_path, self.logger)
        pattern_categories = self.pattern_category.split("|")
        for block in blocks:
            # dir_pat = os.path.join(dir_pat, block)
            for pat_cat in pattern_categories:
                vector_types = self.vector_type.split("|")
                for type in vector_types:
                    preprocess.generate_pats_txt(pat_cat, type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude,
                                                 pin_group, enable_cyc_cnt, block, freq_modes)


def main():
    """
    Choice to use existing json file or generate new json file. Also allows one to update log names to not overwrite even when using existing json file
    Sets up all inputs to be used in wrapper to execute preprocessing flow
    """
    json_generator = generate_json.GenerateJson()
    updated_date_time = time.strftime("%Y%m%d-%H%M%S")
    updated_date = time.strftime("%Y%m%d")
    global chip_version, convert_velocity, copy_zip, dest, generate_pats, pattern_category, py_log_name, py_log_path, rev, vector_type
    chip_version, convert_velocity, copy_zip, dest, generate_pats, pattern_category, py_log_name, py_log_path, rev, vector_type = "", "", "", "", "", "", "", "", "", ""
    global par_vector_path_r1, map_path, enable_del_zip, patch_timesets_50mhz_path, patch_timesets_path, velocity_dft_cfg_path
    par_vector_path_r1, map_path, enable_del_zip, patch_timesets_50mhz_path, patch_timesets_path, velocity_dft_cfg_path = "", "", "", "", "", ""
    global blocks, conversion_log_csv_path, log_name, enable_cyc_cnt, freq_modes, lim, list_dirs_exclude, pin_group
    blocks, conversion_log_csv_path, log_name, enable_cyc_cnt, freq_modes, lim, list_dirs_exclude, pin_group = "", "", "", "", "", "", "", ""
    input_dic = {}
    use_json = str(input(
        "Use json file inputs Y/N #: \n # ENTER NO INPUT - DEFAULT \"N\"\n ") or 'N')

    if use_json.lower() == 'n':

        preprocess_convert = json_generator.generate_json_file(input_dic, updated_date, updated_date_time)
    else:
        while True:
            try:
                json_filename = str(input(
                    "Enter json file path to autofill inputs: \n"))
                with open(json_filename, 'r') as json_file:
                    input_dic = json.load(json_file)
                    globals().update(input_dic)
                    change_log_files = str(input(
                        "Would you like to first update log filenames?\nEnter Y/N:\n"))
                    if change_log_files.lower() == 'y':
                        py_log_name = str(input(
                            "Enter new pylog filename: \n # ENTER NO INPUT - DEFAULT \"py_conversion_" + updated_date_time + ".log\"\n ") or 'py_conversion_' + updated_date_time + '.log')
                        input_dic["py_log_name"] = py_log_name
                        if log_name != "":
                            pat_name = pattern_category.replace("|", "_")
                            vec_name = vector_type.replace("|", "_")
                            log_name = str(input(
                                "Enter new conversion log filename: \n # ENTER NO INPUT - DEFAULT \"conversion_log_" + pat_name + "_" + vec_name + "_" + updated_date + "\"\n ") or 'conversion_log_' + pat_name + "_" + vec_name + "_" + updated_date)
                            input_dic["log_name"] = log_name
                        with open(json_filename, 'w') as outfile:
                            json.dump(input_dic, outfile, indent=2)

                    preprocess_convert = wrapper(rev, chip_version, py_log_path,
                                                 py_log_name, pattern_category,
                                                 vector_type,
                                                 updated_date_time)
                break
            except (IOError, OSError) as e:
                print("incorrect, try again \n")
                continue

    if copy_zip == 'y':
        preprocess_convert.copy_stil_zip_files(dest, map_path, par_vector_path_r1)

    if convert_velocity == 'y':
        preprocess_convert.velocity_conversion(conversion_log_csv_path, dest, blocks, log_name, velocity_dft_cfg_path,
                                               patch_timesets_path, patch_timesets_50mhz_path, map_path, enable_del_zip)

    if generate_pats == 'y':
        preprocess_convert.generate_pats_txt(conversion_log_csv_path, dest, log_name, lim, list_dirs_exclude, pin_group,
                                             enable_cyc_cnt, blocks, freq_modes)


if __name__ == '__main__':
    main()
