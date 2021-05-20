import os
import glob
import shutil
import pandas as pd
import logging
import time
from datetime import timedelta
import fnmatch
from pathlib import Path

# global variable

## map files ##
#lahaina
tdf_map_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\map_files\lahaina\Lahaina_V2p1_TDF_mapping_sheet.csv"
int_saf_map_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\map_files\lahaina\Lahaina_R2p1_ATPG_mapping.csv"

## source path for patterns ##
#lahaina
par_vector_path_r2 = r'\\qctdfsrt\prj\qct\chips\lahaina\sandiego\test\vcd\r2_sec5lpe\tester_vcd' #lahaina r2 common path
par_vector_path_r2p1 = r'\\qctdfsrt\prj\qct\chips\lahaina\sandiego\test\vcd\r2p1_sec5lpe\tester_vcd' #lahaina r2.1 common path

## path to log ##
# lahaina
py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\lahaina\r2\py_log"
conversion_log_csv_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\lahaina\r2\conversion_log"

# set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

# py_log = os.path.join(py_log_path,'INT_pat_store_log.log')
py_log = os.path.join(py_log_path,'py_test.log')
file_handler = logging.FileHandler(py_log)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def load_filter_map(pattern_category, vector_type):
    """load and filter map file"""
    if pattern_category == 'TDF':
        vector_type_col = 'Vector Type'
        map_path = tdf_map_path
    elif pattern_category in ('SAF', 'INT'):
        map_path = int_saf_map_path
        vector_type_col = 'Header Vector type'

    df_map_original = pd.read_csv(map_path)
    df_map = df_map_original[df_map_original[vector_type_col] == vector_type]

    if pattern_category in ('SAF','INT'):
        # filter out non-translated and non-available patterns
        df_map = df_map[df_map['Pattern name'] != '-']
        # filter by pattern category
        kw = '_' + pattern_category.lower() + '_'
        df_map = df_map[df_map['Payload vector name'].str.contains(kw)]
        df_map.insert(2,'Pattern category', pattern_category.upper())
    return df_map

def create_folder(dir):
    """create folder if not exists"""
    if not os.path.exists(dir):
        try:
            os.makedirs(dir)
            logger.debug(f'Directory created: {dir}')
        except Exception:
            logger.exception(f"Error! Could not create directory {f}")

def copy_files(path_to_file, dest_dir, log_level):
    """copy files to target directory, and increment count if copy succeeds"""
    try:
        shutil.copy(path_to_file, dest_dir)
    except Exception:
        logger.exception(f'Error! Cannot copy: {path_to_file}')
        return 0
    else:
        if log_level == 'info':
            logger.info(f'File copied: {os.path.basename(path_to_file)}')
        elif log_level == 'debug':
            logger.debug(f'File copied: {os.path.basename(path_to_file)}')
        return 1

