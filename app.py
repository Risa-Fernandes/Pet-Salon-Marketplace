import os
import re
import secrets
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from flask import session
from flask import Flask, request, jsonify, render_template, json, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from auth import hash_password, verify_password, create_token, get_current_user
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime, timedelta
from datetime import datetime
from twilio.rest import Client
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)  # IMPORTANT for frontend-backend connection

# =============================================================================
# Database configuration
# =============================================================================
app.config["SECRET_KEY"] = "pawfectcare_ai_pet_marketplace_secure_2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///salon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "pawfect_secret"


db = SQLAlchemy(app)
TWILIO_ACCOUNT_SID = "Twilio Acount"
TWILIO_AUTH_TOKEN = "Twilio Token"
TWILIO_PHONE = "Twilio Account Phone number"

sms_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)




# ==============================
# MAIL CONFIGURATION
# ==============================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yourgmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

mail = Mail(app)



class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('Pet_Owner','Doctor','Salon_Owner'), nullable=False)
    
    is_admin = db.Column(db.Boolean, default=False)

    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    doctor_profile = db.relationship("Doctor", backref="user", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email":self.email,
            "role":self.role
        }
    
    #==============Salon Models==================

class Salon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100))
    open_hours = db.Column(db.String(50))
    close_hours= db.Column(db.String(50))
    tagline = db.Column(db.String(200))
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    image = db.Column(db.String(200))
    rating = db.Column(db.Float, default=0)
     
        # ADD THIS
    appointments = db.relationship(
        "SalonAppointment",
        backref="salon",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "open_hours":self.open_hours,
            "close_hours":self.close_hours,
            "tagline": self.tagline,
            "description": self.description,
            "address": self.address,
            "city": self.city,
            "phone": self.phone,
            "image": self.image
        }


    
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, db.ForeignKey('salon.id'), nullable=False)
    service_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    duration = db.Column(db.Integer)

    
    def to_dict(self):# Convert model to dictionary for JSON response
        return {
            "id": self.id,
            "service_name": self.service_name,
            "price": self.price,
            "duration": self.duration
        }

from datetime import datetime
class SalonAppointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
        # CHANGE THIS
    salon_id = db.Column(
        db.Integer,
        db.ForeignKey('salon.id', ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
    db.Integer,
    db.ForeignKey('users.id'),
    nullable=False
    )
    owner_name = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    pet_name = db.Column(db.String(100))
    pet_category = db.Column(db.String(50))
    service_name = db.Column(db.String(100))
    appointment_date = db.Column(db.String(20))
    appointment_time = db.Column(db.String(20))
    notes = db.Column(db.Text)
    status = db.Column( db.String(20), default="CONFIRMED")
    created_at = db.Column( db.DateTime,default=datetime.utcnow)


    def to_dict(self):
        return {
            "id": self.id,
            "salon_id": self.salon_id,
            "owner_name": self.owner_name,
            "mobile": self.mobile,
            "pet_name": self.pet_name,
            "pet_category": self.pet_category,
            "service_name": self.service_name,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "notes": self.notes,
            "status": self.status
        }

#==============markiplace==============
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.String(20))
    price = db.Column(db.Float)
    desc = db.Column(db.Text)
    contact = db.Column(db.String(20))
    img = db.Column(db.String(200))
    category = db.Column(db.String(20))  # 'cat' or 'dog'
    is_sold = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "breed": self.breed,
            "age": self.age,
            "price": f"₹{self.price}" if self.price else "",
            "desc": self.desc,
            "contact": self.contact,
            "img": f"uploads/{self.img}" if self.img else "",
            "category": self.category
        }


from datetime import datetime




class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))

    specialization = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)

    clinic_name = db.Column(db.String(150))
    consultation_fee = db.Column(db.Float)

    city = db.Column(db.String(100))
    bio = db.Column(db.Text)

    profile_pic = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship('DoctorAppointment', backref='doctor', lazy=True)
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "specialization": self.specialization,
            "experience_years": self.experience_years,
            "clinic_name": self.clinic_name,
            "consultation_fee": self.consultation_fee,
            "city": self.city,
            "bio": self.bio,
            "profile_pic": self.profile_pic,
            "created_at": self.created_at
        }
    
class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))

    day_of_week = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    slot_duration_minutes = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "slot_duration_minutes": self.slot_duration_minutes,
            "is_active": self.is_active
        }
    


class Purchase(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'))

    buyer_name = db.Column(db.String(100))

    buyer_phone = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):

        return {
            "id": self.id,
            "pet_id": self.pet_id,
            "buyer_name": self.buyer_name,
            "buyer_phone": self.buyer_phone,
            "created_at": self.created_at
        }
    


class DoctorAppointment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    user_id = db.Column(db.Integer)

    # OWNER DETAILS
    owner_name = db.Column(db.String(100))
    owner_phone = db.Column(db.String(20))

    # PET DETAILS
    pet_name = db.Column(db.String(100))
    pet_type = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    pet_age = db.Column(db.String(50))

    # APPOINTMENT
    appointment_date = db.Column(db.String(20))
    appointment_time = db.Column(db.String(20))

    # MEDICAL
    symptoms = db.Column(db.Text)
    concern = db.Column(db.Text)
    status = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):

        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "user_id": self.user_id,

            "owner_name": self.owner_name,
            "owner_phone": self.owner_phone,

            "pet_name": self.pet_name,
            "pet_type": self.pet_type,
            "gender": self.gender,
            "pet_age": self.pet_age,

            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,

            "symptoms": self.symptoms,
            "concern": self.concern,

            "status": self.status,
            "created_at": self.created_at
        }
    

class PatientRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer)
    doctor_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    pet_id = db.Column(db.Integer)
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "appointment_id": self.appointment_id,
            "doctor_id": self.doctor_id,
            "user_id": self.user_id,
            "pet_id": self.pet_id,
            "symptoms": self.symptoms,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "created_at": self.created_at
        }
doctors_data = [
    {
        "id": 1,
        "full_name": "Dr. Anjali Sharma",
        "specialization": "Veterinary Surgeon",
        "experience_years": 8,
        "clinic_name": "Happy Paws Clinic",
        "city": "Mumbai",
        "consultation_fee": 700,
        "image": "doctor1.jpg"
    },
    {
        "id": 2,
        "full_name": "Dr. Rahul Mehta",
        "specialization": "Pet Dentist",
        "experience_years": 5,
        "clinic_name": "PetCare Dental",
        "city": "Pune",
        "consultation_fee": 500,
        "image": "doctor2.jpg"
    },
    {
        "id": 3,
        "full_name": "Dr. Sneha Kapoor",
        "specialization": "Animal Dermatologist",
        "experience_years": 6,
        "clinic_name": "SkinCare Pets",
        "city": "Delhi",
        "consultation_fee": 600,
        "image": "doctor3.jpg"
    },
    {
        "id": 4,
        "full_name": "Dr. Arjun Patel",
        "specialization": "Pet Nutritionist",
        "experience_years": 7,
        "clinic_name": "Healthy Pets Clinic",
        "city": "Ahmedabad",
        "consultation_fee": 650,
        "image": "doctor4.jpg"
    },
    {
        "id": 5,
        "full_name": "Dr. Priya Nair",
        "specialization": "Veterinary Physician",
        "experience_years": 10,
        "clinic_name": "Pet Wellness Center",
        "city": "Bangalore",
        "consultation_fee": 800,
        "image": "doctor5.jpg"
    }
]
# =============================================================================
# REST API ROUTES
# =============================================================================
import re
from flask import request, jsonify
from werkzeug.security import generate_password_hash

@app.route('/api/register', methods=['POST'])
def api_register():

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    # REQUIRED FIELDS
    if not username or not email or not password or not role:
        return jsonify({'error': 'All fields required'}), 400

    # EMAIL VALIDATION
    if not is_valid_email(email):
        return jsonify({
            'error': 'Invalid email format'
        }), 400

    # PASSWORD VALIDATION
    if not is_strong_password(password):
        return jsonify({
            'error':
            'Password must contain uppercase, lowercase, number and special character'
        }), 400

    

    # CHECK EMAIL EXISTS
    if User.query.filter_by(email=email).first():

        return jsonify({
            'error': 'Email already registered'
        }), 400

    new_user = User(

        username=username,

        email=email,

        password_hash=hash_password(password),

        role=role
    )

    db.session.add(new_user)

    db.session.commit()

    return jsonify({
        'message': 'Registration successful!'
    }), 201






@app.route('/api/login', methods=['POST'])
def api_login():

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    # CHECK USER
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            'error': 'Invalid email'
        }), 401

    # PASSWORD CHECK
    if not verify_password(user.password_hash, password):

        return jsonify({
            'error': 'Invalid password'
        }), 401

    # ROLE CHECK
    if user.role != role:

        return jsonify({
            'error':
            f'This account is registered as {user.role}'
        }), 401

    token = create_token(user.id, user.is_admin)

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    # Doctor profile
    if user.role == "Doctor":

        doctor = Doctor.query.filter_by(
            user_id=user.id
        ).first()

        if doctor:
            session["doctor_id"] = doctor.id

    return jsonify({

        'token': token,

        'user': {

            'id': user.id,

            'username': user.username,

            'email': user.email,

            'role': user.role,

            'is_admin': user.is_admin
        }

    }), 200

# ===================================
# FORGOT PASSWORD
# ===================================

@app.route('/forgot_password')
def forgot_password():

    return render_template(
        'doctor/forgot_password.html'
    )




@app.route('/api/forgot_password', methods=['POST'])
def forgot_password_api():

    data = request.get_json()

    email = data.get("email")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "message": "Email not registered"
        }), 404

    # Generate token
    token = secrets.token_urlsafe(32)

    # Save token
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)

    db.session.commit()

    # Create reset link
    reset_link = f"http://127.0.0.1:5000/reset_password/{token}"

    print("\n========== PASSWORD RESET LINK ==========")
    print(reset_link)
    print("=========================================\n")

    # Return link directly
    return jsonify({
        "message": "Password reset link generated",
        "reset_link": reset_link
    })




@app.route('/reset_password/<token>')
def reset_password_page(token):

    return render_template(
        'doctor/reset_password.html',
        token=token
    )






@app.route('/api/reset-password/<token>', methods=['POST'])
def reset_password(token):

    data = request.get_json()

    new_password = data.get('password')

    user = User.query.filter_by(
        reset_token=token
    ).first()

    if not user:

        return jsonify({
            'error': 'Invalid token'
        }), 400

    if datetime.utcnow() > user.reset_token_expiry:

        return jsonify({
            'error': 'Token expired'
        }), 400

    if not is_strong_password(new_password):

        return jsonify({
            'error':
            'Weak password'
        }), 400

    user.password_hash = hash_password(new_password)

    user.reset_token = None
    user.reset_token_expiry = None

    db.session.commit()

    return jsonify({
        'message': 'Password reset successful'
    }), 200


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    # Clear all session data
    session.clear()

    # Redirect to login page
    return redirect("/login")




# ==============================
# EMAIL VALIDATION
# ==============================

def is_valid_email(email):

    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    return re.match(pattern, email)



# ==============================
# PASSWORD VALIDATION
# ==============================

def is_strong_password(password):

    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"[0-9]", password):
        return False

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False

    return True






# =============================================================================
# FRONTEND ROUTES
# =============================================================================
@app.route("/")
def home():
    return render_template("register.html")

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/sales')
def marketplace():
    return render_template('sales.html')

@app.route('/index')
def index_page():
    return render_template("user/index.html")


@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route("/salon")
def salon():
    print("SEARCH PAGE LOADED")
    return render_template("user/salon.html")

@app.route("/user_doctor")
def user_doctor():
    print("SEARCH PAGE LOADED")
    return render_template("user/doctor.html")

@app.route("/salondetail")
def detilssalon():

    id = int(request.args.get('id'))

    salon = Salon.query.get_or_404(id)

    services = Service.query.filter_by(
        salon_id=id
    ).all()

    reviews = SalonReview.query.filter_by(
        salon_id=id
    ).order_by(
        SalonReview.id.desc()
    ).all()

    # Calculate average rating
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
    else:
        avg_rating = 0

    return render_template(
        'user/salondetail.html',
        salon=salon,
        services=services,
        reviews=reviews,
        avg_rating=avg_rating
    )

@app.route("/salon/dashbord")
def dashbord():
    return render_template("salon/adminviewsalon.html")

@app.route("/search")
def search():
    print("SEARCH PAGE LOADED")
    return render_template("salon/search.html")


@app.route("/about")
def about():
    return render_template("user/about.html")

@app.route("/manage-salon")
def manage_salon():
    return render_template("salon/manage-salon.html")

@app.route("/adminviewsalon")
def admin_view_salon():
    return render_template("salon/adminviewsalon.html")

@app.route("/editsalon")
def edit_salon():
    return render_template("salon/edit-salon.html")

from datetime import datetime,  timedelta
today = datetime.today().strftime('%Y-%m-%d')
max_date = (datetime.today() + timedelta(days=2)).strftime('%Y-%m-%d')
@app.route("/salon-detail")
def detils_salon():
    id = int(request.args.get('id'))

    salon = Salon.query.get_or_404(id)
    services = Service.query.filter_by(salon_id=id).all()
    reviews = SalonReview.query.filter_by(salon_id=id).order_by(SalonReview.id.desc()).all()

    # ⭐ calculate average rating + count
    rating_data = db.session.query(
        db.func.avg(SalonReview.rating),
        db.func.count(SalonReview.id)
    ).filter(SalonReview.salon_id == id).first()

    avg_rating = rating_data[0] if rating_data[0] else 0
    total_reviews = rating_data[1] if rating_data[1] else 0

    # 🕒 time ago logic
    for r in reviews:
        diff = datetime.utcnow() - r.created_at

        if diff.days == 0:
            r.time_ago = "Today"
        elif diff.days == 1:
            r.time_ago = "1 day ago"
        else:
            r.time_ago = f"{diff.days} days ago"

    return render_template(
        'salon/salon-detail.html',
        salon=salon,
        services=services,
        reviews=reviews,
        avg_rating=avg_rating,
        total_reviews=total_reviews,
        today=today,
        max_date=max_date
    )


@app.route("/doctor_home")
def doctor_home():

    doctor_id = session.get("doctor_id")

    return render_template(
        "doctor/doctor_home.html",
        current_doctor_id=doctor_id
    )


@app.route('/api/current-doctor')
def current_doctor():

    doctor_id = session.get('doctor_id')

    if not doctor_id:
        return jsonify({})

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({})

    return jsonify({
        "id": doctor.id,
        "name": doctor.name,
        "specialization": doctor.specialization
    })



@app.route("/add-doctor")
def add_doctor_profile():
    return render_template("doctor/add_doctor.html")

@app.route("/doctors")
def doctor_list():
    doctors = Doctor.query.all()
    return render_template("doctor/doctor_home.html", doctors=doctors)




@app.route("/edit-doctor/<int:doctor_id>")
def edit_doctor_profile(doctor_id):


    # User must be logged in
    if "doctor_id" not in session:
        return redirect("/login")

    # Logged in doctor id
    logged_in_doctor_id = session["doctor_id"]

    # Prevent editing others
    if logged_in_doctor_id != doctor_id:
        return "Unauthorized Access", 403
    

    doctor = Doctor.query.get_or_404(doctor_id)

    availability = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()

    days = []
    start_time = ""
    end_time = ""

    if availability:
        days = [a.day_of_week for a in availability]
        start_time = availability[0].start_time
        end_time = availability[0].end_time

    return render_template(
        "doctor/edit_doctor.html",
        doctor=doctor,
        days=days,
        start_time=start_time,
        end_time=end_time
    )



