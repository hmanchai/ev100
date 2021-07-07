import os
import time
import create_folder_and_logger
import ev100_vector_preprocessing_multi_threading
import json
import ev100_vector_conversion_waipio_std
from create_folder_and_logger import Logger



class wrapper():
    def __init__(self, rev, chip_version, py_log_path, py_log_name, pattern_category, vector_type, updated_date_time):
        self.rev = rev
        self.chip_version = chip_version
        self.updated_date_time = updated_date_time
        self.py_log_name = py_log_name
        self.py_log_path = py_log_path
        self.pattern_category = pattern_category
        self.vector_type = vector_type
        self.logger = Logger.set_up_logger(py_log_path, py_log_name)


    def copy_stil_zip_files(self, dest, map_path, par_vector_path_r1):
        preprocess = ev100_vector_preprocessing_multi_threading.Preprocess(self.rev, self.chip_version,
                                                                           self.py_log_path, self.py_log_name,
                                                                           self.pattern_category, self.vector_type,
                                                                           self.updated_date_time, self.logger, dest,
                                                                           map_path, par_vector_path_r1)
        preprocess.store_all_zip_atpg()

    def velocity_conversion(self, conversion_log_csv_path, dest, blocks, log_name, velocity_dft_cfg_path,
                            patch_timesets_path,
                            patch_timesets_50mhz_path, map_path, enable_del_zip=False):

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
        dir_exec = os.path.join(dir_pat, 'pattern_execution', 'pattern_list')
        version_num = self.rev + "_sec5lpe"
        #dir_pat = os.path.join(dir_pat, self.chip_version, version_num)
        preprocess = ev100_vector_preprocessing_multi_threading.Generate_Pats(conversion_log_csv_path, self.logger)
        pattern_categories = self.pattern_category.split("|")
        for block in blocks:
            #dir_pat = os.path.join(dir_pat, block)
            for pat_cat in pattern_categories:
                vector_types = self.vector_type.split("|")
                for type in vector_types:
                    preprocess.generate_pats_txt(pat_cat, type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude,
                                                 pin_group, enable_cyc_cnt, block, freq_modes)


