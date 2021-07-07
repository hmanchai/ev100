import collections
import glob
import os
import re
import numpy as np
import pandas as pd
import fnmatch
import matplotlib.pyplot as plt


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
        path = glob.glob(dlog_dir + "\\*\\*\\")
        freq_mode = re.search("(.*)(\\\)(.*)(\\\)$", path[0]).group(3)
        output_dir = os.path.join(output_dir, freq_mode, run)

        self.create_folder(output_dir)

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
                    if int(dlog_output.at[0,'PatternRunTime']) > 16:
                        sn_df.at[pattern_index, sn] = 'T'
                    pattern_index += 1

        pattern_rows = list(pattern_names.items())
        df_data = pd.DataFrame(pattern_rows, columns=["Pattern Name", "Index"])
        regex = "(tk_atpg_)(.*)"
        df_data["DFT Type"] = df_data.apply(lambda x: re.search(regex, x["Pattern Name"]).group(2).split("_")[0].upper(),
                                            axis=1)
        df_data = pd.concat([df_data, sn_df], axis = 1)
        df_data.pop('Index')
        output_file = os.path.join(output_dir, freq_mode + "_postprocess_failures.csv")
        df_data.to_csv(output_file, index=False, sep=',', header=True, mode='w')
        return output_file

    def create_folder(self, dir):
        """
        Create the directory if not exists.

        :param dir: str
            directory to create
        """
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except Exception:
                print("Error! Could not create directory " + dir)

    def passing_rate_graph(self, output_path):
        df_data = pd.read_csv(output_path)
        output_path = re.search("(.*)(\\\)(.*)$", output_path).group(1)
        freq_mode = re.search("(.*)(\\\)(.*)(\\\)(.*)$", output_path).group(3)
        run = re.search("(.*)(\\\)(.*)$", output_path).group(3)
        passing_rate = {"INT": "", "SAF": "", "TDF": ""}
        for dft_type in passing_rate.keys():
            pass_fail = {"pass": "", "fail": ""}
            total_chips = 0
            passing = 0
            df_vector_type = df_data[df_data['DFT Type'].str.match(dft_type.upper())]
            if df_vector_type.shape[0] == 0:
                del passing_rate[dft_type]
                break
            df_vector_type.pop('Pattern Name')
            df_vector_type.pop('DFT Type')
            for col in df_vector_type:
                total_chips += 1
                if df_vector_type[col].isnull().sum() == df_vector_type.shape[0]:
                    passing += 1
            pass_fail["pass"] = passing
            pass_fail["fail"] = total_chips - passing
            title = freq_mode + " " + dft_type + " Pass or Fail"
            plt.title(title)
            plt.ylabel("# of Chips")
            self.add_labels(list(pass_fail.keys()), list(pass_fail.values()))
            rates = pd.Series(pass_fail)
            colors = list('bgrkymc')

            rates.plot(
                kind='bar',
                color=colors,
            )
            output_plot = os.path.join(output_path, title + '.jpg')
            plt.savefig(output_plot)

            if total_chips != 0:
                passing_rate[dft_type] = (passing / float(total_chips)) * 100

        title = freq_mode + " " + "_".join(passing_rate.keys()) + " Passing Percentage"
        plt.title(title)
        plt.xlabel('Pattern Category')
        plt.ylabel('Percentage Passing (%)')
        self.add_labels(list(passing_rate.keys()), list(passing_rate.values()), True)
        plt.ylim(0, 100)
        rates = pd.Series(passing_rate)
        colors = list('bgrkymc')

        rates.plot(
            kind='bar',
            color=colors,
        )

        output_plot = os.path.join(output_path, title + '.jpg')
        plt.savefig(output_plot)


    def add_labels(self, x, y, percent = False):
        for i in range(len(x)):
            if percent:
                plt.text(i, y[i], str(round(y[i], 2)) + "%", ha='center', fontweight='bold')
            else:
                plt.text(i, y[i], str(round(y[i], 2)), ha='center', fontweight = 'bold')

    def tdf_shmoo_graph(self):
        print('tdf')

def main():
    chip_version = 'Waipio'
    base_dir = r"G:\ATPG_CDP"
    run = "dft_run_2021-07-07"
    output_dir = r"G:\ATPG_CDP\pattern_execution\output"
    post = PostProcess()
    output_file = post.dlog_csv_post_process(base_dir, run, output_dir)
    post.passing_rate_graph(output_file)


if __name__ == "__main__":
    main()