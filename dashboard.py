from flask import Flask, render_template
from globals import *
import pandas as pd

application = Flask(__name__)

@application.route("/")
def home():
    # get the summary table
    summary_df = get_participant_summary_table()
    return render_template('index.html', table=summary_df.to_html(index=False, escape=False))


@application.route("/compliance/<user>/<date>/")
def compliance(user, date):
    '''
    This function will read the compliance report for a given user and date
    and pass the data to the template.
    Parameters:
    :user: the user id
    :date: the date of the compliance report
    '''
    # get the next date
    next_day = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)
    next_day = next_day.strftime('%Y-%m-%d')
    # get the previous date
    prev_day = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=1)
    prev_day = prev_day.strftime('%Y-%m-%d')
    
    # get the url for the next and previous day
    next_day_url = f"/compliance/{user}/{next_day}/"
    prev_day_url = f"/compliance/{user}/{prev_day}/"
    
    # read the compliance table
    try:
        compliance_df = pd.read_csv(PATH_TO_COMPLIANCE_REPORTS + f"{user}/{date}.csv")
        # remove the Unnamed column
        compliance_df = compliance_df.loc[:, ~compliance_df.columns.str.contains('^Unnamed')]
        # remove the user_id column
        compliance_df = compliance_df.drop(columns=['user_id'])
        # remove all column with epoch in the name
        compliance_df = compliance_df.loc[:, ~compliance_df.columns.str.contains('epoch')]
    except Exception as e:
        return render_template('compliance.html', 
                           user=user, 
                           date=date, 
                           next_day_url=next_day_url,
                           prev_day_url=prev_day_url,
                           table=f"<p>No data found for participant {user} on {date}.</p>")
    # pass the table to the template
    return render_template('compliance.html', 
                           user=user, 
                           date=date, 
                           next_day_url=next_day_url,
                           prev_day_url=prev_day_url,
                           table=compliance_df.to_html(index=False))

@application.route("/proximal/<user>/")
def proximal(user):
    # read the proximal table
    try:
        proximal_df = pd.read_csv(PATH_TO_PROXIMAL_TABLE + f"{user}.csv")  
        # remove all columns containing epoch
        proximal_df = proximal_df.loc[:, ~proximal_df.columns.str.contains('epoch')]
    except Exception as e:
        return render_template('proximal.html',
                            title = f"Proximal PA Table for {user}",
                            user=user,
                            table=f"<p>No data found for participant {user}.</p>")
    
    return render_template('proximal.html',
                           title = f"Proximal PA Table for {user}",
                           user=user,
                           table=proximal_df.to_html(index=False))

@application.route("/auc/<user>/")
def user_auc(user):
    # get the auc table
    user_df = get_participant_auc_table(user)
    return render_template('auc.html', user=user, table=user_df.to_html(index=False, escape=False))

@application.route("/auc/<user>/<date>/")
def auc(user, date):
    # check if the auc html file exists
    # if not os.path.exists(f'/home/hle5/mhealth-sci-dashboard/templates/auc/{date}/{user}.html'):
    #     return render_template('proximal.html',
    #                         title = f"AUC Plot for {user} on {date}",
    #                         user=user,
    #                         table=f"<p>No data found for participant {user}.</p>")
    # else:
    #     return render_template(f'auc/{date}/{user}.html')
    
    try:
        return render_template(f'auc/{date}/{user}.html')
    except Exception as e:
        return render_template('proximal.html',
                            title = f"AUC Plot for {user} on {date}",
                            user=user,
                            table=f"<p>No data found for participant {user}.</p>")

if __name__ == "__main__":
    application.run(host='0.0.0.0')