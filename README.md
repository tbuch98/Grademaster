# Grademaster
Place the following files together in a directory

(1) grademaster_original.py
(2) grade_dummy_file_v2.csv

File (1) is the grademaster python script
File (2) is the grade data file

To run on UB CCR please enter the following

module load python/py38-anaconda-2020.11
python grademaster_original.py --data_file grade_dummy_file_v2.csv

The first command loads the python module and the second runs
the grademaster script with the data file being read in as an option
