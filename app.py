from flask import Flask, render_template, request, redirect, url_for, session, flash

import mysql.connector

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import date, timedelta

from dsa.queue import WaitingQueue
from dsa.stack import HistoryStack


app = Flask(__name__)

app.secret_key = "library-mini-project-secret-key"


# =========================================================
# MYSQL DATABASE CONNECTION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "simran3210;",
    "database": "library_management"
}


def get_db_connection():

    return mysql.connector.connect(**DB_CONFIG)


# =========================================================
# DSA OBJECTS
# =========================================================

waiting_queue = WaitingQueue()

history_stack = HistoryStack()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if not name or not email or not password:

            flash("All fields are required.", "danger")

            return redirect(url_for("register"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()
            conn.close()

            flash("Email already registered.", "danger")

            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (%s, %s, %s, 'student')
            """,
            (name, email, hashed_password)
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total books
    cursor.execute(
        "SELECT COUNT(*) AS total FROM books"
    )

    total_books = cursor.fetchone()["total"]

    # Available copies
    cursor.execute(
        "SELECT COALESCE(SUM(available_copies), 0) AS available FROM books"
    )

    available_books = cursor.fetchone()["available"]

    # User's issued books
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM issues
        WHERE user_id = %s
        AND status = 'issued'
        """,
        (session["user_id"],)
    )

    issued_books = cursor.fetchone()["total"]

    # User's fine
    cursor.execute(
        """
        SELECT COALESCE(SUM(fine), 0) AS total
        FROM issues
        WHERE user_id = %s
        """,
        (session["user_id"],)
    )

    total_fine = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        available_books=available_books,
        issued_books=issued_books,
        total_fine=total_fine
    )


# =========================================================
# BOOK LIST
# =========================================================

@app.route("/books")
def books():

    if "user_id" not in session:

        return redirect(url_for("login"))

    search = request.args.get("search", "")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:

        cursor.execute(
            """
            SELECT *
            FROM books
            WHERE title LIKE %s
            OR author LIKE %s
            OR category LIKE %s
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        )

    else:

        cursor.execute(
            "SELECT * FROM books ORDER BY title"
        )

    books_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "books.html",
        books=books_list,
        search=search
    )


# =========================================================
# ADD BOOK
# =========================================================

@app.route("/add_book", methods=["POST"])
def add_book():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if session.get("role") != "librarian":

        flash("Only librarian can add books.", "danger")

        return redirect(url_for("books"))

    title = request.form["title"]
    author = request.form["author"]
    category = request.form["category"]
    isbn = request.form["isbn"]

    total_copies = int(request.form["total_copies"])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO books
        (title, author, category, isbn, total_copies, available_copies)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            title,
            author,
            category,
            isbn,
            total_copies,
            total_copies
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Book added successfully.", "success")

    return redirect(url_for("books"))


# =========================================================
# DELETE BOOK
# =========================================================

@app.route("/delete_book/<int:book_id>")
def delete_book(book_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    if session.get("role") != "librarian":

        flash("Only librarian can delete books.", "danger")

        return redirect(url_for("books"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM books WHERE id = %s",
        (book_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Book deleted successfully.", "success")

    return redirect(url_for("books"))


# =========================================================
# ISSUE BOOK
# =========================================================

@app.route("/issue/<int:book_id>", methods=["GET", "POST"])
def issue_book(book_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get book
    cursor.execute(
        "SELECT * FROM books WHERE id = %s",
        (book_id,)
    )

    book = cursor.fetchone()

    if not book:

        cursor.close()
        conn.close()

        flash("Book not found.", "danger")

        return redirect(url_for("books"))

    # Check already issued
    cursor.execute(
        """
        SELECT *
        FROM issues
        WHERE user_id = %s
        AND book_id = %s
        AND status = 'issued'
        """,
        (
            session["user_id"],
            book_id
        )
    )

    existing_issue = cursor.fetchone()

    if existing_issue:

        cursor.close()
        conn.close()

        flash("You already have this book.", "warning")

        return redirect(url_for("books"))

    # GET
    if request.method == "GET":

        cursor.close()
        conn.close()

        return render_template(
            "issue.html",
            book=book
        )

    # POST

    if book["available_copies"] <= 0:

        # Check waiting queue in database
        cursor.execute(
            """
            SELECT *
            FROM waiting_queue
            WHERE user_id = %s
            AND book_id = %s
            AND status = 'waiting'
            """,
            (
                session["user_id"],
                book_id
            )
        )

        already_waiting = cursor.fetchone()

        if already_waiting:

            cursor.close()
            conn.close()

            flash("You are already in the waiting list.", "warning")

            return redirect(url_for("books"))

        # Add to database queue
        cursor.execute(
            """
            INSERT INTO waiting_queue
            (user_id, book_id)
            VALUES (%s, %s)
            """,
            (
                session["user_id"],
                book_id
            )
        )

        conn.commit()

        # DSA Queue
        waiting_queue.enqueue(session["user_id"])

        cursor.close()
        conn.close()

        flash(
            "Book unavailable. You have been added to the waiting queue.",
            "warning"
        )

        return redirect(url_for("books"))

    # Issue book

    issue_date = date.today()

    due_date = issue_date + timedelta(days=14)

    cursor.execute(
        """
        INSERT INTO issues
        (user_id, book_id, issue_date, due_date, status)
        VALUES (%s, %s, %s, %s, 'issued')
        """,
        (
            session["user_id"],
            book_id,
            issue_date,
            due_date
        )
    )

    cursor.execute(
        """
        UPDATE books
        SET available_copies = available_copies - 1
        WHERE id = %s
        """,
        (book_id,)
    )

    conn.commit()

    # Stack transaction
    history_stack.push(
        {
            "user_id": session["user_id"],
            "book_id": book_id,
            "action": "ISSUED",
            "date": str(issue_date)
        }
    )

    cursor.close()
    conn.close()

    flash(
        f"Book issued successfully. Due date: {due_date}",
        "success"
    )

    return redirect(url_for("dashboard"))


# =========================================================
# RETURN BOOK
# =========================================================

@app.route("/return_book/<int:issue_id>", methods=["GET", "POST"])
def return_book(issue_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            issues.*,
            books.title,
            books.author
        FROM issues
        JOIN books
        ON issues.book_id = books.id
        WHERE issues.id = %s
        """,
        (issue_id,)
    )

    issue = cursor.fetchone()

    if not issue:

        cursor.close()
        conn.close()

        flash("Issue record not found.", "danger")

        return redirect(url_for("dashboard"))

    # Student can return only own book
    if (
        session["role"] != "librarian"
        and issue["user_id"] != session["user_id"]
    ):

        cursor.close()
        conn.close()

        flash("You cannot return this book.", "danger")

        return redirect(url_for("dashboard"))

    if issue["status"] == "returned":

        cursor.close()
        conn.close()

        flash("Book already returned.", "warning")

        return redirect(url_for("dashboard"))

    # GET
    if request.method == "GET":

        cursor.close()
        conn.close()

        return render_template(
            "return.html",
            issue=issue
        )

    # POST

    return_date = date.today()

    # Calculate late days
    late_days = (
        return_date - issue["due_date"]
    ).days

    if late_days > 0:

        fine = late_days * 5

    else:

        fine = 0

    # Update issue
    cursor.execute(
        """
        UPDATE issues
        SET
            return_date = %s,
            fine = %s,
            status = 'returned'
        WHERE id = %s
        """,
        (
            return_date,
            fine,
            issue_id
        )
    )

    # Increase available copies
    cursor.execute(
        """
        UPDATE books
        SET available_copies = available_copies + 1
        WHERE id = %s
        """,
        (issue["book_id"],)
    )

    conn.commit()

    # Stack
    history_stack.push(
        {
            "user_id": issue["user_id"],
            "book_id": issue["book_id"],
            "action": "RETURNED",
            "date": str(return_date),
            "fine": fine
        }
    )

    # =====================================================
    # CHECK WAITING QUEUE
    # =====================================================

    cursor.execute(
        """
        SELECT
            waiting_queue.id,
            waiting_queue.user_id,
            users.name,
            users.email
        FROM waiting_queue
        JOIN users
        ON waiting_queue.user_id = users.id
        WHERE waiting_queue.book_id = %s
        AND waiting_queue.status = 'waiting'
        ORDER BY waiting_queue.request_date ASC
        LIMIT 1
        """,
        (issue["book_id"],)
    )

    next_user = cursor.fetchone()

    if next_user:

        # DSA Queue
        waiting_queue.enqueue(next_user["user_id"])

        # Mark queue request completed
        cursor.execute(
            """
            UPDATE waiting_queue
            SET status = 'completed'
            WHERE id = %s
            """,
            (next_user["id"],)
        )

        conn.commit()

        queue_message = (
            f" Next waiting user: {next_user['name']}. "
            "They can now issue the book."
        )

    else:

        queue_message = ""

    cursor.close()
    conn.close()

    flash(
        f"Book returned successfully. Fine: ₹{fine}.{queue_message}",
        "success"
    )

    return redirect(url_for("dashboard"))


