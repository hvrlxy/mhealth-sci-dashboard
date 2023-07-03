import os, sys
import datetime
import pandas as pd 
from flask import Markup

PATH_TO_RAW_DATE = '/opt/sci_jitai/'
PATH_TO_AUC_PLOTS = '/home/hle5/sciJitaiScript/figures/auc/'
PATH_TO_COMPLIANCE_REPORTS = '/home/hle5/sciJitaiScript/reports/compliance/'
PATH_TO_PROXIMAL_TABLE = '/home/hle5/sciJitaiScript/reports/proximal/'
PATH_TO_INFO_JSON = '/home/hle5/mhealth-sci-dashboard/static/json/participant.json'

def calculate_compliance_completion(user, start_date):
    '''
    This function will calculate the compliance rate and completion rate for a given user
    from a given start date to today.
    Parameters:
    :user: the user id
    :start_date: the start date in the format of YYYY-MM-DD
    '''
    # convert start_date to datetime object
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    # get today as datetime object
    today = datetime.datetime.today()
    
    # generate a list of dates from start_date to today
    dates_list = [start_date + datetime.timedelta(days=x) for x in range((today-start_date).days + 1)]
    
    total_expected_prompt = 0
    total_delivered_prompt = 0
    total_answered_prompt = 0
    for date in dates_list:
        # convert date to string
        date = date.strftime('%Y-%m-%d')
        # read the compliance report, if it exists
        if os.path.exists(PATH_TO_COMPLIANCE_REPORTS + f"{user}/{date}.csv"):
            compliance_df = pd.read_csv(PATH_TO_COMPLIANCE_REPORTS + f"{user}/{date}.csv")
            #remove row with message_type == wi
            compliance_df = compliance_df[compliance_df['message_type'] != 'wi']
            # count the number of rows with status != NOT_PROMPTED and why_not_prompted != SCHEDULE
            total_expected_prompt += len(compliance_df[(compliance_df['status'] != 'NOT_PROMPTED') & (compliance_df['why_not_prompted'] != 'SCHEDULE')])
            
            # count the number of rows with status == ANS
            total_answered_prompt += len(compliance_df[compliance_df['status'] == 'ANS'])
            
            # count the number of prompt with status != NOT_PROMPTED
            total_delivered_prompt += len(compliance_df[compliance_df['status'] != 'NOT_PROMPTED'])
            
    # compliance rate is the number of answered prompt divided by the number of expected prompt
    if total_expected_prompt == 0:
        compliance_rate = -1
    else:
        compliance_rate = total_answered_prompt / total_expected_prompt
    # completion rate is the number of delivered prompt divided by the number of expected prompt
    if total_expected_prompt == 0:
        completion_rate = -1
    else:
        completion_rate = total_delivered_prompt / total_expected_prompt
    
    # turn the compliance rate and completion rate into percentage
    if compliance_rate == -1:
        compliance_rate = 'N/A'
    else:
        compliance_rate = str(round(compliance_rate * 100, 2)) + "%"
        
    if completion_rate == -1:
        completion_rate = 'N/A'
    else:
        completion_rate = str(round(completion_rate * 100, 2)) + "%"
    return compliance_rate, completion_rate
            

def get_last_data_received_date(user):
    '''
    This function will return the last date that the user's data was received.
    Parameters:
    :user: the user id
    '''
    # get all the folder inside the user's data folder
    if os.path.exists(PATH_TO_RAW_DATE + f"{user}@scijitai_com/logs-watch/"):
        dates_folder = os.listdir(PATH_TO_RAW_DATE + f"{user}@scijitai_com/logs-watch/")
        
        # convert all the folders to datetime object
        dates_folder = [datetime.datetime.strptime(date, '%Y-%m-%d') for date in dates_folder]
        
        # return the latest date
        return max(dates_folder).strftime('%Y-%m-%d')
    else:
        return '1969-01-01'

