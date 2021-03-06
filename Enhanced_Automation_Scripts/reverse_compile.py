# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ #
# This automated script is used to run through the vector file paths to Check SVM Size and LVM Size
# Ideally for EV100: Each pattern SVM size should be less than 8KB, and Cumulative LVM size for the group of patterns should be less tha 128MB
# Some patterns are larger in size and cannot be fed into EV100 to run those and these patterns fail to load
# The Main goal of this script is split into 2 Categories:
#       1. Run a reverse compile command on all the patterns: By doing this we can extract the Current SVM and LVM size
#       2. Uncompress, Reconvert and recompile: This is performed only on the patterns that Greater than or equal to 8KB SVM size
#           When Uncompressed and recompiled, it also changes the Cycle count from .dp file
# Finally we extract the following values that is needed for pats.txt generation
# mode: freq_mode(NOM/SVS/TUR etc.,), vector_type: Vector_type(PROD/RMA/EVAL), Filepath: filepath to .do,
# block: split dirname from filepath, pattern_name: Split Basename to get .do name, CycleCount: Extracting Cycle count from .dp file for executing the pattern on EV100
# SVM_SIZE: Extracted SVM size from .map file output by reverse compile, LVM_SIZE: Extracted LVM size from .map file output by reverse compile
# TODO: This flow should further be refactored for efficient usage
# TODO: Save to CSV continously
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ #
import os
import re
import subprocess
import pandas as pd
import fileinput

SVM = []
LVM = []
freq_mode = []
Vector_type = "PROD"
block = []
filepath = []
pattern_name = []
CycleCount = []

path = input("Enter the Path for sequential SVM check: \n")
for root, dirs, files in os.walk(path):
    for file in files:
        if file.startswith('MBURST') and file.endswith('.do'):
            do_dp_file_path = os.path.join(root, file)
            filepath.append(do_dp_file_path)
            block.append(root)
            do_file_path = os.path.dirname(do_dp_file_path)
            print("Reverse Compile performing in path : ", do_file_path)
            do_file = os.path.splitext(os.path.basename(do_dp_file_path))[0]
            pattern_name.append(os.path.basename(do_dp_file_path))
            mode = (do_file_path.split("\\device\\test")[0].split('\\'))[-1]
            freq_mode.append(mode)
            command = 'ddrc192 -o ' + do_file + '.rc ' + do_file + '.do -M ' + do_file + '.map'
            rev_comp = os.path.join(do_file_path, 'reverse_compile.bat')
            with open(rev_comp, 'w') as f:
                f.write(command)
            print("Starting to reverse compile...............")
            reverse_compile = subprocess.Popen("reverse_compile.bat", shell=True, cwd=root).communicate()
            print("Reverse compiling Successful!!!!")
            map_file = os.path.join(root + '\\' + do_file + ".map")
            print("Extracting SVM and LVM size................")
            with open(map_file, 'r') as f:
                lines = f.readlines()
                svm = int(lines[0][17:])
                lvm = int(lines[1][17:])
                SVM.append(svm)
                LVM.append(lvm)
                print("SVM SIZE: ", svm)
                print("LVM SIZE: ", lvm)
            if svm >= 8000:
                print("SVM Size exceeds 8KB in path: ", root)
                cfg_path = root.split('\\device\\test')[0]
                modify_cfg = os.path.join(cfg_path) + "\\waipio_WY_dft_universal_v1.cfg"
                print("Modifying Configuration file reduce SVM Size...........")
                with fileinput.FileInput(modify_cfg, inplace=True, backup='.bak') as f:
                    i = 1
                    for line in f:
                        if i < 32:
                            print(line.replace("OPTIMIZED\t2", "OPTIMIZED\t1").replace("#MINREPEAT  64", "MINREPEAT   2"), end='')
                    i += 1
                modify_cfg = os.path.join(cfg_path) + "\\conversion.bat"
                print("Uncompressing STIL files and Converting to .dp.............. ")
                with fileinput.FileInput(modify_cfg, inplace=True, backup='.bak') as f:
                    for line in f:
                        print(line.replace("+o2", "+o1"), end='')
                conversion_bat = subprocess.Popen("conversion.bat", shell=True, cwd=root).communicate()
                comp_path = os.path.join(root) + "\\test_TimeSets.h"
                print("Modifying Scan clock period to 16ns......................... ")
                with fileinput.FileInput(modify_cfg, inplace=True, backup='.bak') as f:
                    for line in f:
                        print(line.replace("#define PERIOD 20.0000ns ;", "#define PERIOD 16.0000ns ;"), end='')
                print("Compiling .dp file to .do......................")
                compile_bat = subprocess.Popen("compileAll.bat", shell=True, cwd=root).communicate()
                print("Reverse compiling to extract new SVM size.......")
                reverse_compile = subprocess.Popen("reverse_compile.bat", shell=True, cwd=root).communicate()
                with open(map_file, 'r') as f:
                    lines = f.readlines()
                    svm = int(lines[0][17:])
                    lvm = int(lines[1][17:])
                    SVM.append(svm)
                    LVM.append(lvm)
                    print("Reduced SVM and LVM size after uncompressing..............")
                    print("SVM SIZE: ", svm)
                    print("LVM SIZE: ", lvm)
            dp_file = os.path.join(root + '\\' + do_file + ".dp")
            print("Extracting Cycle count for pattern : ", do_file)
            with open(dp_file, 'rb') as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                last_line = f.readline().decode()
            match = re.search('Cycles:(\d+)', last_line, re.IGNORECASE)
            if match:
                cycle_count = int(match.group(1))
                print("Cycle count extracted: ", cycle_count)
            else:
                print('No cycle count can be found!\n')
                cycle_count = 0
            CycleCount.append(cycle_count)

df = pd.DataFrame({"mode": freq_mode, "vector_type": Vector_type, "Filepath": filepath, "block": block, "pattern_name": pattern_name,
                   "SVM_SIZE": SVM, "LVM_SIZE": LVM, "CycleCount": CycleCount})
print(df)
df.to_csv(r"E:\Hitha\test\Test_SVM_LVM.csv", index=False)