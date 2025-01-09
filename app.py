import cohere
import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from PIL import Image
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import docx

# Load environment variables
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Init Cohere API client
co = cohere.Client(COHERE_API_KEY)

st.set_page_config(page_title="Q&A AI Assistant 📁", page_icon="📁", layout="wide")

hide_streamlit_style = """
    <style>
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

#Title and Description
st.title("File Q&A AI Assistant 📁")
st.write("This interface allows users to upload CSV, Excel, PDF, Word, or enter text and ask questions related to the content.")

with st.expander("Expand to see how it works."):
    st.markdown("""
    - **CSV & Excel Files**: Upload your data file and interact directly with the content. Ask questions or request visualizations.
    - **PDF & Word Files**: Upload a document and ask questions based on the content.
    - **Text Input**: Enter custom text to analyze and query.
    """)

# Function to generate charts
def generate_chart(query, df):
    """
    Generates a chart based on the user's query.
    """
    try:
        if "bar chart" in query.lower():
            x_col, y_col = df.columns[:2]
            df.plot(kind="bar", x=x_col, y=y_col, legend=False)
            plt.title(f"Bar Chart for {x_col} vs {y_col}")
            plt.tight_layout()
            plt.savefig("temp_chart.png")
            st.image("temp_chart.png")
            os.remove("temp_chart.png")
        elif "line chart" in query.lower():
            x_col, y_col = df.columns[:2]
            df.plot(kind="line", x=x_col, y=y_col, legend=False)
            plt.title(f"Line Chart for {x_col} vs {y_col}")
            plt.tight_layout()
            plt.savefig("temp_chart.png")
            st.image("temp_chart.png")
            os.remove("temp_chart.png")
        else:
            st.write("Chart type not recognized. Please specify 'bar chart' or 'line chart'.")
    except Exception as e:
        st.error(f"Error generating chart: {e}")

# Function to handle CSV and Excel files
def process_tabular_file(query, file_data, file_type):
    try:
        if not isinstance(file_data, pd.DataFrame):
            df = pd.read_excel(file_data) if file_type == "Excel" else pd.read_csv(file_data)
        else:
            df = file_data

        st.write("Uploaded Data:")
        st.write(df)

        if "chart" in query.lower():
            generate_chart(query, df)
        else:
            response = co.generate(
                model='command-xlarge-nightly',
                prompt=f"Analyze the following data and answer the question: {query}\nData: {df.to_string()}",
                max_tokens=500
            )
            st.write("Response:", response.generations[0].text.strip())
    except Exception as e:
        st.error(f"Error processing tabular file: {e}")

# Function to handle document files (PDF/Word/Text)
def process_document_file(query, file_data):
    try:
        chunks = [file_data[i:i + 1000] for i in range(0, len(file_data), 1000)]
        response = co.generate(
            model='command-xlarge-nightly',
            prompt=f"Use the following text to answer the question: {query}\nText: {''.join(chunks)}",
            max_tokens=500
        )
        st.write("Response:", response.generations[0].text.strip())
    except Exception as e:
        st.error(f"Error processing document file: {e}")

# Function to extract text from Word files
def extract_word_content(file):
    doc = docx.Document(file)
    return "".join(paragraph.text for paragraph in doc.paragraphs)

# Function to extract text from PDF files
def extract_pdf_content(file):
    pdf_reader = PdfReader(file)
    return "".join(page.extract_text() for page in pdf_reader.pages)

# application logic
query_text = st.text_area("Question", height=100)
file_type = st.selectbox("Select File Type", options=["CSV", "Excel", "PDF", "Word", "Text"])

files_data = []

if file_type in ["CSV", "Excel"]:
    files = st.file_uploader(f"Upload {file_type} files", type=["csv", "xlsx"] if file_type == "Excel" else ["csv"], accept_multiple_files=True)
    if files:
        for file in files:
            files_data.append(file)
elif file_type == "PDF":
    files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
    if files:
        for file in files:
            pdf_content = extract_pdf_content(file)
            files_data.append(pdf_content)
            st.write("Uploaded PDF content:")
            st.text_area(f"PDF content from {file.name}", value=pdf_content, height=300, disabled=True)
elif file_type == "Word":
    files = st.file_uploader("Upload Word files", type="docx", accept_multiple_files=True)
    if files:
        for file in files:
            word_content = extract_word_content(file)
            files_data.append(word_content)
            st.write("Uploaded Word content:")
            st.text_area(f"Word content from {file.name}", value=word_content, height=300, disabled=True)
else:
    text_input = st.text_area("Enter text here")
    if text_input:
        files_data.append(text_input)

# Process query on button click
if st.button("Send"):
    if query_text and files_data:
        for idx, file_data in enumerate(files_data):
            st.write(f"Processing file {idx + 1}...")
            if file_type in ["CSV", "Excel"]:
                process_tabular_file(query_text, file_data, file_type)
            else:
                process_document_file(query_text, file_data)
    else:
        st.warning("Please upload files or enter text, and provide a query.")


# Footer
st.markdown("---")
st.markdown("""<p style='text-align: center'><a href='https://github.com/sandbox259'>Github</a></p>""", unsafe_allow_html=True)
