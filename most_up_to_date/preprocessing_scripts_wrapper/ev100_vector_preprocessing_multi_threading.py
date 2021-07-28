import argparse
import fnmatch
import glob
import multiprocessing
import os
import re
import subprocess
import time
from datetime import timedelta
from preprocess_init import Logger
from preprocess_init import CreateFolder

import pandas as pd
from gevent import monkey

monkey.patch_all()

from gevent.pool import Pool



class Preprocess():
    """
    Preprocessing script retrieves STIL zip files and combines header and payload pairs into unique
    file path based on inputted mapping file that aligns with requirements document
    """

    # C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\ev100_automation>C:\Users\rpenmatc\AppData\Local\Programs\Python\Python37\python.exe
    # "C:/Users/rpenmatc/OneDrive - Qualcomm/Desktop/ev100_automation/most_up_to_date/preprocessing_scripts_wrapper/ev100_vector_preprocessing_multi_threading.py"
    # -rev r1 -chip_version waipio -pattern_category INT  -vector_type PROD -dest C:\Users\rpenmatc -map_path C:\Users\rpenmatc\demo_int_saf.csv

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
        self.folder_ordering = ['Bin Si Revision', 'Block', 'DFT type', 'Vector Type', 'Vector', 'freq mode']
        self.make_folder = CreateFolder()

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

    def load_filter_map(self):
        """
        Load and filter map file.
            choice of vector type has PROD or RMA. As project evolves, more choices might come
        :return: pandas dataframe containing vector header and payload mapping
        """

        df_map = pd.read_csv(self.map_path)
        # filter out non-translated and non-available patterns
        df_map = df_map[df_map['DFT type'].str.match(self.pattern_category)]
        df_map = df_map[df_map['Vector Type'].str.match(self.vector_type)]
        return df_map

    def copy_files(self, df_file_loc, dir_path):
        """
        Copy source and destination of files stored in dataframe to csv file so multithreading can be preformed in copying process

        :param df_file_loc: DataFrame
            dataframe containing source and destination of each file (header and payload)
        :param dir_path: str
            directory of destination to copy source files to

        :return: temp_csv: str
            temp_csv contains source and destination of files to be copied

        """
        temp_csv = os.path.join(dir_path, 'temp.csv')
        csv_file = open(temp_csv, "w")
        df_file_loc.to_csv(temp_csv, index=None, sep=',', header=False, mode='a')
        csv_file.close()
        return temp_csv

    def copy_files_threading(self, path_to_file, dest_dir, log_level):
        """
        Copy files to target directory, through pycopier
        # python -m pip install pycopier
        This method is called through multithreading from the worker

        :param path_to_file: str
            directory to source files to copy
        :param dest_dir: str
            directory of destination to copy source files to
        :param log_level: str
            defines the level of logger
        """
       # cmd = "pycopier " + "\"" + path_to_file + "\"" + " " + "\"" + dest_dir + "\""
        cmd = "python -m pycopier " + "\"" + path_to_file + "\"" + " " + "\"" + dest_dir + "\""
        subprocess.call(cmd, shell=True)
        if log_level == 'info':
            self.logger.info(f'File copied: {os.path.basename(path_to_file)}')
        elif log_level == 'debug':
            self.logger.debug(f'File copied: {os.path.basename(path_to_file)}')

    def store_all_zip_atpg(self):
        """
        :param dest_dir: base destination directory for all copied files to go into respective filepath
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
        df_map = self.load_filter_map()
        # print(df_map)
        df_file_loc = pd.DataFrame(columns=['source', 'dest'])
        # set up pattern source path

        # set up counter
        total_hdr_cnt = 0
        total_pl_cnt = 0
        res_hdr_cpy = 0
        res_pl_cpy = 0
        dict_rev_cnt = {self.rev: 0}

        start = time.time()
        self.logger.info(
            f"***** Starting .stil.gz files storing and classification for {self.pattern_category} {self.vector_type} *****")
        # TODO: optimize this looping
        # looping by dataframe rows
        for index, row in df_map.iterrows():
            df_file_loc, res_hdr_cpy, res_pl_cpy, start_inner = self.determine_src_dest(self.dest, df_file_loc,
                                                                                        res_hdr_cpy, res_pl_cpy, row)
        #  self.folder_ordering = ['Bin Si Revision', 'Block', 'DFT type', 'Vector Type', 'Vector', 'freq mode']

        self.setup_thread_pool(self.dest, df_file_loc)

        dict_rev_cnt[self.rev] += res_hdr_cpy

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
        self.logger.info(
            f'***** Total time elapsed for file storing and classification: {timedelta(seconds=elapsed)} *****')

    def determine_src_dest(self, dest_dir, df_file_loc, res_hdr_cpy, res_pl_cpy, row):
        """
        :param dest_dir: str
            base destination directory that all filepaths for STIL will contain
        :param df_file_loc: DataFrame
            will store list of source and destination for each STIL file to be copied to and from
        :param res_hdr_cpy: int
            keep count of header files to be copied
        :param res_pl_cpy: int
            keep count of payload files to be copied
        :param row: DataFrame row
            row of DFT vector mapping list with all necessary info to create destination filepath
        """
        path_atpg_r1 = os.path.join(self.par_vector_path_r1, row['Block'], 'SRC')
        pl = re.search("(tk_atpg)(.*)", row['payload']).group(2)
        hdr = row['header']
        # copy header and payload zip file
        hdr_zip = hdr + '.stil.gz'
        hdr_path_to_copy = os.path.join(path_atpg_r1, hdr_zip)
        # split using payload delimiter |
        payload_list = re.split("\\|", pl)
        if row['DFT type'] == "TDF":
            payload_list = [""]
        for payload in payload_list:
            if row['DFT type'] != "TDF":
                pl_zip = 'tk_atpg' + payload + '.stil.gz'
                pl_path_to_copy = os.path.join(path_atpg_r1, pl_zip)
            else:
                pl_path_to_copy = path_atpg_r1

            # folder_ordering = ['Block', 'Bin Si Revision', 'DFT type', 'Vector Type', 'Vector', 'freq mode']
            comp_type, dir_path, name = self.create_file_path(dest_dir, payload, row, hdr)
            self.make_folder.create_folder(dir_path)

            start_inner = time.time()

            self.logger.info(
                f"*** Currently storing .stil.gz files for {self.pattern_category} {self.vector_type} {comp_type} {name} {row['freq mode']} ***")
            self.logger.info(
                f"*** Currently storing .stil.gz files for {self.pattern_category} {self.vector_type} {comp_type} {name} {row['freq mode']} ***")

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
        return df_file_loc, res_hdr_cpy, res_pl_cpy, start_inner

    def setup_thread_pool(self, dest_dir, df_file_loc):
        """
        creates csv containing source and destination for each file to be copied
        creates pool size based on number of cpu count
        based on these numbers csv file is divided into chunks that threads will work on
        call worker to execute copying

        :param dest_dir: str
            Base destination directory that all filepaths begin
        :param df_file_loc: DataFrame
            Dataframe that contains all source and destination locations for each file to be copied
        """
        csv_name = self.copy_files(df_file_loc, dest_dir)
        no_of_procs = multiprocessing.cpu_count() * 4
        file_size = os.stat(csv_name).st_size
        file_size_per_chunk = file_size / no_of_procs
        pool = Pool(no_of_procs)

        for chunk in self.getChunks(csv_name, file_size_per_chunk):
            pool.apply_async(self.worker, (csv_name, chunk))
        pool.join()

    def getChunks(self, file, size):
        """
        divide file into chunks that threads can work on to maximize efficiency

        :param file: csv file
            csv file containing source and destinations
        :param size: int
            size of file
        """
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
        """
        find chunk assigned and begins work by calling method to copy with proper inputs

        :param csv_file: filepath
        :param chunk: start, f.tell() - start
        """
        f = open(csv_file)
        f.seek(chunk[0])
        for file in f.read(chunk[1]).splitlines():
            src_dest = file.split(",")

            if len(src_dest) == 2:
                self.copy_files_threading(src_dest[0], src_dest[1], 'info')

    def copy_payload(self, dir_path, pl_path_to_copy, df_file_loc):
        """
        add payload source and destination
        :param dir_path: str
            destination of payload file
        :param: pl_path_to_copy: str
            source of payload file
        :param df_file_loc
            Dataframe to store all sources and destinations
        :return df_file_loc: DataFrame
            Dataframe updated with new source and destination of payload to be copied
        """
        df_file_loc = df_file_loc.append({'source': pl_path_to_copy, 'dest': dir_path}, ignore_index=True)
        return df_file_loc

    def copy_payloads_tdf(self, dir_path, pl_path_to_copy, row, df_file_loc):
        """
        add all payloads for tdf pattern_category
        :param dir_path: str
            destination of payload file
        :param pl_path_to_copy: str
            source of payload file
        :param row: Dataframe row
            row of dataframe to get Vector name to find all payloads for given header/vector
        :param df_file_loc
            Dataframe to store all sources and destinations
        :return df_file_loc: DataFrame
            Dataframe updated with new source and destination of payload to be copied
        """
        pl_name = 'tk_atpg_tdf_lpc' + re.search("(lpc)(.*)(_)(.*)(_)", row['Vector']).group(2) + '_slc_'
        pl_zip = pl_name + '*.stil.gz'
        # get a list of paths for all payload slices
        path_pl_zip = os.path.join(pl_path_to_copy, pl_zip)
        list_path_pl_zip = glob.glob(path_pl_zip)
        # copy payload zip files to target folder
        for zip in list_path_pl_zip:
            df_file_loc = df_file_loc.append({'source': zip, 'dest': dir_path}, ignore_index=True)
            # res_pl_cpy += copy_payload(dict_rev_cnt, dir_path, zip)
        return df_file_loc

    def create_file_path(self, dest_dir, payload, row, header):
        """
        Parses through ['Block', 'Bin Si Revision', 'DFT type', 'Vector Type', 'Vector', 'freq mode'] information for each vector
        to determine unique filepath for destination of each header/payload group
        :param dest_dir: str
            base destination directory for all files
        :param payload: str
            each payload name received from mapping list
        :param row: DataFrame row
            row data such as ['Bin Si Revision', 'Block', 'DFT type', 'Vector Type', 'Vector', 'freq mode'] to parse through
            to determine unique filepath for each header/payload grouping
        """
        dir_path = os.path.join(dest_dir, self.chip_version)
        for folder_name in self.folder_ordering:
            if folder_name == 'Vector':
                comp_type = re.search("(lpc|lpu)", row[folder_name])[0]
                if (row['DFT type'] == 'SAF'):
                    if re.search("(lpc_se0_|lpu_se0_)(.*)", payload):
                        name, split_name = self.find_value_after_regex(payload, "(lpc_se0_|lpu_se0_)(.*)")
                        vector_name, split = self.find_value_after_regex(header, "(lpc_se0_|lpu_se0_)(.*)")
                        dir_path = os.path.join(dir_path, comp_type, 'se0')
                        if name == 'F32':
                            dir_path = os.path.join(dir_path, name, vector_name)
                        else:
                            if re.search("_t$", payload):
                                dir_path = os.path.join(dir_path, 'regular', 'topoff_t', vector_name)
                            elif re.search("_t_ts$", payload):
                                dir_path = os.path.join(dir_path, 'regular', 'topoff_t_ts', vector_name)
                            elif re.search("(.*)(topoff)(.*)", payload):
                                dir_path = os.path.join(dir_path, 'regular', 'topoff', vector_name)
                            else:
                                dir_path = os.path.join(dir_path, 'regular', 'regular', vector_name)
                    else:
                        vector_name, split = self.find_value_after_regex(header, "(lpc_se0_|lpu_se0_)(.*)")
                        dir_path = os.path.join(dir_path, comp_type, 'regular', vector_name)
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

def main():
    updated_date_time = time.strftime("%Y%m%d-%H%M%S")
    updated_date = time.strftime("%Y%m%d")
    py_log_name = 'py_conversion_' + updated_date_time + '.log'



    parser = argparse.ArgumentParser(description='Execute preprocessing script')
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

    args = parser.parse_args()

    py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r'\py_log'
    par_vector_path_r1 = r'\\qctdfsrt\prj\qct\chips' + "\\" + args.chip_version + r'\sandiego\test\vcd' + "\\" + args.rev + r'_sec5lpe\tester_vcd'

    logger = Logger().set_up_logger(py_log_path, py_log_name)

    preprocess = Preprocess(args.rev, args.chip_version, py_log_path, py_log_name, args.pattern_category, args.vector_type, updated_date_time, logger, args.dest,
                                                                               args.map_path, par_vector_path_r1)
    preprocess.store_all_zip_atpg()

if __name__ == '__main__':
    main()