# def store_all_zip_tdf(dest_dir, vector_type, pattern_category='TDF'):
#     """
#     user chooses vector type (PROD, RMA)
#     copy ALL zip files from original dir, classify (by: block, domain, mode, etc.) and store in a target location,
#     e.g. network drive
#     NOTE: double download is OK and will overwrite
#     """
#     # TODO: multi-threading
#     # dir structure:
#     # TDF -> PROD/RMA->Block->Domain ->mode
#
#     # create pattern level dir (INT, SAF or TDF)
#     dir_pattern = os.path.join(dest_dir, pattern_category)
#     # create vector_type level dir (PROD or RMA)
#     dir_vector_type = os.path.join(dir_pattern,vector_type)
#
#     # load and filter map file to pd df
#     df_map = load_filter_map(pattern_category, vector_type)
#     # print(df_map)
#
#     # get a list of blocks
#     list_block = df_map['Block'].unique().tolist() # will be used in a loop
#     # print(list_block)
#
#     child_path_tdf = 'SRC'
#     total_hd_zip_count = 0
#     total_pl_zip_count = 0
#
#     start = time.time()
#     logger.info(f"***** Starting .stil.gz files storing and classification for {pattern_category} {vector_type} *****")
#
#     ## loop starting from block level
#     for block in list_block:
#         # set the source path to tdf patterns
#         path_tdf = os.path.join(par_vector_path_r2, block, child_path_tdf)
#         # create block level dir
#         dir_block = os.path.join(dir_vector_type,block)
#         # get a list of domain
#         df_map_per_block = df_map[df_map['Block']==block]
#         list_domain = df_map_per_block['Domain'].unique().tolist()
#
#         for domain in list_domain:
#             # create domain level dir
#             dir_domain = os.path.join(dir_block,domain)
#             # get a list of modes
#             df_map_per_domain = df_map_per_block[df_map_per_block['Domain'] == domain]
#             list_mode = df_map_per_domain['Mode'].unique().tolist()
#             for mode in list_mode:
#                 # create mode level dir
#                 dir_mode = os.path.join(dir_domain,mode)
#                 create_folder(dir_mode)
#
#                 logger.info(f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {block} {domain} {mode} ***")
#
#                 df_map_per_mode = df_map_per_domain[df_map_per_domain['Mode']==mode]
#                 # get header name
#                 hd_name = df_map_per_mode['Header'].values[0]
#                 hd_zip = hd_name + '.stil.gz'
#                 path_hd_zip = os.path.join(path_tdf, hd_zip)
#
#                 start_inner = time.time()
#
#                 # copy header zip files to target folder
#                 # try:
#                 #     shutil.copy(path_hd_zip, dir_mode)
#                 # except Exception:
#                 #     logger.exception(f'Error! Cannot download header file: {path_hd_zip}')
#                 # else:
#                 #     logger.info(f'Header .stil.gz file downloaded: {os.path.basename(path_hd_zip)}')
#                 #     total_zip_count += 1
#                 total_hd_zip_count = copy_files(path_hd_zip,dir_mode, 'info',total_hd_zip_count)
#
#                 # get payloads name. wildcard is used to grab all slices not specified in map file
#                 pl_name = df_map_per_mode['Payload'].values[0]
#                 pl_zip = pl_name + '*.stil.gz'
#
#                 # get a list of paths for all payload slices
#                 path_pl_zip = os.path.join(path_tdf, pl_zip)
#                 list_path_pl_zip = glob.glob(path_pl_zip)
#
#                 # copy payload zip files to target folder
#                 for zip in list_path_pl_zip:
#                     # try:
#                     #     shutil.copy(zip, dir_mode)
#                     # except Exception:
#                     #     logger.exception(f'Error! Cannot download payload file: {zip}')
#                     # else:
#                     #     logger.debug(f'Payload .stil.gz files downloaded: {os.path.basename(zip)}')
#                     total_pl_zip_count = copy_files(zip,dir_mode,'debug',total_pl_zip_count)
#                 # logger.info(f'{len(list_path_pl_zip)} payload .stil.gz files downloaded successfully.')
#                 logger.info(f'{total_pl_zip_count} payload .stil.gz files downloaded successfully.')
#                 # total_zip_count += len(list_path_pl_zip)
#
#                 #TODO: add count total modes downloaded
#
#                 end_inner = time.time()
#                 elapsed_inner = end_inner - start_inner
#                 if elapsed_inner > 60:
#                     elapsed_inner = round(elapsed_inner / 60, 2)
#                     logger.info(f'*** Time elapsed for file storing for this pattern: {elapsed_inner} min. ***')
#                 else:
#                     elapsed_inner = round(elapsed_inner, 2)
#                     logger.info(f'*** Time elapsed for file storing for this pattern: {elapsed_inner} sec. ***')
#
#     logger.info(f'***** Total count of .stil.gz files stored and classified: {total_hd_zip_count + total_pl_zip_count} *****')
#
#     end = time.time()
#     elapsed = end - start
#     if elapsed > 60:
#         elapsed = round(elapsed / 60, 2)
#         logger.info(f'***** Total time elapsed for file storing and classification: {elapsed} min *****')
#     else:
#         elapsed = round(elapsed, 2)
#         logger.info(f'***** Total time elapsed for file storing and classification: {elapsed} sec *****')

