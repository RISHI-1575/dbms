from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime
import plotly.express as px
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Configuration
db_config = {
    'user': 'root',
    'password': '12345678901',
    'host': 'localhost',
    'database': 'expense_tracker'
}

# Database Connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        amount = request.form['amount']
        payment_type = request.form['payment_type']
        category = request.form['category']
        date = request.form['date']
        description = request.form['description']
        comment = request.form.get('comment', '')

        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, payment_type, category, date, description, comment) VALUES (%s, %s, %s, %s, %s, %s)",
            (amount, payment_type, category, date, description, comment)
        )
        conn.commit()
        conn.close()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_expense.html')

@app.route('/view-expenses', methods=['GET', 'POST'])
def view_expenses():
    filters = {}
    if request.method == 'POST':
        filters['start_date'] = request.form.get('start_date')
        filters['end_date'] = request.form.get('end_date')
        filters['month'] = request.form.get('month')
        filters['category'] = request.form.get('category')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if filters.get('start_date') and filters.get('end_date'):
        query += " AND date BETWEEN %s AND %s"
        params.extend([filters['start_date'], filters['end_date']])
    if filters.get('month'):
        query += " AND MONTH(date) = %s"
        params.append(filters['month'])
    if filters.get('category'):
        query += " AND category = %s"
        params.append(filters['category'])

    cursor.execute(query, params)
    expenses = cursor.fetchall()
    conn.close()

    return render_template('view_expenses.html', expenses=expenses)

@app.route('/update-expense/<int:expense_id>', methods=['GET', 'POST'])
def update_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        amount = request.form['amount']
        payment_type = request.form['payment_type']
        category = request.form['category']
        date = request.form['date']
        description = request.form['description']
        comment = request.form.get('comment', '')

        cursor.execute(
            "UPDATE expenses SET amount = %s, payment_type = %s, category = %s, date = %s, description = %s, comment = %s WHERE id = %s",
            (amount, payment_type, category, date, description, comment, expense_id)
        )
        conn.commit()
        conn.close()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('view_expenses'))

    cursor.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
    expense = cursor.fetchone()
    conn.close()
    return render_template('update_expense.html', expense=expense)

@app.route('/delete-expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
    conn.commit()
    conn.close()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('view_expenses'))

@app.route('/reports')
def reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(expenses)
    if df.empty:
        return render_template('reports.html', graph1=None, graph2=None)

    # Pie Chart
    category_summary = df.groupby('category')['amount'].sum().reset_index()
    pie_chart = px.pie(category_summary, names='category', values='amount', title='Category-wise Expense')
    pie_chart_html = pie_chart.to_html(full_html=False)

    # Line Graph
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')  # Convert to Period
    df['month'] = df['month'].astype(str)  # Convert Period to string
    monthly_trend = df.groupby('month')['amount'].sum().reset_index()
    line_graph = px.line(monthly_trend, x='month', y='amount', title='Monthly Expense Trend')
    line_graph_html = line_graph.to_html(full_html=False)

    return render_template('reports.html', graph1=pie_chart_html, graph2=line_graph_html)

if __name__ == '__main__':
    app.run(debug=True)