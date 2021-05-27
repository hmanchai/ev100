import os
import glob
import shutil
# from distutils.dir_util import copy_tree
import pandas as pd
import re
# import psutil
import csv
import gzip
import fnmatch
import time
from datetime import timedelta
import calendar
import logging
# import subprocess
from pathlib import Path

from ev100_vector_preprocessing_lahaina import create_folder, load_filter_map


# global variable
py_log_name = 'py_conversion_052721_test.log'

## mapping files ##
# tdf_map_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\map_files\lahaina\Lahaina_V2p1_TDF_mapping_sheet.csv"
int_saf_map_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\map_files\waipio\waipio_v1_map_052621_demo.csv"

## seed files ##
velocity_dft_cfg_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\velocity_cfg\waipio\waipio_WY_dft_universal_v1.cfg"
patch_timesets_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\waipio\patch_timesets.txt"
patch_timesets_50mhz_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\lahaina\patch_timesets_50MHz.txt" #TODO Roshni: need to update after waipio timesets methdology is avaialbe from TEV

## paths to log files ##
conversion_log_csv_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\waipio\r1\conversion_log"
py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\waipio\r1\py_log"

## path to network drive ##
net_loc = r'\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\waipio\r1'

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


def copy_all_zip(pattern_category, vector_type, local_loc):
    """
    Copy all zip files at vector_type level dir from an intermediate location (e.g. network drive) to local PC

    :param pattern_category: str
        choices are INT, SAF and TDF
    :param vector_type: str
        choice of vector type has PROD or RMA. As project evolves, more choices might come
    :param local_loc: str
        local dir to copy zip files to
    """
    dir_orig = os.path.join(net_loc, pattern_category, vector_type)
    local_dir = os.path.join(local_loc, pattern_category, vector_type)
    # create_folder(local_dir)

    start = time.time()
    logger.info(f'**** File transfer starts for {pattern_category} {vector_type} ****')
    logger.info(f'src dir: {dir_orig}, dest dir: {local_dir} ')
    try:
        shutil.copytree(dir_orig, local_dir)
    except FileExistsError:
        logger.exception(f'Error! Please check the content in this existing path :{dir_orig}.')
    else:
        end = time.time()
        elapsed = end - start
        logger.info(f'**** Total time elapsed for file transfer: {timedelta(seconds=elapsed)} ****')

# def copy_zip(pattern_category, vector_type, local_loc, dir_level, dir_name):
#     """
#     Copy zip files from an intermediate location (e.g. network drive) to local PC with user to determine which level of dir to copy
#
#     :param pattern_category: str
#         choices are INT, SAF and TDF
#     :param vector_type: str
#         choice of vector type has PROD or RMA. As project evolves, more choices might come
#     :param local_loc: str
#         local dir to copy zip files to
#     :param dir_level: str
#         the level of dir, which is determined by the level of classification in mapping file, to copy zip files from
#     :param dir_name: str
#
#     """
#
#     # pattern category: 'INT', 'SAF', 'TDF'
#     dir_pattern_type = os.path.join(net_loc, pattern_category)
#     # vector_type: 'PROD','RMA'
#     dir_vector_type = os.path.join(dir_pattern_type,vector_type)
#     # block = 'TDF_ATPG_CPU' for TDF
#     dir_block = os.path.join(dir_vector_type,dir_name)
#     # domain = 'apssf139f254'
#     dir_domain = os.path.join(dir_block,dir_name)
#
#     dict_dir_level = {'pattern_type': dir_pattern_type, 'vector_type': dir_vector_type, 'block': dir_block, 'domain': dir_domain}
#     dir_orig = dict_dir_level[dir_level]
#
#     local_dir = os.path.join(local_loc,dir_name)
#     start = time.time()
#     logger.info(f'**** File transfer starts for {pattern_category} {vector_type}: src:{dir_orig}  dest:{local_dir} ****')
#     # print('File copy ongoing.....')
#     # shutil.copytree(dir_orig, local_dir)
#
#     try:
#         shutil.copytree(dir_orig, local_dir)
#     except FileExistsError:
#         logger.exception(f'Error! Please check the content in this existing path :{dir_orig}.')
#     else:
#         end = time.time()
#         # print('File copy completed')
#         elapsed = end - start
#         logger.info(f'**** Total time elapsed for file transfer: {timedelta(seconds=elapsed)} ****')
#


