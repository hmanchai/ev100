import argparse
import time

from preprocessing_conversion_wrapper import wrapper

updated_date_time = time.strftime("%Y%m%d-%H%M%S")
updated_date = time.strftime("%Y%m%d")
py_log_name = 'py_conversion_' + updated_date_time + '.log'

def preprocessing():


    parser = argparse.ArgumentParser(description='Execute preprocessing script')
    parser.add_argument('-rev', dest='rev', type=str,
                        help='revision number ex. r1')
    parser.add_argument('-chip_version', dest='chip_version', type=str,
                        help='chip version type ex. waipio')
    parser.add_argument('-pattern_category', dest='pattern_category', type=str, help='Enter the pattern categories (separated by | ex. SAF|INT|TDF')
    parser.add_argument('-vector_type', dest='vector_type', type=str,
                        help='Enter the vector types separated by | ex. PROD|EVAL')
    parser.add_argument('-dest', dest='dest', type=str,
                        help='destination  of base file path for files to by copied')
    parser.add_argument('-map_path', dest='map_path', type=str, help='file path to vector mapping file')

    args = parser.parse_args()

    py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r'\py_log'
    par_vector_path_r1 = r'\\qctdfsrt\prj\qct\chips' + "\\" + args.chip_version + r'\sandiego\test\vcd' + "\\" + args.rev + r'_sec5lpe\tester_vcd'

    preprocess_convert = wrapper(args.rev, args.chip_version, py_log_path, py_log_name, args.pattern_category, args.vector_type, updated_date_time)
    preprocess_convert.copy_stil_zip_files(args.dest, args.map_path, par_vector_path_r1)

def converting():
    parser = argparse.ArgumentParser(description='Execute preprocessing script')
    parser.add_argument('-rev', dest='rev', type=str,
                        help='revision number ex. r1')
    parser.add_argument('-chip_version', dest='chip_version', type=str,
                        help='chip version type ex. waipio')
    parser.add_argument('-pattern_category', dest='pattern_category', type=str,
                        help='Enter the pattern categories (separated by | ex. SAF|INT|TDF')
    parser.add_argument('-vector_type', dest='vector_type', type=str,
                        help='Enter the vector types separated by | ex. PROD|EVAL')
    parser.add_argument('-dest', dest='dest', type=str,
                        help='destination  of base file path for files to by copied')
    parser.add_argument('-map_path', dest='map_path', type=str, help='file path to vector mapping file')
    parser.add_argument('-enable_del_zip', dest='enable_del_zip', action='store_true', default=False, help='enable deleting zip files True/False')
    parser.add_argument('-block_list', dest='block_list', type=str, help='Enter the blocks (separated by | ex. ATPG|TDF_ATPG_CPU)')

    args = parser.parse_args()

    py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r'\py_log'
    velocity_dft_cfg_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\velocity_cfg" + "\\" + args.chip_version + "\\" + args.chip_version + "_WY_dft_universal_v1.cfg"
    patch_timesets_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\waipio\patch_timesets.txt"
    patch_timesets_50mhz_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\c_weicya\ev100\seed_files\patch_files\lahaina\patch_timesets_50MHz.txt"

    blocks = args.blocks_list.split("|")

    pat_name = args.pattern_category.replace("|", "_")
    vec_name = args.vector_type.replace("|", "_")
    log_name = 'conversion_log_' + pat_name + "_" + vec_name + "_" + updated_date_time

    conversion_log_csv_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r"\conversion_log"

    preprocess_convert = wrapper(args.rev, args.chip_version, py_log_path, py_log_name, args.pattern_category,
                                 args.vector_type, updated_date_time)


    preprocess_convert.velocity_conversion(conversion_log_csv_path, args.dest, blocks, log_name, velocity_dft_cfg_path,
                                           patch_timesets_path, patch_timesets_50mhz_path, args.map_path, args.enable_del_zip)

def generate_pats():
    parser = argparse.ArgumentParser(description='Execute preprocessing script')
    parser.add_argument('-rev', dest='rev', type=str,
                        help='revision number ex. r1')
    parser.add_argument('-chip_version', dest='chip_version', type=str,
                        help='chip version type ex. waipio')
    parser.add_argument('-pattern_category', dest='pattern_category', type=str,
                        help='Enter the pattern categories (separated by | ex. SAF|INT|TDF')
    parser.add_argument('-vector_type', dest='vector_type', type=str,
                        help='Enter the vector types separated by | ex. PROD|EVAL')
    parser.add_argument('-dest', dest='dest', type=str,
                        help='destination  of base file path for files to by copied')
    parser.add_argument('-map_path', dest='map_path', type=str, help='file path to vector mapping file')
    parser.add_argument('-block_list', dest='block_list', type=str,
                        help='Enter the blocks (separated by | ex. ATPG|TDF_ATPG_CPU)')
    parser.add_argument('-lim', dest='lim', type=int, help='Enter lim for # of patterns in each PATS.txt #')
    parser.add_argument('-pin_group', dest='pin_group', type=str, help="Enter pin group (ex. IN, OUT, or ALL_PINS)")
    parser.add_argument('-freq_mode_list', dest='freq_mode_list', type=str, help= "Enter the frequency modes (separated by | ex. SVS|NOM|TUR)")
    parser.add_argument('-enable_cyc_cnt', dest='enable_cyc_cnt', type=int, help="Enter 1 or 0 to set enable cycle count")
    parser.add_argument('-exclude_dirs', dest='exclude_dirs', type=str,
                        help="Enter list of directories to exclude (separated by |)")
    args = parser.parse_args()
    freq_modes = args.freq_mode_list.split("|")
    list_dirs_exclude = args.exclude_dirs.split("|")


    py_log_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r'\py_log'
    blocks = args.blocks_list.split("|")

    pat_name = args.pattern_category.replace("|", "_")
    vec_name = args.vector_type.replace("|", "_")
    log_name = 'conversion_log_' + pat_name + "_" + vec_name + "_" + updated_date_time

    conversion_log_csv_path = r"\\qctdfsrt\prj\vlsi\vetch_pst\atpg_cdp" + "\\" + args.chip_version + "\\" + args.rev + r"\conversion_log"

    preprocess_convert = wrapper(args.rev, args.chip_version, py_log_path, py_log_name, args.pattern_category,
                                 args.vector_type, updated_date_time)

    preprocess_convert.generate_pats_txt(conversion_log_csv_path, args.dest, log_name, args.lim, list_dirs_exclude, args.pin_group,
                                         args.enable_cyc_cnt, blocks, freq_modes)