def store_all_zip_tdf(dest_dir, vector_type, pattern_category='TDF'):
    """
    user chooses vector type (PROD, RMA)
    copy ALL zip files from original dir, classify (by: block, domain, mode, etc.) and store in a target location,
    e.g. network drive
    NOTE: double copy is OK and will overwrite
    """
    # TODO: multi-threading
    # dir structure:
    # TDF -> PROD/RMA->Block->Domain ->mode

    # create pattern level dir (INT, SAF or TDF)
    dir_pattern = os.path.join(dest_dir, pattern_category)
    # create vector_type level dir (PROD or RMA)
    dir_vector_type = os.path.join(dir_pattern,vector_type)

    # load and filter map file to pd df
    df_map = load_filter_map(pattern_category, vector_type)
    # print(df_map)

    # get a list of blocks
    list_block = df_map['Block'].unique().tolist() # will be used in a loop
    # print(list_block)

    child_path_tdf = 'SRC'
    # total_hd_zip_count = 0
    # total_pl_zip_count = 0
    # set up counter
    total_hdr_cnt = 0
    total_pl_cnt = 0
    total_r2_cnt = 0
    total_r2p1_cnt = 0

    start = time.time()
    logger.info(f"***** Starting .stil.gz files storing and classification for {pattern_category} {vector_type} *****")

    ## loop starting from block level
    for block in list_block:
        # # set the source path to tdf patterns
        # path_tdf = os.path.join(par_vector_path_r2, block, child_path_tdf)
        # create block level dir
        dir_block = os.path.join(dir_vector_type,block)
        # get a list of domain
        df_map_per_block = df_map[df_map['Block']==block]
        list_domain = df_map_per_block['Domain'].unique().tolist()

        for domain in list_domain:
            # create domain level dir
            dir_domain = os.path.join(dir_block,domain)
            # get a list of modes
            df_map_per_domain = df_map_per_block[df_map_per_block['Domain'] == domain]
            list_mode = df_map_per_domain['Mode'].unique().tolist()
            for mode in list_mode:
                # create mode level dir
                dir_mode = os.path.join(dir_domain,mode)
                create_folder(dir_mode)

                df_map_per_mode = df_map_per_domain[df_map_per_domain['Mode']==mode]
                # get si revision
                rev = df_map_per_mode['Bin Si Revision'].values[0]
                if rev == 'r2_sec5lpe':
                    path_tdf = os.path.join(par_vector_path_r2, block, child_path_tdf)
                elif rev == 'r2p1_sec5lpe':
                    path_tdf = os.path.join(par_vector_path_r2p1, block, child_path_tdf)

                logger.info(
                    f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {block} {domain} {mode} ***")

                # get header name
                hd_name = df_map_per_mode['Header'].values[0]
                hd_zip = hd_name + '.stil.gz'
                path_hd_zip = os.path.join(path_tdf, hd_zip)

                start_inner = time.time()

                # store header zip file
                res_hdr_cpy = copy_files(path_hd_zip, dir_mode, 'info')
                total_hdr_cnt += res_hdr_cpy
                if res_hdr_cpy:
                    logger.info(f'Header copied from Lahaina {rev} path.')


                # total_hd_zip_count = copy_files(path_hd_zip,dir_mode, 'info',total_hd_zip_count)

                # get payloads name. wildcard is used to grab all slices not specified in map file
                pl_name = df_map_per_mode['Payload'].values[0]
                pl_zip = pl_name + '*.stil.gz'

                # get a list of paths for all payload slices
                path_pl_zip = os.path.join(path_tdf, pl_zip)
                list_path_pl_zip = glob.glob(path_pl_zip)

                temp_pl_cnt = 0
                # store payload zip files
                for zip_file in list_path_pl_zip:
                    # total_pl_zip_count = copy_files(zip,dir_mode,'debug',total_pl_zip_count)
                    res_pl_cpy = copy_files(zip_file, dir_mode, 'debug')
                    # total_pl_cnt += res_pl_cpy
                    temp_pl_cnt += res_pl_cpy
                    if res_pl_cpy:
                        # logger.info('Header downloaded from Lahaina R2p1 path.')
                        if rev == 'r2_sec5lpe':
                            total_r2_cnt += res_pl_cpy
                        elif rev == 'r2p1_sec5lpe':
                            total_r2p1_cnt += res_pl_cpy
                logger.info(f'{temp_pl_cnt} payload .stil.gz files copied from {rev} path successfully.')
                total_pl_cnt += temp_pl_cnt
                if res_hdr_cpy and temp_pl_cnt:
                    if rev == 'r2_sec5lpe':
                        total_r2_cnt += res_hdr_cpy
                    elif rev == 'r2p1_sec5lpe':
                        total_r2p1_cnt += res_hdr_cpy

                end_inner = time.time()
                elapsed_inner = end_inner - start_inner
                logger.info(
                    f'*** Time elapsed for file storing for this pattern: {timedelta(seconds=elapsed_inner)} ***')

    # logger.info(f'***** Total count of .stil.gz files stored and classified: {total_hd_zip_count + total_pl_zip_count} *****')


    logger.info(f'***** Total count of .stil.gz files stored and classified for header: {total_hdr_cnt} *****')
    logger.info(f'***** Total count of .stil.gz files stored and classified for payload: {total_pl_cnt} *****')
    logger.info(f'***** Total count of patterns copied from Lahaina R2 path: {total_r2_cnt} *****')
    logger.info(f'***** Total count of patterns files copied from Lahaina R2p1 path: {total_r2p1_cnt} *****')

    end = time.time()
    elapsed = end - start
    logger.info(f'***** Total time elapsed for file storing and classification: {timedelta(seconds=elapsed)} *****')


# def store_all_zip_atpg(dest_dir, pattern_category, vector_type):
#     """
#     user chooses pattern (INT,SAF) and vector type (PROD, RMA)
#     copy ALL zip files from original dir, classify (by: domain, mode, etc.) and store in a target location,
#     e.g. network drive
#     NOTE: double copying is OK and will overwrite
#     """
#     # INT -> PROD/RMA -> lpc/lpu -> domain ->mode
#     # SAF -> PROD/RMA -> lpc -> topoff/regular (-> F32/regular -> apm/regular) -> domain ->mode
#
#     # # create pattern level dir (INT, SAF)
#     dir_pattern = os.path.join(dest_dir, pattern_category)
#     # # create vector_type level dir (PROD or RMA)
#     dir_vector_type = os.path.join(dir_pattern,vector_type)
#
#     # load and filter map file to pd df
#     df_map = load_filter_map(pattern_category, vector_type)
#     # print(df_map)
#
#     # set up pattern source path
#     path_atpg_r2 = os.path.join(par_vector_path_r2, 'ATPG', 'SRC')
#     path_atpg_r2p1 = os.path.join(par_vector_path_r2p1, 'ATPG', 'SRC')
#
#     # set up counter
#     total_hdr_cnt = 0
#     total_pl_cnt = 0
#     total_r2_cnt = 0
#     total_r2p1_cnt = 0
#
#     start = time.time()
#     logger.info(f"***** Starting .stil.gz files storing and classification for {pattern_category} {vector_type} *****")
#
#     for i in df_map.index:
#         pl = df_map.loc[i,'Payload vector name']
#         list_pl_parsed = pl.split('_')
#         comp_type = list_pl_parsed[3]
#         # comp_type level dir, lpc or lpu
#         dir_comp_type = os.path.join(dir_vector_type, comp_type)
#         # print(comp_type)
#         # domain = list_pl_parsed[-1]
#
#         hdr = df_map.loc[i, 'Header vector name']
#         list_hdr_parsed = hdr.split('_')
#
#         # parse domain
#         if 'se0' in list_hdr_parsed:
#             domain = list_hdr_parsed[5] # after 'se0'
#         else:
#             domain = list_hdr_parsed[4]
#
#         if pattern_category.upper() == 'INT':
#             # domain level dir
#             dir_domain = os.path.join(dir_comp_type,domain)
#         elif pattern_category.upper() == 'SAF':
#             apm_flag = False
#             if 'topoff' in list_pl_parsed:
#                 idx = list_pl_parsed.index('topoff')
#                 to = '_'.join(list_pl_parsed[idx:-1])
#                 # topoff level dir
#                 dir_to = os.path.join(dir_comp_type, to)
#                 # reset domain
#                 domain = list_pl_parsed[-1]
#                 # domain level dir
#                 dir_domain = os.path.join(dir_to, domain)
#             else:
#                 to = 'regular'
#                 # topoff level dir
#                 dir_to = os.path.join(dir_comp_type, to)
#                 if 'F32' in list_pl_parsed:
#                     f32 = 'F32'
#                     apm_flag = True
#                     if 'apm' in list_hdr_parsed:
#                         apm = 'apm'
#                     else:
#                         apm = 'regular'
#                 else:
#                     f32 = 'regular'
#                 # F32 level dir
#                 dir_f32 = os.path.join(dir_to, f32)
#                 if apm_flag:
#                     # apm level dir
#                     dir_apm = os.path.join(dir_f32, apm)
#                     # domain level dir
#                     dir_domain = os.path.join(dir_apm, domain)
#                 else:
#                     dir_domain = os.path.join(dir_f32, domain)
#
#         # parse mode
#         if list_hdr_parsed[-2] == domain:
#             mode = 'na'  # TODO: na might be nominal corner?
#         else:
#             mode = list_hdr_parsed[-2]
#         # mode level dir
#         dir_mode = os.path.join(dir_domain,mode)
#         # create dir
#         create_folder(dir_mode)
#
#         if pattern_category.upper() == 'INT':
#             logger.info(f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {comp_type} {domain} {mode} ***")
#         elif pattern_category.upper() == 'SAF':
#             logger.info(
#                 f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {comp_type} {to} {domain} {mode} ***")
#
#         start_inner = time.time()
#
#         # copy header and payload zip file
#         hdr_zip = hdr + '.stil.gz'
#         path_r2_hdr_zip = os.path.join(path_atpg_r2,hdr_zip)
#         path_r2p1_hdr_zip = os.path.join(path_atpg_r2p1,hdr_zip)
#
#         pl_zip = pl + '.stil.gz'
#         path_r2_pl_zip = os.path.join(path_atpg_r2,pl_zip)
#         path_r2p1_pl_zip = os.path.join(path_atpg_r2p1,pl_zip)
#
#         # check to copy R2.1 or R2 patterns
#
#         if (os.path.exists(path_r2p1_hdr_zip)) & (os.path.exists(path_r2p1_pl_zip)):
#             res_hdr_cpy = copy_files(path_r2p1_hdr_zip, dir_mode, 'info')
#             if res_hdr_cpy:
#                 logger.info('Header copied from Lahaina R2p1 path.')
#             total_r2p1_cnt += res_hdr_cpy
#
#             res_pl_cpy = copy_files(path_r2p1_pl_zip,dir_mode,'info')
#             if res_pl_cpy:
#                 logger.info(('Payload copied from Lahaina R2p1 path.'))
#             total_r2p1_cnt += res_pl_cpy
#         else:
#             res_hdr_cpy = copy_files(path_r2_hdr_zip, dir_mode, 'info')
#             if res_hdr_cpy:
#                 logger.info('Header copied from Lahaina R2 path.')
#             total_r2_cnt += res_hdr_cpy
#
#             res_pl_cpy = copy_files(path_r2_pl_zip, dir_mode, 'info')
#             if res_pl_cpy:
#                 logger.info(('Payload copied from Lahaina R2 path.'))
#             total_r2_cnt += res_pl_cpy
#
#         total_hdr_cnt += res_hdr_cpy
#         total_pl_cnt += res_pl_cpy
#
#         end_inner = time.time()
#         elapsed_inner = end_inner - start_inner
#         logger.info(f'*** Time elapsed for file storing for this pattern: {timedelta(seconds=elapsed_inner)} ***')
#
#     logger.info(f'***** Total count of .stil.gz files stored and classified for header: {total_hdr_cnt} *****')
#     logger.info(f'***** Total count of .stil.gz files stored and classified for payload: {total_pl_cnt} *****')
#     logger.info(f'***** Total count of patterns copied from Lahaina R2 path: {total_r2_cnt} *****')
#     logger.info(f'***** Total count of patterns copied from Lahaina R2p1 path: {total_r2p1_cnt} *****')
#
#     end = time.time()
#     elapsed = end - start
#     logger.info(f'***** Total time elapsed for file storing and classification: {timedelta(seconds=elapsed)} *****')

def store_all_zip_atpg(dest_dir, pattern_category, vector_type):
    """
    user chooses pattern (INT,SAF) and vector type (PROD, RMA)
    copy ALL zip files from original dir, classify (by: domain, mode, etc.) and store in a target location,
    e.g. network drive
    NOTE: double copying is OK and will overwrite
    """
    # INT -> PROD/RMA -> lpc/lpu -> domain ->mode
    # SAF -> PROD/RMA -> lpc -> topoff/regular (-> F32/regular -> apm/regular) -> domain ->mode

    # # # create pattern level dir (INT, SAF)
    # dir_pattern = os.path.join(dest_dir, pattern_category)
    # # # create vector_type level dir (PROD or RMA)
    # dir_vector_type = os.path.join(dir_pattern,vector_type)

    # load and filter map file to pd df
    df_map = load_filter_map(pattern_category, vector_type)
    # print(df_map)

    # set up pattern source path
    path_atpg_r2 = os.path.join(par_vector_path_r2, 'ATPG', 'SRC')
    path_atpg_r2p1 = os.path.join(par_vector_path_r2p1, 'ATPG', 'SRC')

    # set up counter
    total_hdr_cnt = 0
    total_pl_cnt = 0
    # total_r2_cnt = 0
    # total_r2p1_cnt = 0
    dict_rev_cnt = {'r2':0, 'r2p1':0}

    start = time.time()
    logger.info(f"***** Starting .stil.gz files storing and classification for {pattern_category} {vector_type} *****")

    for i in df_map.index:
        pl = df_map.loc[i,'Payload vector name']
        list_pl_parsed = pl.split('_')

        # # # comp_type level dir, lpc or lpu
        # dir_comp_type = os.path.join(dir_vector_type, comp_type)

        hdr = df_map.loc[i, 'Header vector name']
        list_hdr_parsed = hdr.split('_')

        # copy header and payload zip file
        hdr_zip = hdr + '.stil.gz'
        path_r2_hdr_zip = os.path.join(path_atpg_r2,hdr_zip)
        path_r2p1_hdr_zip = os.path.join(path_atpg_r2p1,hdr_zip)

        pl_zip = pl + '.stil.gz'
        path_r2_pl_zip = os.path.join(path_atpg_r2,pl_zip)
        path_r2p1_pl_zip = os.path.join(path_atpg_r2p1,pl_zip)

        # check to copy R2.1 or R2 patterns. Coded based on lahaina case
        if (os.path.exists(path_r2p1_hdr_zip)) & (os.path.exists(path_r2p1_pl_zip)):
            rev = 'r2p1'
            hdr_path_to_copy = path_r2p1_hdr_zip
            pl_path_to_copy = path_r2p1_pl_zip
        else:
            rev = 'r2'
            hdr_path_to_copy = path_r2_hdr_zip
            pl_path_to_copy = path_r2_pl_zip

        # comp_type level dir: lpc or lpu
        comp_type = list_pl_parsed[3]
        dir_comp_type = os.path.join(dest_dir,rev,pattern_category,vector_type,comp_type)

        # parse domain
        if 'se0' in list_hdr_parsed:
            domain = list_hdr_parsed[5]  # after 'se0'
        else:
            domain = list_hdr_parsed[4]

        # parse other info
        if pattern_category.upper() == 'INT':
            # domain level dir
            dir_domain = os.path.join(dir_comp_type, domain)
        elif pattern_category.upper() == 'SAF':
            apm_flag = False
            if 'topoff' in list_pl_parsed:
                idx = list_pl_parsed.index('topoff')
                to = '_'.join(list_pl_parsed[idx:-1])
                # topoff level dir
                dir_to = os.path.join(dir_comp_type, to)
                # reset domain
                domain = list_pl_parsed[-1]
                # domain level dir
                dir_domain = os.path.join(dir_to, domain)
            else:
                to = 'regular'
                # topoff level dir
                dir_to = os.path.join(dir_comp_type, to)
                if 'F32' in list_pl_parsed:
                    f32 = 'F32'
                    apm_flag = True
                    if 'apm' in list_hdr_parsed:
                        apm = 'apm'
                    else:
                        apm = 'regular'
                else:
                    f32 = 'regular'
                # F32 level dir
                dir_f32 = os.path.join(dir_to, f32)
                if apm_flag:
                    # apm level dir
                    dir_apm = os.path.join(dir_f32, apm)
                    # domain level dir
                    dir_domain = os.path.join(dir_apm, domain)
                else:
                    dir_domain = os.path.join(dir_f32, domain)

        # parse mode
        if list_hdr_parsed[-2] == domain:
            mode = 'na'  # TODO: na might be nominal corner?
        else:
            mode = list_hdr_parsed[-2]
        # mode level dir
        dir_mode = os.path.join(dir_domain, mode)
        # create dir
        create_folder(dir_mode)

        start_inner = time.time()
        if pattern_category.upper() == 'INT':
            logger.info(f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {comp_type} {domain} {mode} ***")
        elif pattern_category.upper() == 'SAF':
            logger.info(
                f"*** Currently storing .stil.gz files for {pattern_category} {vector_type} {comp_type} {to} {domain} {mode} ***")

        # copy header and increment counter
        res_hdr_cpy = copy_files(hdr_path_to_copy, dir_mode, 'info')
        dict_rev_cnt[rev] += res_hdr_cpy
        if res_hdr_cpy:
            logger.info(f'Header copied from Lahaina {rev} path.')

        # total_r2_cnt += res_hdr_cpy

        # copy payload and increment counter
        res_pl_cpy = copy_files(pl_path_to_copy, dir_mode, 'info')
        dict_rev_cnt[rev] += res_pl_cpy
        if res_pl_cpy:
            logger.info((f'Payload copied from Lahaina {rev} path.'))
        # total_r2_cnt += res_pl_cpy


        total_hdr_cnt += res_hdr_cpy
        total_pl_cnt += res_pl_cpy

        end_inner = time.time()
        elapsed_inner = end_inner - start_inner
        logger.info(f'*** Time elapsed for file storing for this pattern: {timedelta(seconds=elapsed_inner)} ***')

    r2_cnt = dict_rev_cnt['r2']
    r2p1_cnt = dict_rev_cnt['r2p1']

    logger.info(f'***** Total count of .stil.gz files stored and classified for header: {total_hdr_cnt} *****')
    logger.info(f'***** Total count of .stil.gz files stored and classified for payload: {total_pl_cnt} *****')
    logger.info(f'***** Total count of files copied from Lahaina R2 path: {r2_cnt} *****')
    logger.info(f'***** Total count of files copied from Lahaina R2p1 path: {r2p1_cnt} *****')

    end = time.time()
    elapsed = end - start
    logger.info(f'***** Total time elapsed for file storing and classification: {timedelta(seconds=elapsed)} *****')

# def generate_pats_txt(pattern_category, vector_type, dir_pat, dir_exec, log_name, lim, pin_group = 'OUT', enable_cyc_cnt=1, block=None):
#     """generate a set of PATS.txt files and parent directories (vector_type level) for loading batches of patterns"""
#
#     # block = os.path.basename(path_block)
#     # do_files = glob.glob(path_block + '/**/*.do', recursive=True)
#     if pattern_category.lower() == 'tdf':
#         # dir to grab DO from
#         path_top_level = os.path.join(dir_pat,pattern_category,vector_type, block)
#         # dir to export PATS.txt to
#         dir_sub = os.path.join(dir_exec, pattern_category, vector_type, block)
#         # prefix for PATS.txt file name
#         pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
#     elif pattern_category.lower() in ['int','saf']:
#         path_top_level = os.path.join(dir_pat,pattern_category,vector_type)
#         dir_sub = os.path.join(dir_exec, pattern_category, vector_type)
#         pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'
#
#     create_folder(dir_sub)
#     do_files = glob.glob(path_top_level + '/**/*.do', recursive=True)
#
#     conv_log = os.path.join(conversion_log_csv_path,log_name + '.csv')
#     df_conv_log = pd.read_csv(conv_log)
#
#     pin_group = pin_group # OUT, ALL_PINS
#     keep_state = 0
#     load_pattern = 1
#     dummy_cfg = 'NULL'
#     dummy_xrl = 'NULL'
#     header = '; Pattern, Cycle Count, Enable Fail Mask Pin Group, Keep State, Load Pattern, cfg, xrl'
#
#     # # change all types to string and combine the strings separated by comma
#     # to_write = ','.join(map(str, [do_file_name, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))
#
#     quo, rem = divmod(len(do_files), lim)
#     # set up the number of PATS.txt
#     if quo:
#         if rem:
#             cnt = quo + 1
#         else:
#             cnt = quo
#     else:
#         cnt = 1
#
#     # # create subdir in execution dir
#     # dir_sub = os.path.join(dir_exec,pattern_category,vector_type)
#     # create_folder(dir_sub)
#
#     # TODO: if TDF: group by block; if ATPG: just assign number
#
#     # create individual PATS.txt and folder
#     # pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'
#     for i in range(cnt):
#         pats_dir = os.path.join(dir_sub, str(i+1))
#         create_folder(pats_dir)
#         pats_txt_name = pre_fix + str(i+1) + '.txt'
#         pats_txt = os.path.join(pats_dir, pats_txt_name)
#         # write header
#         with open(pats_txt, 'w+') as f:
#             f.write(header + '\n')
#
#         # write patterns
#         start = i*lim
#         end = (i+1)*lim
#         for do_file in do_files[start:end]:
#             do_file_name = os.path.basename(do_file)
#             if enable_cyc_cnt:
#                 try:
#                     filter = df_conv_log['pattern_name'] == do_file_name
#                 except Exception as e:
#                     print(e)
#                     cyc_cnt = 0
#                 else:
#                     cyc_cnt = df_conv_log.loc[filter, 'extracted_cycle_count'].values[0]
#             else:
#                 cyc_cnt = 0
#             to_write = ','.join(
#                 map(str, [do_file, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))
#             with open(pats_txt, 'a+') as f:
#                 f.write(to_write + '\n')
#
#     print(f'*** PATS.txt generation completed for {pattern_category} {vector_type}')


def generate_pats_txt(pattern_category, vector_type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude = [], pin_group = 'OUT', enable_cyc_cnt=1, block=None):
    """generate a set of PATS.txt files and parent directories (vector_type level) for loading batches of patterns"""

    conv_log = os.path.join(conversion_log_csv_path, log_name + '.csv')
    df_conv_log = pd.read_csv(conv_log)

    pin_group = pin_group  # OUT, ALL_PINS
    keep_state = 0
    load_pattern = 1
    dummy_cfg = 'NULL'
    dummy_xrl = 'NULL'
    header = '; Pattern, Cycle Count, Enable Fail Mask Pin Group, Keep State, Load Pattern, cfg, xrl'

    # # change all types to string and combine the strings separated by comma
    # to_write = ','.join(map(str, [do_file_name, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))


    if pattern_category.lower() == 'tdf':
        # dir to grab DO from
        path_top_level = os.path.join(dir_pat,pattern_category,vector_type, block)
        # dir to export PATS.txt to
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type, block)
        # prefix for PATS.txt file name
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
    elif pattern_category.lower() in ['int','saf']:
        path_top_level = os.path.join(dir_pat, pattern_category, vector_type)
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type)
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

    create_folder(dir_sub)

    do_files = []
    for root, dirs, files in os.walk(path_top_level,topdown=True):
        # exclude dirs
        dirs[:] = [d for d in dirs if d not in list_dirs_exclude]

        for file in files:
            if fnmatch.fnmatch(file, '*.do'):
                # get abs paths for DO patterns
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

    # TODO: if TDF: group by block; if ATPG: just assign number

    # create individual PATS.txt and folder
    # pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'
    for i in range(cnt):
        pats_dir = os.path.join(dir_sub, str(i+1))
        create_folder(pats_dir)
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

    print(f'*** PATS.txt generation completed for {pattern_category} {vector_type}')

