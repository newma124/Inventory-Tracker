# Inventory Tracker (Flask + SQLite)

## Overview

This project is a web-based inventory management system built using **Flask**, **SQLite**, and **SQLAlchemy**. It allows users to create, update, delete, and analyze inventory items through a clean user interface.

The application demonstrates key database concepts including:

* CRUD operations
* Dynamic dropdowns backed by database tables
* Query filtering and reporting
* Indexing for performance optimization
* SQL injection protection
* Transaction management and isolation levels

---

## Author

Joshua Newman

---

## Technologies Used

* Python
* Flask
* SQLite
* SQLAlchemy (ORM)
* HTML/CSS (Jinja templates)

---

## AI Usage Disclosure

Artificial intelligence was used in the making of this project. ChatGPT was my model of choice and I used it to assist with the following things:

### Project Structure and UI

I personally have extremely limited web design experience, so I asked it for advice on what frameworks I should use. It recommended the web and database frameworks that I should use. ChatGPT also helped in setting up and formatting the project so that I could implement the important things. Any overhaul in how I decided to do my project would require significant time redoing the UI elements in the HTML files. I used ChatGPT to generate the **base.html** file, and then I did coded the remaining html files while using ChatGPT to debug problems I had. Additionally, I used ChatGPT to generate the **Installation** portion of this README.

### Generating Sample Data

ChatGPT generated **seed_data.py** so that I could have some sample data to test out, without having to manually create data.

### Debugging

ChatGPT was helpful in assisting with debugging, especially with setting it up. I would explains any issues with outputting and copy in error messages.

### Verifying ChatGPT Output and Correctness

No AI is perfect, and they tend to output incorrect information. The easiest way to test the correctness of the output is to implement it, test it out, and look for any problems with it. I had my fair share of times where ChatGPT outputted incorrect information and I would have to fix it.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/newma124/inventory-tracker.git
cd inventory-tracker
```

### 1b. Create a folder called "templates" and place all the .html files in it. 

```
templates/
  base.html
  item_detail.html
  item_form.html
  items_list.html
  report.html
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask flask-sqlalchemy sqlalchemy
```

### 4. Run the application

```bash
python app.py
```

### 5. Open in browser

```
http://127.0.0.1:5000
```

---

## Sample Data Generation

To quickly populate the database with sample data:

```bash
python seed_data.py
```

This script inserts:

* Multiple categories, locations, statuses, and conditions
* ~60 sample inventory items

