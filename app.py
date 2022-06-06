from os import path
from flask import Flask, render_template, request, redirect
import keras
import numpy as np
import cv2
import requests
from predict import *
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from dominate.tags import img
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from dominate.tags import img
from firebase import firebase
from flask import request, json


import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(
    "find-vehicle-b28b0-firebase-adminsdk-b4nyw-11bbbde5c9.json")
firebase_admin.initialize_app(cred)


db = firestore.client()

logo = img(src='static/logo.jpeg', height="50",
           width="50", style="margin-top:-15px")
topbar = Navbar(logo,
                View('Find', 'find'),
                View('Register', 'submit'),

                )

# registers the "top" menubar
nav = Nav()
nav.register_element('top', topbar)

app = Flask(__name__)
Bootstrap(app)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    return(render_template('index.html'))


# find num plate

@app.route('/find', methods=["GET", "POST"])
def find():
    transcript = ""
    if request.method == "POST":
        print("FORM DATA RECEIVED")

        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)
        print(file.filename)
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save('images/'+filename)
            image_np = cv2.imread('images/'+filename, 1)

            path = 'plate_char_recognition.h5'
            loaded_model = keras.models.load_model(path)

            plate_img, plate = extract_plate(image_np)
            char = segment_characters(plate)
            plate_number = show_results(char, loaded_model)

            num = plate_number.upper()

            data = db.collection('vehicles').document(num).get().to_dict()

            if(data == None):
                data = db.collection('vehicleinfo').document(
                    num).get().to_dict()
                transcript = data
                return render_template('result.html', transcript=transcript)
            else:
                # get location
                # url = 'http://freegeoip.net/json/{}'.format(
                #    request.remote_addr)
                #r = requests.get(url)
                #j = json.loads(r.text)
                #city = j['city']
                # db.collection('vehicles').document(num).update(
                #    {"lastseen": ''})
                transcript = data
                return render_template('find.html', transcript=transcript)

    return render_template('find.html', transcript=transcript)


@app.route('/register', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST' and len(dict(request.form)) > 0:
        userdata = dict(request.form)
        name = userdata["name"]
        vnumber = userdata["number"]
        lostloc = userdata["lostseen"]
        address = userdata["ownaddr"]
        contact = userdata["contact"]
        new_data = {"name": name, "vnumber": vnumber, "lostloc": lostloc, "lastseen": lostloc,
                    "owneraddress": address, "contact": contact}
        db.collection('vehicles').document(vnumber).set(new_data)

    return(render_template('register.html', status="successfully registered"))


nav.init_app(app)


if __name__ == '__main__':
    app.run(debug=True)