def generate_pats_txt_mod(pattern_category, vector_type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude = [], pin_group = 'OUT', enable_cyc_cnt=1, block=None):
    """generate a set of PATS.txt files and parent directories (vector_type level) for loading batches of patterns"""

    conv_log = os.path.join(conversion_log_csv_path, log_name + '.csv')
    df_conv_log = pd.read_csv(conv_log)

    pin_group = pin_group  # OUT, ALL_PINS
    keep_state = 0
    load_pattern = 1
    dummy_cfg = 'NULL'
    dummy_xrl = 'NULL'
    header = '; Pattern, Cycle Count, Enable Fail Mask Pin Group, Keep State, Load Pattern, cfg, xrl'

    # # change all types to string and combine the strings separated by comma
    # to_write = ','.join(map(str, [do_file_name, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))


    if pattern_category.lower() == 'tdf':
        # dir to grab DO from
        path_top_level = os.path.join(dir_pat,pattern_category,vector_type, block)
        # dir to export PATS.txt to
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type, block)
        # prefix for PATS.txt file name
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
    elif pattern_category.lower() in ['int','saf']:
        path_top_level = os.path.join(dir_pat, pattern_category, vector_type)
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type)
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

    create_folder(dir_sub)

    kw_burst = 'XMD'
    kw_header = 'MHz'
    do_files = []
    for root, dirs, files in os.walk(path_top_level,topdown=True):
        # exclude dirs
        dirs[:] = [d for d in dirs if d not in list_dirs_exclude]

        for file in files:
            if (fnmatch.fnmatch(file, '*.do')) & (kw_header in file) & (kw_burst not in file):
                # get abs paths for DO patterns
                do_file = os.path.join(root,file)
                do_files.append(do_file)

    # block = os.path.basename(path_block)
    # do_files = glob.glob(path_block + '/**/*.do', recursive=True)
    if pattern_category.lower() == 'tdf':
        # dir to grab DO from
        path_top_level = os.path.join(dir_pat,pattern_category,vector_type, block)
        # dir to export PATS.txt to
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type, block)
        # prefix for PATS.txt file name
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
    elif pattern_category.lower() in ['int','saf']:
        path_top_level = os.path.join(dir_pat,pattern_category,vector_type)
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type)
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'



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

    # TODO: if TDF: group by block; if ATPG: just assign number

    # create individual PATS.txt and folder
    # pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'
    for i in range(cnt):
        pats_dir = os.path.join(dir_sub, str(i+1))
        create_folder(pats_dir)
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

    print(f'*** PATS.txt generation completed for {pattern_category} {vector_type}')

