
from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.secret_key = "careerpath-ai-secret-key"


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = sqlite3.connect("database/careerpath.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    # PROFILE COLUMNS
    profile_columns = [
        ("education", "TEXT"),
        ("college", "TEXT"),
        ("year", "TEXT"),
        ("career", "TEXT"),
        ("about", "TEXT")
    ]

    for column, data_type in profile_columns:

        try:

            cursor.execute(
                f"ALTER TABLE users ADD COLUMN {column} {data_type}"
            )

        except sqlite3.OperationalError:

            pass


    # ASSESSMENTS TABLE
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            career TEXT,
            score INTEGER,
            skills TEXT
        )
        """
    )


    # PROGRESS TABLE
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            skill TEXT,
            progress INTEGER
        )
        """
    )


    conn.commit()
    conn.close()


# CREATE DATABASE
init_db()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]


        conn = sqlite3.connect("database/careerpath.db")
        cursor = conn.cursor()


        try:

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")


        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered."


    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]


        conn = sqlite3.connect("database/careerpath.db")
        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        )


        user = cursor.fetchone()

        conn.close()


        if user:

            session["user_email"] = email

            return redirect("/dashboard")


        return "Invalid email or password."


    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_email" not in session:

        return redirect("/login")


    user_email = session["user_email"]


    conn = sqlite3.connect("database/careerpath.db")
    cursor = conn.cursor()


    # USER NAME

    cursor.execute(
        """
        SELECT name
        FROM users
        WHERE email = ?
        """,
        (user_email,)
    )


    user = cursor.fetchone()


    # LATEST ASSESSMENT

    cursor.execute(
        """
        SELECT career, score, skills
        FROM assessments
        WHERE user_email = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_email,)
    )


    result = cursor.fetchone()


    # PROGRESS

    cursor.execute(
        """
        SELECT skill, progress
        FROM progress
        WHERE user_email = ?
        """,
        (user_email,)
    )


    progress_data = cursor.fetchall()


    conn.close()


    # DEFAULT VALUES

    if result:

        career = result[0]
        score = result[1]

        skills = [
            x.strip()
            for x in result[2].split(",")
        ]

    else:

        career = "Not Available"
        score = 0
        skills = [
            "Complete assessment first"
        ]


    # PROGRESS DICTIONARY

    progress = {}


    for skill, value in progress_data:

        progress[skill] = value


    # ROADMAP

    roadmap = [

        "Learn the required basic skills",

        "Practice with small projects",

        "Build real-world projects",

        "Prepare your resume and apply for opportunities"

    ]


    return render_template(
        "dashboard.html",
        name=user[0] if user else "Student",
        career=career,
        score=score,
        skills=skills,
        roadmap=roadmap,
        progress=progress
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_email" not in session:

        return redirect("/login")


    user_email = session["user_email"]


    conn = sqlite3.connect("database/careerpath.db")
    cursor = conn.cursor()


    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        education = request.form["education"]
        college = request.form["college"]
        year = request.form["year"]
        career = request.form["career"]
        about = request.form["about"]


        try:

            cursor.execute(
                """
                UPDATE users
                SET name = ?,
                    email = ?,
                    education = ?,
                    college = ?,
                    year = ?,
                    career = ?,
                    about = ?
                WHERE email = ?
                """,
                (
                    name,
                    email,
                    education,
                    college,
                    year,
                    career,
                    about,
                    user_email
                )
            )


            conn.commit()


            # UPDATE SESSION EMAIL

            session["user_email"] = email

            user_email = email


        except sqlite3.IntegrityError:

            conn.close()

            return "This email is already registered."


    # GET USER DATA

    cursor.execute(
        """
        SELECT
            name,
            email,
            education,
            college,
            year,
            career,
            about
        FROM users
        WHERE email = ?
        """,
        (user_email,)
    )


    user = cursor.fetchone()


    conn.close()


    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# RESUME BUILDER
# =========================================================

@app.route("/resume")
def resume():

    if "user_email" not in session:

        return redirect("/login")


    user_email = session["user_email"]


    conn = sqlite3.connect("database/careerpath.db")
    cursor = conn.cursor()


    # USER PROFILE

    cursor.execute(
        """
        SELECT
            name,
            email,
            education,
            college,
            year,
            career,
            about
        FROM users
        WHERE email = ?
        """,
        (user_email,)
    )


    user = cursor.fetchone()


    # LATEST ASSESSMENT SKILLS

    cursor.execute(
        """
        SELECT skills
        FROM assessments
        WHERE user_email = ?
        ORDER BY id DESC
        LIMIT 1
        """
        ,
        (user_email,)
    )


    assessment = cursor.fetchone()


    conn.close()


    # DEFAULT SKILLS

    skills = ""


    if assessment:

        skills = assessment[0]


    return render_template(
        "resume.html",
        user=user,
        skills=skills
    )


# =========================================================
# UPDATE PROGRESS
# =========================================================

@app.route("/update-progress", methods=["POST"])
def update_progress():

    if "user_email" not in session:

        return redirect("/login")


    user_email = session["user_email"]

    skill = request.form["skill"]

    progress = int(
        request.form["progress"]
    )


    # LIMIT PROGRESS

    if progress < 0:

        progress = 0


    if progress > 100:

        progress = 100


    conn = sqlite3.connect("database/careerpath.db")
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE progress
        SET progress = ?
        WHERE user_email = ?
        AND skill = ?
        """,
        (
            progress,
            user_email,
            skill
        )
    )


    conn.commit()
    conn.close()


    return redirect("/dashboard")


# =========================================================
# CAREER ASSESSMENT
# =========================================================

@app.route("/assessment", methods=["GET", "POST"])
def assessment():

    if "user_email" not in session:

        return redirect("/login")


    if request.method == "POST":

        interest = request.form.get("interest")

        coding = request.form.get("coding")

        problem_solving = request.form.get(
            "problem_solving"
        )

        work = request.form.get("work")

        goal = request.form.get("goal")


        score = 0


        # =================================================
        # CAREER RECOMMENDATION
        # =================================================

        if goal == "developer":

            career = "Software Developer"

            skills = (
                "Python, JavaScript, HTML, CSS"
            )


        elif goal == "designer":

            career = "UI/UX Designer"

            skills = (
                "UI Design, Figma, UX Research"
            )


        elif goal == "data":

            career = "Data Analyst"

            skills = (
                "Python, SQL, Excel, Data Visualization"
            )


        else:

            career = "Business Analyst"

            skills = (
                "Business Analysis, Communication, Excel"
            )


        # =================================================
        # SCORE CALCULATION
        # =================================================

        if coding == "advanced":

            score += 25

        elif coding == "intermediate":

            score += 20

        elif coding == "beginner":

            score += 10


        if problem_solving == "high":

            score += 25

        elif problem_solving == "medium":

            score += 15


        if interest in ["coding", "data"]:

            score += 20

        else:

            score += 15


        if work in ["technical", "analytical"]:

            score += 15

        else:

            score += 10


        if goal:

            score += 15


        if score > 100:

            score = 100


        user_email = session["user_email"]


        conn = sqlite3.connect("database/careerpath.db")
        cursor = conn.cursor()


        # =================================================
        # SAVE ASSESSMENT
        # =================================================

        cursor.execute(
            """
            INSERT INTO assessments
            (
                user_email,
                career,
                score,
                skills
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_email,
                career,
                score,
                skills
            )
        )


        # =================================================
        # DEFAULT PROGRESS
        # =================================================

        skill_list = [
            x.strip()
            for x in skills.split(",")
        ]


        for skill in skill_list:

            cursor.execute(
                """
                INSERT OR IGNORE INTO progress
                (
                    user_email,
                    skill,
                    progress
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_email,
                    skill,
                    0
                )
            )


        conn.commit()
        conn.close()


        return render_template(
            "result.html",
            career=career,
            score=score,
            skills=skill_list
        )


    return render_template(
        "assessment.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.pop(
        "user_email",
        None
    )

    return redirect("/login")


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]


        if (
            email == "admin@gmail.com"
            and password == "admin123"
        ):

            session["admin_logged_in"] = True

            return redirect("/admin")


        return "Invalid admin email or password."


    return render_template(
        "admin-login.html"
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):

        return redirect("/admin-login")


    conn = sqlite3.connect("database/careerpath.db")
    cursor = conn.cursor()


    # TOTAL STUDENTS

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        """
    )

    total_students = cursor.fetchone()[0]


    # TOTAL ASSESSMENTS

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM assessments
        """
    )

    total_assessments = cursor.fetchone()[0]


    # CAREER RESULTS

    cursor.execute(
        """
        SELECT career, COUNT(*)
        FROM assessments
        GROUP BY career
        """
    )

    career_results = cursor.fetchall()


    # REGISTERED STUDENTS

    cursor.execute(
        """
        SELECT
            users.name,
            users.email,
            assessments.career,
            assessments.score
        FROM users
        LEFT JOIN assessments
        ON users.email = assessments.user_email
        AND assessments.id = (
            SELECT MAX(a2.id)
            FROM assessments a2
            WHERE a2.user_email = users.email
        )
        ORDER BY users.id DESC
        """
    )


    students = cursor.fetchall()


    # STUDENT PROGRESS

    cursor.execute(
        """
        SELECT
            user_email,
            skill,
            progress
        FROM progress
        ORDER BY user_email
        """
    )


    progress_data = cursor.fetchall()


    conn.close()


    return render_template(
        "admin.html",
        total_students=total_students,
        total_assessments=total_assessments,
        career_results=career_results,
        students=students,
        progress_data=progress_data
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin-logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect("/admin-login")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
