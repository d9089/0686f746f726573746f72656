import streamlit as st
import pandas as pd
import base64
import time
import datetime
import pymysql
from pyresparser import ResumeParser
from pdfminer.high_level import extract_text
import random
import requests
import openai

# Set OpenAI API key
openai.api_key = "your_openai_api_key"

# Connect to MySQL database
connection = pymysql.connect(host="localhost", user="root", password="", database="sandhya")
cursor = connection.cursor()

# Function to insert data into MySQL database
def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    insert_sql = """
        INSERT INTO resumedata
        VALUES (0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    rec_values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

# Function to calculate score
def calculate_score(resume_text):
    resume_score = 0
    if "Objective" in resume_text:
        resume_score += 10
    if "Declaration" in resume_text:
        resume_score += 10
    if "Hobbies" in resume_text or "Interests" in resume_text:
        resume_score += 10
    if "Achievements" in resume_text:
        resume_score += 10
    if "Projects" in resume_text:
        resume_score += 10
    return resume_score

# Function to display recommended skills
def display_recommendations(field, skills):
    st.success(f"**Our analysis suggests you are looking for {field} Jobs.**")
    st.subheader("Recommended skills for you:")
    st.write(skills)

# Function to send resume data to API and receive interview questions
def send_resume_data_and_receive_questions(resume_data):
    prompt = "Generate interview questions based on the following resume:\n" + resume_data
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.5,
        )
        interview_questions = response.choices[0].text.strip()
        return interview_questions
    except Exception as e:
        print("Error:", e)
        return None

# Set Streamlit page config
st.set_page_config(page_title="A Novel Technological Prototype Enhancing Recruitment Techniques using artificial intelligence")

# Main function to run Streamlit app
def run():
    st.title("A Novel Technological Prototype Enhancing Recruitment Techniques using artificial intelligence")
    activities = ["User Login", "Admin Login"]
    choice = st.selectbox("Choose among the given options:", activities)

    if choice == "User Login":
        st.subheader("Upload your Resume")
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            save_image_path = "./uploads/" + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                resume_text = extract_text(save_image_path)
                st.success("Hello " + resume_data["name"])
                st.subheader("Your Basic info")
                st.text("Name: " + resume_data["name"])
                st.text("Email: " + resume_data["email"])
                st.text("Contact: " + resume_data["mobile_number"])
                st.text("Resume pages: " + str(resume_data["no_of_pages"]))
                # Other parts of the code for skill recommendation and analysis...
            else:
                st.error("Error processing the uploaded resume.")

    elif choice == "Admin Login":
        st.success("Logging you in as Admin")
        st.session_state.is_logged_in = True
        st.success("Welcome Admin")
        # Display Data...
        cursor.execute("SELECT ID, Name, Email_ID, resume_score, Timestamp, Page_no, Predicted_Field, Actual_skills FROM resumedata")
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=["ID", "Name", "Email", "Resume Score", "Timestamp", "Total Page", "Predicted Field", "Skills"])
        st.dataframe(df)
        st.markdown(get_table_download_link(df, "resumedata.csv", "Download Report"), unsafe_allow_html=True)
        # Resume Upload for Admin...
        uploaded_files = st.file_uploader("Choose your Resumes", accept_multiple_files=True, type=["pdf"])
        if uploaded_files is not None:
            for uploaded_file in uploaded_files:
                if hasattr(uploaded_file, "read"):
                    random_filename = str(random.randint(1, 1000000)) + ".pdf"
                    save_image_path = "./uploads/" + random_filename
                    with open(save_image_path, "wb") as f:
                        f.write(uploaded_file.read())
                    resume_data = ResumeParser(save_image_path).get_extracted_data()
                    if resume_data:
                        insert_data(resume_data["name"], resume_data["email"], str(0), "", str(resume_data["no_of_pages"]), "", "", str(resume_data["skills"]), "", "")
                        st.success(f"Resume uploaded successfully: {resume_data['name']}")
                    else:
                        st.error("Error processing the uploaded resume.")
                else:
                    st.error("Uploaded file is not valid.")

# Run the Streamlit app
run()