def traverse_levels(par_dir,pattern_category,vector_type, log_name, enable_del_zip, list_dirs_exclude=[]):
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
    if pattern_category == 'TDF':
        # list_attr = ['mode','domain','block','vector_type','pattern_category']
        list_attr = ['mode','domain','block']
    start = time.time()
    # traverse file structure from top down
    for (root,dirs,files) in os.walk(par_dir,topdown=True):
        # exclude dirs
        dirs[:] = [d for d in dirs if d not in list_dirs_exclude]

        for file in files:
            # find the level of dir containing stil zip files and process
            if fnmatch.fnmatch(file,'*.stil.gz'):
                if pattern_category.lower() == 'tdf':
                    dict['mode'] = os.path.basename(Path(root))
                    for i, attr in enumerate(list_attr[1:]):
                        dict[attr] = os.path.basename(Path(root).parents[i])
                    logger.info(f"\n**** Currently processing {pattern_category} {vector_type} {dict['block']} {dict['domain']} {dict['mode']} ****")
                elif pattern_category.lower() in ['int','saf']:
                    logger.info(
                        f"\n**** Currently processing {pattern_category} {vector_type} pattern from: {root} ****")
                # call processing func
                start_loop = time.time()
                try:
                    # perform all conversion related actions
                    convert_all_pats(root, pattern_category, vector_type, log_name, enable_del_zip)
                except Exception:
                    logger.exception('Error! Conversion related actions not finished completely.')
                end_loop = time.time()
                elapse_loop = end_loop - start_loop
                logger.info(f'**** Time elapsed for this pattern processing: {timedelta(seconds=elapse_loop)} ****')
                break
    end = time.time()
    elapse = end - start
    logger.info(f'====>> Total time elapsed for entire process: {timedelta(seconds=elapse)} <<====\n')


def convert_all_pats(path_stil_files, pattern_category, vector_type, log_name, enable_del_zip):
    """
    perform all conversion related actions.

    :param path_stil_files: str
        directory to STIL patterns
    :param pattern_category: str
        choices are INT, SAF and TDF
    :param vector_type: str
        choice of vector type has PROD or RMA. As project evolves, more choices might come
    :param log_name: str
        conversion log name (w/o .csv extension)
    :param enable_del_zip: bool
        if True, delete zip files after conversion
    """

    # unzip STIL files, func has internal logger
    unzip_result = unzip_n_rename(path_stil_files)
    if not unzip_result:
        logger.error('Error! Unzipping fails, so no further steps will be executed.')
    else:
        # copy Velocity CFG file to the specified dir
        copy_cfg(path_stil_files, pattern_category)
        # modify Velocity CFG to add BURST block
        modify_cfg(path_stil_files, pattern_category)
        # convert STIL to DP, func has internal logger and timer
        conv_result = convert_stil_files(path_stil_files,pattern_category)
        if not conv_result:
            logger.error('Error! Conversion fails, so no further steps will be executed.')
        else:
            try:
                # # screen corners to determine if period adjustment is needed
                # change_period = screen_mode(path_stil_files)
                # if change_period:
                #     new_period = 16
                #     period_initial = change_timing(path_stil_files,new_period)
                # else:
                #     new_period = 'na'
                #     period_initial = get_timing(path_stil_files)

                # FOR NOW, for TDF patterns, change timing to 16ns regardless
                if pattern_category.lower() == 'tdf':
                    new_period = 16
                # for INT, SAF, change timing to 20ns (50MHz)
                elif pattern_category.lower() in ['int','saf']:
                    new_period = 20
                change_period = True
                period_initial = change_timing(path_stil_files, new_period)

                # extract cycle count from DP
                cyc_cnt = extract_cycle_count(path_stil_files)
                logger.info(f'Extracted cycle count is {cyc_cnt}')
                # add pingroup info to .h file
                # TODO: temporarily comment out for demo on 5/26/21 until waipio patch files are fully prepared
                #patch_timesets_header(path_stil_files, pattern_category)
                # remove extra pingroups from slc combination
                remove_extra_pingroup(path_stil_files)
                # compile DP to DO, func has internal logger and timer
                compile_err, do_file = compile_do_files(path_stil_files)
                # log final DO pattern info to csv
                log_conversion_info(path_stil_files,pattern_category,vector_type,compile_err,do_file,change_period,period_initial,new_period,cyc_cnt,log_name)

            except Exception:
                logger.exception('Error! Conversion related actions not finished completely.')
            else:
                if not compile_err: # in case compilation fails but no traceback error returned
                    logger.info('All conversion related actions completed.')
                if enable_del_zip:
                    # delete ZIP
                    del_zip(path_stil_files)