# =========================================================
# MY BOOKS
# =========================================================

@app.route("/my_books")
def my_books():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            issues.*,
            books.title,
            books.author
        FROM issues
        JOIN books
        ON issues.book_id = books.id
        WHERE issues.user_id = %s
        ORDER BY issues.issue_date DESC
        """,
        (session["user_id"],)
    )

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        records=records
    )


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if session["role"] == "librarian":

        cursor.execute(
            """
            SELECT
                issues.*,
                users.name,
                users.email,
                books.title,
                books.author
            FROM issues
            JOIN users
            ON issues.user_id = users.id
            JOIN books
            ON issues.book_id = books.id
            ORDER BY issues.id DESC
            """
        )

    else:

        cursor.execute(
            """
            SELECT
                issues.*,
                users.name,
                users.email,
                books.title,
                books.author
            FROM issues
            JOIN users
            ON issues.user_id = users.id
            JOIN books
            ON issues.book_id = books.id
            WHERE issues.user_id = %s
            ORDER BY issues.id DESC
            """,
            (session["user_id"],)
        )

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        records=records
    )


# =========================================================
# WAITING QUEUE
# =========================================================

@app.route("/queue")
def queue_view():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if session["role"] == "librarian":

        cursor.execute(
            """
            SELECT
                waiting_queue.*,
                users.name,
                users.email,
                books.title
            FROM waiting_queue
            JOIN users
            ON waiting_queue.user_id = users.id
            JOIN books
            ON waiting_queue.book_id = books.id
            WHERE waiting_queue.status = 'waiting'
            ORDER BY waiting_queue.request_date ASC
            """
        )

    else:

        cursor.execute(
            """
            SELECT
                waiting_queue.*,
                users.name,
                users.email,
                books.title
            FROM waiting_queue
            JOIN users
            ON waiting_queue.user_id = users.id
            JOIN books
            ON waiting_queue.book_id = books.id
            WHERE waiting_queue.user_id = %s
            AND waiting_queue.status = 'waiting'
            ORDER BY waiting_queue.request_date ASC
            """,
            (session["user_id"],)
        )

    queue_records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        records=queue_records,
        queue_page=True
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )