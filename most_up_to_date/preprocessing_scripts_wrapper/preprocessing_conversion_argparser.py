import argparse
import time

from preprocessing_conversion_wrapper import wrapper


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