def temp_recompile(path_stil_files):
    """
    For temporary use only: to remoe extra pin groups and re-compile patterns

    :param path_stil_files: str
        directory to STIL patterns
    """
    try:
        remove_extra_pingroup(path_stil_files)
        compile_err, do_file = compile_do_files(path_stil_files)
    except Exception:
        logger.exception('Error! Pingroup removal and re-compilation actions not finished completely.')
    else:
        if not compile_err:  # in case compilation fails but no traceback error returned
            logger.info('Pingroup removal and re-compilation actions completed.')

def unzip_n_rename(path_stil_files):
    """
    unzip .gz files and match .stil file names to .gz file names
    NOTE: double unzipping is fine, and will just overwrite the previous unzipped files

    :param path_stil_files: str
        directory to STIL patterns
    :return: bool
        1 if successful, 0 in case of errors
    """
    try:
        # grab names of all .gz zip files and save to a list
        zip_file_path = os.path.join(path_stil_files, '*.stil.gz')
        list_zip_files = glob.glob(zip_file_path)
        # sort alphanumerically
        list_zip_files_sorted = sorted_alphanumeric(list_zip_files)
        if not list_zip_files:
            raise FileNotFoundError("No .gz zip file exists in this directory: {}\n".format(path_stil_files))
        logger.info(f'{len(list_zip_files_sorted)} .gz zip files exist in the directory : {path_stil_files}')
        # print(*list_zip_files_sorted, sep='\n')

        # unzip and name .stil file to match .gz file
        for zip_file in list_zip_files:
            stil_file = os.path.splitext(zip_file)[0]
            with gzip.open(zip_file,'rb') as f_in:
                with open(stil_file,'wb') as f_out:
                    shutil.copyfileobj(f_in,f_out)
        return 1
    except FileNotFoundError as e:
        # print(e)
        logger.error(e)
        return 0
    # more general exceptions
    except Exception as e:
        logger.error(e)
        return 0

def copy_cfg(dest_dir, pattern_category):
    """
    copy seed CFG file to pattern directory

    :param dest_dir: str
        destination directory to copy CFG file to
    :param pattern_category: str
        choices are INT, SAF and TDF
    """
    if pattern_category.lower() in ('int','saf','tdf'):
        shutil.copy(velocity_dft_cfg_path, dest_dir)
    elif pattern_category.lower() == 'mbist':
        shutil.copy(velocity_dft_cfg_path, dest_dir) #TODO: change to mbist CFG

def generate_cfg_path(path_stil_files,pattern):
    """
    generate path to cfg file in each individual pattern folder

    :param path_stil_files: str
        directory to STIL patterns
    :param pattern: str
        current choices are INT,SAF,TDF and MBIST
    :return: str
        generated directory to cfg file
    """

    if pattern.lower() in ('int','saf','tdf'):
        # cfg = os.path.join(path_stil_files, "lahaina_WCY_dft_universal.cfg")
        cfg = os.path.join(path_stil_files, "waipio_WY_dft_universal_v1.cfg") #TODO Roshni: replace hardcoding of cfg file name
    elif pattern.lower() == 'mbist':
        cfg = os.path.join(path_stil_files, "MBIST.cfg")
    return cfg

def sorted_alphanumeric(data):
    """sort alphanumerically. Developed to order TDF payload slice numbers correctly, as regular sort didn't work"""
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(data, key=alphanum_key)

