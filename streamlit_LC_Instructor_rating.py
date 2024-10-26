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

######

def convert_to_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d')


def get_equidistant_dates(start_date_str, end_date_str):
    start = convert_to_date(start_date_str)
    end = convert_to_date(end_date_str)

    total_days = (end - start).days
    step = total_days // 4  


    date1 = start + timedelta(days=step)
    date2 = start + timedelta(days=2 * step)
    date3 = start + timedelta(days=3 * step)

    return [start.strftime('%Y-%m-%d'), date1.strftime('%Y-%m-%d'), date2.strftime('%Y-%m-%d'), date3.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')]



def generate_interval_results(start_date_str, end_date_str):
    
    dates = get_equidistant_dates(start_date_str, end_date_str)
    print(dates)


    result_df = pd.DataFrame()


    for i in range(4):
        interval_start = dates[i]
        interval_end = dates[i+1]

        interval_df = generate_ratings_report(interval_start, interval_end)

    
        interval_df['Interval'] = i + 1


        result_df = pd.concat([result_df, interval_df], ignore_index=True)

    result_df = result_df[['Teacher', 'Interval', 'Average Content Rating', 'Average Instructor Rating', '# of Unique Learner Rated']]

    return result_df



def generate_ratings_report(start_date: str, end_date: str):
    print("Generating the ratings report...")

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

    def get_teacher_header(id, start_date, end_date):
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

    # Fetch student data
    json_data = {
        'id': 932,
        'parameters': {
            'Start Date': start_date,
            'End Date': end_date,
        },
    }

    response = requests.post('https://redash.impartus.com/api/queries/932/results', headers=headers, json=json_data, timeout=30)
    json_data = response.json()
    df = json_to_dataframe(json_data)


    # Fetch teachers' mapping data
    df2 = pd.DataFrame()
    LC_id = [1728, 1724, 1730]
    for id in LC_id:
        json_data2 = {
            'id': 930,
            'parameters': {
                'Institute Name': str(id),
                'Start Date': start_date,
                'End Date': end_date,
            },
        }
        headers2 = get_teacher_header(id, start_date, end_date)
        response2 = requests.post('https://redash.impartus.com/api/queries/930/results', headers=headers2, json=json_data2, timeout=30)
        json_data2 = response2.json()

        temp = json_to_dataframe(json_data2)
        df2 = pd.concat([df2, temp], ignore_index=True)


    # Merge student and teacher data
    merged_df = pd.merge(df, df2, left_on='Timetableid', right_on='Id', how='inner')

    # Aggregate results
    result = merged_df.groupby(['Teacher', 'Instiute']).agg(
        avg_content_rating=('Content Rating', 'mean'),
        avg_instructor_rating=('Instructor Rating', 'mean'),
        num_unique_sessions=('Email', 'nunique')
    ).reset_index()

    # Rename columns for better readability
    result = result.rename(columns={
        'Instiute': 'Learning Center',
        'avg_content_rating': 'Average Content Rating',
        'avg_instructor_rating': 'Average Instructor Rating',
        'num_unique_sessions': '# of Unique Learner Rated'
    })

    return result

#######

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
            st.error("Redash API busy! Try reloading fetching later")
            ###########

            # Plotting and saving as image for PDF
            images = []  # List to hold image paths for PDF compilation
            # Unique teachers

            final_result_df = generate_interval_results(Start_Date, End_Date)
            teachers = final_result_df['Teacher'].unique()
            for teacher in teachers:
                teacher_data = final_result_df[final_result_df['Teacher'] == teacher]
                plt.figure(figsize=(10, 5))

                # Create line plots for Average Content Rating and Average Instructor Rating
                ax1 = plt.gca()
                ax2 = ax1.twinx()
                sns.lineplot(x=teacher_data['Interval'],
                            y=teacher_data['Average Content Rating'],
                            marker='o', label='Content Rating', color='blue', ax=ax1)
                sns.lineplot(x=teacher_data['Interval'],
                            y=teacher_data['Average Instructor Rating'],
                            marker='o', label='Instructor Rating', color='orange', ax=ax2)

                # Histogram for # of Unique Learner Rated (no separate axis)
                bars = ax1.bar(teacher_data['Interval'],
                            teacher_data['# of Unique Learner Rated'],
                            alpha=0.3, color='gray', width=0.4)

                # Titles and labels
                ax1.set_title(f'Rating Trends and Unique Learner Counts for {teacher}')
                ax1.set_xlabel(f"--------{Start_Date}-------to-----{End_Date}---->")
                ax1.set_ylabel('Rating')
                ax2.set_ylabel('Instructor Rating')
                ax1.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
                ax2.legend(loc='upper left', bbox_to_anchor=(0.1, 0.85))

                # Save plot as image
                image_path = f"{teacher}_plot.png"
                plt.savefig(image_path)
                images.append(image_path)
                plt.close()  # Close the plot to avoid memory issues

            # Create PDF from images
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            for image_path in images:
                pdf.add_page()
                pdf.image(image_path, x=10, y=20, w=180)  # Adjust size and position as needed

            # Save PDF
            pdf_file_path = f"LC_Ratings_{start_date_str}_{end_date_str}.pdf"
            pdf.output(pdf_file_path)

            # Display success message and download button for PDF
            st.success(f"PDF report created: {pdf_file_path}")
            with open(pdf_file_path, "rb") as f:
                st.download_button("Download PDF Report", f, file_name=os.path.basename(pdf_file_path), mime="application/pdf")

            # Cleanup temporary images after PDF is created
            for image_path in images:
                os.remove(image_path)
             
            ####
    else:
        st.error("Please select both start and end dates.")
