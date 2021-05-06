#!/usr/bin/env python

SCRIPT_NAME = "grademaster"
SCRIPT_VERSION = "v0.3.0"
REVISION_DATE = "2021-04-11"
AUTHOR = """
Johannes Hachmann (hachmann@buffalo.edu) with contributions by:
   Mojtaba Haghighatlari (jobfile, Pandas dataframe) 
   Updates for CE451/551 by Tim Buchanan
"""
DESCRIPTION = "This program manages course grades and supplies grade projections for students"

###################################################################################################
# TASKS OF THIS SCRIPT:
# -assorted collection of tools for the analysis of grade data
###################################################################################################

import sys
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from optparse import OptionParser

#Email module imports
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Store the date in yyyy-mm-dd format for use in the filenames of output files
today = str(datetime.now())
today = today[0:10]

###################################################################################################
# Inclusive grade cutoffs for each letter grade

grade_scale = {
 "A":  {"low": 96, "high":100},
 "A-": {"low": 91, "high":95},
 "B+": {"low": 86, "high":90},
 "B" : {"low": 81, "high":85},
 "B-": {"low": 76, "high":80},
 "C+": {"low": 71, "high":75},
 "C" : {"low": 66, "high":70},
 "C-": {"low": 61, "high":65},
 "D+": {"low": 56, "high":60},
 "D" : {"low": 51, "high":55},
}

def percent_to_lettergrade(grade_scale, percentgrade):
    """(percent_to_lettergrade):
         This function converts percent grades into letter grades according to the grade_scale.
     """
    for (key, data) in grade_scale.items():
        if round(percentgrade) <= data['high'] and round(percentgrade) >= data['low']:
            return key
    return 'F'

###################################################################################################

def histogram(val_list):
    """(histogram_dict):
        Takes a list and returns a dictionary with histogram data. 
    """
    dict = {}
    for x in val_list:
        if x in dict:
            dict[x] += 1
        else:
            dict[x] = 1
    return dict

###################################################################################################