def modify_cfg(path_stil_files, pattern_category):
    """
    modify velocity cfg file by adding BURST section

    :param path_stil_files: str
        directory to STIL patterns
    :param pattern_category: str
        choices are INT, SAF and TDF
    """
    cfg = generate_cfg_path(path_stil_files,pattern_category)

    if os.path.exists(cfg):
        # grab paths of all STIL files and save to a list
        stil_file_path = os.path.join(path_stil_files, '*.stil')
        list_stil_path = glob.glob(stil_file_path)
        if not list_stil_path:
            logger.error(f'Error! This directory {path_stil_files} has no STIL files, and hence CFG file is not modified')
        else:
            # sort list_stil_path alphanumerically
            list_stil_path_sorted = sorted_alphanumeric(list_stil_path)
            # empty list to hold payload names
            list_pl_name = []
            for stil_path in list_stil_path_sorted:
                stil_basename = os.path.basename(stil_path)
                # print(stil_basename)
                # identify header and payload
                if pattern_category.lower() == 'tdf':
                    if fnmatch.fnmatch(stil_basename,'*_slc_*'):
                        list_pl_name.append("\n  " + os.path.splitext(stil_basename)[0])
                    else:
                        hdr_name = os.path.splitext(stil_basename)[0]

                elif pattern_category.lower() in ['int','saf']:
                    if fnmatch.fnmatch(stil_basename,'*_ts.stil'):
                        hdr_name = os.path.splitext(stil_basename)[0]
                        # print('hdr:', hdr_name)
                    else:
                        pl_name = os.path.splitext(stil_basename)[0]
                        # print('pl:',pl_name)

            if pattern_category.lower() == 'tdf':
                #grab pattern name from map file
                df_map = pd.read_csv(tdf_map_path)
                #for TDF, header alone is sufficient to identify pattern name in map file
                pattern_name = df_map.loc[df_map['Header'] == hdr_name, 'Pattern'].values[0]
                # add BURST section to the end of CFG file; NOTE: header needs to be listed above payloads!
                list_lines = ["\nBURST  " + pattern_name, "\n  " + hdr_name] + list_pl_name + ["\nEND BURST"]
            elif pattern_category.lower() in ['int','saf']:
                df_map = pd.read_csv(int_saf_map_path)
                #for INT/SAF, both header and payload are needed to identify pattern name in map file
                filter = (df_map['Header vector name'] == hdr_name) & (df_map['Payload vector name'] == pl_name)
                pattern_name = df_map.loc[filter, 'Pattern name'].values[0]
                # add BURST section to the end of CFG file; NOTE: header needs to be listed above payloads!
                list_lines = ["\nBURST  " + pattern_name, "\n  " + hdr_name, "\n  " + pl_name, "\nEND BURST"]

            with open(cfg,'a') as f:
                f.writelines(list_lines)
    else:
        logger.error('Error! No correct CFG file is found! Please check the directory.')

