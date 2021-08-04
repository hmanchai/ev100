import collections
import csv
import glob
import os
import re
import numpy as np
import pandas as pd
import fnmatch
import matplotlib.pyplot as plt
import copy
import seaborn as sns
from matplotlib import image
from matplotlib.colors import LinearSegmentedColormap


class PostProcess():
    """
    class to hold all post processing scripts
    generates graphs and csv files
    """

    def dlog_csv_post_process(self, base_dir, runs, output_dir, exclude_chips):
        """
        process individual dlog csv's to generate a summary test log csv of all runs
        removes all duplicates (saves first occurring duplicate)
        :param base_dir: str
            base directory for all patterns - folder above pattern_execution (pattern_execution, execution_dlog, run, dlog)
            all added automatically to filepath
        :param runs: list str
            run folder names - folder level above dlog
        :param output_dir: str
            output directory to store postprocessing output
        :param exclude_chips: list str
            sn of chips to exclude from post processing
        """
        for run in runs:
            # csv_path = os.path.join(dlog_dir, '*.csv')
            dlog_dir = os.path.join(base_dir, "pattern_execution", "execution_dlog", run, 'dlog')
            pattern_names = collections.OrderedDict()
            pattern_index = 0

            list_results = []
            sn_list = []
            sn_files = {}
            #path = glob.glob(dlog_dir + "\\*\\*\\")

            # freq_mode = re.search("(.*)(\\\)(.*)(\\\)$", path[0]).group(3)
            output_dir = os.path.join(output_dir)

            self.create_folder(output_dir)

            for d in os.listdir(dlog_dir):
                if d not in exclude_chips:
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
                        if int(dlog_output.at[0, 'PatternRunTime']) > 16:
                            sn_df.at[pattern_index, sn] = 'T'
                        pattern_index += 1

            pattern_rows = list(pattern_names.items())
            df_data = pd.DataFrame(pattern_rows, columns=["Pattern Name", "Index"])
            regex = "(tk_atpg_)(.*)"
            df_data["DFT Type"] = df_data.apply(
                lambda x: re.search(regex, x["Pattern Name"]).group(2).split("_")[0].upper(),
                axis=1)
            df_data["freq mode"] = df_data.apply(lambda x: "SVS" if re.search("svs_", x["Pattern Name"])
            else "TUR" if re.search("tur_", x["Pattern Name"])
            else "SVSD1" if re.search("svsd1_", x["Pattern Name"])
            else "NOM", axis=1)

            df_data["# failing"] = sn_df.notnull().sum(axis=1)
            df_data["# failing"].fillna("0", inplace=True)
            df_data = pd.concat([df_data, sn_df], axis=1)
            df_data.pop('Index')
            output_file = os.path.join(output_dir, "postprocess_failures.csv")
            if os.path.exists(output_file):
                df_data.to_csv(output_file, index=False, sep=',', header=False, mode='a')
            else:
                df_data.to_csv(output_file, index=False, sep=',', header=True, mode='w')
        final = pd.read_csv(output_file)
        final = final.drop_duplicates(subset=['Pattern Name'], keep='first')
        final.to_csv(output_file, index=False, sep=',', header=True, mode='w')

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

    # def passing_rate_graph(self, output_path):
    #     """
    #     Determine passing statistics and plot individual bar graphs
    #     :param output_path:
    #     :type output_path:
    #     """
    #     df_data = pd.read_csv(output_path)
    #     output_path = re.search("(.*)(\\\)(.*)$", output_path).group(1)
    #     freq_mode = re.search("(.*)(\\\)(.*)(\\\)(.*)$", output_path).group(3)
    #     run = re.search("(.*)(\\\)(.*)$", output_path).group(3)
    #     passing_rate = {"INT": "", "SAF": "", "TDF": ""}
    #     for dft_type in passing_rate.keys():
    #         pass_fail = {"pass": "", "fail": ""}
    #         total_chips = 0
    #         passing = 0
    #         df_vector_type = df_data[df_data['DFT Type'].str.match(dft_type.upper())]
    #         if df_vector_type.shape[0] == 0:
    #             del passing_rate[dft_type]
    #             break
    #         df_vector_type.pop('Pattern Name')
    #         df_vector_type.pop('DFT Type')
    #         for col in df_vector_type:
    #             total_chips += 1
    #             if df_vector_type[col].isnull().sum() == df_vector_type.shape[0]:
    #                 passing += 1
    #         pass_fail["pass"] = passing
    #         pass_fail["fail"] = total_chips - passing
    #         title = freq_mode + " " + dft_type + " Pass or Fail"
    #         plt.title(title)
    #         plt.ylabel("# of Chips")
    #         self.add_labels(list(pass_fail.keys()), list(pass_fail.values()))
    #         rates = pd.Series(pass_fail)
    #         colors = list('bgrkymc')
    #
    #         rates.plot(
    #             kind='bar',
    #             color=colors,
    #         )
    #         output_plot = os.path.join(output_path, title + '.jpg')
    #         plt.savefig(output_plot)
    #
    #         if total_chips != 0:
    #             passing_rate[dft_type] = (passing / float(total_chips)) * 100
    #
    #     title = freq_mode + " " + "_".join(passing_rate.keys()) + " Passing Percentage"
    #     plt.title(title)
    #     plt.xlabel('Pattern Category')
    #     plt.ylabel('Percentage Passing (%)')
    #     self.add_labels(list(passing_rate.keys()), list(passing_rate.values()), True)
    #     plt.ylim(0, 100)
    #     rates = pd.Series(passing_rate)
    #     colors = list('bgrkymc')
    #
    #     rates.plot(
    #         kind='bar',
    #         color=colors,
    #     )
    #
    #     output_plot = os.path.join(output_path, title + '.jpg')
    #     plt.savefig(output_plot)

    def all_data_compiled(self, output_dir):
        """
        Based on summary csv data, generates summary tables and graphs to depict different passing rate statistics for
        all freq modes and dft types
        :param output_dir: base directory where graphs and tables will be generated
        :type output_dir: str
        """
        paths = glob.glob(output_dir + '\*.csv')
        passing_rate = {"INT": [], "SAF": [], "TDF": []}
        failing_vectors = []
        output_path = paths[0]
        df_map = pd.read_csv(output_path)
        freq_modes = df_map['freq mode'].unique()
        dft_options = ["INT", "SAF", "TDF"]
        for freq_mode in freq_modes:
            df_data = df_map[df_map["freq mode"].str.match(freq_mode)]
            for dft_type in passing_rate.keys():
                total_chips = 0
                passing = 0
                df_vector_type = df_data[df_data['DFT Type'].str.match(dft_type.upper())]

                df_vector_type.pop('Pattern Name')
                df_vector_type.pop('DFT Type')
                df_vector_type.pop('freq mode')
                df_vector_type.pop('# failing')
                failing_vectors.append(df_vector_type.notnull().sum(axis=0).tolist())
                for col in df_vector_type:
                    total_chips += 1
                    if df_vector_type[col].isnull().sum() == df_vector_type.shape[0]:
                        passing += 1

                if df_vector_type.shape[0] != 0:
                    rate_list = passing_rate.get(dft_type)
                    rate_list.append((passing / float(total_chips)) * 100)
                    passing_rate[dft_type] = rate_list

                else:
                    rate_list = passing_rate.get(dft_type)
                    rate_list.append(0.0)
                    passing_rate[dft_type] = rate_list

        total_parts = copy.deepcopy(list(passing_rate.values()))
        for i in range(len(total_parts)):
            for j in range(len(total_parts[0])):
                total_parts[i][j] = int((total_parts[i][j] / 100.00) * total_chips)

        df_failing_vectors = pd.DataFrame(failing_vectors, columns=list(df_vector_type))
        df_failing_vectors.insert(loc=0, column='freq mode', value="")
        df_failing_vectors.insert(loc=1, column='DFT Type', value="")
        len_rows = df_failing_vectors.shape[0]
        len_type = len(dft_options)

        for r in range(int(len_rows / len_type)):
            for j in range(len_type):
                df_failing_vectors.iloc[r * len_type + j, 1] = dft_options[j]
                df_failing_vectors.iloc[r * len_type + j, 0] = freq_modes[r]

        df_passing_rate = pd.DataFrame(np.array(list(passing_rate.values())).T.tolist(),
                                       columns=list(passing_rate.keys()), index=freq_modes)
        df_parts_passing = pd.DataFrame(np.array(total_parts).T.tolist(),
                                        columns=list(passing_rate.keys()), index=freq_modes)
        df_parts_passing["total #"] = total_chips

        self.create_summary_tables(df_failing_vectors, df_parts_passing, df_passing_rate, freq_modes, output_dir)

        self.plot_multibar_graphs(freq_modes, output_dir, passing_rate, total_parts)

    def plot_multibar_graphs(self, freq_modes, output_dir, passing_rate, total_parts):
        """
        Plots passing percentage and passing number of chips
        :param freq_modes: frequency modes run
        :type freq_modes: list str
        :param output_dir: base directory where graphs will be saved
        :type output_dir: str
        :param passing_rate: Passing rate of chips percentage for each frequency mode at each dft type
        :type passing_rate: dictionary
        :param total_parts: total number of chips
        :type total_parts: int
        """
        title = "_".join(freq_modes) + " " + " Passing Percentage"
        plt.title(title)
        X_axis = np.arange(len(freq_modes))
        plt.bar(X_axis - 0.2, list(passing_rate.values())[0], 0.2, label="INT")
        plt.bar(X_axis, list(passing_rate.values())[1], 0.2, label="SAF")
        plt.bar(X_axis + 0.2, list(passing_rate.values())[2], 0.2, label="TDF")
        plt.xticks(X_axis, freq_modes)
        plt.xlabel('Pattern Category')
        plt.ylabel('Percentage Passing (%)')
        plt.legend()
        spacing = [-.2, .8, 1.8, 2.8]
        self.add_labels(list(passing_rate.values()), spacing, True)
        plt.ylim(0, 100)
        output_plot = os.path.join(output_dir, title + '.jpg')
        plt.savefig(output_plot)
        plt.clf()
        title = "_".join(freq_modes) + " " + " # of Passing Parts"
        plt.title(title)
        X_axis = np.arange(len(freq_modes))
        plt.bar(X_axis - 0.2, total_parts[0], 0.2, label="INT")
        plt.bar(X_axis, total_parts[1], 0.2, label="SAF")
        plt.bar(X_axis + 0.2, total_parts[2], 0.2, label="TDF")
        plt.xticks(X_axis, freq_modes)
        plt.xlabel('Pattern Category')
        plt.ylabel('# of Passing Parts')
        plt.legend()
        spacing = [-.2, .8, 1.8, 2.8]
        self.add_labels(total_parts, spacing)
        output_plot = os.path.join(output_dir, title + '.jpg')
        plt.savefig(output_plot)

    def create_summary_tables(self, df_failing_vectors, df_parts_passing, df_passing_rate, freq_modes, output_dir):
        """
        write summary tables to csv
        """
        summary_data = os.path.join(output_dir, "_".join(freq_modes) + " summary data.csv")
        with open(summary_data, 'w', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Parts Passing Rate (%)"])
        df_passing_rate.to_csv(summary_data, index=True, sep=',', header=True, mode='a')
        with open(summary_data, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow("")
            writer.writerow(["# of Parts Passing"])
        df_parts_passing.to_csv(summary_data, index=True, sep=',', header=True, mode='a')
        with open(summary_data, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow("")
            writer.writerow(["# of Vectors Failed by Part"])
        df_failing_vectors.to_csv(summary_data, index=False, sep=',', header=True, mode='a')

    def add_labels(self, data, pos, percent=False):
        """
        Add labels to bar graphs with appropriate spacing to properly mark each bar of multibar graph
        :param data: value of bar
        :type data: float
        :param pos: spacing to label each bar at correct centered position
        :type pos: float
        :param percent: Should label include percent sign
        :type percent: boolean
        """
        for value in data:
            for i in range(len(value)):
                if percent:
                    plt.text(pos[i], value[i], str(round(value[i], 2)) + "%", ha='center', fontweight='bold',
                             fontsize="xx-small")
                else:
                    plt.text(pos[i], value[i], str(round(value[i], 2)), ha='center', fontweight='bold',
                             fontsize="xx-small")
                pos[i] = pos[i] + .2

    def tdf_shmoo_graph(self, shmoo_data, output_dir):
        """
        Create color graded graph to represent passing chips at various freq and volt combinations (shmoo table)
        """
        columns = ['Freq Mode', 'Volts', "MHz", "Temp", "Passing"]
        # frames = [mvp_df, sub_df]
        # mvp_df = pd.concat(frames)
        df_shmoo = pd.DataFrame(columns=columns)

        list_csv = glob.glob(shmoo_data + "\\*")
        for data in list_csv:
            with open(data) as fh:
                i = 0
                reader = csv.reader(fh, delimiter=",")
                for row in reader:
                    if i == 1:
                        freq_mode = row[1]
                        break
                    i += 1
            df = pd.read_csv(data, skiprows=5, header=None)
            df.insert(0, "Freq Mode", freq_mode, True)
            df = df.set_axis(columns, axis=1)
            df["Passing"] = df.apply(lambda x: 1 if re.search("PASS", x["Passing"])
            else 0, axis=1)
            frames = [df_shmoo, df]
            df_shmoo = pd.concat(frames)

        pivot = df_shmoo.pivot_table(columns=['MHz'], index=['Freq Mode', 'Volts'], values=['Passing'], aggfunc=np.sum)
        cm = LinearSegmentedColormap.from_list(
            name='test',
            colors=sns.color_palette("RdYlGn", 6)
        )
        df_styled = pivot.style.background_gradient(cmap=cm)

        df_styled.to_excel(output_dir + "\\tdf_shmoo.xlsx")


def main():
    """
    Post process results of runs for dft vectors and various freq modes
    """
    chip_version = 'Waipio'
    base_dir = r"G:\ATPG_CDP"
    runs = ["dft_run_2021-07-06", "dft_run_2021-07-07", "dft_run_2021-07-08"]
    output_dir = r"G:\ATPG_CDP\pattern_execution\output_new"
    # base_dir = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop"
    # runs = ["dft_run_2021-07-01"]
    output_dir = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\pattern_execution\output"
    post = PostProcess()
    post.dlog_csv_post_process(base_dir, runs, output_dir, ["0x0x3C273C5"])

    post.all_data_compiled(output_dir)
    post.tdf_shmoo_graph(r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\data", output_dir)


if __name__ == "__main__":
    main()