def main(opts,commline_list):
    """(main):
        Driver of the grademaster script.
    """
    # Now the standard part of the script begins
    time_start = time.time()

    # Open a logfile and errorfile for writing
    try:
        logfile = open("logfile.txt", 'w+')
        error_file = open("errorfile.txt", 'w+')
    except IOError:
        tmp_str = "Error: can't open .txt file"
        error_file.write(tmp_str)
        logfile.write(tmp_str)
    else:
        tmp_str = "...successfully opened the logfile and errorfile for writing "
        print(tmp_str)
        logfile.write(tmp_str + '\n')

    #################################################################################################
    # Print the current working directly to the logfile and error_file
    home_dir = os.getcwd()
    print(home_dir)
    tmp_str = home_dir
    logfile.write(tmp_str + '\n')
    error_file.write(tmp_str + '\n')

    tmp_str = "------------------------------------------------------------------------------ "
    print(tmp_str)
    logfile.write(tmp_str + '\n')
    error_file.write(tmp_str + '\n')
    #################################################################################################

    tmp_str = "Starting data acquisition..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')
    
    # Check that file exists, get filename from optparse
    if opts.data_file is None:
        tmp_str = "... data file not specified!"
        print(tmp_str)
        logfile.write(tmp_str + '\n')
        error_file.write(tmp_str + '\n')

        tmp_str = "Aborting due to missing data file!"
        logfile.write(tmp_str + '\n')
        error_file.write(tmp_str + '\n')
        sys.exit(tmp_str)

    tmp_str = "   ...reading in data..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Open the .csv file of the raw grade data
    rawdata_df = pd.read_csv(opts.data_file)

    tmp_str = "   ...cleaning data structure..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Remove empty entries
    for i in rawdata_df.columns:
        if 'Unnamed'in i:
            rawdata_df = rawdata_df.drop(i,1)

    tmp_str = "   ...identify keys..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Read top line of data file, which defines the keys
    keys_list = list(rawdata_df.columns)
    n_keys = len(keys_list)

    tmp_str = "   ...checking validity of data structure..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Check that the standard keys are in the data frame
    keys_to_check = ["Last name", "First name", "Student ID", "email"]
    for key in keys_to_check:
        if key not in keys_list[0:len(keys_list)-1]:
            print(type(key))
            tmp_str = "   ..." + key + " missing in data structure!"
            print(tmp_str)
            logfile.write(tmp_str + '\n')
            error_file.write(tmp_str + '\n')
            tmp_str = "Aborting due to invalid data structure!"
            logfile.write(tmp_str + '\n')
            error_file.write(tmp_str + '\n')
            sys.exit(tmp_str)

    # Check if all the grades are in float type (not object)
    for i in keys_list[4:]:
        if rawdata_df[i].dtypes == object:  
            tmp_str = "Aborting due to unknown grade format in column %s!" %i 
            logfile.write(tmp_str + '\n')
            error_file.write(tmp_str + '\n')
            sys.exit(tmp_str)

    # Count the number of HWs, midterms and final exam entries at this point
    # by iterating through keys_list
    # Initialize count at 0
    n_hws = 0
    n_midterms = 0
    n_final = 0

    for key in keys_list[4:]:
        if "HW" in key:
            n_hws += 1
        elif "M" in key:
            n_midterms += 1  
        elif "Final" in key:
            n_final += 1
        else:                
            tmp_str = "Aborting due to unknown key!"
            logfile.write(tmp_str + '\n')
            error_file.write(tmp_str + '\n')
            sys.exit(tmp_str)

    # Print out the number of students, HWs, midterms and finals that are currently in the gradebook
    # Summary of acquired data
    tmp_str = "------------------------------------------------------------------------------ "
    print(tmp_str)
    logfile.write(tmp_str + '\n')
    tmp_str = "Summary of acquired data:"
    print(tmp_str + '\n')
    logfile.write(tmp_str + '\n')

    tmp_str = "\tNumber of students:  " + str(len(rawdata_df))
    print(tmp_str + '\n')
    logfile.write(tmp_str + '\n')

    # This is the case where we are in any part of the semester that is before the final exam
    if n_final == 0:
        tmp_str = "\t" + str(n_hws) + "/10 HWs done. \n" + "\t" + str(n_midterms) + "/2 midterms done. No final exam data yet. "
        print(tmp_str + '\n')
        logfile.write(tmp_str + '\n')

    # This is the case where we are completely done with the semester (all HWs, midterms, and final is in)
    if n_final == 1 and (n_hws == 10 and n_midterms == 2):
        tmp_str = "\t" + str(n_hws) + "/10 HWs \n\t" + str(n_midterms) + "/2 midterms \n\t" + str(n_final) + "/1 final exam \n\tSuccess! All grades are in."
        print(tmp_str + '\n')
        logfile.write(tmp_str + '\n')

    # This is the case where the final is in but some HW or midterms are missing from the gradebook
    elif n_final == 1 and (n_hws != 10 or n_midterms != 2):
        tmp_str = "\t" + str(n_hws) + "/10 HWs \n\t" + str(n_midterms) + "/2 midterms \n\t" + str(n_final) + "/1 final exam \n\tMissing data!"
        print(tmp_str + '\n')
        logfile.write(tmp_str + '\n')

    tmp_str = "...data acquisition finished."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    #################################################################################################

    tmp_str = "------------------------------------------------------------------------------ "
    print(tmp_str)
    logfile.write(tmp_str + '\n')
    tmp_str = "Starting calculation of grades and grade projections..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Set up projection dataframe   
    hwdata_df = rawdata_df.copy()
    examdata_df = rawdata_df.copy()

    # Iterate through keys_list to populate the examdata_df
    # and the hwdata_df with only exam data and HW data, respectively
    for i in range(4,n_keys):
        key = keys_list[i]
        if 'HW' in key:
            # Exam data formed by Removing HW columns from data frame
            examdata_df.drop(key, axis=1, inplace=True)
        elif key in ('M1', 'M2', 'Final'):
            # HW data formed by Removing Exam columns from data frame
            hwdata_df.drop(key, axis=1, inplace=True)

    # Uncomment print statements to better understand how the new dataframes work
    #print("hw data is")
    #print(hwdata_df)
    #print("exam data is")
    #print(examdata_df)

    hwkeys_list = list(hwdata_df.columns)
    # Remove the first 4 columns of the list leaving only HW columns left
    hwkeys_list = hwkeys_list[4:]
    #print(hwkeys_list)
    n_hwkeys = len(hwkeys_list)

    examkeys_list = list(examdata_df.columns[4:])
    n_examkeys = len(examkeys_list)

    # Accumulative dataframes will add up each grade from each column
    # leaving the last column containing the cumulative score
    acc_hwdata_df = hwdata_df.copy()
    acc_examdata_df = examdata_df.copy()
    
    for i in range(0,n_hwkeys):
        key = hwkeys_list[i]
        if key == 'HW1':
            continue
        else:
            prevkey = hwkeys_list[i-1]
            # Add the score of the previous HW column to the current one
            # The result is a cumulative HW score in last column of acc_hwdata_df
            acc_hwdata_df[key] += acc_hwdata_df[prevkey]

    for i in range(0,n_examkeys):
        key = examkeys_list[i]
        if key == 'M1':
            continue
        else:
            prevkey = examkeys_list[i-1]
            # Add the score of the previous exam column to the current one
            # Result is a cumulative exam score in last column of acc_examdata_df
            acc_examdata_df[key] += acc_examdata_df[prevkey]

    # Cumulative homework score (last HW column contains total HW score for semester)
    #print(acc_hwdata_df)
    # Cumulative exam score (last HW column contains total exam score for semester)
    #print(acc_examdata_df)

    # Create dataframes for average hwdata and average examdata
    av_hwdata_df = acc_hwdata_df.copy()
    av_examdata_df = acc_examdata_df.copy()

    # Create dataframes for Min and Max midterm data
    # The grading scheme depends on the min/max exam scores for students
    min_midtermdata_df = examdata_df.copy()
    max_midtermdata_df = examdata_df.copy()

    # Populate the average hw data dataframe
    for i in range(0,n_hwkeys):
        key = hwkeys_list[i]
        hw_n = int(key[2:])
        # The last column of av_hwdata_df will be the average hw score of each student at this point
        av_hwdata_df[key] = 1.0*av_hwdata_df[key]/hw_n

    # Populate the average exam data dataframe
    for i in range(0,n_examkeys):
        key = examkeys_list[i]
        if key == 'Final':
            av_examdata_df[key] = 1.0*av_examdata_df[key]/3            
        else:
            exam_n = int(key[1:])
            av_examdata_df[key] = 1.0*av_examdata_df[key]/exam_n

    #print(av_hwdata_df)
    #print(av_examdata_df)

    # If both midterms are done, calculate the min/max midterm scores
    if n_midterms == 2:
        # Use pandas.DataFrame.min to get the row-wise minimum between M1 and M2
        # Place the minimum midterm value in the last column (key = 'Final') of min_midtermdata_df
        min_midtermdata_df['Final'] = min_midtermdata_df[['M1','M2']].min(axis = 1)
        # Repeat for the max score
        max_midtermdata_df['Final'] = min_midtermdata_df[['M1','M2']].max(axis = 1)

        #print(max_midtermdata_df)
        #print(min_midtermdata_df)
        #print("avg exam data")
        #print(av_examdata_df)
        #print("exam data")
        #print(examdata_df)

    projection_df = rawdata_df.copy()

    tmp_str = "...building projection_df based on the grading scheme for this point in the semester. "
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    for i in range(0,n_keys):
        key = keys_list[i]
        projection_df[key] = 0
        if key in ('HW1','HW2','HW3','HW4'):
            projection_df[key] = av_hwdata_df[key]
        elif key == 'M1':
            # At the point where there is 1 midterm in, there are 4 hws in as well
            projection_df[key] = 0.2*av_hwdata_df['HW4']+0.8*av_examdata_df['M1']
        elif key in ('HW5','HW6','HW7','HW8'):
            projection_df[key] = 0.2*av_hwdata_df[key]+0.8*av_examdata_df['M1']
        elif key == 'M2':
            # Once M2 is in, projection based on 20% hw and the remaining 80% split between the two midterms
            # in the same ratio of 0.35/0.15 as if the final was in.
            # This results in 24% for the min and 56% for the max midterm. 0.2+0.24+0.56=1
            # Recall that the min/max midterm score is contained in the last column of the min/max_midtermdata_df
            projection_df[key] = 0.2*av_hwdata_df['HW8']+0.24*min_midtermdata_df.iloc[:,-1]+0.56*max_midtermdata_df.iloc[:,-1]
        elif key in ('HW9','HW10'):
            projection_df[key] = 0.2*av_hwdata_df[key]+0.24*min_midtermdata_df.iloc[:,-1]+0.56*max_midtermdata_df.iloc[:,-1]
        elif key == ('Final'):
            projection_df[key] = 0.2*av_hwdata_df['HW10']+0.15*min_midtermdata_df.iloc[:,-1]+0.35*max_midtermdata_df.iloc[:,-1]+0.30*examdata_df.iloc[:,-1]

    tmp_str = "...projection_df is successfully written."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    #print("projection df: ")
    #print(projection_df)

    # Open messagefile.txt with exception handling
    try:
        messagefile = open("messagefile.txt", "w+")
    except IOError:
        tmp_str = "Error: can't open .txt file"
        error_file.write(tmp_str)
    else:
        tmp_str = "...successfully writing to messagefile.txt"
        print(tmp_str)
        logfile.write(tmp_str + '\n')
        messagefile.write(tmp_str + '\n')

    #################################################################################################
    # This block of code writes the messagefile that will be sent to each student
    # containing the most current grade projection and class statistic
    # the email_body is being built alongside the messagefile (they will be the same in the end)

    tmp_str = "...sending emails to students with grade projections and class statistics."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Loop across the length of the data frame (this is the number of students)
    for index in rawdata_df.index:
        tmp_str = rawdata_df.loc[index, 'email']
        email_body = ''
        email_body += tmp_str
        messagefile.write(tmp_str + '\n')
        update_n = n_hws + n_midterms + n_final 
        tmp_str = "Grade summary and projection for CE 317 (#" + str(update_n) + ")"
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n')

        firstname = rawdata_df.loc[index, 'First name'].split()[0]
        if firstname == ".":
            firstname = rawdata_df.loc[index, 'Last name'].split()[0]
        
        tmp_str = "Dear " + firstname + ","
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n')
        
        tmp_str = "I'm writing to give you a brief update on where you stand in CE 317. Here are the grades I have on record for you so far:"
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n\n')

        tmp_str = "In the following you can find the class statistics for each assignment/exam:"
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n')

        pd.options.display.float_format = '{:7.2f}'.format

        # Pandas automatically truncates large dataframes when they are displayed
        # Display all of the columns in the dataframe with the 'display.max_columns' option
        pd.set_option('display.max_columns', None)

        # Generate descriptive statistics for each assignment with pandas.DataFrame.describe()
        tmp_str = str(rawdata_df.loc[:, rawdata_df.columns != 'Student ID'].describe())
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n\n')

        tmp_str = "Based on your assignment marks, I arrived at the following grade projections:"
        email_body += tmp_str
        messagefile.write(tmp_str + '\n')

        # Instead of giving all the grade projections at every point so far ...
        # just give the latest grade projection (i.e., the relevant grade projection)
        key = keys_list[-1]
        tmp_str = "Grade projection after " + key + ": "
        if len(key) == 2:
            tmp_str += " "
        tmp_str += " %5.1f " % (projection_df.iloc[index, i])
        tmp_str += "(" + percent_to_lettergrade(grade_scale, projection_df.iloc[index, i]) + ")"
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n')

        if percent_to_lettergrade(grade_scale, projection_df.iloc[index, i]) == 'A':
            tmp_str = "Well done - excellent job, " + firstname + "! Keep up the good work!"
            email_body += tmp_str
            messagefile.write(tmp_str + '\n\n')

        tmp_str = "Note: These grade projections are based on default 5-point lettergrade brackets as well as the weights for exams and homeworks indicated in the course syllabus. " 
        tmp_str += "Your prior homework and exam averages are used as placeholders for the missing homeworks and exams, respectively. \n" 
        tmp_str += "They do NOT yet incorporate extra credit for in-class participation, nor do they consider potential adjustments to the grade brackets. \n"
        tmp_str += "I'm providing the grades after each assignment to give you an idea about your progress. "
        tmp_str += "It is worth noting that grades tend to pick up after the first midterm.\n"
        tmp_str += "Please let me know if you have any questions or concerns."
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n')

        if opts.requestmeeting is True:
            if projection_df.iloc[index, i] < 66:
                tmp_str = firstname + ", since you are currently not doing so great, I wanted to offer to have a meeting with you to see what we can do to improve things. Please let me know what you think."
                email_body += tmp_str
                messagefile.write(tmp_str + '\n\n\n')

        tmp_str = "Best wishes,"
        messagefile.write(tmp_str + '\n\n')
        email_body += tmp_str
        tmp_str = "JH"
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n\n')
        tmp_str = "------------------------------------------------------------------------------ "
        email_body += tmp_str
        messagefile.write(tmp_str + '\n\n')
        #print(email_body)

    #################################################################################################

    # Email the messagefile to each student
        # -- Mailtrap only allows 5 emails to be sent at once for the FREE plan -- #
        if index < 5: #Change 5 to len(projection_df) after purchasing Mailtrap premium
            port = 2525
            smtp_server = "smtp.mailtrap.io"
            login = "3754991cf632be"  # paste your login generated by Mailtrap
            password = "c16cc2ada35e77"  # paste your password generated by Mailtrap

            subject = "Grade summary and projection for CE 317 (#" + str(update_n) + ")"
            sender_email = "7f2ed100ce-5e0429@inbox.mailtrap.io"
            # The sender email would be rawdata_df.loc[index, 'email'] to send to each student's email address
            # But we only want to actually send to our safe mailtrap inbox
            # If you're grading this for CE451/551, you can simply enter your email below to receive the emails #
            receiver_email = "7f2ed100ce-5e0429@inbox.mailtrap.io"

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject

            # Add email_body as plain text to email
            message.attach(MIMEText(email_body, "plain"))

            text = message.as_string()
            # send your email
            with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
                server.login(login, password)
                server.sendmail(sender_email, receiver_email, text)

            email_number = index + 1
            tmp_str =  str(email_number) + " email sent"
            logfile.write(tmp_str + '\n')

    messagefile.close()
    tmp_str = "emails successfully sent..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    tmp_str = "calculation of grades and grade projections finished...messagefile is complete."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    tmp_str = "------------------------------------------------------------------------------ "
    print(tmp_str)
    logfile.write(tmp_str + '\n')
    #################################################################################################

    # Create assignment keys list for better readability
    # introduce assignment keys list; note: we trade resources for readability
    assignment_keys_list = keys_list[3:]
    n_assignment_keys = len(assignment_keys_list)


    tmp_str = "Starting calculation of course statistics..."
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Open a file to mark the top and bottom students
    rankfile = open("rankfile.txt", 'w+')

    # This finds the row which contains highest number in the last column of projection_df
    # This is the highest overall course grade
    idmax = projection_df.iloc[:,-1].idxmax()
    idmin = projection_df.iloc[:,-1].idxmin()

    tmp_str = "The top student is " + str(rawdata_df.loc[idmax]['First name']) +" "+ str(rawdata_df.loc[idmax]['Last name']+'.')
    rankfile.write(tmp_str + '\n')

    tmp_str = "The bottom student is " + str(rawdata_df.loc[idmin]['First name']) +" "+ str(rawdata_df.loc[idmin]['Last name']+'.')
    rankfile.write(tmp_str + '\n')

    rankfile.close()

    #################################################################################################
    tmp_str = "...Creating a histogram plot of student averages"
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Create a histogram plot of student averages at this point
    plt.hist(projection_df.iloc[:,-1], bins = 20, color = 'green', edgecolor = 'k')
    plt.axvline(projection_df.iloc[:,-1].mean(), color='k', linestyle='dashed', linewidth=1)
    min_ylim, max_ylim = plt.ylim()
    plt.text(projection_df.iloc[:,-1].mean() * 1.1, max_ylim * 0.9, 'Average: {:.2f}'.format(projection_df.iloc[:,-1].mean()))
    plt.xlabel('Course Average')
    plt.ylabel('Number of Students')
    plt.title('Class Average Histogram')
    plt.savefig('Class_avg_dist' + today + '.png')
    #plt.show()

    tmp_str = "...histogram successfully saved as " +  'Class_avg_dist' + today + '.png'
    print(tmp_str)
    logfile.write(tmp_str + '\n')
    #################################################################################################

    # Wrap-up section
    # Print the code execution time to the logfile
    time_end = time.time()
    tot_exec_time_str = str(time_end - time_start)
    tmp_str = "The execution time of the code was " + tot_exec_time_str[:4] + " seconds \n"
    logfile.write(tmp_str + 4*'\n')

    tmp_str = "... Code finished successfully."
    print(tmp_str)
    logfile.write(tmp_str + '\n')
    tmp_str = "------------------------------------------------------------------------------ "
    print(tmp_str)
    logfile.write(tmp_str + '\n')

    # Close the logfile and error_file
    logfile.close()
    error_file.close()

    return 0    #successful termination of program
    #################################################################################################

