#########################################
# This version of DigshellExec.py is an #
# enhanced version, friendly for        #
# integration with HVV infrastructure   #
#########################################

# REVISION = 'DigShellExec.py REV : 1.00.00 10/09/20'
# print(REVISION)
import json
import os
import pandas as pd
import numpy as np
import fnmatch
import subprocess
# from ev100_dlog_postprocess import dlog_csv_post_process
import argparse
import glob
from datetime import date
import time


## Below section is for Runsequence set up ##
# runseq_json = r'C:\AXITestPrograms\Qualcomm\RUNSEQUENCE_Mar1_DEMO\go_RUNSEQUENCE.json'
# runseq_cmd = r'C:\AXITestPrograms\DigShell\DigShell.exe {0}'.format(runseq_json)
# print('\nCommand: ' + runseq_cmd)
# res = os.system(runseq_cmd)
# print('os.sytem execution result: ', res)
# print('\n**** EV100 Control Signal setup completed. DFT patterns execution coming next ****')


def digshell_exec(sn_to_append, log_dir, pat_type, voltage_mode, dest):
    """
    execute digshell to run DFT patterns
    :param sn_to_append: str
        serial number of the DUT (w/o "0x")
    :param log_dir: str
        directory to dump test log (.csv format).
    :param pat_type:
        atpg (int and saf) or tdf
    :param voltage_mode: str
        voltage modes associated with DFT patterns, e.g. svs, nom, tur
    :return:
    """

    # TODO Roshni: change pats.txt paths for Waipio once available; add functionality to select between projects so project-specific pats.txt paths can be used
    if pat_type == 'tdf':
        pats_base_dir = r'F:\ATPG_CDP\Lahaina\r2\pattern_execution\Pattern_list\Seed_file_DO_NOT_modify\tdf'
    elif pat_type == 'atpg':
        pats_base_dir = os.path.join(dest, 'pattern_execution', 'pattern_list')

    temp_path = r'\\qctdfsrt\prj\vlsi\vetch_pst\jianingz\handler_integration\temp_file_DO_NOT_MODIFY'
    exit_file = 'digshell_exec_success.txt'
    exit_file_path = os.path.join(temp_path, exit_file)
    if os.path.exists(exit_file_path):
        print('\n****** Removing previous {}. ******'.format(exit_file))
        try:
            os.remove(exit_file_path)
            print('\n****** Previous {} removed. ******'.format(exit_file))
        except Exception as e:
            print(e)
            os.rename(exit_file_path, os.path.join(temp_path, 'renamed.txt'))
    else:
        print('\n****** No {} found.******'.format(exit_file))

    # TODO Roshni: add functionality to select between projects so project-specific JSON file can be loaded
    jsonfile = r"C:\vi\pats_abs\go_" + chip_version.capitalize() + "_abs.json"
    tempfile = r"C:\AXITestPrograms\DigShell" + "\\" + chip_version + r"_temp.json"
    with open(jsonfile) as f:
        data = json.load(f)
    # print(json.dumps(data, sort_keys=True, indent=4))

    ## define paths to pats.txt ##
    # pat_txt_dir = r'F:\demo\demo_test_022421'  # svs INT/SAF demo pattern
    pat_txt_dir = os.path.join(pats_base_dir, voltage_mode)  # svs INT/SAF demo pattern
    print('\n****** DFT patterns will be loaded from {} ******'.format(pat_txt_dir))
    list_dirs_exclude = ['SAF']
    # if test_dir == r'F:\demo\demo_test_022421' or r'F:\demo\demo_test_022421 - Copy' :
    #     summary_dlog = sn + '_demo_test'
    # else:
    #     summary_dlog = sn + '_INT_test_results'
    # summary_dlog = sn + '_INT_nom_results'
    # summary_dlog = sn + '_test_new'

    sn = '0x' + sn_to_append
    summary_dlog = sn + '_dft_test_results'  # fixed log naming for jenkins flow

    ## user to modify parameters in temp json ##
    freq_to_test = 0
    freq_step = 0

    data['FAILPINS'] = "ALL_PINS"
    data['BREAKPOINT'] = 0
    data["LOOPS"] = 1
    data["SERVER_LOOP"] = 0
    data["RESET_AT_END"] = 2
    data["ADDER0"] = freq_step
    data["ADDER1"] = freq_step
    data["T0FREQ"] = freq_to_test
    data["T1FREQ"] = freq_to_test
    data["PATMODE"] = "ABSOLUTE"
    data["SKIPLOAD"] = 0
    ############################################

    today = date.today()
    base_dir = os.path.join(dest, 'pattern_execution', 'execution_dlog')

    today_dir = os.path.join(base_dir, 'dft_run_' + str(today))
    if not os.path.exists(today_dir):
        os.makedirs(today_dir)

    # modify PATS.txt name and relevant directories dynamically
    for root, dirs, files in os.walk(pat_txt_dir, topdown=True):
        # exclude folers
        dirs[:] = [d for d in dirs if d not in list_dirs_exclude]

        for file in files:

            if fnmatch.fnmatch(file, 'PATS_*.txt'):
                par_dir = root + '\\'
                # par_dir = log_dir + '\\'
                data['PATDIR'] = par_dir
                # dlog_dir = today_dir + r'dlog\' + sn + r'\' + voltage_mode + r'\'
                dlog_dir = os.path.join(today_dir, 'dlog', sn)
                dlog_dir = dlog_dir + '\\'
                data['DLOGDIR'] = dlog_dir
                # fail_dir = today_dir + r'failures\' + sn + r'\' + voltage_mode + r'\'
                fail_dir = os.path.join(today_dir, 'failures', sn)
                fail_dir = fail_dir + '\\'
                data['FAILDIR'] = fail_dir

                data["PATFILE"] = file

                with open(tempfile, 'w') as write_file:
                    x = json.dump(data, write_file, indent=4)

                command = r'C:\AXITestPrograms\DigShell\DigShell.exe {0}'.format(tempfile)
                print('\nCommand: ' + command)
                res = os.system(command)
                print('Printing DIGSHELL execution result:')
                print(res)
                # subprocess.call(command, shell=True)

                # print('os.sytem execution result: ', res)

                # generate summary dlog csv
                # dlog_csv_post_process(dlog_dir, output_dir, summary_dlog, file)
                file_path = os.path.join(root, file)
                print("execution logdir: " + log_dir)
                dlog_csv_post_process(dlog_dir, log_dir, summary_dlog, file_path, voltage_mode)

    # print('\n**** Test execution completed. Data processing in progress ****')
    print('\n****** Test execution completed. ******')

    with open(exit_file_path, 'w') as f:
        pass
    print('\n****** {} created. ******'.format(exit_file))

    time.sleep(6)


