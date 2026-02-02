from flask import Flask, request, jsonify,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__,static_folder="frontend")
CORS(app)  # IMPORTANT for frontend-backend connection

# =============================================================================
# Database configuration
# =============================================================================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///salon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Salon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tagline = db.Column(db.String(200))
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    services = db.relationship('Service', backref='salon', cascade="all, delete")

    def to_dict(self):# Convert model to dictionary for JSON response
        return {
            "id": self.id,
            "name": self.name,
            "tagline": self.tagline,
            "description": self.description,
            "address": self.address,
            "city": self.city,
            "phone": self.phone,
            "services": [service.to_dict() for service in self.services]
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

# =============================================================================
# REST API ROUTES
# =============================================================================

# =============================================================================
# FRONTEND ROUTES
# =============================================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search")
def search():
    print("SEARCH PAGE LOADED")
    return render_template("search.html")

@app.route("/manage-salon")
def manage_salon():
    return render_template("manage-salon.html")

@app.route("/salon/<int:salon_id>")
def salon_detail(salon_id):
    return render_template("salon-detail.html", salon_id=salon_id)

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
       
@app.route("/api/salons", methods=["GET"])
def get_salons():
    salons = Salon.query.all()
    return jsonify([salon.to_dict() for salon in salons])


# POST /api/salon - Create new salon
@app.route('/api/salon', methods=['POST'])
@app.route('/api/salon', methods=['POST'])
def create_salon():
    data = request.json
    print(data)

    salon = Salon(
        name=data['name'],
        tagline=data.get('tagline'),
        description=data.get('description'),
        address=data.get('address'),
        city=data.get('city'),
        phone=data.get('phone')
    )

    db.session.add(salon)
    db.session.commit()  # get salon.id

    # ✅ SAVE MULTIPLE SERVICES
    services = data.get('services', [])
    for s in services:
        service = Service(
            salon_id=salon.id,
            service_name=s.get('service_name'),
            price=s.get('price'),
            duration=s.get('duration')
        )
        db.session.add(service)

    db.session.commit()

    return jsonify({
        "message": "Salon + services created successfully",
        "salon": salon.to_dict()
    }), 201

#single salon
@app.route('/api/salon/<int:salon_id>', methods=['GET'])
def get_single_salon(salon_id):
    salon = Salon.query.get_or_404(salon_id)
    return jsonify(salon.to_dict())


# PUT /api/salon/<int:salon_id> -Update salon
def update_salon(salon_id):
    salon = Salon.query.get_or_404(salon_id)
    data = request.json

    salon.name = data.get('name', salon.name)
    salon.tagline = data.get('tagline', salon.tagline)
    salon.description = data.get('description', salon.description)
    salon.address = data.get('address', salon.address)
    salon.city = data.get('city', salon.city)
    salon.phone = data.get('phone', salon.phone)

    # ✅ DELETE OLD SERVICES
    Service.query.filter_by(salon_id=salon.id).delete()

    # ✅ ADD UPDATED SERVICES
    services = data.get('services', [])
    for s in services:
        service = Service(
            salon_id=salon.id,
            service_name=s.get('service_name'),
            price=s.get('price'),
            duration=s.get('duration')
        )
        db.session.add(service)

    db.session.commit()

    return jsonify({
        "message": "Salon + services updated successfully",
        "salon": salon.to_dict()
    })

#delete salon
@app.route('/api/salon/<int:salon_id>', methods=['DELETE'])
def delete_salon(salon_id):
    salon = Salon.query.get_or_404(salon_id)

    db.session.delete(salon)
    db.session.commit()

    return jsonify({"message": "Salon deleted successfully"})

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)