from datetime import datetime, timedelta


@app.route("/ai-health")
def ai_health():
    return render_template("user/ai_health.html")


# =====================================================
# AI Health
# =====================================================

@app.route("/api/ai-health", methods=["POST"])
def ai_health_api():

    data = request.get_json()

    symptoms = data.get("symptoms", "").lower().strip()

    response = "Please consult a veterinarian."

    # Emergency Cases

    if "bleeding" in symptoms:
        response = "⚠ Emergency: Your dog may have a serious injury. Apply gentle pressure to stop bleeding and visit a vet immediately."

    elif "seizure" in symptoms:
        response = "⚠ Emergency: Keep your pet safe from sharp objects and contact a veterinarian immediately."

    elif "fainted" in symptoms:
        response = "⚠ Your cat may be suffering from shock, poisoning, or illness. Seek emergency veterinary care."

    elif "ate chocolate" in symptoms:
        response = "⚠ Chocolate is toxic for dogs and cats. Visit a veterinary clinic immediately."

    elif "swallowed plastic" in symptoms:
        response = "⚠ Plastic may block digestion. Monitor your dog and contact a veterinarian quickly."

    # General Disease Detection

    elif "vomit" in symptoms:
        response = "Your pet may have stomach infection or food poisoning. Keep your pet hydrated."

    elif "itch" in symptoms or "scratching" in symptoms:
        response = "Possible skin allergy or flea infection detected."

    elif "cough" in symptoms:
        response = "Possible respiratory infection detected."

    elif "fever" in symptoms:
        response = "Your pet may have viral or bacterial infection."

    elif "diarrhea" in symptoms:
        response = "Digestive disorder detected."

    elif "weak" in symptoms:
        response = "Weakness may indicate illness or low nutrition."

    # General Health Questions

    elif "food is best for puppies" in symptoms:
        response = "Puppies need high-protein food with balanced nutrition. Consult your vet for breed-specific diets."

    elif "vaccinate my dog" in symptoms:
        response = "Dogs should receive vaccinations regularly, especially during puppy stages and yearly booster doses."

    elif "healthy in summer" in symptoms:
        response = "Provide plenty of water, avoid direct heat, and keep pets in cool shaded areas during summer."

    elif "signs of infection" in symptoms:
        response = "Common signs include fever, weakness, vomiting, coughing, diarrhea, and loss of appetite."

    elif "water should a dog drink" in symptoms:
        response = "A healthy dog generally drinks about 50–60 ml of water per kilogram of body weight daily."

    return jsonify({
        "response": response
    })

# ==========================================
# APPOINTMENT MODULE ROUTES (app.py)
# ==========================================

from flask import render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta


# =====================================================
# 1. OPEN DOCTOR DETAILS PAGE
# =====================================================
@app.route("/doctor-detail/<int:doctor_id>")
def doctor_detail(doctor_id):

    doctor = Doctor.query.get_or_404(doctor_id)

    availability = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id
    ).all()

    return render_template(
        "doctor/view_doctor_details.html",
        doctor=doctor,
        availability=availability
    )


@app.route("/doctordetail/<int:doctor_id>")
def doctordetail(doctor_id):

    doctor = Doctor.query.get_or_404(doctor_id)

    availability = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id
    ).all()

    return render_template(
        "user/doctor_view.html",
        doctor=doctor,
        availability=availability
    )
# =====================================================
# 2. OPEN BOOK APPOINTMENT PAGE
# =====================================================
@app.route("/book-appointment/<int:doctor_id>")
def book_appointment_page(doctor_id):

    if "user_id" not in session:
        return redirect("/login")

    doctor = Doctor.query.get_or_404(doctor_id)

    return render_template("doctor/book_appointment.html", doctor=doctor)


# =====================================================
# 4. DOCTOR DASHBOARD PAGE
# =====================================================
@app.route("/doctor-requests")
def doctor_requests_page():

    if "doctor_id" not in session:
        return redirect("/login")

    return render_template("doctor/doctor_requests.html")


# =====================================================
# 5. GET AVAILABLE SLOTS
# =====================================================
@app.route("/api/doctors/<int:doctor_id>/slots")
def get_slots(doctor_id):

    date = request.args.get("date")

    if not date:
        return jsonify([])

    date_obj = datetime.strptime(date, "%Y-%m-%d")

    day = date_obj.strftime("%a")   # Mon Tue Wed

    availability = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=day
    ).first()

    if not availability:
        return jsonify([])

    start = datetime.strptime(availability.start_time, "%H:%M")
    end = datetime.strptime(availability.end_time, "%H:%M")

    duration = availability.slot_duration_minutes

    slots = []

    current = start

    while current < end:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration)

    booked = DoctorAppointment.query.filter(
        DoctorAppointment.doctor_id == doctor_id,
        DoctorAppointment.appointment_date == date,
        DoctorAppointment.status != "rejected"
    ).all()

    booked_times = [a.appointment_time for a in booked]

    available_slots = []

    for s in slots:
        if s not in booked_times:
            available_slots.append(s)

    return jsonify(available_slots)


# =====================================================
# 6. CREATE APPOINTMENT
# =====================================================
@app.route("/api/appointments", methods=["POST"])
def create_appointment():

    if "user_id" not in session:
        return jsonify({"message": "Login required"}), 401

    user_id = session["user_id"]

    doctor_id = request.form.get("doctor_id")
    appointment_date = request.form.get("appointment_date")
    appointment_time = request.form.get("appointment_time")

    # ==========================================
    # CHECK IF SLOT ALREADY BOOKED
    # ==========================================

    existing = DoctorAppointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time
    ).filter(
        DoctorAppointment.status != "rejected"
    ).first()

    if existing:
        return jsonify({
            "message": "This appointment slot is already booked. Please choose another slot."
        }), 409

    # ==========================================
    # CREATE APPOINTMENT
    # ==========================================

    appointment = DoctorAppointment(

        doctor_id=doctor_id,
        user_id=user_id,

        # OWNER
        owner_name=request.form.get("owner_name"),
        owner_phone=request.form.get("owner_phone"),

        # PET
        pet_name=request.form.get("pet_name"),
        pet_type=request.form.get("pet_type"),
        gender=request.form.get("gender"),
        pet_age=request.form.get("pet_age"),

        # APPOINTMENT
        appointment_date=appointment_date,
        appointment_time=appointment_time,

        # MEDICAL
        symptoms=request.form.get("symptoms"),
        concern=request.form.get("reason"),

        status="pending"
    )

    db.session.add(appointment)
    db.session.commit()

    return jsonify({
        "message": "Appointment request sent successfully!"
    }), 201


# =====================================================
# 7. USER GET OWN APPOINTMENTS
# =====================================================
@app.route("/api/my-appointments")
def get_my_appointments():

    if "user_id" not in session:
        return jsonify([])

    user_id = session["user_id"]

    appointments = DoctorAppointment.query.filter_by(
        user_id=user_id
    ).all()

    data = []

    for a in appointments:

        doctor = Doctor.query.get(a.doctor_id)

        data.append({
            "id": a.id,
            "doctor": doctor.name,
            "date": str(a.appointment_date),
            "time": a.appointment_time,
            "status": a.status
        })

    return jsonify(data)


# =====================================================
# 8. DOCTOR GET REQUESTS
# =====================================================
@app.route("/api/doctor/appointments")
def doctor_get_requests():

    if "doctor_id" not in session:
        return jsonify([])

    doctor_id = session["doctor_id"]

    search = request.args.get("search","")
    status_filter = request.args.get("status","all")

    query = DoctorAppointment.query.filter_by(
        doctor_id=doctor_id
    )

    # SEARCH
    if search:

        query = query.filter(

            or_(
                DoctorAppointment.pet_name.ilike(f"%{search}%"),
                DoctorAppointment.owner_name.ilike(f"%{search}%"),
                DoctorAppointment.pet_type.ilike(f"%{search}%")
            )
        )

    # FILTER
    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    appointments = query.order_by(
        DoctorAppointment.created_at.desc()
    ).all()

    data = []

    for a in appointments:

        data.append({
            "id": a.id,

            # OWNER
            "owner_name": a.owner_name,
            "owner_phone": a.owner_phone,

            # PET
            "pet_name": a.pet_name,
            "pet_type": a.pet_type,
            "gender": a.gender,
            "pet_age": a.pet_age,

            # APPOINTMENT
            "date": a.appointment_date,
            "time": a.appointment_time,

            # MEDICAL
            "symptoms": a.symptoms,
            "concern": a.concern,

            # STATUS
            "status": a.status
        })

    return jsonify(data)






# =====================================================
# GET SINGLE APPOINTMENT DETAILS
# =====================================================
@app.route("/api/doctor/appointments/<int:appointment_id>")
def get_single_appointment(appointment_id):

    if "doctor_id" not in session:
        return jsonify({"message":"Unauthorized"}),401

    appointment = DoctorAppointment.query.get_or_404(appointment_id)

    # Security check
    if appointment.doctor_id != session["doctor_id"]:
        return jsonify({"message":"Unauthorized"}),403

    return jsonify({

        "id": appointment.id,

        "owner_name": appointment.owner_name,
        "owner_phone": appointment.owner_phone,

        "pet_name": appointment.pet_name,
        "pet_type": appointment.pet_type,
        "gender": appointment.gender,
        "pet_age": appointment.pet_age,

        "appointment_date": appointment.appointment_date,
        "appointment_time": appointment.appointment_time,

        "symptoms": appointment.symptoms,
        "concern": appointment.concern,

        "status": appointment.status,

        "created_at": appointment.created_at.strftime("%Y-%m-%d")
        if appointment.created_at else ""
    })






# =====================================================
# 9. CONFIRM APPOINTMENT
# =====================================================
@app.route("/api/appointments/<int:id>/confirm", methods=["PUT"])
def confirm_appointment(id):

    appointment = DoctorAppointment.query.get_or_404(id)

    appointment.status = "confirmed"

    db.session.commit()

    return jsonify({"message": "Appointment confirmed"})


# =====================================================
# 10. REJECT APPOINTMENT
# =====================================================
@app.route("/api/appointments/<int:id>/reject", methods=["PUT"])
def reject_appointment(id):

    appointment = DoctorAppointment.query.get_or_404(id)

    appointment.status = "rejected"

    db.session.commit()

    return jsonify({"message": "Appointment rejected"})


# =====================================================
# 11. COMPLETE APPOINTMENT
# =====================================================
@app.route("/api/appointments/<int:id>/complete", methods=["PUT"])
def complete_appointment(id):

    appointment = DoctorAppointment.query.get_or_404(id)

    appointment.status = "completed"

    db.session.commit()

    return jsonify({"message": "Appointment completed"})


# =====================================================
# 12. PENDING BADGE COUNT
# =====================================================
@app.route("/api/doctor/pending-count")
def pending_count():

    if "doctor_id" not in session:
        return jsonify({"count": 0})

    doctor_id = session["doctor_id"]

    count = DoctorAppointment.query.filter_by(
        doctor_id=doctor_id,
        status="pending"
    ).count()

    return jsonify({"count": count})





# ADD THIS IN app.py

from sqlalchemy import func
from datetime import datetime


# ==========================================================
# app.py  (ADD THESE ROUTES BELOW YOUR OTHER ROUTES)
# ==========================================================

@app.route("/doctor-analysis")
def doctor_analysis():
    return render_template("doctor/doctor_analysis.html")


# ==============================
# app.py
# REPLACE ONLY THIS ROUTE
# ==============================

# ============================================
# app.py
# REPLACE ONLY /api/doctor-analysis ROUTE
# ============================================

@app.route("/api/doctor-analysis")
def doctor_analysis_data():

    if "doctor_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    doctor_id = session["doctor_id"]

    filter_type = request.args.get("filter", "30")

    appointments_query = DoctorAppointment.query.filter_by(
        doctor_id=doctor_id
    )

    # ==========================================
    # FILTERS
    # ==========================================
    today = datetime.utcnow()

    if filter_type == "7":
        start_date = today - timedelta(days=7)

    elif filter_type == "30":
        start_date = today - timedelta(days=30)

    else:
        start_date = None

    appointments = appointments_query.all()

    filtered = []

    for a in appointments:
        try:
            dt = datetime.strptime(
                a.appointment_date,
                "%Y-%m-%d"
            )

            if start_date:
                if dt >= start_date:
                    filtered.append(a)
            else:
                filtered.append(a)

        except:
            pass

    # ==========================================
    # STATUS COUNTS
    # ==========================================
    pending = len([
        a for a in filtered
        if a.status == "pending"
    ])

    confirmed = len([
        a for a in filtered
        if a.status == "confirmed"
    ])

    completed = len([
        a for a in filtered
        if a.status == "completed"
    ])

    rejected = len([
        a for a in filtered
        if a.status == "rejected"
    ])

    total_appointments = len(filtered)

    # ==========================================
    # DOCTOR
    # ==========================================
    doctor = Doctor.query.get(doctor_id)

    consultation_fee = doctor.consultation_fee or 0

    total_revenue = (
        (confirmed + completed)
        * consultation_fee
    )

    # ==========================================
    # WEEKLY APPOINTMENTS
    # ==========================================
    days = [
        "Mon", "Tue", "Wed",
        "Thu", "Fri", "Sat", "Sun"
    ]

    weekly_map = {
        "Mon": 0,
        "Tue": 0,
        "Wed": 0,
        "Thu": 0,
        "Fri": 0,
        "Sat": 0,
        "Sun": 0
    }

    # ==========================================
    # PEAK HOURS
    # ==========================================
    hour_map = {}

    # ==========================================
    # PET TYPES
    # ==========================================
    pet_map = {}

    # ==========================================
    # MONTHLY TREND
    # ==========================================
    month_map = {}

    # ==========================================
    # UPCOMING APPOINTMENTS
    # ==========================================
    upcoming_appointments = []

    today_date = datetime.utcnow().date()

    for a in appointments:

        try:
            appt_date = datetime.strptime(
                a.appointment_date,
                "%Y-%m-%d"
            ).date()

            if appt_date >= today_date:

                upcoming_appointments.append({
                    "title": a.pet_name,
                    "start": a.appointment_date,
                    "time": a.appointment_time,
                    "status": a.status
                })

        except:
            pass

    # ==========================================
    # OTHER ANALYTICS
    # ==========================================
    for a in filtered:

        try:
            dt = datetime.strptime(
                a.appointment_date,
                "%Y-%m-%d"
            )

            day = dt.strftime("%a")

            if day in weekly_map:
                weekly_map[day] += 1

            month = dt.strftime("%b")

            month_map[month] = (
                month_map.get(month, 0) + 1
            )

        except:
            pass

        # Peak hours
        if a.appointment_time:

            hr = a.appointment_time[:2] + ":00"

            hour_map[hr] = (
                hour_map.get(hr, 0) + 1
            )

        # Pet types
        pet = (
            a.pet_type
            if a.pet_type
            else "Unknown"
        )

        pet_map[pet] = (
            pet_map.get(pet, 0) + 1
        )

    # ==========================================
    # RETURN JSON
    # ==========================================
    return jsonify({

        "doctor": {
            "name": doctor.name,
            "specialization": doctor.specialization,
            "fee": consultation_fee
        },

        "cards": {
            "appointments": total_appointments,
            "revenue": total_revenue,
            "completed": completed,
            "pending": pending,
            "confirmed": confirmed,
            "rejected": rejected
        },

        "status": {
            "labels": [
                "Pending",
                "Confirmed",
                "Completed",
                "Rejected"
            ],
            "values": [
                pending,
                confirmed,
                completed,
                rejected
            ]
        },

        "weekly": {
            "labels": days,
            "values": [
                weekly_map[d]
                for d in days
            ]
        },

        "hours": {
            "labels": list(hour_map.keys()),
            "values": list(hour_map.values())
        },

        "pets": {
            "labels": list(pet_map.keys()),
            "values": list(pet_map.values())
        },

        "monthly": {
            "labels": list(month_map.keys()),
            "values": list(month_map.values())
        },

        "upcoming": upcoming_appointments

    })








    
