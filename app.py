from flask import Flask, render_template, request, redirect, send_file, url_for
import csv
import os
from datetime import datetime
import random
import hashlib
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)

# Ensure donations.csv exists with updated headers including hash
csv_file = 'donations.csv'
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Donor Name', 'Food Type', 'Quantity', 'Location', 'Time Since Cooked',
                         'Storage Method', 'Timestamp', 'Safe to Donate', 'Previous Hash'])

@app.route('/')
def index():
    return render_template('index.html')

def compute_hash(row):
    row_string = ','.join(str(i) for i in row)
    return hashlib.sha256(row_string.encode()).hexdigest()

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        donor_name = request.form['donor_name']
        food_type = request.form['food_type']
        quantity = request.form['quantity']
        location = request.form['location']
        time_cooked = request.form['time_cooked']
        storage_method = request.form['storage_method']
        safe_to_donate = request.form.get('safe_to_donate', 'No')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(csv_file, 'r') as file:
            reader = list(csv.reader(file))
            if len(reader) > 1:
                last_row = reader[-1]
                last_hash = compute_hash(last_row[:-1])
            else:
                last_hash = "GENESIS"

        new_row = [donor_name, food_type, quantity, location, time_cooked,
                   storage_method, timestamp, safe_to_donate, last_hash]

        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(new_row)

        return redirect('/')
    return render_template('donate.html')

@app.route('/view')
def view_donations():
    donations = []
    headers = []
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            for row in reader:
                donations.append(row)
    except FileNotFoundError:
        pass
    return render_template('view_donations.html', donations=donations, headers=headers)

@app.route('/certificate', methods=['GET', 'POST'])
def certificate():
    if request.method == 'POST':
        name = request.form['name']
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.utils import ImageReader
        import io

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        logo_path = "static/logo.png"
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            c.drawImage(logo, width/2 - 50, height - 120, width=100, preserveAspectRatio=True, mask='auto')

        c.setStrokeColor(colors.HexColor("#2b4f81"))
        c.setLineWidth(6)
        c.rect(30, 30, width - 60, height - 60)

        c.setFont("Helvetica-Bold", 30)
        c.setFillColor(colors.HexColor("#2b4f81"))
        c.drawCentredString(width / 2, height - 160, "Certificate of Contribution")

        c.setFont("Times-Italic", 18)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2, height - 200, "This is to certify that")

        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 240, name)

        c.setFont("Helvetica", 16)
        c.drawCentredString(width / 2, height - 280, "has contributed to reducing food waste and hunger")

        date_str = datetime.now().strftime("%d %B %Y")
        c.setFont("Helvetica-Oblique", 12)
        c.drawCentredString(width / 2, height - 320, f"Issued on: {date_str}")

        c.setFont("Helvetica", 12)
        c.drawString(80, 80, "_____________________")
        c.drawString(80, 65, "Organizer Signature")

        c.showPage()
        c.save()
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name=f"{name}_certificate.pdf", mimetype='application/pdf')

    return render_template('certificate.html')

@app.route('/claim')
def claim():
    claims = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        for row in reader:
            if row and row[7].strip().lower() == 'yes':
                claims.append(row)
    return render_template('claim.html', claims=claims)

@app.route('/training')
def training():
    videos = [
        "https://youtu.be/7f_91Tbp0ew",
        "https://youtu.be/9xV8vf_P_nU",
        "https://youtu.be/osA74cAqMLc"
    ]
    return render_template('training.html', videos=videos)

@app.route('/ai-scan')
def ai_scan():
    return render_template('coming_soon.html', feature="AI Food Quality Scanner")

@app.route('/learning')
def learning_dashboard():
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        return "donations.csv not found."

    os.makedirs('static/charts', exist_ok=True)

    def estimate_meals(qty):
        qty = str(qty).lower()
        if 'plate' in qty:
            return int(qty.split()[0])
        elif 'kg' in qty:
            return int(float(qty.split()[0]) * 4)
        return 1

    df['Estimated Meals'] = df['Quantity'].apply(estimate_meals)
    total_meals = df['Estimated Meals'].sum()

    if total_meals >= 100:
        badge = "🏇 Gold Contributor"
    elif total_meals >= 50:
        badge = "🥈 Silver Contributor"
    elif total_meals >= 10:
        badge = "🥉 Bronze Contributor"
    else:
        badge = "👣 Keep Going!"

    try:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Month'] = df['Timestamp'].dt.strftime('%b %Y')
        monthly = df.groupby('Month')['Estimated Meals'].sum()
        monthly.plot(kind='bar', color='#2196F3')
        plt.title('Monthly Meals Donated')
        plt.ylabel('Meals')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/charts/monthly_progress.png')
        plt.clf()
    except:
        pass

    try:
        safe_counts = df['Safe to Donate'].value_counts()
        safe_counts.plot(kind='pie', autopct='%1.1f%%', colors=['#4CAF50', '#F44336'], title='Food Safety')
        plt.ylabel('')
        plt.savefig('static/charts/safety_chart.png')
        plt.clf()
    except:
        pass

    return render_template('learning.html', total_meals=total_meals, badge=badge)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        ngo_name = request.form['ngo_name']
        food_item = request.form['food_item']
        feedback_type = request.form['feedback_type']
        comments = request.form['comments']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open('feedback.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([ngo_name, food_item, feedback_type, comments, timestamp])

        return redirect('/')
    return render_template('feedback.html')

@app.route('/view_feedback')
def view_feedback():
    feedback = []
    try:
        with open('feedback.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                feedback.append(row)
    except FileNotFoundError:
        pass
    return render_template('view_feedback.html', feedback=feedback)

@app.route('/verify-chain')
def verify_chain():
    try:
        with open('donations.csv', 'r') as file:
            reader = list(csv.reader(file))
            headers = reader[0]
            previous_hash = "GENESIS"

            for i in range(1, len(reader)):
                row = reader[i]
                expected_hash = compute_hash(row[:-1])
                if row[-1] != previous_hash:
                    return f"❌ Chain broken at line {i+1}. Data may be tampered!"
                previous_hash = expected_hash

        return "✅ Donation log chain is valid. No tampering detected."

    except:
        return "⚠️ Error reading or verifying chain."
@app.context_processor
def inject_chain_status():
    import csv
    status = "⚠️ Unable to verify"
    try:
        with open('donations.csv', 'r') as file:
            reader = list(csv.reader(file))
            previous_hash = "GENESIS"

            for i in range(1, len(reader)):
                row = reader[i]
                expected_hash = compute_hash(row[:-1])
                if row[-1] != previous_hash:
                    status = "❌ Chain Broken"
                    break
                previous_hash = expected_hash
            else:
                status = "✅ Chain Verified"
    except:
        status = "⚠️ Verification Error"

    return dict(chain_status=status)


if __name__ == '__main__':
 from os import environ
    app.run(host='0.0.0.0', port=int(environ.get('PORT', 5000)))

