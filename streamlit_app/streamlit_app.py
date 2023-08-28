import streamlit as st
import subprocess
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
import os

def generate_plot(data, scales, selected_style, selected_palette):
    plt.figure(figsize=(14, 10))
    plt.subplots_adjust(hspace=0.7)
    sns.set(style=selected_style, palette=selected_palette)  # Set Seaborn style
    

    for i, scale in enumerate(scales, start=1):
        scale_data = data[data['scale_name'] == scale]

        plt.subplot(len(scales), 1, i)
        sns.lineplot(data=scale_data, x='item', y='self', marker='o', label='Selbst')
        sns.lineplot(data=scale_data, x='item', y='blk', marker='o', label='BLK')
        sns.lineplot(data=scale_data, x='item', y='pk_mean', marker='o', label='PK')
        sns.lineplot(data=scale_data, x='item', y='sus_mean', marker='o', label='SUS')
        plt.xlabel('Item', fontweight='bold')
        plt.ylabel('Bewertung', fontweight='bold')
        plt.title(f'{scale}', fontweight='bold')
        plt.legend(loc='upper left', prop={'weight': 'bold'}, bbox_to_anchor=(1, 1))
        plt.ylim(0.5, 4.5)
        plt.yticks([1, 2, 3, 4])

    # Save the plot as a PNG file
    temp_png = 'temp_plot.png'
    plt.savefig(temp_png, format='png')

    plt.close()
    return temp_png

def generate_bar_graph(data, scales, selected_style, selected_palette):
    # Initialize lists to store means for each scale and viewer
    means_self = []
    means_blk = []
    means_pk = []
    means_sus = []

    for scale in scales:
        scale_data = data[data['scale_name'] == scale]

        # Calculate means for each viewer
        mean_self = scale_data['self'].mean()
        mean_blk = scale_data['blk'].mean()
        mean_pk = scale_data['pk_mean'].mean()
        mean_sus = scale_data['sus_mean'].mean()

        # Append means to respective lists
        means_self.append(mean_self)
        means_blk.append(mean_blk)
        means_pk.append(mean_pk)
        means_sus.append(mean_sus)

    # Set Seaborn style
    sns.set(style=selected_style, palette=selected_palette)
    

    # Create a bar graph
    plt.figure(figsize=(14, 12))
    bar_width = 0.2

    plt.bar(range(len(scales)), means_self, width=bar_width, label='Selbst', align='center')
    plt.bar([i + bar_width for i in range(len(scales))], means_blk, width=bar_width, label='BLK', align='center')
    plt.bar([i + 2 * bar_width for i in range(len(scales))], means_pk, width=bar_width, label='PK', align='center')
    plt.bar([i + 3 * bar_width for i in range(len(scales))], means_sus, width=bar_width, label='SUS', align='center')

    # Set the x-axis labels to scale_short
    scale_labels = data.drop_duplicates(subset=['scale_name', 'scale_short'])[['scale_name', 'scale_short']]
    x_labels = [label for label in scale_labels['scale_short']]

    plt.xlabel('Merkmal', fontweight='bold')
    plt.ylabel('Mittelwert', fontweight='bold')
    plt.title('Mittelwerte je Merkmal', fontweight='bold')
    plt.xticks([i + 1.5 * bar_width for i in range(len(scales))], x_labels, rotation=0, ha='center', fontweight='bold', fontsize=12)
    plt.legend(loc='upper left', prop={'weight': 'bold'})
    plt.ylim(0.5, 4.5)
    plt.yticks([1, 2, 3, 4])
    plt.tight_layout()

    # Save the bar graph as a PNG file
    temp_bar_png = 'temp_bar_plot.png'
    plt.savefig(temp_bar_png, format='png')

    plt.close()
    return temp_bar_png



def create_pdf_with_graph(file_path, output_file, additional_info, selected_style, selected_palette):
    # Read the CSV file
    data = pd.read_excel(file_path)

    # Delete rows with all missing values
    data = data.dropna(axis=0, how='all')
    # Delete columns with all missing values
    data = data.dropna(axis=1, how='all')

    # Fill missing values with the mean
    pk_columns = [col for col in data.columns if col.startswith('pk')]
    sus_columns = [col for col in data.columns if col.startswith('sus')]
    data[pk_columns] = data[pk_columns].fillna(data[pk_columns].mean())
    data[sus_columns] = data[sus_columns].fillna(data[sus_columns].mean())

    # Compute the mean for PK values and SUS scores on each scale
    data['pk_mean'] = data[pk_columns].mean(axis=1)
    data['sus_mean'] = data[sus_columns].mean(axis=1)

    scales = data['scale_name'].unique()

    # Create a new PDF document
    c = canvas.Canvas(output_file, pagesize=letter)

    # Add additional text to the PDF
    y_position = 30
    font_size = 12
    line_spacing = 20

    additional_text = [
        f"Name: {additional_info['name']}",
        f"Schule und Schulform: {additional_info['school']}",
        f"Klassenstufe: {additional_info['class_level']}",
        f"Tag und Uhrzeit: {additional_info['date_time']}",
        f"Thema: {additional_info['topic']}"
    ]

    c.setFont("Helvetica", font_size)

    # Calculate the required height for the graph and additional text
    graph_height = 600
    additional_text_height = (len(additional_text) + 1) * line_spacing

    # Adjust the y-position if the graph will overlap with the additional text
    if graph_height + additional_text_height > y_position:
        y_position = graph_height + additional_text_height + line_spacing

    for line in additional_text:
        c.drawString(100, y_position, line)
        y_position -= line_spacing

    # Generate the plot and get the temporary PNG file
    temp_png = generate_plot(data, scales, selected_style, selected_palette)

    # Draw the PNG on the PDF canvas
    c.drawImage(temp_png, 0, 50, width=600, height=600)

    # Remove the temporary PNG file
    os.remove(temp_png)

    # Add a new page for the bar graph
    c.showPage()

    # Set the page size to landscape mode (querformat)
    c.setPageSize(landscape(letter))

    # Generate the bar graph and get the temporary PNG file
    temp_bar_png = generate_bar_graph(data, scales, selected_style, selected_palette)

    # Calculate the required width and height to fit the bar graph within the canvas
    width, height = landscape(letter)
    bar_graph_width = 800
    bar_graph_height = 400

    x_offset = (width - bar_graph_width) / 2
    y_offset = (height - bar_graph_height) / 2

    # Draw the PNG on the PDF canvas
    c.drawImage(temp_bar_png, x_offset, y_offset, width=bar_graph_width, height=bar_graph_height)

    # Remove the temporary PNG file
    os.remove(temp_bar_png)

    # Save the PDF document
    c.showPage()
    c.save()

    print(f"PDF file '{output_file}' created successfully.")

def main():
    st.title("Grafik Unterrichtsbeobachtung")

    name = st.text_input("Name der Praktikantin/des Praktikanten:")
    school = st.text_input("Name der Schule und Schulform:")
    class_level = st.text_input("Klassenstufe:")
    date_time = st.text_input("Tag und Uhrzeit des Unterrichts:")
    topic = st.text_input("Thema des Unterrichts:")
    selected_style = st.selectbox("Select a Seaborn style", ["darkgrid", "whitegrid"])
    selected_palette = st.selectbox("Select a Seaborn palette", ["bright", "deep", "muted", "pastel", "dark", "colorblind"])

    file_path = st.file_uploader("Datei auswählen (.xlsx)", type=["xlsx"])

    if st.button("Grafik erstellen"):
        if file_path is not None:
            additional_info = {
                'name': name,
                'school': school,
                'class_level': class_level,
                'date_time': date_time,
                'topic': topic
            }

            create_pdf_with_graph(file_path, 'output.pdf', additional_info, selected_style, selected_palette)

            try:
                if sys.platform.startswith('win32'):
                    subprocess.run(['start', 'output.pdf'], check=True, shell=True)
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', 'output.pdf'], check=True)
                else:
                    st.error("Unsupported platform.")
            except subprocess.CalledProcessError as e:
                st.error("Failed to open the PDF file.")

if __name__ == "__main__":
    main()