# =====================================================
# APPOINTMENT DETAILS PAGE
# =====================================================
@app.route("/appointment/<int:appointment_id>")
def appointment_details_page(appointment_id):

    if "doctor_id" not in session:
        return redirect("/login")

    return render_template(
        "doctor/appointment_details.html",
        appointment_id=appointment_id
    )


# =============================================================================
# SALONS
# =============================================================================
# GET /api/salon - GET all salons
@app.route('/api/salon', methods=['GET'])
def get_all_salons():
    salons = Salon.query.all()
    return jsonify({
        'count':len(salons),
        'salons':[salon.to_dict() for salon in salons]
    })
       


@app.route("/api/salons")
def get_salons():

    if "user_id" not in session:
        return jsonify([])

    user_id = session["user_id"]
    role = session.get("role")

    # Salon owner → only own salons
    if role == "Salon_Owner":
        salons = Salon.query.filter_by(user_id=user_id).all()

    # Pet owner → all salons
    else:
        salons = Salon.query.all()

    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "open_hours": s.open_hours,
            "close_hours": s.close_hours,
            "tagline": s.tagline,
            "city": s.city,
            "image": f"uploads/{s.image}" if s.image else "images/default.jpg"
        }
        for s in salons
    ])


from flask import request, jsonify

@app.route("/api/salon", methods=["POST"])
def add_salon():

    if "user_id" not in session:
        return jsonify({"message": "Login required"}), 401

    try:
        user_id = session["user_id"]

        # form data
        name = request.form.get("name")
        open_hours = request.form.get("open_hours")
        close_hours = request.form.get("close_hours")
        tagline = request.form.get("tagline")
        description = request.form.get("description")
        address = request.form.get("address")
        city = request.form.get("city")
        phone = request.form.get("phone")

        # image
        image = request.files.get("image")
        image_filename = None

        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, image_filename))

        # save salon
        salon = Salon(
            user_id=user_id,   # IMPORTANT
            name=name,
            open_hours=open_hours,
            close_hours=close_hours,
            tagline=tagline,
            description=description,
            address=address,
            city=city,
            phone=phone,
            image=image_filename
        )

        db.session.add(salon)
        db.session.commit()

        # services
        services_json = request.form.get("services")
        services = json.loads(services_json) if services_json else []

        for s in services:
            service = Service(
                salon_id=salon.id,
                service_name=s.get("service_name"),
                price=float(s.get("price", 0)),
                duration=int(s.get("duration", 0))
            )
            db.session.add(service)

        db.session.commit()

        return jsonify({
            "message": "Salon saved successfully",
            "salon": salon.to_dict()
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "message": "Error saving salon",
            "error": str(e)
        }), 500
    


#single salon
@app.route('/api/salon/<int:salon_id>', methods=['GET'])
def get_single_salon(salon_id):
    salon = Salon.query.get_or_404(salon_id)
    services = Service.query.filter_by(salon_id=salon.id).all()

    return jsonify({
        **salon.to_dict(),
        "services": [s.to_dict() for s in services]
    })



@app.route('/api/salon/<int:salon_id>', methods=['PUT'])
def update_salon(salon_id):
    salon = Salon.query.get_or_404(salon_id)

    if salon.user_id != session.get("user_id"):
        return jsonify({"message":"Unauthorized"}), 403

    # Update salon basic details
    salon.name = request.form.get('name')
    salon.tagline = request.form.get('tagline')
    salon.open_hours = request.form.get('open_hours')
    salon.close_hours = request.form.get('close_hours')
    salon.description = request.form.get('description')
    salon.address = request.form.get('address')
    salon.city = request.form.get('city')
    salon.phone = request.form.get('phone')

    #  Update image (if new image uploaded)
    image = request.files.get("image")
    if image:
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, image_filename))
        salon.image = image_filename

    #  DELETE old services
    Service.query.filter_by(salon_id=salon.id).delete()

    #  ADD new services
    services_json = request.form.get("services")
    services = json.loads(services_json) if services_json else []

    for s in services:
        service = Service(
            salon_id=salon.id,
            service_name=s.get("service_name"),
            price=float(s.get("price", 0)),
            duration=int(s.get("duration", 0))
        )
        db.session.add(service)

    db.session.commit()

    return jsonify({"message": "Salon updated successfully"})



#delete salon 
@app.route('/api/salon/<int:salon_id>', methods=['DELETE'])
def delete_salon(salon_id):

    # delete all services
    Service.query.filter_by(salon_id=salon_id).delete()

    # delete all appointments
    SalonAppointment.query.filter_by(salon_id=salon_id).delete()

    # delete salon
    salon = Salon.query.get_or_404(salon_id)

    if salon.user_id != session.get("user_id"):
        return jsonify({"message":"Unauthorized"}), 403
    db.session.delete(salon)

    # Commit changes
    db.session.commit()

    return jsonify({
        "message": "Salon, services and appointments deleted successfully"
    })


from flask import session, jsonify

@app.route("/api/current-owner")
def current_owner():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"message": "Login required"}), 401

    user = User.query.get(user_id)

    return jsonify({
        "name": user.username,
        "email": user.email
    })




# =============================================================================
#SERVICE
# =============================================================================

# GET  Services of a Salon
# =============================================================================
@app.route('/api/salon/<int:salon_id>/service', methods=['GET'])
def get_services_of_salon(salon_id):
    services = Service.query.filter_by(salon_id=salon_id).all()
    return jsonify([service.to_dict() for service in services])


#POST /api/salon/<int:salon_id> /service
@app.route('/api/salon/<int:salon_id>/service', methods=['POST'])
def create_service(salon_id):
    Salon.query.get_or_404(salon_id)  # ensure salon exists
    data = request.json

    service = Service(
        salon_id=salon_id,
        service_name=data['service_name'],
        price=data['price'],
        duration=data['duration']
    )

    db.session.add(service)
    db.session.commit()

    return jsonify({
        "message": "Service created successfully",
        "service": service.to_dict()
    }), 201