def get_participant_summary_table():
    '''
    This function will return a summary table for a given user.
    Information including: compliance rate, completion rate, link to compliance report, link to proximal report, link to auc plot
    Parameters: None
    '''
    # read the info json file
    info_obj = pd.read_json(PATH_TO_INFO_JSON)
    
    # get the list of participants - keys in the json file
    subjects = list(info_obj.keys())
    
    # get the start date and AUC threshold for each participant
    subject_info_dict = {}
    for subject in subjects:
        subject_info_dict[subject] = {'start_date': info_obj[subject][0]['start_date'],
                                        'AUC_threshold': info_obj[subject][0]['AUC']}
    
    # create a data frame, with columns user_id, last_data_received_date, compliance_rate, completion_rate
    # link to compliance report, link to proximal report, link to auc plot
    summary_df = pd.DataFrame(columns=['user_id', 
                                       'AUC_threshold',
                                       'start_date',
                                       'last_data_received', 
                                       'compliance_rate', 
                                       'completion_rate', 
                                       'latest_compliance_report', 
                                       'proximal_report', 
                                       'data_plots'])
    
    # loop through each participant
    for subject in subjects:
        # create the row for the participant
        row = {'user_id': subject, 
               'AUC_threshold': subject_info_dict[subject]['AUC_threshold'],
               'start_date': subject_info_dict[subject]['start_date'],
               'last_data_received': get_last_data_received_date(subject), 
               'compliance_rate': calculate_compliance_completion(subject, subject_info_dict[subject]['start_date'])[0], 
               'completion_rate': calculate_compliance_completion(subject, subject_info_dict[subject]['start_date'])[1], 
               'latest_compliance_report': f"/compliance/{subject}/{get_last_data_received_date(subject)}/", 
               'proximal_report': f"/proximal/{subject}/", 
               'data_plots': f"/auc/{subject}/"}
        
        # concatenate the row to the summary_df
        summary_df = pd.concat([summary_df, pd.DataFrame(row, index=[0])], ignore_index=True)
        
    # convert link to compliance report to url href format
    summary_df['latest_compliance_report'] = summary_df['latest_compliance_report'].apply(lambda x: f"<a href='{x}'>link</a>")
    # convert link to proximal report to url href format
    summary_df['proximal_report'] = summary_df['proximal_report'].apply(lambda x: f"<a href='{x}'>link</a>")
    # convert link to auc plot to url href format
    summary_df['data_plots'] = summary_df['data_plots'].apply(lambda x: f"<a href='{x}'>link</a>")
    
    return summary_df

def get_participant_auc_table(user):
    '''
    This function will return a table with all the dates and links to auc plots and compliance table.
    Parameters:
    :user: the user id
    :start_date: the start date of the user
    '''
    # read the info json file
    info_obj = pd.read_json(PATH_TO_INFO_JSON)
    # get user's start date
    start_date = info_obj[user][0]['start_date']
    # convert start date to datetime object
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    # get the list of dates from start date to today
    dates_list = [start_date + datetime.timedelta(days=x) for x in range((datetime.datetime.today() - start_date).days + 1)]
    # convert dates to string
    dates_list = [date.strftime('%Y-%m-%d') for date in dates_list]
    
    # create a dataframe with column date, link_to_auc_plot and link_to_compliance_report
    user_df = pd.DataFrame(columns=['date', 'link_to_auc_plot', 'link_to_compliance_report'])
    
    # for each date, link_to_auc_plot is /auc/user/date/, and link_to_compliance_report is /compliance/user/date/
    for date in dates_list:
        # create the row for the date
        row = {'date': date, 
               'link_to_auc_plot': f"/auc/{user}/{date}/", 
               'link_to_compliance_report': f"/compliance/{user}/{date}/"}
        # concatenate the row to the user_df
        user_df = pd.concat([user_df, pd.DataFrame(row, index=[0])], ignore_index=True)
        
    # convert link to auc plot to url href format
    user_df['link_to_auc_plot'] = user_df['link_to_auc_plot'].apply(lambda x: f"<a href='{x}'>auc_plot</a>")
    # convert link to compliance report to url href format
    user_df['link_to_compliance_report'] = user_df['link_to_compliance_report'].apply(lambda x: f"<a href='{x}'>compliance_report</a>")
    
    return user_df
        
    
    