def convert_stil_files(path_stil_files, pattern_category):
    """
    convert stil files to .dp files

    :param path_stil_files: str
        directory to STIL patterns
    :param pattern_category: str
        choices are INT, SAF and TDF
    :return: bool
        1 if successful; 0 in case of errors
    """
    cfg = generate_cfg_path(path_stil_files, pattern_category)

    # check if velocity cfg exists in the dir
    if os.path.exists(cfg):
        # grab names of all STIL files and save to a list
        stil_file_path = os.path.join(path_stil_files, '*.stil')
        list_stil_files = glob.glob(stil_file_path)

        if not list_stil_files:
            logger.error(f'This directory {path_stil_files} has no STIL files, and hence conversion is not performed')
            return 0
        else:
            logger.info(f'{len(list_stil_files)} STIL files exist in the directory: {path_stil_files}')
            # sort list_stil_path alphanumerically
            list_stil_files_sorted = sorted_alphanumeric(list_stil_files)
            # print(*list_stil_files_sorted, sep='\n')
            list_stil_basename_sorted = list(map(lambda x: os.path.basename(x), list_stil_files_sorted))

            # velocity path
            velocity_root = r'C:\AllianceATE\bin' # velocity V8.1.0.0
            velocity_path = os.path.join(velocity_root,'velocity.exe -STILtoTEV')
            # attributes for velocity setting
            # veloctiy_setting = '+o2 +n +x1 +e2 +S +c'
            # veloctiy_setting = '+o2 +n +x1 +e2 +S' #+S enables scan mode
            veloctiy_setting = '+o2 +n +x1 +e2'

            # print('\n****** Conversion Begins ******\n')
            # change cwd to STIL dir
            os.chdir(path_stil_files)
            # # command to change dir
            # cmd_cd = 'cd ' + path_stil_files + '\n'
            # command to run
            # cmd_conv = velocity_path + ' ' + cfg + ' ' + veloctiy_setting
            cmd_conv = velocity_path + ' ' + os.path.basename(cfg) + ' ' + veloctiy_setting
            for stil_file in list_stil_basename_sorted:
                cmd_conv = cmd_conv + ' ' + stil_file
            # print('Conversion command:\n{}'.format(cmd_conv))

            # create a batch file to hold conversion command
            conv_bat = os.path.join(path_stil_files,'conversion.bat')
            with open(conv_bat, 'w') as f:
                # f.write(cmd_cd)
                f.write(cmd_conv)

            logger.info('Starting to convert STIL to DP .....')
            start = time.time()
            conv_result = os.system(conv_bat)
            logger.info(f'conversion_result: {conv_result}')
            end = time.time()
            elapsed = end - start
            logger.info(f'== Time elapsed for converting STIL to DP: {timedelta(seconds=elapsed)} ==')

            # check if all individual STIL files are converted, and a combined DP is burst
            list_dp_files = glob.glob(path_stil_files + '/**/*.dp', recursive=True)
            if len(list_dp_files) == (len(list_stil_files) + 1):
                # print('\n****** Conversion Completed ******\n')
                logger.info('Cool! Conversion Successful')
                return 1
            else:
                # print('\n****** Conversion NOT Successful ******\n')
                logger.error('Error! Conversion NOT Successful')
                return 0

            # # execute conversion
            # conv_result = os.system(cmd_conv)
            # print(f'\n****conversion result: {conv_result}\n')
            # # This flag seems questionable, might need to check for DP file for actual conversion result
            # if conv_result == 1: # Velocity error "The command line is too long." will yield a conv_result of 1
            #     print('\n****** Conversion Failed ******\n')
            #     # return a flag
            #     return 0
            # else: # a succesful conversion yield a conv_result of -1
            #     print('\n****** Conversion Completed ******\n')
            #     return 1
    else:
        logger.error('Error! No correct CFG file is found, so conversion cannot be done! Please check the directory.')
        return 0

def screen_mode(path_stil_files):
    """
    screen voltage mode to determine if scan freq needs change due to the restriction that EV100 freq limit is 100MHz

    :param path_stil_files: str
        directory to STIL patterns
    :return: bool
    """
    mode = os.path.basename(path_stil_files)
    if mode == 'LSVS':
        change_period = False
    else:
        change_period = True
    return change_period

