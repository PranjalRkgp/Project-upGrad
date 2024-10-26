import streamlit as st
import numpy
import pandas as pd
import requests
import json

st.title("upGrad LC Instructors and Content Ratings Aggregator")
st.write("This app generates an Excel file with aggregated ratings for LC Instructors and Content.")

Start_Date = st.text_input("Enter the start date (YYYY-MM-DD):")
End_Date = st.text_input("Enter the end date (YYYY-MM-DD):")




if Start_Date and End_Date:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': 'Key hs0OlUpw9wXiahyWnZc7N8SI1rEu35GxgDVhf9FH',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://redash.impartus.com',
        'priority': 'u=1, i',
        'referer': 'https://redash.impartus.com/public/dashboards/hs0OlUpw9wXiahyWnZc7N8SI1rEu35GxgDVhf9FH?',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }


    def json_to_dataframe(json_data):
        rows_data = json_data['query_result']['data']['rows']
        df = pd.DataFrame(rows_data)
        return df

    def get_teacher_header(id,Start_Date,End_Date):
        headers2 = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Key Mkzi6dI3GXsQtmlWrlWAHbgLKfCfOYXOJT8m0keT',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://redash.impartus.com',
            'priority': 'u=1, i',
            'referer': 'https://redash.impartus.com/public/dashboards/Mkzi6dI3GXsQtmlWrlWAHbgLKfCfOYXOJT8m0keT?',
            'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        }
        return headers2


    # FOR STUDENTS DATA 
    json_data = {
        'id': 932,
        'parameters': {
            'Start Date': Start_Date,
            'End Date': End_Date,
        },
    }

    response = requests.post('https://redash.impartus.com/api/queries/932/results', headers=headers, json=json_data, timeout=30)
    json_data_response=response.json()
    df = json_to_dataframe(json_data_response)



    # FOR TEACHERS MAPPING DATA
    df2 = pd.DataFrame()
    LC_id = [1728, 1724, 1730]
    for id in LC_id:    
        json_data2 = {
            'id': 930,
            'parameters': {
                'Institute Name': str(id), 
                'Start Date': Start_Date,
                'End Date': End_Date,
            },
        }
        headers2=get_teacher_header(id,Start_Date,End_Date)
        
        response2 = requests.post('https://redash.impartus.com/api/queries/930/results', headers=headers2,json=json_data2, timeout=30)
        
        json_data_response2 = response2.json()
        
        # print(json_data_response2)
        temp = json_to_dataframe(json_data_response2)  
        df2 = pd.concat([df2, temp], ignore_index=True)


    # MERGED DATA
    merged_df = pd.merge(df ,df2, left_on='Timetableid', right_on='Id', how='inner')

    # RESULTS
    result = merged_df.groupby(['Teacher','Instiute']).agg(
        
        avg_content_rating=('Content Rating', 'mean'),
        avg_instructor_rating=('Instructor Rating', 'mean'),
        num_unique_sessions=('Email', 'nunique')
    ).reset_index()
    result = result.rename(columns={
        'Instiute':'Learning Center',
        'avg_content_rating': 'Average Content Rating',
        'avg_instructor_rating': 'Average Instructor Rating',
        'num_unique_sessions': '# of Unique Learner Rated'
    })




    excel_file_path = 'Attendance Mastersheet.xlsx'
    df_students = pd.read_excel(excel_file_path)

    merged_df_with_cohort = pd.merge(merged_df, 
                                    df_students[['Email id', 'Cohort id', 'firstname', 'lastname', 'Location']], 
                                    left_on='Email', 
                                    right_on='Email id', 
                                    how='left')


    sessions_attended = merged_df_with_cohort.groupby(['Email', 'Cohort id', 'Teacher'])['Timetableid'].nunique().reset_index()
    sessions_attended.columns = ['Email', 'Cohort id', 'Teacher', '# session attended']


    teacher_sessions = merged_df_with_cohort.groupby(['Cohort id', 'Teacher'])['Timetableid'].nunique().reset_index()
    teacher_sessions.columns = ['Cohort id', 'Teacher', '# of session taken']


    final_result = pd.merge(df_students[['Email id', 'Cohort id']], 
                            pd.merge(sessions_attended, teacher_sessions, on=['Cohort id', 'Teacher'], how='right'), 
                            left_on=['Email id', 'Cohort id'], 
                            right_on=['Email', 'Cohort id'], 
                            how='left')


    final_result['# session attended'] = final_result['# session attended'].fillna(0)

    final_result['% attendance'] = (final_result['# session attended'] / final_result['# of session taken']) * 100

    final_result_with_names = pd.merge(final_result, 
                                    df_students[['Email id', 'Cohort id', 'firstname', 'lastname', 'Location']], 
                                    left_on=['Email id', 'Cohort id'], 
                                    right_on=['Email id', 'Cohort id'], 
                                    how='left')


    final_attendance = final_result_with_names[['firstname', 'lastname', 'Email id', 'Cohort id', 'Location', 'Teacher', '# session attended', '# of session taken', '% attendance']]



    final_excel_file_path = f'LC_Ratings_{Start_Date}_{End_Date}.xlsx'  
    dfs = {
        'Aggregated Results': result,
        'Attendance Report': final_attendance,
        'Students Raw Data': df,
        'Instructors Raw Data': df2,
    }

    with pd.ExcelWriter(final_excel_file_path, engine='openpyxl') as writer:
        for sheet_name, dataframe in dfs.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
            
    # Provide download link
    with open(final_excel_file_path, 'rb') as file:
        st.download_button(
            label="Download Aggregated Ratings & Attendance Report",
            data=file,
            file_name=final_excel_file_path,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )