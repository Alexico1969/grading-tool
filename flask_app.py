# Importing required modules
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os
import pandas as pd
from db import init_db, insert_student, get_students, get_student, update_student, delete_student


# Creating Flask object
app = Flask(__name__)
data = []

# Configuring upload folder and allowed file extensions
#app.config['UPLOAD_FOLDER'] = '/path/to/upload/folder'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'xls'}

# Function to check allowed file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for upload form
@app.route('/')
def home():
    return render_template('home.html')

# Route for handling file upload
@app.route('/grades', methods=['GET','POST'])
def grades():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        newfilename = request.form.get('newfilename')
        # If user does not select file, browser submits an empty part without filename
        if file.filename == '':
            return 'No selected file', 400
        if not newfilename:
            return 'No filename provided', 400
        if file and allowed_file(file.filename):
            newfilename = secure_filename(newfilename)
            chapter = request.form.get('chapter')
            # Keep the extension of the original file
            extension = file.filename.rsplit('.', 1)[1].lower()
            newfilename = f"{newfilename}.{extension}"
            filepath=os.path.join(app.config['UPLOAD_FOLDER'], newfilename)
            file.save(filepath)
            # Read the file and return the data
            if extension == 'csv':
                data = pd.read_csv(filepath)
            elif extension == 'txt':
                data = pd.read_csv(filepath, sep='\t')
            elif extension == 'pdf':
                data = pd.read_csv(filepath, sep='\t')
            else:
                return 'File not allowed', 400

            # Include "Student" column
            new_df = data[['Student']]

            # Include any column that contains the current chapter
            for col in data.columns:
                if chapter in col:
                    new_df = pd.concat([new_df, data[col]], axis=1)

            list_2d = new_df.values.tolist()

            points_possible = list_2d[0]
            points_possible = points_possible[1:]
            total_points_possible = 0
            for i in points_possible:
                total_points_possible += i

            #new_list = []

            for student in list_2d:
                total = 0

                for grade in student[1:]:
                    total += grade
                try:
                    student.append(int(total/total_points_possible*100))
                except:
                    student.append(0)

            #print(f"filtered data: {filtered_data}")

            return render_template('output_grades.html', data=list_2d)
        else:
            return 'File not allowed', 400
        
    return render_template('upload_grades.html')

@app.route('/groups', methods=['GET','POST'])
def groups():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        newfilename = request.form.get('newfilename')
        # If user does not select file, browser submits an empty part without filename
        if file.filename == '':
            return 'No selected file', 400
        if not newfilename:
            return 'No filename provided', 400
        if file and allowed_file(file.filename):
            newfilename = secure_filename(newfilename)
            # Keep the extension of the original file
            extension = file.filename.rsplit('.', 1)[1].lower()
            newfilename = f"students.{extension}"
            filepath=os.path.join(app.config['UPLOAD_FOLDER'], newfilename)
            file.save(filepath)
            # Read the file and return the data
            if extension == 'xls':
                data = pd.read_excel(filepath)
            else:
                return f'File type not allowed: {extension}', 400

            # Include "Student" column
            new_df = data

            # Include any column that contains the current chapter
            #for col in data.columns:
            #    first_name = col[0]
            #    print(f"first_name: {first_name}")

            list_2d = new_df.values.tolist()
            new_list = []
            for student in list_2d:
                temp = student[0]
                if temp != 'nan':
                    new_list.append(temp)
                else:
                    print("NaN !!")
            


            print(new_list)

            return render_template('output_groups.html', data=new_list)
        else:
            return 'File not allowed', 400
        
    return render_template('upload_groups.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)