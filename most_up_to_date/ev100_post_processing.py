import collections
import glob
import numbers
import os
import re
import numpy as np
import pandas as pd
import fnmatch


class PostProcess():
    def dlog_csv_post_process(self, base_dir, run, output_dir):
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
        dlog_dir = os.path.join(base_dir, 'pattern_execution', 'execution_dlog', run, 'dlog')
        pattern_names = collections.OrderedDict()
        pattern_index = 0

        list_results = []
        sn_list = []
        sn_files = {}

        for d in os.listdir(dlog_dir):
            sn_dir = os.path.join(dlog_dir, d)
            csv_path = sn_dir + '\\' + '*.csv'
            list_all_csv = glob.glob(csv_path)
            sn_files[d] = list_all_csv
            sn_list.append(d)
        # csv_path = "E:\johnny\dlog_csv_debugging\int_and_saf.csv"
        sn_df = pd.DataFrame(columns=sn_list)
        for sn, paths in sn_files.items():
            for path in paths:
                dlog_output = pd.read_csv(path)
                pattern = dlog_output.at[0, 'PatternName']
                if pattern in pattern_names:
                    index = pattern_names.get(pattern)
                    if int(dlog_output['Failures']) != 0:
                        sn_df.at[index, sn] = 'F'
                else:
                    pattern_names[pattern] = pattern_index
                    if int(dlog_output.at[0, 'Failures']) != 0:
                        sn_df.at[pattern_index, sn] = 'F'
                    pattern_index += 1

        pattern_rows = list(pattern_names.items())
        df_data = pd.DataFrame(pattern_rows, columns=["vector name", "Index"])
        df_data = pd.concat([df_data, sn_df], axis = 1)
        df_data.pop('Index')
        output_path = os.path.join(output_dir, run + "_postprocess.csv")
        df_data.to_csv(output_path, index=False, sep=',', header=True, mode='w')

        # try:
        #     # grab the latest csv
        #     csv_to_edit = max(list_all_csv, key=os.path.getctime)
        #     # csv_to_edit = "E:\johnny\dlog_csv_debugging\int_and_saf.csv"
        # except ValueError:
        #     print('\n*** Error! No dlog csv exists.')
        # except Exception as e:
        #     print(e)
        #     print('\n*** Error! Please refer to Traceback message.')
        # else:
        #     # load csv
        #     # df_dlog_raw = pd.read_csv(csv_to_edit, index_col=False)
        #     df_dlog_raw = pd.read_csv(csv_to_edit, index_col=False)
        #     # grab all gpio columns
        #     df_dlog_gpio = df_dlog_raw.filter(regex='gpio_')
        #     # add gpio names to fail count value
        #     df_dlog_gpio_new = df_dlog_gpio.astype(str).apply(lambda x: x.name + ':' + x)
        #     # replace 0 fail values with null
        #     df_dlog_gpio_new.replace(':0', np.nan, regex=True, inplace=True)
        #     # add a column to combine all the fail pin info
        #     df_dlog_gpio_new['fail_pin'] = df_dlog_gpio_new.apply(lambda x: ','.join(x.dropna()), axis=1)
        #
        #     # columns to extract data from
        #     list_cols = ['Date_Time', 'PatternName', 'Failures']
        #     # trim raw dlog df
        #     df_dlog = df_dlog_raw[list_cols]
        #     # add in fail pin column
        #     df_dlog['fail_pin'] = df_dlog_gpio_new['fail_pin']
        #
        #     # add a column for PATS.txt name
        #     df_dlog['pats_txt'] = pats_txt
        #     # print('df_dlog:\n', df_dlog.to_string())
        #     df_dlog['voltage_mode'] = voltage_mode
        #
        #     # set up for csv output
        #     csv_output = os.path.join(output_dir, output_csv_name + '.csv')
        #     if os.path.exists(csv_output):
        #         try:
        #             print(f'\n*** Saving trimmed dlog csv to {csv_output}')
        #             df_dlog.to_csv(csv_output, header=False, index=False, mode='a')
        #         except PermissionError as e:
        #             print(e)
        #             csv_output_temp = os.path.join(output_dir, output_csv_name + '_backup.csv')
        #             print(f'\n*** Saving to {csv_output_temp} instead.')
        #             if os.path.exists(csv_output_temp):
        #                 df_dlog.to_csv(csv_output_temp, header=False, index=False, mode='a')
        #             else:
        #                 df_dlog.to_csv(csv_output_temp, header=True, index=False, mode='w')
        #         else:
        #             print('\n***Dlog csv saving completed.')
        #     else:
        #         df_dlog.to_csv(csv_output, header=True, index=False, mode='w')
        #         print('\n*** Dlog csv saving completed.')

def main():
    chip_version = 'Waipio'
    base_dir = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop"
    run = "dft_run_2021-07-01"
    output_dir = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\post_test"
    post = PostProcess()
    post.dlog_csv_post_process(base_dir, run, output_dir)


if __name__ == "__main__":
    main()