from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import random
import itertools

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database setup
def create_table():
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, score INTEGER)''')
    conn.commit()
    conn.close()

create_table()

# Helper functions
def register_user(username, password):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, score) VALUES (?, ?, ?)", (username, password, 0))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_login(username, password):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def update_score(username, score):
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("UPDATE users SET score = ? WHERE username = ?", (score, username))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect("game.db")
    c = conn.cursor()
    c.execute("SELECT username, score FROM users ORDER BY score DESC LIMIT 10")
    leaderboard = c.fetchall()
    conn.close()
    return leaderboard

# Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register2", methods=["GET", "POST"])
def register2():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if register_user(username, password):
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login2"))
        else:
            flash("Username already exists!", "danger")
    return render_template("register2.html")

@app.route("/login2", methods=["GET", "POST"])
def login2():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = check_login(username, password)
        if user:
            session["user"] = user[0]
            session["score"] = user[2]
            flash("Login successful!", "success")
            return redirect(url_for("game"))
        else:
            flash("Invalid username or password!", "danger")
    return render_template("login2.html")

@app.route("/game", methods=["GET", "POST"])
def game():
    if "user" not in session:
        return redirect(url_for("login2"))

    # Initialize guess history if not present
    if "guess_history" not in session:
        session["guess_history"] = []

    if request.method == "POST":
        # Collect individual digit values from the form
        guess = ''.join([request.form.get(f'guess{i}') for i in range(1, 7)])

        if not guess or len(set(guess)) != len(guess) or len(guess) != 6 or not guess.isdigit():
            flash("Invalid guess. Please enter 6 unique digits.", "warning")
        else:
            target = session.get("target", random.sample(range(10), 6))
            session["target"] = target
            correct_position = sum(1 for i in range(6) if int(guess[i]) == target[i])
            correct_numbers = sum(1 for d in map(int, guess) if d in target) - correct_position

            # Add the guess and result to the history
            session["guess_history"].insert(0, {
                "value": guess,
                "correct_numbers": correct_numbers,
                "correct_positions": correct_position
            })
            
            # Limit the history to the last 10 guesses
            if len(session["guess_history"]) > 10:
                session["guess_history"].pop()

            if correct_position == 6:
                session["score"] += 1000000
                update_score(session["user"], session["score"])
                flash(f"Congratulations! You've guessed correctly: {''.join(map(str, target))}.", "success")
                session["target"] = random.sample(range(10), 6)  # Reset target
            else:
                flash(f"Guess: {guess}. Correct Numbers: {correct_numbers}. Correct Positions: {correct_position}.", "info")

    return render_template("game.html", score=session.get("score", 0), guess_history=session["guess_history"])


@app.route("/leaderboard")
def leaderboard():
    leaders = get_leaderboard()
    return render_template("leaderboard.html", leaderboard=leaders, enumerate=enumerate)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