def get_timing(path_stil_files, change_timing=False):
    """
    get scan clock period from .h file

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


def change_timing(path_stil_files, period_new):
    """change scan clock period in .h file

    :param path_stil_files: str
        directory to STIL patterns
    :param period_new: int
        new scan period
    :return:
        intial scan period in int if successful; 'na' in str in case of errors
    """
    try:
        h_file, list_lines, index_line_period, period_initial = get_timing(path_stil_files, change_timing=True)
        # edit the line with new timing
        str_new_period_float = '{:.4f}'.format(period_new)
        str_replace = '#define PERIOD ' + str_new_period_float + 'ns ;\n'
        list_lines[index_line_period] = str_replace
        # rewrite TEV_TimeSets.h file
        with open(h_file, 'w') as f:
            f.writelines(list_lines)
        logger.info('{} is updated with a new scan clock period {}ns.'.format(os.path.basename(h_file), period_new))
        return period_initial
    except Exception:
        logger.exception('Error! Period failed to be changed.')
        return 'na'

def compile_do_files(path_stil_files):
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
    path_ddc192 = "\"C:\Program Files\TEV\AXI\Bin\ddc192.exe\""

    for dp_file in dp_file_list:
        # only compile the burst .dp file
        if kw in dp_file:
            # create .do pattern and compilation log file names
            do_file = dp_file.replace('.dp','.do')
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


# def extract_cycle_count_mod(path_stil_files):
#     """extract cycle count info from .dp files"""
#
#     dp_file_list = glob.glob(path_stil_files + '/**/*.dp', recursive=True)
#     kw = 'MHz'
#
#     for dp_path in dp_file_list:
#         if kw in dp_path:
#             # with open(dp_path, 'r') as f:
#             #     for line in f:
#             #         pass
#             #     last_line = line
#
#             # last line of burst DP contains cycle count info
#             # seek to the end of the file, and move backwards to find a new line
#             # NOTE: avoid f.readlines() to flood the memory!
#             with open(dp_path, 'rb') as f:
#                 f.seek(-2, os.SEEK_END)
#                 while f.read(1) != b'\n':
#                     f.seek(-2, os.SEEK_CUR)
#                 last_line = f.readline().decode()
#
#             # find cycle count
#             match = re.search('Cycles:(\d+)', last_line, re.IGNORECASE)
#             if match:
#                 cycle_count = int(match.group(1))
#             else:
#                 print('No cycle count can be found!\n')
#                 cycle_count = 0
#             break
#     return cycle_count


def extract_cycle_count(path_stil_files):
    """
    extract cycle count info from .dp files

    :param path_stil_files: str
        directory to STIL patterns
    :return: int
        vector cycle count
    """

    dp_file_list = glob.glob(path_stil_files + '/**/*.dp', recursive=True)
    kw = 'MBURST'

    for dp_path in dp_file_list:
        if kw in dp_path:
            # with open(dp_path, 'r') as f:
            #     for line in f:
            #         pass
            #     last_line = line

            # last line of burst DP contains cycle count info
            # seek to the end of the file, and move backwards to find a new line
            # NOTE: avoid f.readlines() to flood the memory!
            with open(dp_path, 'rb') as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                last_line = f.readline().decode()

            # find cycle count
            match = re.search('Cycles:(\d+)', last_line, re.IGNORECASE)
            if match:
                cycle_count = int(match.group(1))
            else:
                print('No cycle count can be found!\n')
                cycle_count = 0
            break
    return cycle_count

def patch_timesets_header(path_stil_files, pattern_category):
    """
    modify edgeset for INT, SAF
    patch test_TimeSets.h with pingroup IN,OUT,CLK

    :param path_stil_files: str
        directory to STIL patterns
    :param pattern_category: str
        choices are INT, SAF and TDF
    """
    path_timesets = os.path.join(path_stil_files,'device','test','test_TimeSets.h')
    if os.path.exists(path_timesets):
        if pattern_category.lower() in ['int','saf']: #optimize edgeset timing for 1.25ns resolution for 50MHz scan freq
            # grab edgeset patch from a template
            with open(patch_timesets_50mhz_path, 'r') as f:
                patch_50mhz = f.readlines()
            # remove original edgeset info from .h file and add in new edgeset info
            with open(path_timesets, 'r+') as f:
                lines = f.readlines()
                new_lines = [x for x in lines if '.edgeset' not in x]
                # find the location to insert new edgeset info
                for idx, l in enumerate(new_lines):
                    if '; ### EDGE SETS ###' in l:
                        pos = idx + 3
                        break
                # use list slicing to insert one list in another
                new_lines[pos:pos] = patch_50mhz
                # move to the beginning of the file
                f.seek(0)
                # remove existing content
                f.truncate()
                # write new lines
                f.writelines(new_lines)

        # grab pingroup info from a template and add to the timesets header file
        with open(patch_timesets_path, 'r') as f:
            pingroup = f.readlines()
        # TODO: check if existing timesets header already has the pingroup info needed (already patched)
        # append pingroup info to test_TimeSets.h
        with open(path_timesets, 'a') as f:
            f.writelines(pingroup)
    else:
        logger.error(f'Error! test_TimeSets.h cannot be found! Please check in the directory: {path_stil_files}')

def remove_extra_pingroup(path_stil_files):
    """
    temporarily used to remove extra pingroups generated from all the TDF slice combination

    :param path_stil_files: str
        directory to STIL patterns
    """
    path_timesets = os.path.join(path_stil_files, 'device', 'test', 'test_TimeSets.h')
    if os.path.exists(path_timesets):
        with open(path_timesets, 'r+') as f:
            lines = f.readlines()
            # remove pingroups associated with all the slices
            new_lines = [x for x in lines if '_slc_' not in x]
            # move to the beginning of the file
            f.seek(0)
            # remove existing content
            f.truncate()
            # write new lines
            f.writelines(new_lines)
    else:
        logger.error(f'Error! test_TimeSets.h cannot be found! Please check in the directory: {path_stil_files}')

def log_conversion_info(path_stil_files, pattern_category, vector_type, compile_error, do_file_base, change_period, initial_period, new_period, cyc_cnt, log_name):
    """
    log conversion information into a csv file

    :param path_stil_files: str
        directory to STIL patterns
    :param pattern_category: str
        choices are INT, SAF and TDF
    :param vector_type: str
        choice of vector type has PROD or RMA. As project evolves, more choices might come
    :param compile_error: int
        non-zero: error happened in compilation; zero: compilation successful
    :param do_file_base: str
        .do pattern name
    :param change_period: bool
        flag to determine if scan period change in pattern is needed
    :param initial_period: int
        intial scan period native to the pattern
    :param new_period:
        target new scan period
    :param cyc_cnt: int
        vector cycle count extracted from .dp file
    :param log_name: str
        conversion log name (w/o .csv extension)
    :return:
    """

    # create dir if not exist
    create_folder(conversion_log_csv_path)

    # set up header
    header = ['time', 'category', 'vector_type', 'block', 'domain', 'mode', 'compilation_successful',
              'pattern_name', 'initial_period(ns)', 'timing_adjusted',
              'modified_period(ns)', 'extracted_cycle_count']

    if log_name == 0:
        # mode = 'a'
        path_all_csv = os.path.join(conversion_log_csv_path, '*csv')
        list_all_csv = glob.glob(path_all_csv)
        try:
            # grab the latest csv
            csv_to_edit = max(list_all_csv, key=os.path.getctime)
        except ValueError:
            # print(e)
            logger.exception('Error! No csv file exists. Need to create one first!')
    else:
        # mode = 'w'
        csv_to_edit = os.path.join(conversion_log_csv_path,log_name + '.csv')
        if not os.path.exists(csv_to_edit):
            with open(csv_to_edit, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(header)


    # get timestamp
    # ts = time.gmtime()
    # date_time = time.strftime('%x %X', ts) # this gave me wrong hour
    ts = calendar.timegm(time.gmtime())
    date_time = time.ctime(ts)

    # list_attr = ['mode', 'domain', 'block', 'vector_type', 'pattern_category']


    # get mode
    mode = os.path.basename(path_stil_files)
    list_attr_val = [mode]
    if pattern_category.lower() == 'tdf':
        list_attr = ['domain', 'block']
        # get domain, block
        for i in range(len(list_attr)):
            list_attr_val.append(os.path.basename(Path(path_stil_files).parents[i]))
    elif pattern_category.lower() in ['int','saf']:
        # get domain
        list_attr_val.append(os.path.basename(Path(path_stil_files).parents[0]))
        # fill 'block' column with abs path
        list_attr_val.append(path_stil_files)

    list_attr_val_new = list_attr_val + [vector_type, pattern_category]
    list_attr_val_new.reverse()

    if compile_error:
        compile_ok = 'no'
        pattern = 'na'
    else:
        compile_ok = 'yes'
        pattern = do_file_base

    if change_period:
        period_changed = 'yes'
    else:
        period_changed = 'no'

    # row = [date_time,category,vector_type,block,domain,mode,compile_ok,pattern,initial_period,period_changed,new_period,cyc_cnt]
    # row = [date_time] + list_attr_val + [mode,compile_ok,pattern,initial_period,period_changed,new_period,cyc_cnt]
    row = [date_time] + list_attr_val_new + [compile_ok,pattern,initial_period,period_changed,new_period,cyc_cnt]

    try:
        with open(csv_to_edit, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)
        logger.info(f'Pattern info recorded to {csv_to_edit}')
    except PermissionError as e:
        csv_temp = csv_to_edit.replace('.csv','_temp.csv')
        logger.error(e)
        with open(csv_temp, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)
        logger.info(f'Pattern info recorded to {csv_temp}')



    # list_row = []
    # for do_file in dict_compile.keys():
    #     do_file_name = os.path.basename(do_file)
    #     stil_file_name = do_file_name.replace('.do', '.stil')
    #     if not dict_compile[do_file]:
    #         conversion_result = 'pass'
    #     else:
    #         conversion_result = 'fail'
    #     row = [path_stil_files, stil_file_name, conversion_result, do_file_name, period_initial, period_new]
    #     list_row.append(row)
    #
    # header = ['parent_dir', 'stil_file_name', 'conversion_result', 'do_file_name', 'initial_period(ns)',
    #           'modified_period(ns)']
    #
    # if not compile_err:
    #     conversion_result = 'pass'
    # else:
    #     conversion_result = 'fail'
    # # get a list of all .do file paths in the subdirectories
    # do_file_list = glob.glob(path_stil_files + '/**/*.do', recursive=True)
    # for do_file in do_file_list:
    #     do_file_name = os.path.basename(do_file)
    #     stil_file_name = do_file_name.replace('.do', '.stil')
    #     stil_file = os.path.join(path_stil_files,stil_file_name)
    #     print(stil_file)
    #     # if os.path.exists(stil_file_name)
    #     row = [path_stil_files, stil_file_name, conversion_result, do_file_name, period_initial, period_new]
    #     list_row.append(row)
    #
    # parent_dir = os.path.dirname(path_stil_files)
    # conversion_log = os.path.join(parent_dir, 'pattern_conversion_log.csv')
    # print(conversion_log)
    # with open(conversion_log, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerows(list_row)

def del_zip(path_stil_files):
    """
    delete all the stil.gz zip files

    :param path_stil_files: str
        directory to STIL patterns
    """
    # grab names of all .gz zip files and save to a list
    zip_file_path = os.path.join(path_stil_files, '*.stil.gz')
    list_zip_files = glob.glob(zip_file_path)
    if not list_zip_files:
        logger.warning(f'Warning! No stil.gz zip file exists in this directory: {path_stil_files}')
        # raise FileNotFoundError("No .gz zip file exists in this directory: {}\n".format(path_stil_files))
    else:
        print(f'These stil.gz zip files are to be deleted from the directory: {path_stil_files}\n')
        print(*list_zip_files, sep='\n')
        for zip_file in list_zip_files:
            try:
                os.remove(zip_file)
            except Exception:
                logger.exception('Error in deleting zip files.')
            else:
                logger.info(f'{len(list_zip_files)} zip files are successfully deleted.')

def patch_dp_file(path_stil_files):
    """temporarily used to patch the combined .dp file to incorporate runsequence pattern"""
    # find the combined .dp file
    dp_file_list = glob.glob(path_stil_files + '/**/*combined.dp', recursive=True)
    if not len(dp_file_list):
        raise Exception('No combined .dp file is found!')
    else:
        dp_file = dp_file_list[0]

    # get the line of '.extern START', and insert '.extern RUNSEQUENCE' to the line below
    with open(dp_file, 'r') as f:
        list_lines = f.readlines()
        index_line = 0
        for num, line in enumerate(list_lines):
            if '.extern START' in line:
                # print(line)
                index_line = num
        list_lines.insert(index_line + 1, '.extern RUNSEQUENCE\n')

    # grab runsequence pattern from a template and add to the final .dp file
    runsequence_seed_file = r"C:\Weichuan\lahaina_r2_conv_test\runsequence_dp_template\runsequence_dp_template.txt"
    with open(runsequence_seed_file, 'r') as f:
        runsequence_template = f.readlines()
        print(type(runsequence_template))
        joined_list = list_lines + runsequence_template

    with open(dp_file,'w') as f:
        # f.writelines(all_lines)
        f.writelines(joined_list)

def main():

    ##*** 5/26/21,  Examples demoed to Kunag. Demoed on SVE-EV100-1 PC***##
    ### 1. Copy all STIL zip files from network drive to local PC ###
    pattern_category = 'INT'
    vector_type = 'PROD'
    local_loc = r'F:\ATPG_CDP\Waipio\r1'
    # Uncomment the below func call (copy_all_zip()) to enable STIL zip files copying
    # copy_all_zip(pattern_category,vector_type,local_loc)

    ### 2. Convert patterns from STIL to DO format ###
    dir_to_conv = os.path.join(local_loc, pattern_category, vector_type)
    log_name = '052721_conv_test_log'
    # Uncomment the below func call (traverse_levels()) to enable pattern conversion
    # traverse_levels(dir_to_conv,pattern_category,vector_type,log_name,enable_del_zip=False)

    ### 3. View doc string ###
    print(traverse_levels.__doc__) # get the docstring of function traverse_levels()

if __name__ == "__main__":
    main()
