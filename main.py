from flask import Flask, render_template, request, redirect, url_for
import collections.abc as collections

import pyrebase

app = Flask(__name__)

# Firebase configuration
config = {
	'apiKey': "AIzaSyDpYSJIBiqWWBZzcjby616zTU-k09Su4j0",
	'authDomain': "earth-rise-upuhbp.firebaseapp.com",
	'projectId': "earth-rise-upuhbp",
	'storageBucket': "earth-rise-upuhbp.appspot.com",
	'messagingSenderId': "824623462077",
	'appId': "1:824623462077:web:4859c2c4a689f1aa8229d4",
	'databaseURL': "https://earth-rise-upuhbp-default-rtdb.firebaseio.com/"
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()

# Define the email of the admin user
ADMIN_EMAIL = "sam.nusair@gmail.com"

# Routes
@app.route('/')
def index():
	# Check if user is authenticated
	return render_template("index.html")


############## AUTHENTIFICATION METHODS ##############

@app.context_processor
def inject_user():
	return dict(current_user=auth.current_user, ADMIN_EMAIL=ADMIN_EMAIL)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		try:
			# Authenticate user with email and password
			user = auth.sign_in_with_email_and_password(email, password)
			auth.current_user = user  # Set current_user
			# Check if the authenticated user is the admin
			if email == ADMIN_EMAIL:
				return redirect(url_for('admin_panel'))
			else:
				return redirect(url_for('index'))
		except pyrebase.pyrebase.HTTPError as e:
			# Handle HTTP errors, which may indicate invalid email, invalid password, or user not found
			error_message = str(e)
			return render_template("login.html", error=error_message)
		except Exception as e:
			# Handle other exceptions
			error_message = str(e)
			return render_template("login.html", error=error_message)
	# Render the login form
	return render_template("login.html", error=None)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		try:
			# Create user with email and password
			user = auth.create_user_with_email_and_password(email, password)
			# If signup succeeds, redirect to the index page
			return redirect(url_for('index'))
		except pyrebase.pyrebase.HTTPError as e:
			# Handle HTTP errors, which may indicate invalid email or weak password
			if "EMAIL_EXISTS" in str(e):
				error_message = "Email already in use"
				return render_template("signup.html", error=error_message)
			else:
				return render_template("signup.html", error="Invalid email or weak password")
		except Exception as e:
			# Handle other exceptions
			error_message = str(e)
			return render_template("signup.html", error=error_message)
	# Render the signup form
	return render_template("signup.html", error=None)

@app.route('/logout')
def logout():
	auth.current_user = None
	return redirect(url_for('index'))


############## THIS PART OF THE CODE IS THE ADMIN PANEL WHERE YOU CAN POST STUFF (UPDATES)

@app.route('/admin_panel')
def admin_panel():
	# Check if user is authenticated and is the admin
	user = auth.current_user
	if user is not None and user['email'] == ADMIN_EMAIL:
		updates_ref = db.child("updates")

		# Get all updates
		updates = updates_ref.get()

		# Prepare data for rendering in HTML
		updates_data = []
		if updates.each():
			for update in updates.each():
				if isinstance(update.val(), dict):
					title = update.val().get("title")
					content = update.val().get("content")
					if title is not None and content is not None:
						updates_data.append({"title": title, "content": content})

		return render_template("admin_panel.html", user_email=user['email'], updates=updates_data)
	else:
		return redirect(url_for('login'))

@app.route('/create_post', methods=['POST'])
def create_post():
	# Check if user is authenticated and is the admin
	user = auth.current_user
	if user is not None and user['email'] == ADMIN_EMAIL:
		# Get title and content from the form
		title = request.form['title']
		content = request.form['content']
		# Save the post to the Firebase "updates" collection
		db.child("updates").push({"title": title, "content": content})
		print(f"Post created: {title} + {content}")
		# Redirect to the admin panel after creating the post
		return redirect(url_for('admin_panel'))
	else:
		return redirect(url_for('login'))

@app.route('/updates')
def updates():
	user = auth.current_user
	if user is not None:
		updates_ref = db.child("updates")

		# Get all updates
		updates = updates_ref.get()

		# Prepare data for rendering in HTML
		updates_data = []
		if updates.each():
			for update in updates.each():
				if isinstance(update.val(), dict):
					title = update.val().get("title")
					content = update.val().get("content")
					if title is not None and content is not None:
						updates_data.append({"title": title, "content": content})

		return render_template("community.html", updates=updates_data)
	else:
		return redirect(url_for('login'))


################################ PROFILE PAGE #########################################

@app.route('/profile')
def profile():
	user = auth.current_user
	if user is not None:
		return render_template("profile.html", user_email=user['email'])
	else:
		return redirect(url_for('login'))

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
	user = auth.current_user
	if user is not None:
		if 'profile_picture' in request.files:
			profile_picture = request.files['profile_picture']
			# Handle profile picture upload, you can store it in Firebase Storage or any other preferred storage
			# Example: storage.child("profile_pictures").child(user['uid']).put(profile_picture)
			return redirect(url_for('profile'))
		else:
			return "No profile picture uploaded"
	else:
		return redirect(url_for('login'))


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)