def dlog_csv_post_process(dlog_dir, output_dir, output_csv_name, pats_txt, voltage_mode):
    """
    process individual dlog csv's to generate a summary test log csv
    :param dlog_dir: str
        directory to individual dlog csv
    :param output_dir: str
        directory to dump test log (.csv format)
    :param output_csv_name: str
        test log name (w/o .csv)
    :param pats_txt: str
        pats.txt file name
    :param voltage_mode: str
        voltage modes associated with DFT patterns, e.g. svs, nom, tur
    """
    # csv_path = os.path.join(dlog_dir, '*.csv')
    csv_path = dlog_dir + '*.csv'
    # csv_path = "E:\johnny\dlog_csv_debugging\int_and_saf.csv"
    list_all_csv = glob.glob(csv_path)

    try:
        # grab the latest csv
        csv_to_edit = max(list_all_csv, key=os.path.getctime)
        # csv_to_edit = "E:\johnny\dlog_csv_debugging\int_and_saf.csv"
    except ValueError:
        print('\n*** Error! No dlog csv exists.')
    except Exception as e:
        print(e)
        print('\n*** Error! Please refer to Traceback message.')
    else:
        # load csv
        # df_dlog_raw = pd.read_csv(csv_to_edit, index_col=False)
        df_dlog_raw = pd.read_csv(csv_to_edit, index_col=False)
        # grab all gpio columns
        df_dlog_gpio = df_dlog_raw.filter(regex='gpio_')
        # add gpio names to fail count value
        df_dlog_gpio_new = df_dlog_gpio.astype(str).apply(lambda x: x.name + ':' + x)
        # replace 0 fail values with null
        df_dlog_gpio_new.replace(':0', np.nan, regex=True, inplace=True)
        # add a column to combine all the fail pin info
        df_dlog_gpio_new['fail_pin'] = df_dlog_gpio_new.apply(lambda x: ','.join(x.dropna()), axis=1)

        # columns to extract data from
        list_cols = ['Date_Time', 'PatternName', 'Failures']
        # trim raw dlog df
        df_dlog = df_dlog_raw[list_cols]
        # add in fail pin column
        df_dlog['fail_pin'] = df_dlog_gpio_new['fail_pin']

        # add a column for PATS.txt name
        df_dlog['pats_txt'] = pats_txt
        # print('df_dlog:\n', df_dlog.to_string())
        df_dlog['voltage_mode'] = voltage_mode

        # set up for csv output
        print("post process output: " + output_dir)
        csv_output = os.path.join(output_dir, output_csv_name + '.csv')
        print("post process output full path: " + csv_output)
        if not os.path.exists(output_dir):
            csv_output = os.path.join(output_dir + "_0xbeeeeeef", output_csv_name + '.csv')
        if os.path.exists(csv_output):
            try:
                print(f'\n*** Saving trimmed dlog csv to {csv_output}')
                df_dlog.to_csv(csv_output, header=False, index=False, mode='a')
            except PermissionError as e:
                print(e)
                csv_output_temp = os.path.join(output_dir, output_csv_name + '_backup.csv')
                print(f'\n*** Saving to {csv_output_temp} instead.')
                if os.path.exists(csv_output_temp):
                    df_dlog.to_csv(csv_output_temp, header=False, index=False, mode='a')
                else:
                    df_dlog.to_csv(csv_output_temp, header=True, index=False, mode='w')
            else:
                print('\n***Dlog csv saving completed.')
        else:
            df_dlog.to_csv(csv_output, header=True, index=False, mode='w')
            print('\n*** Dlog csv saving completed.')


def main():
    parser = argparse.ArgumentParser(description='Execute DFT patterns with EV100 Digshell program')
    parser.add_argument('-sn', dest='sn', type=str, help='sn of the part from its fuse dump')
    parser.add_argument('-log_dir', dest='log_dir', type=str,
                        help='directory to store the summary csv of each individual dft pattern test result')
    parser.add_argument('-pat_type', dest='pat_type', type=str,
                        help='DFT pattern type')
    parser.add_argument('-voltage_mode', dest='voltage_mode', type=str,
                        help='voltage mode associated with DFT patterns')
    parser.add_argument('-dest', dest='dest', type=str,
                        help='output logs destination')
    args = parser.parse_args()

    freq_mode = str(args.voltage_mode).upper()
    if freq_mode == "LSVS":
        freq_mode = "SVSD1"

    # call digshell_exec()
    digshell_exec(args.sn, args.log_dir, args.pat_type, freq_mode, args.dest)
    print("main log_dir: " + args.log_dir)


if __name__ == '__main__':
    main()