if __name__=="__main__":
    usage_str = "usage: %prog [options] arg"
    version_str = "%prog " + SCRIPT_VERSION
    parser = OptionParser(usage=usage_str, version=version_str)
    
    parser.add_option('--data_file', 
                      dest='data_file', 
                      type='string', 
                      help='specifies the name of the raw data file in CSV format')

    parser.add_option('--job_file', 
                      dest='job_file', 
                      type='string', 
                      help='specifies the name of the job file that specifies sets ')

    parser.add_option('--requestmeeting', 
                      dest='requestmeeting', 
                      action='store_true', 
                      default=False, 
                      help='specifies the a meeting is requested in the student email')

    # Generic options 
    parser.add_option('--print_level', 
                      dest='print_level', 
                      type='int', 
                      default=2, 
                      help='specifies the print level for on screen and the logfile [default: %default]')
        
    # specify log files 
    parser.add_option('--logfile', 
                      dest='logfile', 
                      type='string', 
                      default='grademaster.log',  
                      help='specifies the name of the log-file [default: %default]')

    parser.add_option('--error_file', 
                      dest='error_file', 
                      type='string', 
                      default='grademaster.err',  
                      help='specifies the name of the error-file [default: %default]')

    opts, args = parser.parse_args(sys.argv[1:])
    if len(sys.argv) < 2:
        sys.exit("You tried to run grademaster without options.")
    main(opts,sys.argv)
    
else:
    sys.exit("Sorry, must run as driver...")