def main():
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

        preprocess_convert = generate_json_file(input_dic, updated_date, updated_date_time)
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

                    preprocess_convert = wrapper(rev, chip_version, py_log_path, py_log_name, pattern_category,
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


def generate_json_file(input_dic, updated_date, updated_date_time):
    global chip_version, convert_velocity, copy_zip, dest, generate_pats, pattern_category, py_log_name, py_log_path, rev, vector_type, par_vector_path_r1, map_path, enable_del_zip, patch_timesets_50mhz_path, patch_timesets_path, velocity_dft_cfg_path, blocks, conversion_log_csv_path, log_name, enable_cyc_cnt, freq_modes, lim, list_dirs_exclude, pin_group
    chip_version, convert_velocity, copy_zip, dest, generate_pats, pattern_category, py_log_name, py_log_path, rev, vector_type = input_to_run(
        input_dic, updated_date_time)
    preprocess_convert = wrapper(rev, chip_version, py_log_path, py_log_name, pattern_category, vector_type,
                                 updated_date_time)
    ## to run copy zip STIL files
    if copy_zip.lower() == 'y':
        par_vector_path_r1 = needed_for_zip(chip_version, input_dic, rev)
    ## to run copy zip STIL files and conversion velocity
    if copy_zip.lower() == 'y' or convert_velocity.lower() == 'y':
        map_path = needed_zip_conversion(input_dic)
    if convert_velocity.lower() == 'y':
        # to run conversion velocity
        enable_del_zip, patch_timesets_50mhz_path, patch_timesets_path, velocity_dft_cfg_path = needed_conversion(
            input_dic)
    # to run conversion velocity and PATS.txt generation
    if convert_velocity == 'y' or generate_pats == 'y':
        blocks, conversion_log_csv_path, log_name = needed_conversion_pats(chip_version,
                                                                           input_dic, pattern_category, rev,
                                                                           updated_date,
                                                                           vector_type)
    if generate_pats == 'y':
        enable_cyc_cnt, freq_modes, lim, list_dirs_exclude, pin_group = needed_pats(input_dic)
    json_filename = str(input(
        "Save inputs in .json file: \n # ENTER NO INPUT - DEFAULT \"inputs_" + updated_date_time + ".json\"\n ") or 'inputs_' + updated_date_time + '.json')
    with open(json_filename, 'w') as outfile:
        json.dump(input_dic, outfile, indent=2)
    return preprocess_convert


def needed_pats(input_dic):
    lim = int(input("Enter lim for # of patterns in each PATS.txt #: \n # ENTER NO INPUT - DEFAULT \"1\"\n ") or 1)
    input_dic['lim'] = lim

    pin_group = str(input(
        "Enter pin group (ex. IN, OUT, or ALL_PINS) #: \n # ENTER NO INPUT - DEFAULT \"ALL_PINS\"\n ") or 'ALL_PINS')
    input_dic['pin_group'] = pin_group

    modes_str = str(input(
        "Enter the frequency modes (separated by | ex. SVS|NOM|TUR): \n # ENTER NO INPUT - DEFAULT \"SVS|NOM|TUR|SVSD1\"\n ") or r"SVS|NOM|TUR|SVSD1")

    freq_modes = modes_str.split("|")
    input_dic['freq_modes'] = freq_modes

    enable_cyc_cnt = int(
        input("Enter 1 or 0 to set enable cycle count: \n # ENTER NO INPUT - DEFAULT \"1\"\n ") or 1)
    input_dic['enable_cyc_cnt'] = enable_cyc_cnt

    exclude_str = str(input(
        "Enter list of directories to exclude (separated by |): \n # ENTER NO INPUT - DEFAULT \"<none>\"\n ") or r"")
    list_dirs_exclude = exclude_str.split("|")
    input_dic['list_dirs_exclude'] = list_dirs_exclude
    return enable_cyc_cnt, freq_modes, lim, list_dirs_exclude, pin_group


def needed_conversion_pats(chip_version, input_dic, pattern_category, rev,
                           updated_date, vector_type):
    blocks_str = str(input(
        "Enter the blocks (separated by | ex. ATPG|TDF_ATPG_CPU): \n # ENTER NO INPUT - DEFAULT \"ATPG\"\n ") or r"ATPG")
    # make list based on dest
    blocks = blocks_str.split("|")
    input_dic['blocks'] = blocks
    pat_name = pattern_category.replace("|", "_")
    vec_name = vector_type.replace("|", "_")
    log_name = str(input(
        "Enter conversion log filename: \n # ENTER NO INPUT - DEFAULT \"conversion_log_" + pat_name + "_" + vec_name + "_" + updated_date + "\"\n ") or 'conversion_log_' + pat_name + "_" + vec_name + "_" + updated_date)
    input_dic['log_name'] = log_name

    conversion_log_csv_path = str(input("Enter conversion log file path: \n # ENTER NO INPUT - DEFAULT \"" +
                                        r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + r"\conversion_log" + "\"\n ") or
                                  r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + r"\conversion_log")
    input_dic['conversion_log_csv_path'] = conversion_log_csv_path
    return blocks, conversion_log_csv_path, log_name


def needed_conversion(input_dic):
    # velocity_dft_cfg_path = str(input(
    #     "Enter velocity configuration file path: \n # ENTER NO INPUT - DEFAULT \"" +
    #     r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\velocity_cfg\waipio\waipio_WY_dft_universal_v1.cfg" + "\"\n ")
    #                             or r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\velocity_cfg\waipio\waipio_WY_dft_universal_v1.cfg")

    velocity_dft_cfg_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\velocity_cfg" + "\\" + chip_version + "\\" + chip_version + "_WY_dft_universal_v1.cfg"
    input_dic['velocity_dft_cfg_path'] = velocity_dft_cfg_path

    # patch_timesets_path = str(input(
    #     "Enter patch timesets file path: \n # ENTER NO INPUT - DEFAULT \"" +
    #     r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\waipio\patch_timesets.txt" + "\"\n ")
    #                           or r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\waipio\patch_timesets.txt")
    patch_timesets_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\waipio\patch_timesets.txt"
    input_dic['patch_timesets_path'] = patch_timesets_path

    # patch_timesets_50mhz_path = str(input(
    #     "Enter patch timesets 50 MHz file path: \n # ENTER NO INPUT - DEFAULT \"" +
    #     r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\lahaina\patch_timesets_50MHz.txt" + "\"\n ")
    #                                 or r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\lahaina\patch_timesets_50MHz.txt")
    patch_timesets_50mhz_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\lahaina\patch_timesets_50MHz.txt"
    input_dic['patch_timesets_50mhz_path'] = patch_timesets_50mhz_path

    enable_del_zip_bool = str(
        input("Enter to T/F set enable_del_zip: \n # ENTER NO INPUT - DEFAULT \"" + "F" + "\"\n "))

    if enable_del_zip_bool.lower() == 't':
        enable_del_zip = True
    else:
        enable_del_zip = False

    input_dic['enable_del_zip'] = enable_del_zip
    return enable_del_zip, patch_timesets_50mhz_path, patch_timesets_path, velocity_dft_cfg_path


def needed_zip_conversion(input_dic):
    map_path = str(input(
        "Enter vector mapping file path: \n # ENTER NO INPUT - DEFAULT \"" + r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\Automation csv\demo_int_saf.csv" + "\"\n ")
                   or r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\Automation csv\demo_int_saf.csv")
    input_dic['map_path'] = map_path
    # map_path = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\Automation csv\demo_int_saf.csv"
    return map_path


def needed_for_zip(chip_version, input_dic, rev):
    # par_vector_path_r1 = str(input("Enter the STIL file resource folder: \n # ENTER NO INPUT - DEFAULT \"" +
    #                                r'\\qctdfsrt\prj\qct\chips' + "\\" + chip_version + r'\sandiego\test\vcd' + "\\" + rev + r'_sec5lpe\tester_vcd' + "\"\n ") or
    #                          r'\\qctdfsrt\prj\qct\chips' + "\\" + chip_version + r'\sandiego\test\vcd' + "\\" + rev + r'_sec5lpe\tester_vcd')
    par_vector_path_r1 =  r'\\qctdfsrt\prj\qct\chips' + "\\" + chip_version + r'\sandiego\test\vcd' + "\\" + rev + r'_sec5lpe\tester_vcd'
    input_dic['par_vector_path_r1'] = par_vector_path_r1
    return par_vector_path_r1


def input_to_run(input_dic, updated_date_time):
    rev = str(input("Enter the rev #: \n # ENTER NO INPUT - DEFAULT \"r1\"\n ") or "r1")
    input_dic['rev'] = rev
    chip_version = str(input("Enter the chip version: \n # ENTER NO INPUT - DEFAULT \"waipio\"\n ") or "waipio")
    input_dic['chip_version'] = chip_version
    py_log_name = str(input(
        "Enter pylog filename: \n # ENTER NO INPUT - DEFAULT \"py_conversion_" + updated_date_time + ".log\"\n ") or 'py_conversion_' + updated_date_time + '.log')
    input_dic['py_log_name'] = py_log_name
    py_log_path = str(input(
        "Enter pylog pathname: \n # ENTER NO INPUT - DEFAULT \"" + r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + r'\py_log' + "\"\n ")
                      or r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + r'\py_log')
    input_dic['py_log_path'] = py_log_path
    pattern_category = str(input(
        "Enter the pattern categories (separated by | ex. SAF|INT|TDF): \n # ENTER NO INPUT - DEFAULT \"INT|SAF\"\n ") or r"INT|SAF")
    input_dic['pattern_category'] = pattern_category
    vector_type = str(input(
        "Enter the vector types (separated by | ex. PROD|EVAL): \n # ENTER NO INPUT - DEFAULT \"PROD\"\n ") or r"PROD")
    input_dic['vector_type'] = vector_type
    dest = str(input(
        "Enter destination path: \n # ENTER NO INPUT - DEFAULT \"" + r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\test_multi" + "\"\n ")
               or r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\test_multi")
    input_dic['dest'] = dest
    copy_zip = str(input("Run Copy STIL Zip Files \nEnter Y/N:\n") or "N")
    input_dic['copy_zip'] = copy_zip
    convert_velocity = str(input("Run Velocity Conversion .do \nEnter Y/N:\n") or "N")
    input_dic['convert_velocity'] = convert_velocity
    generate_pats = str(input("Run Generate PATS.txt \nEnter Y/N:\n") or "N")
    input_dic['generate_pats'] = generate_pats
    return chip_version, convert_velocity, copy_zip, dest, generate_pats, pattern_category, py_log_name, py_log_path, rev, vector_type


if __name__ == '__main__':
    main()
