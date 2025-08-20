import streamlit as st
import fitz 
import spacy
import requests

nlp = spacy.load("en_core_web_sm")

SKILL_CATEGORIES = {
    "Languages": ["python", "java", "c++", "c", "javascript", "typescript"],
    "Frameworks": ["react", "node.js", "express", "django", "flask"],
    "Databases": ["mongodb", "mysql", "postgresql", "oracle"],
    "Tools": ["git", "docker", "aws", "gcp", "azure"]
}

LOCATIONS = ["Bengaluru", "Hyderabad", "Pune", "Chennai", "Mumbai", "Delhi", "Gurgaon", "Kolkata","Coimbatore"]

def extract_text_from_pdf(uploaded_file):
    text = ""
    if uploaded_file is not None:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text()
    return text


def extract_skills(text):
    text = text.lower()
    tokens = [token.text for token in nlp(text) if not token.is_stop and not token.is_punct]
    found_skills = {category: [] for category in SKILL_CATEGORIES}
    for category, keywords in SKILL_CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in tokens:
                found_skills[category].append(keyword)
    return {k: v for k, v in found_skills.items() if v}


def fetch_jobs_from_jsearch(role, location):
    query = f"{role} in {location}"
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {"query": query, "page": "1", "num_pages": "1", "page_size": "5", "country": "IN"}
    headers = {
        "X-RapidAPI-Key": "4a918a2b62msh5cd1a3601c39646p1516eajsn720daf470c21",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    results = []

    if response.status_code == 200:
        data = response.json()
        for job in data.get("data", [])[:5]:
            title = job.get("job_title", "N/A")
            company = job.get("employer_name", "Unknown")
            city = job.get("job_city") or "Unknown City"
            country = job.get("job_country") or "Unknown Country"
            location = f"{city}, {country}"
            link = job.get("job_apply_link") or job.get("job_google_link") or "#"
            results.append((title, company, location, link))
    else:
        raise Exception(f"API error: {response.status_code} - {response.text}")

    return results

st.set_page_config(page_title="Resume Skill Extractor & Job Finder", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f4f6f8; }
    .reportview-container { padding: 2rem 1.5rem 1.5rem; }
    h1 { color: #2c3e50; font-size: 2.5rem; text-align: center; }
    .skill-block {
        background-color: #eaf4fc;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 6px solid #2980b9;
    }
    .job-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .job-card h4 { margin-bottom: 5px; color: #1a237e; }
    .job-card a {
        color: #388e3c;
        font-weight: bold;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

st.title("AI Resume Skill Extractor & Job Recommender")
st.write("Upload your resume to extract skills and find relevant job openings.")

uploaded_file = st.file_uploader("Upload your resume (PDF format)", type=["pdf"])

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    st.subheader("Extracted Skills")
    skills_by_category = extract_skills(resume_text)

    if skills_by_category:
        for category, skills in skills_by_category.items():
            st.markdown(f'<div class="skill-block"><b>{category}:</b> {", ".join(skills)}</div>', unsafe_allow_html=True)
    else:
        st.warning("No matching skills found from the known categories.")


    roles = []
    if "Frameworks" in skills_by_category and "react" in skills_by_category["Frameworks"]:
        roles.append("Frontend Developer")
    if "Frameworks" in skills_by_category and "node.js" in skills_by_category["Frameworks"]:
        roles.append("Backend Developer")
    if set(["react", "node.js", "mongodb"]).issubset([s for slist in skills_by_category.values() for s in slist]):
        roles.append("MERN Stack Developer")
    if "Languages" in skills_by_category and any(lang in ["python", "java", "c++"] for lang in skills_by_category["Languages"]):
        roles.append("Full Stack Developer")

   
    st.subheader("Select Preferred Job Location")
    selected_location = st.selectbox("Choose a city in India:", LOCATIONS)

    # Display jobs
    st.subheader(f"Job Recommendations in {selected_location}")
    if roles:
        for role in roles:
            st.markdown(f"### 🔸 {role}")
            try:
                jobs = fetch_jobs_from_jsearch(role, selected_location)
                if jobs:
                    for title, company, location, link in jobs:
                        st.markdown(
                            f"""
                            <div class="job-card">
                                <h4>🔹 {title}</h4>
                                <p><b>🏢 {company}</b><br>📍 {location}</p>
                                <a href="{link}" target="_blank">🟢 Apply Now</a>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning(f"No jobs found for {role} in {selected_location}.")
            except Exception as e:
                st.error(f"Error fetching jobs for {role}: {e}")
    else:
        st.info("Try uploading a resume with more tech-oriented skills to get role-based recommendations.")
