from flask import Flask, render_template, request, redirect, send_file
import csv
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO

app = Flask(__name__)

# Folder where all dramas will be stored
DRAMAS_FOLDER = 'Dramas'

# Create the main Dramas folder if it doesn't exist
if not os.path.exists(DRAMAS_FOLDER):
    os.makedirs(DRAMAS_FOLDER)

# Read dramas from CSV file
def read_dramas():
    dramas = []
    try:
        with open('dramas.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            dramas = list(reader)
    except FileNotFoundError:
        pass
    return dramas

# Write updated dramas to CSV file
def write_dramas(dramas):
    with open('dramas.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(dramas)

# Route to display the form and list
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        drama_name = request.form['drama_name']
        genre = request.form['genre']

        # Create a folder for the drama inside the Dramas folder
        drama_folder_path = os.path.join(DRAMAS_FOLDER, drama_name)
        if not os.path.exists(drama_folder_path):
            os.makedirs(drama_folder_path)

        # Save the drama details to a CSV file
        dramas = read_dramas()
        dramas.append([drama_name, genre])
        write_dramas(dramas)

        return redirect('/')

    dramas = read_dramas()
    return render_template('index.html', dramas=dramas)

# Route to delete a drama
@app.route('/delete/<int:index>')
def delete_drama(index):
    dramas = read_dramas()
    if 0 <= index < len(dramas):
        drama_name = dramas[index][0]
        # Delete the drama folder if it exists
        drama_folder_path = os.path.join(DRAMAS_FOLDER, drama_name)
        if os.path.exists(drama_folder_path):
            os.rmdir(drama_folder_path)

        dramas.pop(index)
    write_dramas(dramas)
    return redirect('/')

# Route to edit a drama
@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_drama(index):
    dramas = read_dramas()
    if request.method == 'POST':
        new_drama_name = request.form['drama_name']
        new_genre = request.form['genre']

        old_drama_name = dramas[index][0]

        # Update folder name if the drama name changes
        old_drama_folder_path = os.path.join(DRAMAS_FOLDER, old_drama_name)
        new_drama_folder_path = os.path.join(DRAMAS_FOLDER, new_drama_name)

        if old_drama_folder_path != new_drama_folder_path:
            if os.path.exists(old_drama_folder_path):
                os.rename(old_drama_folder_path, new_drama_folder_path)

        if 0 <= index < len(dramas):
            dramas[index] = [new_drama_name, new_genre]
        write_dramas(dramas)
        return redirect('/')

    if 0 <= index < len(dramas):
        return render_template('edit.html', drama=dramas[index], index=index)
    return redirect('/')

# Route to generate and download the PDF with enhanced style
@app.route('/download_pdf')
def download_pdf():
    # Create an in-memory buffer for the PDF
    buffer = BytesIO()

    # Create a PDF document
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Add title with custom style
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontSize=24,
        textColor=colors.darkblue,
        alignment=1,  # Center alignment
        spaceAfter=20
    )
    title = Paragraph("Saved K-Dramas", title_style)
    elements.append(title)

    # Add space after the title
    elements.append(Spacer(1, 0.25 * inch))

    # Create table data
    dramas = read_dramas()
    table_data = [['Drama Name', 'Genre']] + dramas

    # Create a table with more advanced styling
    table = Table(table_data, colWidths=[250, 250])

    # Table styling for a prettier look
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))

    elements.append(table)

    # Build the PDF
    pdf.build(elements)

    # Seek the buffer to the beginning
    buffer.seek(0)

    # Send the PDF as a downloadable file
    return send_file(buffer, as_attachment=True, download_name="kdramas.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