def generate_pats_txt_special(pattern_category, vector_type, dir_pat, dir_exec, log_name, lim, list_dirs_exclude = [], pin_group = 'OUT', enable_cyc_cnt=1, block=None):
    """generate a set of PATS.txt files and parent directories (vector_type level) for loading batches of patterns"""
    pat_csv = r'F:\ATPG_CDP\Lahaina\r2\pattern_execution\Output\021121_G745board_0x826CFB17\allpass.csv'
    df_pat = pd.read_csv(pat_csv)
    list_pat = list(df_pat['PatternName'])


    conv_log = os.path.join(conversion_log_csv_path, log_name + '.csv')
    df_conv_log = pd.read_csv(conv_log)

    pin_group = pin_group  # OUT, ALL_PINS
    keep_state = 0
    load_pattern = 1
    dummy_cfg = 'NULL'
    dummy_xrl = 'NULL'
    header = '; Pattern, Cycle Count, Enable Fail Mask Pin Group, Keep State, Load Pattern, cfg, xrl'

    # # change all types to string and combine the strings separated by comma
    # to_write = ','.join(map(str, [do_file_name, cyc_cnt, pin_group, keep_state, load_pattern, dummy_cfg, dummy_xrl]))


    if pattern_category.lower() == 'tdf':
        # dir to grab DO from
        path_top_level = os.path.join(dir_pat,pattern_category,vector_type, block)
        # dir to export PATS.txt to
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type, block)
        # prefix for PATS.txt file name
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_' + block + '_'
    elif pattern_category.lower() in ['int','saf']:
        path_top_level = os.path.join(dir_pat, pattern_category, vector_type)
        dir_sub = os.path.join(dir_exec, pattern_category, vector_type)
        pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'

    create_folder(dir_sub)

    do_files = []
    for root, dirs, files in os.walk(path_top_level,topdown=True):
        # exclude dirs
        dirs[:] = [d for d in dirs if d not in list_dirs_exclude]

        for file in files:
            if fnmatch.fnmatch(file, '*.do'):
                if file in list_pat:
                    # get abs paths for DO patterns
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

    # TODO: if TDF: group by block; if ATPG: just assign number

    # create individual PATS.txt and folder
    # pre_fix = 'PATS_' + pattern_category + '_' + vector_type + '_'
    for i in range(cnt):
        pats_dir = os.path.join(dir_sub, str(i+1))
        create_folder(pats_dir)
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

    print(f'*** PATS.txt generation completed for {pattern_category} {vector_type}')

