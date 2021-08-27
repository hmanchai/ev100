import fnmatch
import glob
import logging
import os
import re
import time
from datetime import timedelta, date
from pathlib import Path

import pandas as pd


class AutomaticVectorDebug():
    def set_up_logger(self, py_log_path, py_log_name):
        """
        sets up logger
        :param py_log_path: path for log output
        :type py_log_path: str
        :param py_log_name: file name of log output
        :type py_log_name: str
        :return: logger: to be used throughout preprocessing flow
        """
        # set up logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

        # py_log = os.path.join(py_log_path,'conversion_test.log')
        py_log = os.path.join(py_log_path, py_log_name)
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

    def traverse_levels(self, par_dir, pattern_category, vector_type, logger, output_dir, did_pass,
                        list_dirs_exclude=[]):
        """
        The central function to execute conversion related actions across all levels of dir
        par_dir can be any level of dir as the entry point

        :param par_dir: str
            dir to start traverse from top down
        :param pattern_category: str
            choices are INT, SAF and TDF
        :param vector_type: str
            choice of vector type has PROD or RMA. As project evolves, more choices might come
        :param log_name: str
            conversion log name (w/o .csv extension)
        :param enable_del_zip: bool
            if True, delete zip files after conversion
        :param list_dirs_exclude: list. default = []
            dir of DFT patterns to EXCLUDE from traverse
        """

        dict = {}
        df_log = pd.DataFrame(columns=[".do recompiled", "period_initial", "period_new"])
        if pattern_category == 'TDF':
            # list_attr = ['mode','domain','block','vector_type','pattern_category']
            list_attr = ['mode', 'domain', 'block']
        start = time.time()
        # traverse file structure from top down
        for (root, dirs, files) in os.walk(par_dir, topdown=True):

            # exclude dirs
            dirs[:] = [d for d in dirs if d not in list_dirs_exclude]

            for file in files:
                # find the level of dir containing stil zip files and process
                if fnmatch.fnmatch(file, '*.stil.gz'):
                    if pattern_category.lower() == 'tdf':
                        dict['mode'] = os.path.basename(Path(root))
                        for i, attr in enumerate(list_attr[1:]):
                            dict[attr] = os.path.basename(Path(root).parents[i])
                        logger.info(
                            f"\n**** Currently processing {pattern_category} {vector_type} {dict['block']} {dict['domain']} {dict['mode']} ****")
                    elif pattern_category.lower() in ['int', 'saf']:
                        logger.info(
                            f"\n**** Currently processing {pattern_category} {vector_type} pattern from: {root} ****")
                    # call processing func
                    start_loop = time.time()
                    try:
                        # perform all conversion related actions
                        period_initial, period_new = self.tune_capturing_time(root, logger, did_pass)
                        pattern_files = glob.glob(root + '/**/MBURST*.do', recursive=True)
                        new_row = {".do recompiled": re.search("(.*)(\\\)(.*)$", pattern_files[0]).group(3),
                                   'period_initial': period_initial, 'period_new': period_new}
                        df_log = df_log.append(new_row, ignore_index=True)
                    except Exception:
                        logger.exception('Error! Conversion related actions not finished completely.')
                    end_loop = time.time()
                    elapse_loop = end_loop - start_loop
                    logger.info(
                        f'**** Time elapsed for this pattern processing: {timedelta(seconds=elapse_loop)} ****')
                    break
        today = date.today()
        df_log.insert(0, "date", str(today))
        if os.path.exists(output_dir):
            df_log.to_csv(output_dir, index=False, sep=',', header=False, mode='a')
        else:
            df_log.to_csv(output_dir, index=False, sep=',', header=True, mode='w')
        end = time.time()
        elapse = end - start
        logger.info(f'====>> Total time elapsed for entire process: {timedelta(seconds=elapse)} <<====\n')


    def tune_capturing_time(self, path_stil_files, logger, did_pass):
        period_initial, period_new = self.change_timing(path_stil_files, logger, did_pass)
        compile_err, do_file = self.compile_do_files(path_stil_files, logger)
        return period_initial, period_new


    def change_timing(self, path_stil_files, logger, did_pass):
        """change scan clock period in .h file

        :param logger:
        :type logger:
        :param path_stil_files: str
            directory to STIL patterns
        :param period_new: int
            new scan period
        :return:
            intial scan period in int if successful; 'na' in str in case of errors
        """
        try:
            change_timing = True
            h_file, list_lines, index_line_period, period_initial = self.get_timing(path_stil_files, change_timing,
                                                                                    logger)
            period_new = self.adjust_timing(period_initial, did_pass)
            # edit the line with new timing
            str_new_period_float = '{:.4f}'.format(period_new)
            str_replace = '#define PERIOD ' + str_new_period_float + 'ns ;\n'
            list_lines[index_line_period] = str_replace
            # rewrite TEV_TimeSets.h file
            with open(h_file, 'w') as f:
                f.writelines(list_lines)
            logger.info(
                '{} is updated with a new scan clock period {}ns.'.format(os.path.basename(h_file), period_new))
            return period_initial, period_new
        except Exception:
            logger.exception('Error! Period failed to be changed.')
            return 'na'

    def adjust_timing(self, period_initial, did_pass):
        # if within ev100 limit
        lower_bound = 10

        if period_initial > lower_bound and did_pass:
            return period_initial - 1
        else:
            return period_initial + 1


    def get_timing(self, path_stil_files, change_timing, logger):
        """
        get scan clock period from .h file

        :param logger: 
        :type logger: 
        :param path_stil_files: str
            directory to STIL patterns
        :param change_timing: bool
            default = False. flag to determine if scan freq change is needed
        :return: different returns depending on "change_timing"
        """
        # get a list of .h files
        h_file_list = glob.glob(path_stil_files + '/**/*.h', recursive=True)
        # only one .h file should be present for batch conversion
        try:
            if len(h_file_list) == 1:
                h_file = h_file_list[0]
                # find the initial timing in .h file
                with open(h_file, 'r') as f:
                    list_lines = f.readlines()
                    index_line_period = 0
                    for num, line in enumerate(list_lines):
                        if '#define PERIOD' in line:
                            # print(line)
                            index_line_period = num
                            # print(index_line_period)
                            break
                    match = re.search('PERIOD (\d+)', list_lines[index_line_period], re.IGNORECASE)
                    if match:
                        period_initial = match.group(1)
                        period_initial = int(period_initial)
                        logger.info('Initial scan clock period is {}ns'.format(period_initial))

                    if change_timing:
                        return h_file, list_lines, index_line_period, period_initial
                    else:
                        return period_initial
            else:
                # logger.error(f'Error! {len(h_file_list)} .h files are found')
                raise Exception(f'{len(h_file_list)} .h files are found!')
        except Exception:
            logger.exception('Error! Initial period info cannot be obtained.')
            return 'na'


    def compile_do_files(self, path_stil_files, logger):
        """
        compile .dp files to .do files

        :param path_stil_files: str
            directory to STIL patterns
        :return: int
            non-zero: error happened in compilation; zero: compilation successful
            .do pattern name
        """
        # get a list of all .dp file paths in the subdirectories
        dp_file_list = glob.glob(path_stil_files + '/**/*.dp', recursive=True)

        kw = 'MBURST'
        # set up paths
        path_tsets = os.path.join(path_stil_files, 'device', 'test')
        path_ddc192 = r'C:\"Program Files"\TEV\AXI\Bin\ddc192.exe'

        for dp_file in dp_file_list:
            # only compile the burst .dp file
            if kw in dp_file:
                # create .do pattern and compilation log file names
                do_file = dp_file.replace('.dp', '.do')
                compile_log_file = dp_file.replace('.dp', '.log')

                compile_cmd = path_ddc192 + ' -v -I ' + path_tsets + ' -L ' + compile_log_file + ' -o ' + do_file + ' ' + dp_file
                logger.debug('Compilation command:\n{}\n'.format(compile_cmd))

                logger.info('Starting to compile DO .....')
                start = time.time()
                err = os.system(compile_cmd)
                # print('Compilation error: {}\n'.format(err))
                if err:
                    # print('****** Compilation Has Error! ******\n')
                    logger.error('Error! Compilation NOT Successful.')
                else:
                    # print('****** Compilation Completed ******\n')
                    logger.info('Cool! Compilation Successful.')
                end = time.time()
                elapsed = end - start
                logger.info(f'== Time elapsed for compiling DO: {timedelta(seconds=elapsed)} ==')
                do_file_base = os.path.basename(do_file)
                # once burst pattern compiled, break out of for loop
                break
        # return dict_compile
        return err, do_file_base


def main():
    auto_debug = AutomaticVectorDebug()
    chip_version = 'waipio'
    rev = 'r1'
    par_dir = r"C:\Users\hmanchai\Desktop\test"
    pattern_category = "SAF"
    vector_type = "PROD"

    updated_date_time = time.strftime("%Y%m%d-%H%M%S")
    py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + chip_version + "\\" + rev + r'\py_log'
    py_log_name = 'py_conversion_' + updated_date_time + '.log'
    output_log = r"C:\Users\hmanchai\Desktop\test\timing_update.csv"
    did_pass = True
    logger = auto_debug.set_up_logger(py_log_path, py_log_name)
    auto_debug.traverse_levels(par_dir, pattern_category, vector_type, logger, output_log, did_pass)


if __name__ == "__main__":
    main()
