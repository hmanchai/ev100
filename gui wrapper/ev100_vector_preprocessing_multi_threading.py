import os
import glob

import pandas as pd
import time
from datetime import timedelta
import fnmatch
import re
import multiprocessing

from gevent import monkey
import subprocess

monkey.patch_all()

from gevent.pool import Pool


class Preprocess():
    def __init__(self, rev, chip_version, py_log_path, py_log_name, pattern_category, vector_type,
                 updated_date_time, logger, dest, map_path, par_vector_path_r1):
        self.rev = rev
        self.chip_version = chip_version
        self.updated_date_time = updated_date_time
        self.py_log_name = py_log_name
        self.py_log_path = py_log_path
        self.pattern_category = pattern_category
        self.vector_type = vector_type
        self.logger = logger
        self.dest = dest
        self.map_path = map_path
        self.par_vector_path_r1 = par_vector_path_r1

    # def set_up_logger(self):
    #     global logger, updated_data_time
    #     # set up logger
    #     logger = logging.getLogger(__name__)
    #     logger.setLevel(logging.DEBUG)
    #     formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
    #     updated_data_time = time.strftime("%Y%m%d-%H%M%S")
    #     # py_log = os.path.join(py_log_path,'INT_pat_store_log.log')
    #     py_log = os.path.join(py_log_path, 'py_' + updated_data_time + '_demo.log')
    #     file_handler = logging.FileHandler(py_log)
    #     file_handler.setLevel(logging.INFO)
    #     file_handler.setFormatter(formatter)
    #     stream_handler = logging.StreamHandler()
    #     stream_handler.setFormatter(formatter)
    #     logger.addHandler(file_handler)
    #     logger.addHandler(stream_handler)


    def load_filter_map(self,pattern_category, vector_type):
        """
        Load and filter map file.

        :param pattern_category: str
            choice of pattern category has TDF, INT, or SAF
        :param vector_type: str
            choice of vector type has PROD or RMA. As project evolves, more choices might come
        :return: pandas dataframe containing vector header and payload mapping
        """

        df_map = pd.read_csv(self.map_path)
        # filter out non-translated and non-available patterns
        df_map = df_map[df_map['DFT type'].str.match(pattern_category)]
        df_map = df_map[df_map['Vector Type'].str.match(vector_type)]
        return df_map

    def create_folder(self, dir):
        """
        Create the directory if not exists.

        :param dir: str
            directory to create
        """
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
                self.logger.debug(f'Directory created: {dir}')
            except Exception:
                self.logger.exception(f"Error! Could not create directory {dir}")

    def copy_files(self, log_level, df_file_loc, dir_path):
        """
        Copy files to target directory, and increment count if copy succeeds.

        :param path_to_file: str
            directory to source files to copy
        :param dest_dir: str
            directory of destination to copy source files to
        :param log_level: str
            defines the level of logger
        :return: bool
            0 if failed; 1 if successful
        """

        temp_csv = os.path.join(dir_path, 'temp.csv')
        csv_file = open(temp_csv, "w")
        df_file_loc.to_csv(temp_csv, index=None, sep=',', header=False, mode='a')
        csv_file.close()
        return temp_csv


    def copy_files_threading(self, path_to_file, dest_dir, log_level):
        """
        Copy files to target directory, and increment count if copy succeeds.

        :param path_to_file: str
            directory to source files to copy
        :param dest_dir: str
            directory of destination to copy source files to
        :param log_level: str
            defines the level of logger
        :return: bool
            0 if failed; 1 if successful
        """

        cmd = "pycopier " + "\"" + path_to_file + "\"" + " " + "\"" + dest_dir + "\""
        subprocess.call(cmd)
        if log_level == 'info':
            self.logger.info(f'File copied: {os.path.basename(path_to_file)}')
        elif log_level == 'debug':
            self.logger.debug(f'File copied: {os.path.basename(path_to_file)}')



    def store_all_zip_atpg(self, dest_dir, pattern_category, vector_type):
        """
        Copy INT or SAF STIL zip files from original dir, classify (by: block, domain, mode, etc.) and store in a target location,
        e.g. network drive
        NOTE: double copy is OK and will overwrite
        """

        # rev -> dft type -> vector type -> lpu/lpc -> domain -> freq mode
        # # # create pattern level dir (INT, SAF)
        # dir_pattern = os.path.join(dest_dir, pattern_category)
        # # # create vector_type level dir (PROD or RMA)
        # dir_vector_type = os.path.join(dir_pattern,vector_type)

        # load and filter map file to pd df
        df_map = self.load_filter_map(pattern_category, vector_type)
        # print(df_map)
        df_file_loc = pd.DataFrame(columns=['source', 'dest'])
        # set up pattern source path

        # set up counter
        total_hdr_cnt = 0
        total_pl_cnt = 0
        res_hdr_cpy = 0
        res_pl_cpy = 0
        dict_rev_cnt = {'r1': 0}

        start = time.time()
        self.logger.info(f"***** Starting .stil.gz files storing and classification for {pattern_category} {vector_type} *****")

        # TODO: optimize this looping
        # looping by dataframe rows
        for index, row in df_map.iterrows():
            # create payload filename
            # TODO: can simplify once requirement mapping list implemented
            path_atpg_r1 = os.path.join(self.par_vector_path_r1, row['Block'], 'SRC')
            pl = re.search("(tk_atpg)(.*)", row['payload']).group(2)
            hdr = row['header']

            # copy header and payload zip file
            hdr_zip = hdr + '.stil.gz'
            hdr_path_to_copy = os.path.join(path_atpg_r1,hdr_zip)

            # split using payload delimiter |
            payload_list = re.split("\\|", pl)
            if row['DFT type'] == "TDF":
                payload_list = [""]
            for payload in payload_list:
                if row['DFT type'] != "TDF":
                    pl_zip = 'tk_atpg' + payload + '.stil.gz'
                    pl_path_to_copy = os.path.join(path_atpg_r1,pl_zip)
                else:
                    pl_path_to_copy = path_atpg_r1

                # folder_ordering = ['Block', 'Bin Si Revision', 'DFT type', 'Vector Type', 'Vector', 'freq mode']
                comp_type, dir_path, name = self.create_file_path(dest_dir, payload, row)
                self.create_folder(dir_path)

                start_inner = time.time()

                self.logger.info(f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {comp_type} {name} {row['freq mode']} ***")
                self.logger.info(
                        f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {comp_type} {name} {row['freq mode']} ***")

                # copy header and increment counter

                # res_hdr_cpy = copy_files(hdr_path_to_copy, dir_path, 'info')
                new_row = {'source': hdr_path_to_copy, 'dest': dir_path}
                df_file_loc = df_file_loc.append(new_row, ignore_index=True)
                res_hdr_cpy += 1
                if row['DFT type'] == 'TDF':
                    res_pl_cpy += 1
                    df_file_loc = self.copy_payloads_tdf(dir_path, pl_path_to_copy, row, df_file_loc)
                else:
                    res_pl_cpy += 1
                    df_file_loc = self.copy_payload(dir_path, pl_path_to_copy, df_file_loc)

        self.setup_thread_pool(dest_dir, df_file_loc)

        dict_rev_cnt[self.rev] += res_hdr_cpy

        # copy payload and increment counter


        # increment total count
        total_hdr_cnt += res_hdr_cpy
        total_pl_cnt += res_pl_cpy

        end_inner = time.time()
        elapsed_inner = end_inner - start_inner
        self.logger.info(f'*** Time elapsed for file storing for this pattern: {timedelta(seconds=elapsed_inner)} ***')


        self.logger.info(f'***** Total count of .stil.gz files stored and classified for header: {total_hdr_cnt} *****')
        self.logger.info(f'***** Total count of .stil.gz files stored and classified for payload: {total_pl_cnt} *****')

        end = time.time()
        elapsed = end - start
        self.logger.info(f'***** Total time elapsed for file storing and classification: {timedelta(seconds=elapsed)} *****')


    def setup_thread_pool(self, dest_dir, df_file_loc):
        csv_name = self.copy_files('info', df_file_loc, dest_dir)
        no_of_procs = multiprocessing.cpu_count() * 4
        file_size = os.stat(csv_name).st_size
        file_size_per_chunk = file_size / no_of_procs
        pool = Pool(no_of_procs)

        for chunk in self.getChunks(csv_name, file_size_per_chunk):
            pool.apply_async(self.worker, (csv_name, chunk))
        pool.join()


    def getChunks(self,file, size):
        f = open(file, 'rb')
        while 1:
            start = f.tell()
            f.seek(int(size), 1)
            s = f.readline()
            yield start, f.tell() - start
            if not s:
                f.close()
                break

    def worker(self, csv_file, chunk):
        f = open(csv_file)
        f.seek(chunk[0])
        for file in f.read(chunk[1]).splitlines():
            src_dest = file.split(",")

            if len(src_dest) == 2:
                self.copy_files_threading(src_dest[0], src_dest[1], 'info')

    def copy_payload(self, dir_path, pl_path_to_copy, df_file_loc):
        df_file_loc = df_file_loc.append({'source': pl_path_to_copy, 'dest': dir_path}, ignore_index=True)
        return df_file_loc
        # res_pl_cpy = copy_files(pl_path_to_copy, dir_path, 'info')
        # dict_rev_cnt[rev] += res_pl_cpy
        # if res_pl_cpy:
        #     logger.info(f'{res_pl_cpy} payload .stil.gz files downloaded successfully.')
        #     logger.info((f'Payload copied from Waipio r1 path.'))
        # return res_pl_cpy


    def copy_payloads_tdf(dict_rev_cnt, dir_path, pl_path_to_copy, row, df_file_loc):
        pl_name = 'tk_atpg_tdf_lpc' + re.search("(lpc)(.*)(_)(.*)(_)", row['Vector']).group(2) + '_slc_'
        pl_zip = pl_name + '*.stil.gz'
        # get a list of paths for all payload slices
        path_pl_zip = os.path.join(pl_path_to_copy, pl_zip)
        list_path_pl_zip = glob.glob(path_pl_zip)
        # copy payload zip files to target folder
        for zip in list_path_pl_zip:
            df_file_loc = df_file_loc.append({'source': zip, 'dest': dir_path}, ignore_index=True)
            #res_pl_cpy += copy_payload(dict_rev_cnt, dir_path, zip)
        return df_file_loc


    def create_file_path(self,dest_dir, payload, row):
        dir_path = os.path.join(dest_dir, self.chip_version)
        folder_ordering = ['Bin Si Revision', 'Block', 'DFT type', 'Vector Type', 'Vector', 'freq mode']
        for folder_name in folder_ordering:
            if folder_name == 'Vector':
                comp_type = re.search("(lpc|lpu)", row[folder_name])[0]
                if (row['DFT type'] == 'SAF'):
                    if re.search("(lpc_se0_|lpu_se0_)(.*)", payload):
                        name, split_name = self.find_value_after_regex(payload, "(lpc_se0_|lpu_se0_)(.*)")
                        dir_path = os.path.join(dir_path, comp_type, 'se0')
                        if name == 'F32':
                            dir_path = os.path.join(dir_path, name, split_name[1])
                        else:
                            if re.search("t$", payload):
                                dir_path = os.path.join(dir_path, 'regular', 't', name)
                            else:
                                dir_path = os.path.join(dir_path, 'regular', 'regular', name)
                    else:
                        name, split_name = self.find_value_after_regex(payload, "(lpc_|lpu_)(.*)")
                        dir_path = os.path.join(dir_path, comp_type, 'regular', name)
                else:
                    full_name = re.search("(lpc_|lpu_)(.*)", row[folder_name]).group(2)
                    name = re.split("_", full_name)[0]
                    dir_path = os.path.join(dir_path, comp_type, name)

            else:
                name = ""
                dir_path = os.path.join(dir_path, row[folder_name])
        return comp_type, dir_path, name


    def find_value_after_regex(self, payload, regex_value):
        full_name = re.search(regex_value, payload).group(2)
        split_name = re.split("_", full_name)
        name = split_name[0]
        return name, split_name


class Generate_Pats():

    def __init__(self, conversion_log_csv_path, logger):

        self.conversion_log_csv_path = conversion_log_csv_path
        self.logger = logger

    def create_folder(self, dir):
        """
        Create the directory if not exists.

        :param dir: str
            directory to create
        """
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
                self.logger.debug(f'Directory created: {dir}')
            except Exception:
                self.logger.exception(f"Error! Could not create directory {dir}")

    def generate_pats_txt(self, pattern_category, vector_type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude = [], pin_group ='OUT', enable_cyc_cnt=1, blocks=[], freq_modes = ['NOM', 'SVS', 'TUR', 'SVSD1']):
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
        :param list_dirs_exclude_full: list. default = []
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
                for block in blocks:
                    path_top_level = os.path.join(dir_pat, block, pattern_category,vector_type)
                    # dir to export PATS.txt to
                    dir_sub = os.path.join(dir_exec, block, pattern_category, vector_type)
                    # prefix for PATS.txt file name
                    pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
            elif pattern_category.lower() in ['int','saf']:
                path_top_level = os.path.join(dir_pat, pattern_category, vector_type)
                dir_sub = os.path.join(dir_exec, mode, pattern_category, vector_type)
                pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

            self.create_folder(dir_sub)

            do_files = []
            for root, dirs, files in os.walk(path_top_level,topdown=True):
                # exclude dirs
                dirs[:] = [d for d in dirs if d not in list_dirs_exclude_full]

                for file in files:
                    if fnmatch.fnmatch(file, '*_XMD.do'):
                        # get abs paths for DO patterns
                        modes = "|".join(freq_modes)
                        modes_pattern = "(.*)(\\\)(" + modes + ")(\\\)(.*)"
                        if re.search(modes_pattern, root):

                            do_file = os.path.join(root,file)
                            do_files.append(do_file)

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

            quo, rem = divmod(len(do_files), lim)
            # set up the number of PATS.txt
            if quo:
                if rem:
                    cnt = quo + 1
                else:
                    cnt = quo
            else:
                cnt = 1

            # # create subdir in execution dir
            # dir_sub = os.path.join(dir_exec,pattern_category,vector_type)
            # create_folder(dir_sub)

            # create individual PATS.txt and folder
            # pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

            for i in range(cnt):

                pats_dir = os.path.join(dir_sub, str(i+1))
                self.create_folder(pats_dir)
                pats_txt_name = pre_fix + str(i+1) + '.txt'
                pats_txt = os.path.join(pats_dir, pats_txt_name)
                # write header
                with open(pats_txt, 'w+') as f:
                    f.write(header + '\n')

                # write patterns
                start = i*lim
                end = (i+1)*lim
                for do_file in do_files[start:end]:

                    do_file_name = os.path.basename(do_file)

                    if enable_cyc_cnt:

                        try:
                            filter = df_conv_log['pattern_name'] == do_file_name
                            cyc_cnt = df_conv_log.loc[filter, 'extracted_cycle_count'].values[0]

                        except Exception as e:
                            print(e)
                            cyc_cnt = 0
                        # else:

                    else:
                        cyc_cnt = 0

                    # path_do_file = Path(do_file)
                    # print(path_do_file)

                    to_write = ','.join(
                        map(str, [do_file, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))
                    with open(pats_txt, 'a+') as f:
                        f.write(to_write + '\n')

            print(f'*** PATS.txt generation completed for {pattern_category} {vector_type}{mode}')


# def main():
#     # global rev
#     # global chip_version
#     # global map_path
#     # global par_vector_path_r1
#     # global py_log_path
#     # global conversion_log_csv_path
#     #
#     # preprocess = Preprocess()
#
#     ##**** 05/26/21. Examples demoed to Kuang ***##
#     ### 1. Store and Classify INT/SAF patterns ###
#     # network drive location to store all pattern zip files
#     # dest = r'\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\waipio'
#
#     # dest = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\test_multi"
#     # pattern_category = r"INT|SAF"
#     # vector_type = r"PROD"
#     #
#     #
#     # # filter patterns
#     # rev = 'r1'
#     # chip_version = 'waipio'
#
#     # rev -> dft type -> vector type -> lpu/lpc -> domain name -> freq mode
#
#     #map_path = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\Automation csv\demo_int_saf.csv"
#     #map_path = r"C:\Users\jianingz\Desktop\freq_mode_fixed_saf.csv"
#
#     # int_saf_map_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\map_files\waipio\waipio_v1_map_test_p1.csv"
#     # int_saf_map_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\map_files\waipio\waipio_v1_map_052621_demo.csv"
#
#     ## source path for patterns ##
#     # waipio
#     # par_vector_path_r1 = r'\\qctdfsrt\prj\qct\chips' + "\\" + chip_version + r'\sandiego\test\vcd' + "\\" + rev + r'_sec5lpe\tester_vcd'  # waipio r1 common path
#
#     ## path to log ##
#     # waipio
#     #py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + "\\" + r"py_log"
#     # py_log_path = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop"
#
#     # conversion_log_csv_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + "\\" + r"\conversion_log"
#     # Uncomment the below func call (store_all_zip_atpg()) to enable store and classification of STIL zip files
#     # preprocess.set_up_logger()
#     # preprocess.store_all_zip_atpg(dest, pattern_category, vector_type)
#
#     ### 2. Generate pats.txt ###
#     # parent directory for DFT patterns, based on SVE-EV100-1 PC
#
#     generate = Generate_Pats()
#     #dir_pat = r"G:\ATPG_CDP\freq_mode_5_updated\waipio\r1_sec5lpe\ATPG"
#     dir_pat = r"G:\ATPG_CDP"
#     # create a folder under the parent directory to host the pats.txt to be generated
#     dir_exec = os.path.join(dir_pat, 'pattern_execution', 'pattern_list')
#     # copy the conversion log name from ev100_vector_conversion.py after the conversion process is finished
#     # log_name = '061021_conv_test_log' # wapio INT conv log
#
#     log_name = '061021_conv_test_log'
#
#     # put 3 patterns in a pats.txt
#     lim = 1
#     pin_group = 'ALL_PINS'
#     # Uncomment the below func call (generate_pats_txt()) to generate pats.txt for pattern batch execution
#     freq_modes = ['SVS', 'NOM', 'TUR', 'SVSD1']
#     #generate.generate_pats_txt(pattern_category,vector_type, dir_pat, dir_exec,log_name,lim, ['5'], pin_group,1, None, freq_modes)


# if __name__ == "__main__":
#     main()