def main():

    ### Store and Classify INT/SAF patterns ###
    # a network drive location to store all pattern zip files
    # dest = r'\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\lahaina'
    dest = r'\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp\waipio'
    pattern_category = 'SAF'
    # for vector_type in ['PROD','RMA']:
    for vector_type in ['PROD']:
        store_all_zip_atpg(dest,pattern_category,vector_type)

    ### Store and Classify TDF patterns ###

    ### Prepare PATS.txt ###
    # pattern_category = 'SAF'
    # vector_type = 'PROD'
    # # list_block_hp = ['TDF_ATPG_CPU', 'TDF_ATPG_GFX', 'TDF_ATPG_DDR', 'TDF_ATPG_Q6', 'TDF_ATPG_REST']
    # # list_block_lp = ['TDF_ATPG_CAMDV', 'TDF_ATPG_MODEM', 'TDF_ATPG_SP', 'TDF_ATPG_TILE', 'TDF_ATPG_TOP']
    # dir_pat = r"F:\ATPG_CDP\Lahaina\r2"
    # dir_exec = os.path.join(dir_pat,'pattern_execution','Pattern_list')
    # if pattern_category.upper() == 'TDF':
    #     log_name = 'lahaina_r2_tdf_prod_new_velocity'
    # elif pattern_category.upper() == 'SAF':
    #     log_name = 'lahaina_r2_saf_prod_new_velocity'
    # elif pattern_category.upper() == 'INT':
    #     log_name = 'lahaina_r2_int_prod_new_velocity'
    # else:
    #     print('Please check your pattern_category variable for accuracy!')

    # list_exclusion = ['regular','topoff_cgc_t_sr_t']

    # ## TDF ###
    # # lim=1
    # # for block in list_block_hp:
    # #     generate_pats_txt(pattern_category,vector_type,dir_pat,dir_exec,log_name,lim, block=block)
    # # blk = 'TDF_ATPG_CPU'
    # # list_dirs_exclude = ['SVS','LSVS']
    # # for blk in list_block_lp:
    # #     generate_pats_txt(pattern_category,vector_type,dir_pat,dir_exec,list_dirs_exclude,log_name,lim,block=blk)
    # # generate_pats_txt(pattern_category,vector_type,dir_pat,dir_exec,log_name,lim,list_dirs_exclude=list_dirs_exclude,block=blk)
    # # generate_pats_txt_mod(pattern_category,vector_type,dir_pat,dir_exec,log_name,lim,list_dirs_exclude=list_dirs_exclude,enable_cyc_cnt=0,block=blk)
    #
    # ## INT, SAF ##
    # lim = 50
    # # list_dirs_exclude = ['na','svs','tur']
    # # list_dirs_exclude = ['na','svs']
    # generate_pats_txt_special(pattern_category,vector_type,dir_pat,dir_exec,log_name,lim)
    # # generate_pats_txt(pattern_category,vector_type,dir_pat,dir_exec,log_name,lim, list_dirs_exclude=list_dirs_exclude)

if __name__ == "__main__":
    main()