#put the sevice --update the sevice
@app.route('/api/service/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    data = request.json

    service.service_name = data.get('service_name', service.service_name)
    service.price = data.get('price', service.price)
    service.duration = data.get('duration', service.duration)

    db.session.commit()

    return jsonify({
        "message": "Service updated successfully",
        "service": service.to_dict()
    })


#DELETE Service
@app.route('/api/service/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)

    db.session.delete(service)
    db.session.commit()

    return jsonify({"message": "Service deleted successfully"})





# ================================
# PETS ROUTES (DB-Backed)
# ================================


from flask import jsonify, request
from werkzeug.utils import secure_filename
import os

GALLERY_FOLDER = "static/gallery"

os.makedirs(GALLERY_FOLDER, exist_ok=True)


@app.route("/api/gallery-upload", methods=["POST"])
def upload_gallery_image():

    if "image" not in request.files:
        return jsonify({"error": "No image"}), 400

    file = request.files["image"]

    filename = secure_filename(file.filename)

    filepath = os.path.join(GALLERY_FOLDER, filename)

    file.save(filepath)

    return jsonify({
        "message": "Uploaded successfully",
        "image": filename
    })


@app.route("/api/gallery", methods=["GET"])
def get_gallery_images():

    images = []

    for file in os.listdir(GALLERY_FOLDER):

        images.append(file)

    return jsonify(images)
# GET all pets
@app.route("/api/pets", methods=["GET"])
def get_pets():

    all_pets = Pet.query.filter_by(is_sold=False).all()

    return jsonify([
        p.to_dict() for p in all_pets
    ])

# POST new pet
# POST new pet with file upload
@app.route("/api/pets", methods=["POST"])
def add_pet():
    # Check if the request contains form data (multipart/form-data)
    if "name" not in request.form:
        return jsonify({"error": "No data provided"}), 400

    try:
        # 1️⃣ Get pet details from form
        name = request.form.get("name")
        breed = request.form.get("breed")
        age = request.form.get("age")
        price = float(request.form.get("price", 0))
        desc = request.form.get("desc")
        contact = request.form.get("contact")
        category = request.form.get("category")

        # 2️⃣ Handle image upload
        img_file = request.files.get("img")
        if img_file:
            img_filename = secure_filename(img_file.filename)
            img_file.save(os.path.join(UPLOAD_FOLDER, img_filename))
        # 3️⃣ Create Pet object
        new_pet = Pet(
            name=name,
            breed=breed,
            age=age,
            price=price,
            desc=desc,
            contact=contact,
            category=category,
            img=img_filename
        )
        db.session.add(new_pet)
        db.session.commit()

        return jsonify({"message": "Pet added", "pet": new_pet.to_dict()}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# PUT update pet
@app.route("/api/pets/<int:id>", methods=["PUT"])
def update_pet(id):

    pet = Pet.query.get(id)

    if not pet:
        return jsonify({"message": "Pet not found"}), 404

    pet.name = request.form.get("name")
    pet.breed = request.form.get("breed")
    pet.age = request.form.get("age")
    pet.price = request.form.get("price")
    pet.contact = request.form.get("contact")
    pet.desc = request.form.get("desc")

    file = request.files.get("img")

    if file:

        filename = secure_filename(file.filename)

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        file.save(filepath)

        pet.img = f"uploads/{filename}"

    db.session.commit()

    return jsonify({
        "message": "Pet updated successfully"
    })




# DELETE pet
@app.route("/api/pets/<int:pet_id>", methods=["DELETE"])
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    try:
        db.session.delete(pet)
        db.session.commit()
        return jsonify({"message": "Pet deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    



from datetime import datetime

@app.route("/api/buy/<int:pet_id>", methods=["POST"])
def buy_pet(pet_id):

    pet = Pet.query.get(pet_id)

    if not pet:
        return jsonify({
            "message":"Pet not found"
        }),404

    if pet.is_sold:
        return jsonify({
            "message":"This pet is already sold"
        }),400

    data = request.get_json()

    purchase = Purchase(
        pet_id=pet.id,
        buyer_name=data.get("buyer_name"),
        buyer_phone=data.get("buyer_phone")
    )

    pet.is_sold = True

    db.session.add(purchase)

    db.session.commit()

    return jsonify({
        "message":"🎉 Pet purchased successfully!"
    })




from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# -------------------------------
# CREATE DOCTOR
# -------------------------------
@app.route("/api/doctors", methods=["POST"])
def create_doctor():

    
    user_id = session.get("user_id")
    name = request.form.get("name")
    clinic_name = request.form.get("clinic_name")
    specialization = request.form.get("specialization")
    phone = request.form.get("phone")
    experience = request.form.get("experience")
    experience_years = int(experience) if experience else None
    consultation_fee = request.form.get("consultation_fee")
    city = request.form.get("address")   # frontend sends address
    available_days = request.form.get("available_days")
    available_time = request.form.get("available_time")
    bio = request.form.get("bio")

    # Image Upload
    profile_pic = request.files.get("profile_pic")
    profile_pic_filename = None

    if profile_pic:
        profile_pic_filename = secure_filename(profile_pic.filename)
        profile_pic.save(os.path.join(UPLOAD_FOLDER, profile_pic_filename))

    # Create doctor
    doctor = Doctor(
        user_id=user_id,
        name=name,
        clinic_name=clinic_name,
        specialization=specialization,
        phone=phone,
        experience_years=experience_years,
        consultation_fee=float(consultation_fee) if consultation_fee else None,
        city=city,
        bio=bio,
        profile_pic=profile_pic_filename
    )

    db.session.add(doctor)
    db.session.commit()

    # Add availability
    if available_days and available_time:

        try:
            start_time, end_time = map(str.strip, available_time.split("-"))

            for day in available_days.split(","):

                availability = DoctorAvailability(
                    doctor_id=doctor.id,
                    day_of_week=day.strip(),
                    start_time=start_time,
                    end_time=end_time,
                    slot_duration_minutes=30,
                    is_active=True
                )

                db.session.add(availability)

            db.session.commit()

        except Exception as e:
            print("Availability parse error:", e)

    return jsonify({"message": "Doctor added successfully!"})
# -------------------------------
# GET ALL DOCTORS
# -------------------------------
@app.route("/api/doctors", methods=["GET"])
def get_doctors():
    doctors = Doctor.query.all()
    return jsonify([d.to_dict() for d in doctors])

# -------------------------------
# GET SINGLE DOCTOR
# -------------------------------
@app.route("/api/doctors/<int:doctor_id>", methods=["GET"])
def get_single_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    availability = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    appointments = DoctorAppointment.query.filter_by(doctor_id=doctor.id).all()

    return jsonify({
        **doctor.to_dict(),
        "availability": [a.to_dict() for a in availability],
        "appointments": [a.to_dict() for a in appointments]
    })

# -------------------------------
# UPDATE DOCTOR
# -------------------------------
@app.route('/api/doctors/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):


    # Must login
    if "doctor_id" not in session:
        return jsonify({"message":"Login required"}), 401

    # Prevent editing others
    if session["doctor_id"] != doctor_id:
        return jsonify({"message":"Unauthorized"}), 403

    doctor = Doctor.query.get_or_404(doctor_id)

    # Get form data
    name = request.form.get("name")
    clinic_name = request.form.get("clinic_name")
    specialization = request.form.get("specialization")
    phone = request.form.get("phone")
    experience = request.form.get("experience")
    consultation_fee = request.form.get("consultation_fee")
    city = request.form.get("address")
    bio = request.form.get("bio")

    available_days = request.form.get("available_days")
    available_time = request.form.get("available_time")

    # Convert experience
    experience_years = int(experience) if experience else None

    # Update doctor fields
    doctor.name = name
    doctor.clinic_name = clinic_name
    doctor.specialization = specialization
    doctor.phone = phone
    doctor.experience_years = experience_years
    doctor.consultation_fee = float(consultation_fee) if consultation_fee else None
    doctor.city = city
    doctor.bio = bio

    # -------------------------
    # HANDLE IMAGE UPDATE
    # -------------------------
    profile_pic = request.files.get("profile_pic")

    if profile_pic:
        filename = secure_filename(profile_pic.filename)
        profile_pic.save(os.path.join(UPLOAD_FOLDER, filename))
        doctor.profile_pic = filename


    # -------------------------
    # UPDATE AVAILABILITY
    # -------------------------
    if available_days and available_time:

        # Remove old availability
        DoctorAvailability.query.filter_by(doctor_id=doctor.id).delete()

        try:

            start_time, end_time = map(str.strip, available_time.split("-"))

            for day in available_days.split(","):

                availability = DoctorAvailability(
                    doctor_id=doctor.id,
                    day_of_week=day.strip(),
                    start_time=start_time,
                    end_time=end_time,
                    slot_duration_minutes=30,
                    is_active=True
                )

                db.session.add(availability)

        except Exception as e:
            print("Availability parse error:", e)

    # Commit all changes
    db.session.commit()

    return jsonify({"message": "Doctor updated successfully!"})
# -------------------------------
# DELETE DOCTOR
# -------------------------------
@app.route("/api/doctors/<int:doctor_id>", methods=["DELETE"])
def delete_doctor(doctor_id):

    # Must login
    if "doctor_id" not in session:
        return jsonify({"message":"Login required"}), 401

    # Prevent deleting others
    if session["doctor_id"] != doctor_id:
        return jsonify({"message":"Unauthorized"}), 403
    
    # Delete availability
    DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()
    # Delete appointments
    DoctorAppointment.query.filter_by(doctor_id=doctor_id).delete()
    # Delete doctor
    doctor = Doctor.query.get_or_404(doctor_id)
    db.session.delete(doctor)
    db.session.commit()
    return jsonify({"message": "Doctor deleted successfully"})


#========================================================================================================================================
#========================================================================================================================================

# ================= USER PROFILE TABLE =================

class UserProfile(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    fullname = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100))

    profile_image = db.Column(db.String(200))

    # PET DETAILS
    pet_name = db.Column(db.String(100))
    pet_type = db.Column(db.String(100))
    pet_age = db.Column(db.String(20))
    pet_image = db.Column(db.String(200))

with app.app_context():
    db.create_all()


@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # EXISTING USER TABLE
    user = User.query.get(user_id)

    # NEW PROFILE TABLE
    profile = UserProfile.query.filter_by(user_id=user_id).first()

    # CREATE EMPTY PROFILE FIRST TIME
    if not profile:

        profile = UserProfile(
            user_id=user_id,
            fullname=user.name if hasattr(user, "name") else "",
        )

        db.session.add(profile)
        db.session.commit()

    return render_template(
        "user/profile.html",
        user=user,
        profile=profile
    )

@app.route("/update-profile", methods=["POST"])
def update_profile():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    profile = UserProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        profile = UserProfile(user_id=user_id)

    profile.fullname = request.form.get("fullname")
    profile.phone = request.form.get("phone")
    profile.city = request.form.get("city")

    profile.pet_name = request.form.get("pet_name")
    profile.pet_type = request.form.get("pet_type")
    profile.pet_age = request.form.get("pet_age")

    # PROFILE IMAGE
    if "profile_image" in request.files:

        file = request.files["profile_image"]

        if file.filename != "":

            filename = secure_filename(file.filename)

            filepath = os.path.join(UPLOAD_FOLDER, filename)

            file.save(filepath)

            profile.profile_image = filename

    # PET IMAGE
    if "pet_image" in request.files:

        pet = request.files["pet_image"]

        if pet.filename != "":

            pet_filename = secure_filename(pet.filename)

            pet_path = os.path.join(UPLOAD_FOLDER, pet_filename)

            pet.save(pet_path)

            profile.pet_image = pet_filename

    db.session.add(profile)

    db.session.commit()

    return redirect("/profile")



#======================SALON Appointments Part ====================
# ===== salon appointments page =====
@app.route("/salon-appointments/<int:salon_id>")
def salon_appointments(salon_id):

    appointments = SalonAppointment.query.filter_by(
        salon_id=salon_id
    ).all()

    salon = Salon.query.get_or_404(salon_id)

    services = Service.query.filter_by(
        salon_id=salon_id
    ).all()

    return render_template(
        "salon/salon-appointments.html",
        appointments=appointments,
        salon=salon,
        services=services
    )


from flask import request, redirect, render_template, flash

# ===== create appointment =====
from datetime import datetime, timedelta


# ===== create appointment =====
@app.route('/api/salon-appointments', methods=['POST'])
def create_salon_appointment():

    data = request.form.to_dict()

    selected_services = request.form.getlist("service_name")

    # =========================
    # CHECK SERVICES
    # =========================
    if not selected_services:
        flash("❌ Please select at least one service.")
        return redirect(request.referrer)

    # =========================
    # DATE VALIDATION
    # =========================
    appointment_date = data.get("appointment_date")

    selected_date = datetime.strptime(
        appointment_date,
        "%Y-%m-%d"
    ).date()

    today = datetime.today().date()

    max_date = today + timedelta(days=2)

    # Past date block
    if selected_date < today:
        flash("❌ Past date booking not allowed.")
        return redirect(request.referrer)

    # Future limit block
    if selected_date > max_date:
        flash("❌ You can book only for next 2 days.")
        return redirect(request.referrer)

    # =========================
    # SERVICES + PRICE
    # =========================
    service_names = ", ".join(selected_services)

    services = Service.query.filter(
        Service.salon_id == data.get("salon_id"),
        Service.service_name.in_(selected_services)
    ).all()

    service_price = sum(service.price for service in services)

    # =========================
    # SLOT CHECK
    # =========================
    existing_booking = SalonAppointment.query.filter(
    SalonAppointment.salon_id == data.get("salon_id"),
    SalonAppointment.appointment_date == data.get("appointment_date"),
    SalonAppointment.appointment_time == data.get("appointment_time"),
    SalonAppointment.status == "confirmed"
   ).first()

    if existing_booking:
        flash("❌ This slot is already booked.")
        return redirect(request.referrer)

    # =========================
    # SAVE APPOINTMENT
    # =========================
    appointment = SalonAppointment(

        salon_id=data.get("salon_id"),

        user_id=session['user_id'],

        owner_name=data.get("owner_name"),

        mobile=data.get("mobile"),

        pet_name=data.get("pet_name"),

        pet_category=data.get("pet_category"),

        service_name=service_names,

        appointment_date=data.get("appointment_date"),

        appointment_time=data.get("appointment_time"),

        notes=data.get("notes"),

        status="confirmed"
    )

    db.session.add(appointment)
    db.session.commit()

    # =========================
    # GET SALON
    # =========================
    salon = Salon.query.get(data.get("salon_id"))

    # =========================
    # SEND CONFIRM SMS
    # =========================
    try:

        mobile = str(data.get("mobile")).strip().replace(" ", "")

        # REMOVE +91 IF USER ALREADY ENTERED IT
        if mobile.startswith("+91"):
            phone_number = mobile
        else:
            phone_number = "+91" + mobile

        print("PHONE NUMBER:", phone_number)

        sms_text = f"""
Hello {data.get('owner_name')},

Your appointment is confirmed 🐾

Salon: {salon.name}
Pet: {data.get('pet_name')}
Date: {data.get('appointment_date')}
Time: {data.get('appointment_time')}
Services: {service_names}
Total Price: ₹{service_price}

Thank you.
"""

        print("SMS TEXT:", sms_text)

        message = sms_client.messages.create(
            body=sms_text,
            from_=TWILIO_PHONE,
            to=phone_number
        )

        print("✅ CONFIRM SMS SENT")
        print("MESSAGE SID:", message.sid)
        print("STATUS:", message.status)

    except Exception as e:

        import traceback
        traceback.print_exc()

        print("❌ CONFIRM SMS ERROR")
        print(str(e))

    # =========================
    # THANK YOU PAGE
    # =========================
    return render_template(

        "salon/thankyou.html",

        owner_name=appointment.owner_name,

        pet_name=appointment.pet_name,

        mobile=appointment.mobile,

        service_name=service_names,

        service_price=service_price,

        salon_id=salon.id,

        rating=salon.rating if salon.rating else 0
    )
# ===== update appointment status =====
@app.route("/update_appointment_status/<int:appointment_id>", methods=["POST"])
def update_appointment_status(appointment_id):

    appointment = SalonAppointment.query.get_or_404(appointment_id)
    new_status = request.form.get("status")

    print("NEW STATUS:", new_status)

    appointment.status = new_status
    db.session.commit()

    if new_status and new_status.lower() in ["canceled", "cancelled"]:

        print("INSIDE CANCEL BLOCK")

        try:
            mobile = str(appointment.mobile).strip().replace(" ", "")

            if mobile.startswith("+91"):
                phone_number = mobile
            else:
                phone_number = "+91" + mobile

            print("PHONE NUMBER:", phone_number)

            salon = db.session.get(Salon, appointment.salon_id)

            sms_text = f"""
Hello {appointment.owner_name},

Your appointment has been cancelled ❌

Salon: {salon.name}
Pet: {appointment.pet_name}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}

Please book another slot.
"""

            print("SMS TEXT:", sms_text)

            message = sms_client.messages.create(
                body=sms_text,
                from_=TWILIO_PHONE,
                to=phone_number
            )

            print("CANCEL SMS SENT:", message.sid)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print("CANCEL SMS ERROR:", str(e))

    return redirect(request.referrer)



#======================================================================================================
#Rating
#======================================================================================================
from datetime import datetime

class SalonReview(db.Model):
    __tablename__ = 'salon_reviews'
    id = db.Column(db.Integer, primary_key=True)
    salon_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "salon_id": self.salon_id,
            "user_id": self.user_id,
            "username": self.username,
            "rating": self.rating,
            "review": self.review
        }
    
with app.app_context():
    db.create_all()


@app.route('/submit-review', methods=['POST'])
def submit_review():

    if 'user_id' not in session:
        flash("Please login first")
        return redirect('/login')

    salon_id = request.form['salon_id']
    rating = request.form['rating']
    review_text = request.form['review']

    new_review = SalonReview(
        salon_id=salon_id,
        user_id=session['user_id'],
        username=session['username'],
        rating=rating,
        review=review_text
    )

    db.session.add(new_review)
    db.session.commit()

    flash("Review submitted successfully")

    return redirect(request.referrer)

#======= salon rating page =======
@app.route('/rate-salon')
def rate_salon():
    salon_id = request.args.get('id')

    if not salon_id:
        return "Salon ID missing"

    salon = Salon.query.get(int(salon_id))

    return render_template('salon/rate-salon.html', salon=salon)


@app.route('/submit-rating', methods=['POST'])
def submit_rating():

    if 'user_id' not in session:
        flash("Please login first")
        return redirect('/login')

    salon_id = request.form.get('salon_id')
    rating = request.form.get('rating')
    review_text = request.form.get('review')

    salon = Salon.query.get(int(salon_id))

    if salon:

        salon.rating = float(rating)

        new_review = SalonReview(
            salon_id=salon_id,
            user_id=session['user_id'],
            username=session['username'],
            rating=int(rating),
            review=review_text
        )

        db.session.add(new_review)
        db.session.commit()

        flash("Thank you for rating ❤️")

    return redirect(f'/salondetail?id={salon_id}')



from datetime import datetime

def time_ago(dt):
    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    elif seconds < 7 * 86400:
        return f"{int(seconds // 86400)} days ago"
    else:
        return dt.strftime("%d %b %Y")


# register filter
app.jinja_env.filters['timeago'] = time_ago

from collections import defaultdict

#============ SALON ANALYTICS PAGE ===========

@app.route("/analytics")
def salon_analytics():

    salon_id = request.args.get("salon_id")

    salon = Salon.query.get_or_404(salon_id)

    # =========================
    # ALL APPOINTMENTS
    # =========================

    appointments = SalonAppointment.query.filter_by(
        salon_id=salon_id
    ).all()

    # =========================
    # TOTAL APPOINTMENTS
    # =========================

    total_appointments = len(appointments)

    # =========================
    # COMPLETED
    # =========================

    completed = SalonAppointment.query.filter(
    SalonAppointment.salon_id == salon_id,
    SalonAppointment.status.ilike("confirmed")
).count()

    # =========================
    # CANCELLED
    # =========================

    cancelled = SalonAppointment.query.filter(
    SalonAppointment.salon_id == salon_id,
    SalonAppointment.status.ilike("cancel%")
).count()

    # =========================
    # TOTAL REVENUE
    # =========================

    total_revenue = 0

    for appointment in appointments:

        if not appointment.service_name:
            continue

        services = appointment.service_name.split(",")

        for service_name in services:

            service = Service.query.filter_by(
                salon_id=salon_id,
                service_name=service_name.strip()
            ).first()

            if service:
                total_revenue += service.price

    # =========================
    # APPOINTMENTS CHART DATA
    # =========================

    chart_labels = []
    chart_values = []

    for appointment in appointments:

        date = str(appointment.appointment_date)

        if date in chart_labels:

            index = chart_labels.index(date)
            chart_values[index] += 1

        else:

            chart_labels.append(date)
            chart_values.append(1)

    # =========================
    # MONTHLY REVENUE DATA
    # =========================

    monthly_revenue = defaultdict(int)

    for appointment in appointments:

        if not appointment.service_name:
            continue

        try:
            month = appointment.appointment_date.strftime("%b %Y")
        except:
            month = str(appointment.appointment_date)

        revenue = 0

        services = appointment.service_name.split(",")

        for service_name in services:

            service = Service.query.filter_by(
                salon_id=salon_id,
                service_name=service_name.strip()
            ).first()

            if service:
                revenue += service.price

        monthly_revenue[month] += revenue

    revenue_labels = list(monthly_revenue.keys())
    revenue_values = list(monthly_revenue.values())
    


    pet_counts = {
    "Dog": 0,
    "Cat": 0,
    "Other": 0
}

    for appt in appointments:

         category = (appt.pet_category or "").lower()
  
         if "dog" in category:
             pet_counts["Dog"] += 1
         elif "cat" in category:
            pet_counts["Cat"] += 1
         else:
            pet_counts["Other"] += 1
    # =========================
    # RENDER PAGE
    # =========================

    return render_template(

        "salon/salon_analytics.html",

        salon=salon,

        total_appointments=total_appointments,
        completed=completed,
        cancelled=cancelled,

        total_revenue=total_revenue,

        chart_labels=chart_labels,
        chart_values=chart_values,

        revenue_labels=revenue_labels,
        revenue_values=revenue_values,

        pet_counts=pet_counts
    )

#=======================================================================================================
#User Appointment Routes
#=======================================================================================================

@app.route('/my_appointments')
def myappointments():

    if "user_id" not in session:
        return redirect('/login')

    user_id = session['user_id']

    salon_appointments = SalonAppointment.query.filter_by(
        user_id=user_id
    ).all()

    doctor_appointments = DoctorAppointment.query.filter_by(
        user_id=user_id
    ).all()

    return render_template(
        'user/my_appointment.html',
        salon_appointments=salon_appointments,
        doctor_appointments=doctor_appointments
    )

@app.route('/cancel-salon/<int:id>')
def cancel_salon(id):

    appointment = SalonAppointment.query.get_or_404(id)

    appointment.status = "cancelled"

    db.session.commit()

    return redirect(url_for('myappointments'))

@app.route('/cancel-doctor/<int:id>')
def cancel_doctor(id):

    appointment = DoctorAppointment.query.get_or_404(id)

    appointment.status = "cancelled"

    db.session.commit()

    return redirect(url_for('myappointments'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)