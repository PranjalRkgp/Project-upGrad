import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
from fpdf import FPDF  
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit title and description
st.title("upGrad LC Instructors and Content Ratings Aggregator")
st.write("This app generates an Excel file with aggregated ratings for LC Instructors and Content.")

# Input fields for dates using calendar input
Start_Date = st.date_input("Select the start date:", pd.to_datetime("2024-10-01"))
End_Date = st.date_input("Select the end date:", pd.to_datetime("2024-10-25"))


# Add a submit button
if st.button("Submit"):
    if Start_Date and End_Date:
        # Convert dates to string format for queries
        start_date_str = Start_Date.strftime("%Y-%m-%d")
        end_date_str = End_Date.strftime("%Y-%m-%d")


        def get_headers(auth_key):
            return {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'en-US,en;q=0.9',
                'authorization': f'Key {auth_key}',
                'content-type': 'application/json;charset=UTF-8',
                'origin': 'https://redash.impartus.com',
                'priority': 'u=1, i',
                'referer': f'https://redash.impartus.com/public/dashboards/{auth_key}?',
                'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }

        def json_to_dataframe(json_data):
            rows_data = json_data.get('query_result', {}).get('data', {}).get('rows', [])
            return pd.DataFrame(rows_data)

        def fetch_student_data(start_date, end_date):
            json_data = {
                'id': 932,
                'parameters': {
                    'Start Date': start_date,
                    'End Date': end_date,
                },
            }
            with requests.Session() as session:
                response = session.post('https://redash.impartus.com/api/queries/932/results', headers=get_headers('hs0OlUpw9wXiahyWnZc7N8SI1rEu35GxgDVhf9FH'), json=json_data)
                response_data = response.json()
                return json_to_dataframe(response_data)

        def fetch_teacher_data(start_date, end_date, lc_id):
            json_data = {
                'id': 930,
                'parameters': {
                    'Institute Name': str(lc_id),
                    'Start Date': start_date,
                    'End Date': end_date,
                },
            }
            with requests.Session() as session:
                response = session.post('https://redash.impartus.com/api/queries/930/results', headers=get_headers('Mkzi6dI3GXsQtmlWrlWAHbgLKfCfOYXOJT8m0keT'), json=json_data)
                response_data = response.json()
                return json_to_dataframe(response_data)

        # Fetch student data
        df = fetch_student_data(start_date_str, end_date_str)

        print(df)
        st.write('students data fetched!')

        # Fetch teacher data for specific LC IDs
        LC_ids = [1728, 1724, 1730]
        df2 = pd.DataFrame()

        for lc_id in LC_ids:
            teacher_data = fetch_teacher_data(start_date_str, end_date_str, lc_id)
            df2 = pd.concat([df2, teacher_data], ignore_index=True)

        print(df2)
        st.write('Teachers data fetched!')


        # Merging data
        if 'Timetableid' in df.columns and 'Id' in df2.columns:
            # Merge dataframes
            merged_df = pd.merge(df, df2, left_on='Timetableid', right_on='Id', how='inner')

            # Aggregated results
            result = merged_df.groupby(['Teacher', 'Instiute']).agg(
                avg_content_rating=('Content Rating', 'mean'),
                avg_instructor_rating=('Instructor Rating', 'mean'),
                num_unique_sessions=('Email', 'nunique')
            ).reset_index()
            result = result.rename(columns={
                'Instiute': 'Learning Center',
                'avg_content_rating': 'Average Content Rating',
                'avg_instructor_rating': 'Average Instructor Rating',
                'num_unique_sessions': '# of Unique Learner Rated'
            })

            # Load student data from Excel
            excel_file_path = 'Attendance Mastersheet.xlsx'
            df_students = pd.read_excel(excel_file_path)


            # Merging merged_df with df_students
            merged_df_with_cohort = pd.merge(merged_df, 
                                             df_students[['Email id', 'Cohort id', 'firstname', 'lastname', 'Location']], 
                                             left_on='Email', 
                                             right_on='Email id', 
                                             how='left')

            # Sessions attended
            sessions_attended = merged_df_with_cohort.groupby(['Email', 'Cohort id', 'Teacher'])['Timetableid'].nunique().reset_index()
            sessions_attended.columns = ['Email', 'Cohort id', 'Teacher', '# session attended']

            # Teacher sessions
            teacher_sessions = merged_df_with_cohort.groupby(['Cohort id', 'Teacher'])['Timetableid'].nunique().reset_index()
            teacher_sessions.columns = ['Cohort id', 'Teacher', '# of session taken']

            # Final result
            final_result = pd.merge(df_students[['Email id', 'Cohort id']], 
                                    pd.merge(sessions_attended, teacher_sessions, on=['Cohort id', 'Teacher'], how='right'), 
                                    left_on=['Email id', 'Cohort id'], 
                                    right_on=['Email', 'Cohort id'], 
                                    how='left')

            final_result['# session attended'] = final_result['# session attended'].fillna(0)
            final_result['% attendance'] = (final_result['# session attended'] / final_result['# of session taken']) * 100

            # Final result with names
            final_result_with_names = pd.merge(final_result, 
                                               df_students[['Email id', 'Cohort id', 'firstname', 'lastname', 'Location']], 
                                               left_on=['Email id', 'Cohort id'], 
                                               right_on=['Email id', 'Cohort id'], 
                                               how='left')

            # Select final attendance
            final_attendance = final_result_with_names[['firstname', 'lastname', 'Email id', 'Cohort id', 'Location', 'Teacher', '# session attended', '# of session taken', '% attendance']]

            # Final Excel file path
            final_excel_file_path = f'LC_Ratings_{start_date_str}_{end_date_str}.xlsx'

            # Write to Excel
            dfs = {
                'Aggregated Results': result,
                'Attendance Report': final_attendance,
                'Students Raw Data': df,
                'Instructors Raw Data': df2,
            }

            with pd.ExcelWriter(final_excel_file_path, engine='openpyxl') as writer:
                for sheet_name, dataframe in dfs.items():
                    dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

            st.success(f'Excel file created: {final_excel_file_path}')

            # Provide a download button
            with open(final_excel_file_path, "rb") as f:
                st.download_button("Download Excel File", f, file_name=os.path.basename(final_excel_file_path), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("Redash API is currently busy. Please try submitting again; this often retrieves the output.")
    else:
        st.error("Please select both start and end dates.")
