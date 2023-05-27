# Importing required modules
from flask import Flask, request, render_template, redirect, url_for
from jinja2 import Environment, FileSystemLoader

from werkzeug.utils import secure_filename
import os
import pandas as pd
import numpy as np
import math
from db import init_db, insert_student, get_students, get_student, update_student, delete_student, get_all_students



# Creating Flask object
app = Flask(__name__)


data = []

init_db()

# Configuring upload folder and allowed file extensions
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
        group_name = request.form.get('groupName')
        # If user does not select file, browser submits an empty part without filename
        if file.filename == '':
            return 'No selected file', 400
        if not group_name:
            return 'No filename provided', 400
        if file and allowed_file(file.filename):
            newfilename = secure_filename(group_name)
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

            list_2d = new_df.values.tolist()
            new_list = []
            for student in list_2d:
                temp1 = str(student[0])[:-3] #Arcabascio , Alessia
                if "," in temp1:
                    if " ," in temp1:
                        temp1 = temp1.replace(" ,",",")
                        print(f"fixed: {temp1}")

                    temp2 = temp1.split(" ")
                    temp3 = temp2[0] + temp2[1]
                    new_list.append(temp3)
                    temp4 = temp3.split(",")
                    if temp4[1] == "" or len(temp4[1]) <2:
                        print(f"Odd name: {temp4}")
                    insert_student(temp4[0], temp4[1], group_name)
            


            print(new_list)

            return render_template('output_groups.html', data=new_list)
        else:
            return 'File not allowed', 400
        
    return render_template('upload_groups.html')


@app.route('/table', methods=['GET','POST'])
def table():
    if request.method == 'POST':
        group_name = request.form.get('groupName')
        unit = request.form.get('unit')
        student_list = get_students(group_name)
        check_list = []
        for student in student_list:
            name = student[0] + ", " + student[1]
            check_list.append(name)
        #print(f"Check list: {check_list}")
        file_name = unit + ".csv"
        #read csv file with name unit
        grades_list = []
        filepath=os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        data = pd.read_csv(filepath)
        new_df = data[['Student']]

        # Include any column that contains the current chapter
        for col in data.columns:
            if unit in col:
                new_df = pd.concat([new_df, data[col]], axis=1)

        list_2d = new_df.values.tolist()

        points_possible = list_2d[0]
        points_possible = points_possible[1:]
        total_points_possible = 0
        for i in points_possible:
            total_points_possible += i

        new_list = []
        print(f"checklist: {check_list}")
        for student in list_2d:
            temp = student[0].split(" ")
            student[0] = temp[0] + " " + temp[1]
            if student[0] in check_list:
                total = 0
                counter = 0
                for grade in student[1:]:
                    if math.isnan(grade) :
                        grade = 0
                    total += grade
                    student[counter+1] = grade
                    counter += 1
                else:
                    grade = float(grade)
                try:
                    student.append(int(total/total_points_possible*100))
                except:
                    student.append(0)
                

                if student[0] == "Budhwani, Fiza":
                    print(f"student Fiza : {student}")
                
                new_list.append(student)
            else:
                print(f"NOT IN LIST: {student[0]}")


            #print(f"filtered data: {filtered_data}")

        return render_template('output_table.html', data=new_list, unit=unit, group=group_name)
    

    return render_template('ask_table_properties.html')

@app.route('/edit_groups', methods=['GET','POST'])
def edit_groups():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        group_name = request.form.get('groupName')

        print(f"first_name: {first_name}")
        print(f"last_name: {last_name}")
        print(f"group_name: {group_name}")

        if first_name and last_name and group_name:
            return render_template('update_student.html', first_name=first_name, last_name=last_name, group_name=group_name)
        else:
            last_name = ""
            return render_template('update_student.html', first_name=first_name, last_name=last_name, group_name=group_name)

    students = get_all_students()

    return render_template('edit_groups.html', students=students)
    

@app.route('/upd_student', methods=['GET','POST'])
def upd_student():
    if request.method == 'POST':
        print("Updating student")
        first_name = request.form.get('old_first_name')
        last_name = request.form.get('old_last_name')
        group_name = request.form.get('old_group_name')
        new_first_name = request.form.get('new_first_name')
        new_last_name = request.form.get('new_last_name')
        new_group_name = request.form.get('new_group_name')

        print(f"first_name: {first_name}")
        print(f"last_name: {last_name}")
        print(f"group_name: {group_name}")
        print(f"new_first_name: {new_first_name}")
        print(f"new_last_name: {new_last_name}")
        print(f"new_group_name: {new_group_name}")

        if first_name and last_name and group_name and new_first_name and new_last_name and new_group_name:
            update_student(first_name, last_name, group_name, new_first_name, new_last_name, new_group_name)
            return redirect( url_for('edit_groups') )
        else:
            last_name = ""
            update_student(first_name, last_name, group_name, new_first_name, new_last_name, new_group_name)
            return redirect( url_for('edit_groups') )
    
    students = get_all_students()

    return render_template('edit_groups.html', students=students)

# ------------------------------------------------------------

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)