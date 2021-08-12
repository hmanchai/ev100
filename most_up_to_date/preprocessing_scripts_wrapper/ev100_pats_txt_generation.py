from preprocess_init import CreateFolder
import argparse
import fnmatch
import os
import re
import time
from preprocess_init import Logger
from preprocess_init import CreateFolder

import pandas as pd

class Generate_Pats():
    # TODO: create option to automatically check svm and lvm KB/MB size limit to fit maximum patterns in pats.txt
    """
    Class generates PATS.txt files separated out into folders labeled with sequential numbers
    Filepath dest + \pattern_execution\pattern_list\<freq_mode>\<pattern_type>\<vector_type>\<#>
    Each batch of patterns is separated out by
    """

    # C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\ev100_automation > C:\Users\rpenmatc\AppData\Local\Programs\Python\Python37\python.exe
    # "C:/Users/rpenmatc/OneDrive - Qualcomm/Desktop/ev100_automation/most_up_to_date/preprocessing_scripts_wrapper / ev100_pats_txt_generation.py"
    # -rev r1 -chip_version waipio -pattern_category INT  -vector_type PROD -dest C:\Users\rpenmatc -map_path C:\Users\rpenmatc\demo_int_saf.csv
    # -block ATPG -lim 1 -pin_group ALL_PINS -freq_mode_list SVS -enable_cyc_cnt 1 -exclude_dirs ""

    def __init__(self, conversion_log_csv_path, logger):

        self.conversion_log_csv_path = conversion_log_csv_path
        self.logger = logger
        self.make_folder = CreateFolder()

    def generate_pats_txt(self, pattern_category, vector_type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude=[],
                          pin_group='OUT', enable_cyc_cnt=1, block = None, freq_modes=['NOM', 'SVS', 'TUR', 'SVSD1']):
        """
        Generate a set of PATS.txt files for pattern batch execution.
        :param vector_type: str
            choice of vector type has PROD or RMA. As project evolves, more choices might come
        :param pattern_category: str
            choices are INT, SAF and TDF
        :param dir_pat: str
            top level dir for DFT patterns. e.g. in SVE-EV100-1 PC, dir_pat can be F:\ATPG_CDP\Lahaina\r2 for Lahaina R2
        :param dir_exec: str
            top level for PATS.txt files. e.g. in SVE-EV100-1 PC, dir_exec can be F:\ATPG_CDP\Lahaina\r2\pattern_execution\Pattern_list for Lahaina R2
        :param log_name: str
            conversion log name (w/o .csv extension)
        :param lim: int
            limit for the number of patterns to host in a PATS.txt file
        :param list_dirs_exclude: list. default = []
            dir of DFT patterns to EXCLUDE from PATS.TXT
        :param pin_group: str. default = 'OUT'
            pin group mask. Choices are 'IN','OUT','ALL_PINS'
        :param enable_cyc_cnt: bool. default = True
            if True, actual cycle count of each pattern will be extracted from conversion log and put in PATS.txt; if false, cycle count will be 0 in PATS.txt
        :param block: str. default = None
            Only needed for TDF pattern. This rule is derived based on Lahaina mapping files obtained from PTE (i.e. In Lahaina PTE mapping files,
            TDF patterns are classified by block, such as CPU and GPU, but ATPG are not. The rule can change if mapping file changes in other projects
        :param freq_modes: list. default = ['NOM', 'SVS', 'TUR', 'SVSD1']
            frequency mode used for folder organization mode/pattern_category/vector_type
        """
        for index, mode in enumerate(freq_modes):

            sub_freq_modes = [x for x in freq_modes if x != mode]
            list_dirs_exclude_full = list_dirs_exclude + sub_freq_modes

            conv_log = os.path.join(self.conversion_log_csv_path, log_name + '.csv')
            df_conv_log = pd.read_csv(conv_log)

            pin_group = pin_group  # OUT, ALL_PINS
            keep_state = 0
            load_pattern = 1
            dummy_cfg = 'NULL'
            dummy_xrl = 'NULL'
            header = '; Pattern, Cycle Count, Enable Fail Mask Pin Group, Keep State, Load Pattern, cfg, xrl'

            # # change all types to string and combine the strings separated by comma
            # to_write = ','.join(map(str, [do_file_name, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))

            if pattern_category.lower() in 'tdf':
                # dir to grab DO from
                #for block in blocks:
                #path_top_level = os.path.join(dir_pat, block, pattern_category, vector_type)
                path_top_level = dir_pat
                # dir to export PATS.txt to
                dir_sub = os.path.join(dir_exec, block, mode, pattern_category, vector_type)
                # prefix for PATS.txt file name
                pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
            elif pattern_category.lower() in ['int', 'saf']:
                #path_top_level = os.path.join(dir_pat, pattern_category, vector_type)
                path_top_level = dir_pat
                dir_sub = os.path.join(dir_exec, mode, pattern_category, vector_type)
                pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

            self.make_folder.create_folder(dir_sub)

            do_files = self.total_do_files(df_conv_log, freq_modes, list_dirs_exclude_full, path_top_level, pattern_category, vector_type, block)

            # block = os.path.basename(path_block)
            # do_files = glob.glob(path_block + '/**/*.do', recursive=True)

            # if pattern_category.lower() == 'tdf':
            #     # dir to grab DO from
            #     path_top_level = os.path.join(dir_pat,pattern_category,vector_type, block)
            #     # dir to export PATS.txt to
            #     dir_sub = os.path.join(dir_exec, pattern_category, vector_type, block)
            #     # prefix for PATS.txt file name
            #     pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
            # elif pattern_category.lower() in ['int','saf']:
            #     path_top_level = os.path.join(dir_pat,pattern_category,vector_type)
            #     dir_sub = os.path.join(dir_exec, pattern_category, vector_type)
            #     pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

            cnt = self.pats_per_txt(do_files, lim)

            # # create subdir in execution dir
            # dir_sub = os.path.join(dir_exec,pattern_category,vector_type)
            # create_folder(dir_sub)

            # create individual PATS.txt and folder
            # pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

            for i in range(cnt):

                pats_txt = self.create_pats_txt(dir_sub, header, i, pre_fix)

                # write patterns
                start = i * lim
                end = (i + 1) * lim
                for do_file in do_files[start:end]:

                    cyc_cnt = self.add_pattern_info(df_conv_log, do_file, enable_cyc_cnt)

                    # path_do_file = Path(do_file)
                    # print(path_do_file)

                    to_write = ','.join(
                        map(str, [do_file, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))
                    with open(pats_txt, 'a+') as f:
                        f.write(to_write + '\n')

            print(f'*** PATS.txt generation completed for {pattern_category} {vector_type}{mode}')

    def add_pattern_info(self, df_conv_log, do_file, enable_cyc_cnt):
        """
        Applies filter to extract the cycle count for each .do file that needs to be added to pats.txt
        :param df_conv_log: DataFrame
            dataframe of conversion log data
        :param do_file: str
            .do file name allows us to filter the conversion log dataframe for cycle count for specific vector
        :param enable_cyc_cnt:

        """
        do_file_name = os.path.basename(do_file)
        if enable_cyc_cnt:

            try:
                path = re.search("(.*)(\\\)(.*)(\\\)(.*)(\\\)(.*)$", do_file).group(1)

                filter = df_conv_log['block'] == path
                cyc_cnt = df_conv_log.loc[filter, 'extracted_cycle_count'].values[0]

            except Exception as e:
                print(e)
                cyc_cnt = 0
            # else:

        else:
            cyc_cnt = 0
        return cyc_cnt

    def total_do_files(self, df_conv_log, freq_modes, list_dirs_exclude_full, path_top_level, pattern_category, vector_type, block):
        """
        Add file paths of all .do files to have a PATS.txt file created for
        :param df_conv_log: DataFrame
            conversion log dataframe
        :param freq_modes: array
            List of frequency modes that are used for filtering out filepaths
        :param list_dirs_exclude_full: array
            will exclude directories in array from creating pats.txt if found in filepath name
        :param path_top_level: str
            root path to begin topdown loop
        """
        do_files = []
        for root, dirs, files in os.walk(path_top_level, topdown=True):
            # exclude dirs
            dirs[:] = [d for d in dirs if d not in list_dirs_exclude_full]

            for file in files:
                if fnmatch.fnmatch(file, '*_XMD.do'):

                    # get abs paths for DO patterns
                    modes = "|".join(freq_modes)
                    modes_pattern = "(.*)(\\\)(" + modes + ")(\\\)(.*)"
                    #root.replace("\\", r"\\")
                    if re.search(modes_pattern, root):
                        if re.search(pattern_category, root):
                            if re.search(vector_type, root):
                                if re.search(block, root):
                                    if df_conv_log['pattern_name'].str.contains(file).any():
                                        for df_block in df_conv_log['block']:
                                            if df_block + "\\device\\test" == root:
                                              
                                                do_file = os.path.join(root, file)
                                                do_files.append(do_file)
        return do_files

    def pats_per_txt(self, do_files, lim):
        """
        Divides up number of .do file patterns to be run in each batch of pats.txt files based on the limit defined
        :param do_files: array
            list of all .do files that match criteria to be added to pats.txt
        :param lim: int
            max number of .do files to be run in single pats.txt
        """
        quo, rem = divmod(len(do_files), lim)
        # set up the number of PATS.txt
        if quo:
            if rem:
                cnt = quo + 1
            else:
                cnt = quo
        else:
            cnt = 1
        return cnt

    def create_pats_txt(self, dir_sub, header, i, pre_fix):
        """
        creates actual file and folder with sequential # to store pattern execution data
        :param dir_sub: str
            directory for pats.txt files to be stored
        :param header: str
            name of header file
        :param i: int
            folder number to store pats.txt in unique location
        :param pre_fix: str
            prefix to make pats.txt naming convention
        """
        pats_dir = os.path.join(dir_sub, str(i + 1))
        self.make_folder.create_folder(pats_dir)
        pats_txt_name = pre_fix + str(i + 1) + '.txt'
        pats_txt = os.path.join(pats_dir, pats_txt_name)
        # write header
        with open(pats_txt, 'w+') as f:
            f.write(header + '\n')
        return pats_txt


def main():
    """
    main method allows for arguments to be directly added through command line
    Generates pats.txt files in respective folders
    """
    updated_date_time = time.strftime("%Y%m%d-%H%M%S")
    updated_date = time.strftime("%Y%m%d")
    py_log_name = 'py_conversion_' + updated_date_time + '.log'

    parser = argparse.ArgumentParser(description='Execute GeneratePats script')

    parser.add_argument('-rev', dest='rev', type=str,
                        help='revision number ex. r1')
    parser.add_argument('-chip_version', dest='chip_version', type=str,
                        help='chip version type ex. waipio')
    parser.add_argument('-pattern_category', dest='pattern_category', type=str,
                        help='Enter the pattern category ( ex. SAF, INT, TDF')
    parser.add_argument('-vector_type', dest='vector_type', type=str,
                        help='Enter the vector type ex. PROD, EVAL')
    parser.add_argument('-dest', dest='dest', type=str,
                        help='destination  of base file path for files to by copied')
    parser.add_argument('-map_path', dest='map_path', type=str, help='file path to vector mapping file')
    parser.add_argument('-block', dest='block', type=str,
                        help='Enter the block (ex. TDF_ATPG_CPU)')
    parser.add_argument('-lim', dest='lim', type=int, help='Enter lim for # of patterns in each PATS.txt #')
    parser.add_argument('-pin_group', dest='pin_group', type=str, help="Enter pin group (ex. IN, OUT, or ALL_PINS)")
    parser.add_argument('-freq_mode_list', dest='freq_mode_list', type=str,
                        help="Enter the frequency modes (separated by , ex. SVS,NOM,TUR)")
    parser.add_argument('-enable_cyc_cnt', dest='enable_cyc_cnt', type=int, help="Enter 1 or 0 to set enable cycle count")
    parser.add_argument('-exclude_dirs', dest='exclude_dirs', type=str,
                        help="Enter list of directories to exclude (separated by ,)")
    args = parser.parse_args()
    freq_modes = args.freq_mode_list.split(",")
    list_dirs_exclude = args.exclude_dirs.split(",")

    py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r'\py_log'

    log_name = 'conversion_log_' + args.pattern_category + "_" + args.vector_type + "_" + updated_date

    conversion_log_csv_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r"\conversion_log"

    logger = Logger().set_up_logger(py_log_path, py_log_name)
    dir_exec = os.path.join(args.dest, 'pattern_execution', 'pattern_list')

    preprocess_convert = Generate_Pats(conversion_log_csv_path, logger)

    preprocess_convert.generate_pats_txt(args.pattern_category, args.vector_type, args.dest, dir_exec, log_name, args.lim, list_dirs_exclude,
                              args.pin_group, args.enable_cyc_cnt, args.block, freq_modes)


if __name__ == '__main__':
    main()