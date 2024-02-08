import streamlit as st
import nltk
import spacy

nltk.download("stopwords")
spacy.load("en_core_web_sm")

import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
import pafy
import plotly.express as px
from openai import OpenAI
import streamlit as st


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, "rb") as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


connection = pymysql.connect(host="localhost", user="root", password="")
cursor = connection.cursor()


def insert_data(
    name,
    email,
    res_score,
    timestamp,
    no_of_pages,
    reco_field,
    cand_level,
    skills,
    recommended_skills,
    courses,
):
    DB_table_name = "resumedata"
    insert_sql = (
        "insert into "
        + DB_table_name
        + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    )
    rec_values = (
        name,
        email,
        str(res_score),
        timestamp,
        str(no_of_pages),
        reco_field,
        cand_level,
        skills,
        recommended_skills,
        courses,
    )
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="A Novel Technological Prototype Enhancing Recruitment Techniques using artificial intelligence",
)


def run():
    st.title(
        "A Novel Technological Prototype Enhancing Recruitment Techniques using artificial intelligence"
    )
    st.markdown("# Login as")
    activities = ["User Login", "Admin Login"]
    choice = st.selectbox("Choose among the given options:", activities)

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS sandhya;"""
    cursor.execute(db_sql)
    connection.select_db("sandhya")

    # Create table
    DB_table_name = "resumedata"
    table_sql = (
        "CREATE TABLE IF NOT EXISTS "
        + DB_table_name
        + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));
                    """
    )
    cursor.execute(table_sql)
    if choice == "User Login":
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        print("hey")
        print(pdf_file)
        print(pdf_file)
        print("end")
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = "./uploads/" + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data["name"])
                st.subheader("**Your Basic info**")
                try:
                    st.text("Name: " + resume_data["name"])
                    st.text("Email: " + resume_data["email"])
                    st.text("Contact: " + resume_data["mobile_number"])
                    st.text("Resume pages: " + str(resume_data["no_of_pages"]))
                except:
                    pass
                cand_level = ""
                if resume_data["no_of_pages"] == 1:
                    cand_level = "Fresher"
                    st.markdown(
                        """<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>""",
                        unsafe_allow_html=True,
                    )
                elif resume_data["no_of_pages"] == 2:
                    cand_level = "Intermediate"
                    st.markdown(
                        """<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>""",
                        unsafe_allow_html=True,
                    )
                elif resume_data["no_of_pages"] >= 3:
                    cand_level = "Experienced"
                    st.markdown(
                        """<h4 style='text-align: left; color: #fba171;'>You are at experience level!""",
                        unsafe_allow_html=True,
                    )

                st.subheader("**Recommendations for Skills💡**")
                ## Skill shows
                keywords = st_tags(
                    label="### Skills that you have",
                    text="See our skills recommendation",
                    value=resume_data["skills"],
                    key="1",
                )

                ##  recommendation
                ds_keyword = [
                    "tensorflow",
                    "keras",
                    "pytorch",
                    "machine learning",
                    "deep Learning",
                    "flask",
                    "streamlit",
                ]
                web_keyword = [
                    "react",
                    "django",
                    "node jS",
                    "react js",
                    "php",
                    "laravel",
                    "magento",
                    "wordpress",
                    "javascript",
                    "angular js",
                    "c#",
                    "flask",
                ]
                android_keyword = [
                    "android",
                    "android development",
                    "flutter",
                    "kotlin",
                    "xml",
                    "kivy",
                ]
                ios_keyword = [
                    "ios",
                    "ios development",
                    "swift",
                    "cocoa",
                    "cocoa touch",
                    "xcode",
                ]
                uiux_keyword = [
                    "ux",
                    "adobe xd",
                    "figma",
                    "zeplin",
                    "balsamiq",
                    "ui",
                    "prototyping",
                    "wireframes",
                    "storyframes",
                    "adobe photoshop",
                    "photoshop",
                    "editing",
                    "adobe illustrator",
                    "illustrator",
                    "adobe after effects",
                    "after effects",
                    "adobe premier pro",
                    "premier pro",
                    "adobe indesign",
                    "indesign",
                    "wireframe",
                    "solid",
                    "grasp",
                    "user research",
                    "user experience",
                ]

                recommended_skills = []
                reco_field = ""
                rec_course = ""
                ## Courses recommendation
                for i in resume_data["skills"]:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = "Data Science"
                        st.success(
                            "** According to our analysis, you're seeking for Data Science Jobs.**"
                        )
                        recommended_skills = [
                            "Data Visualization",
                            "Predictive Analysis",
                            "Statistical Modeling",
                            "Data Mining",
                            "Clustering & Classification",
                            "Data Analytics",
                            "Quantitative Analysis",
                            "Web Scraping",
                            "ML Algorithms",
                            "Keras",
                            "Pytorch",
                            "Probability",
                            "Scikit-learn",
                            "Tensorflow",
                            "Flask",
                            "Streamlit",
                        ]
                        recommended_keywords = st_tags(
                            label="### Recommended skills for you.",
                            text="Recommended skills generated from System",
                            value=recommended_skills,
                            key="2",
                        )
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>Including these abilities on your resume will increase your chances of landing a job💼</h4>""",
                            unsafe_allow_html=True,
                        )

                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = "Web Development"
                        st.success(
                            "** According to our analysis, you're seeking for Web Development Jobs **"
                        )
                        recommended_skills = [
                            "React",
                            "Django",
                            "Node JS",
                            "React JS",
                            "php",
                            "laravel",
                            "Magento",
                            "wordpress",
                            "Javascript",
                            "Angular JS",
                            "c#",
                            "Flask",
                            "SDK",
                        ]
                        recommended_keywords = st_tags(
                            label="### Recommended skills for you.",
                            text="Recommended skills generated from System",
                            value=recommended_skills,
                            key="3",
                        )
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>Incorporating these skills into your resume will significantly enhance your prospects of securing a job.</h4>""",
                            unsafe_allow_html=True,
                        )

                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = "Android Development"
                        st.success(
                            "** According to our analysis, you're seeking for Android App Development Jobs **"
                        )
                        recommended_skills = [
                            "Android",
                            "Android development",
                            "Flutter",
                            "Kotlin",
                            "XML",
                            "Java",
                            "Kivy",
                            "GIT",
                            "SDK",
                            "SQLite",
                        ]
                        recommended_keywords = st_tags(
                            label="### Recommended skills for you.",
                            text="Recommended skills generated from System",
                            value=recommended_skills,
                            key="4",
                        )
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>Including these abilities on a resume will increase the likelihood of being hired💼</h4>""",
                            unsafe_allow_html=True,
                        )

                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = "IOS Development"
                        st.success(
                            "** According to our analysis, you're seeking for IOS App Development Jobs **"
                        )
                        recommended_skills = [
                            "IOS",
                            "IOS Development",
                            "Swift",
                            "Cocoa",
                            "Cocoa Touch",
                            "Xcode",
                            "Objective-C",
                            "SQLite",
                            "Plist",
                            "StoreKit",
                            "UI-Kit",
                            "AV Foundation",
                            "Auto-Layout",
                        ]
                        recommended_keywords = st_tags(
                            label="### Recommended skills for you.",
                            text="Recommended skills generated from System",
                            value=recommended_skills,
                            key="5",
                        )
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>Gaining a job is more likely if you include these talents in your resume🚀</h4>""",
                            unsafe_allow_html=True,
                        )

                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = "UI-UX Development"
                        st.success(
                            "** According to our analysis, you're seeking for UI-UX Development Jobs **"
                        )
                        recommended_skills = [
                            "UI",
                            "User Experience",
                            "Adobe XD",
                            "Figma",
                            "Zeplin",
                            "Balsamiq",
                            "Prototyping",
                            "Wireframes",
                            "Storyframes",
                            "Adobe Photoshop",
                            "Editing",
                            "Illustrator",
                            "After Effects",
                            "Premier Pro",
                            "Indesign",
                            "Wireframe",
                            "Solid",
                            "Grasp",
                            "User Research",
                        ]
                        recommended_keywords = st_tags(
                            label="### Recommended skills for you.",
                            text="Recommended skills generated from System",
                            value=recommended_skills,
                            key="6",
                        )
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>Including these abilities in your resume will increase your chances of landing a job💼</h4>""",
                            unsafe_allow_html=True,
                        )

                        break

                #
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                cur_time = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                timestamp = str(cur_date + "_" + cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if "Objective" in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        """<h4 style='text-align: left; color: #1ed760;'>[+] Fantastic! You've included the goal.</h4>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """<h4 style='text-align: left; color: orange;'>[-] In order to help recruiters understand your goals, please include your career objective in accordance with our guidelines.
</h4>""",
                        unsafe_allow_html=True,
                    )

                if "Declaration" in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        """<h4 style='text-align: left; color: #1ed760;'>[+] Fantastic! You have Delcaration added./h4>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>""",
                        unsafe_allow_html=True,
                    )

                if "Hobbies" or "Interests" in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>""",
                        unsafe_allow_html=True,
                    )

                if "Achievements" in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>""",
                        unsafe_allow_html=True,
                    )

                if "Projects" in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>""",
                        unsafe_allow_html=True,
                    )

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success("** Your Resume Writing Score: " + str(score) + "**")
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **"
                )
                


                st.title("ChatNow")

                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

                if "openai_model" not in st.session_state:
                    st.session_state["openai_model"] = "gpt-3.5-turbo"

                if "messages" not in st.session_state:
                    st.session_state.messages = []

                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                if prompt := st.chat_input("What is up?"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        stream = client.chat.completions.create(
                            model=st.session_state["openai_model"],
                            messages=[
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.messages
                            ],
                            stream=True,
                        )
                        response = st.write_stream(stream)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                insert_data(
                    resume_data["name"],
                    resume_data["email"],
                    str(resume_score),
                    timestamp,
                    str(resume_data["no_of_pages"]),
                    reco_field,
                    cand_level,
                    str(resume_data["skills"]),
                    str(recommended_skills),
                    str(rec_course),
                )

                connection.commit()
            else:
                st.error("Something went wrong..")
    elif choice == "Admin Login":
        # Admin Login logic
        st.success("Logging you in as Admin")

        # Set login state to True
        st.session_state.is_logged_in = True
        st.success("Welcome Admin")

        # Display Data
        cursor.execute(
            """SELECT ID,Name,Email_ID,resume_score,Timestamp,Page_no,Predicted_Field,Actual_skills FROM resumedata"""
        )
        data = cursor.fetchall()
        st.header("**User Data**")
        df = pd.DataFrame(
            data,
            columns=[
                "ID",
                "Name",
                "Email",
                "Resume Score",
                "Timestamp",
                "Total Page",
                "Predicted Field",
                "Skills",
            ],
        )
        st.dataframe(df)
        st.markdown(
            get_table_download_link(df, "resumedata.csv", "Download Report"),
            unsafe_allow_html=True,
        )

        ## Resume Upload for Admin
        ## Resume Upload for Admin
        st.subheader("**Upload Resumes for Analysis**")
        uploaded_files = st.file_uploader(
            "Choose your Resumes", accept_multiple_files=True, type=["pdf"]
        )
        if uploaded_files is not None:
            for uploaded_file in uploaded_files:
                if hasattr(
                    uploaded_file, "read"
                ):  # Check if uploaded_file is file-like
                    # Generate a random filename for the uploaded file
                    random_filename = str(random.randint(1, 1000000)) + ".pdf"
                    save_image_path = "./uploads/" + random_filename
                    # Write the bytes content to a file
                    with open(save_image_path, "wb") as f:
                        f.write(uploaded_file.read())  # Read content as bytes
                    st.success(f"Resume uploaded successfully: {random_filename}")

                    resume_data = ResumeParser(save_image_path).get_extracted_data()
                    if resume_data:

                        resume_text = pdf_reader(save_image_path)
                        resume_score = 0
                        if "Objective" in resume_text:
                            resume_score = resume_score + 20
                            st.markdown(
                                """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>""",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>""",
                                unsafe_allow_html=True,
                            )

                        if "Declaration" in resume_text:
                            resume_score = resume_score + 20
                            st.markdown(
                                """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration✍/h4>""",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>""",
                                unsafe_allow_html=True,
                            )

                        if "Hobbies" or "Interests" in resume_text:
                            resume_score = resume_score + 20
                            st.markdown(
                                """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>""",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>""",
                                unsafe_allow_html=True,
                            )

                        if "Achievements" in resume_text:
                            resume_score = resume_score + 20
                            st.markdown(
                                """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>""",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>""",
                                unsafe_allow_html=True,
                            )

                        if "Projects" in resume_text:
                            resume_score = resume_score + 20
                            st.markdown(
                                """<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>""",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                """<h4 style='text-align: left; color: orange;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>""",
                                unsafe_allow_html=True,
                            )

                        ts = time.time()
                        cur_date = datetime.datetime.fromtimestamp(ts).strftime(
                            "%Y-%m-%d"
                        )
                        cur_time = datetime.datetime.fromtimestamp(ts).strftime(
                            "%H:%M:%S"
                        )
                        timestamp = str(cur_date + "_" + cur_time)

                        # Insert data with score 0 initially
                        insert_data(
                            resume_data["name"],
                            resume_data["email"],
                            str(
                                resume_score
                            ),  # Set resume score as 0 initially for admin-added resumes
                            timestamp,  # Empty timestamp
                            str(resume_data["no_of_pages"]),
                            "",  # Empty predicted field
                            "",  # Empty candidate level
                            str(resume_data["skills"]),  # Store skills
                            "",  # Recommended skills initially empty
                            "",  # Empty string for courses
                        )
                        st.success(
                            f"Resume uploaded successfully: {resume_data['name']}"
                        )
                    else:
                        st.error("Error processing the uploaded resume.")
                else:
                    st.error("Uploaded file is not valid.")


run()
