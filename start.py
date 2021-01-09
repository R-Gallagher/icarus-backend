"""
TO BE USED ON NEW HEROKU DEPLOYS ONLY.
Create database tables, fill in values for relationship tables.
This is run on heroku review apps. If database needs to be cleared, can be run again with:

heroku run python start.py --app icarus-rest-api
"""
from models.designation import DesignationModel
from models.language import LanguageModel
from models.provider_type import ProviderTypeModel
from models.specialty import SpecialtyModel

from os import environ
from app import app
from extensions import db, ma

with app.app_context():        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if environ.get('DEV_ENV') == ('prod' or 'staging'):
        app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') + '?sslmode=require'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL')

    db.init_app(app)
    db.create_all()
    db.session.commit()
    # order matters here
    ma.init_app(app)

designations = [
    "MD",
]

languages = [
    "Acholi",
    "Afrikaans",
    "Akan",
    "Albanian",
    "American Sign Language",
    "Amharic",
    "Arabic",
    "Armenian",
    "Assyrian",
    "Azari",
    "Belarusian",
    "Bengali",
    "Bislama",
    "Bosnian",
    "Bulgarian",
    "Burmese",
    "Cambodian",
    "Cantonese",
    "Catalan",
    "Cebuano",
    "Chewa",
    "Chinese",
    "Chitumbuka",
    "Creole",
    "Croatian",
    "Czech",
    "Dagaare",
    "Danish",
    "Dari",
    "Dutch",
    "English",
    "Eritrean",
    "Estonian",
    "Ethiopian",
    "Farsi",
    "Filipino",
    "Finnish",
    "Flemish",
    "French",
    "Fukien",
    "Fuzhou",
    "Ga",
    "Ga-Adangme-Krobo",
    "Gaelic",
    "Ganda",
    "Georgian",
    "German",
    "Ghana",
    "Greek",
    "Gujarati",
    "Hakka",
    "Hausa",
    "Hebrew",
    "Hindi",
    "Hungarian",
    "Ibibio",
    "Ibo",
    "Icelandic",
    "Igbo",
    "Ilocano",
    "Indonesian",
    "Iranian",
    "Italian",
    "Jamaican Creole",
    "Japanese",
    "Kaamba",
    "Kabyle",
    "Kachchi",
    "Kannada",
    "Kashmiri",
    "Konkani",
    "Korean",
    "Kurdi",
    "Lao",
    "Latvian",
    "Lingala",
    "Lithuanian",
    "Macedonian",
    "Malay",
    "Malayalam",
    "Maltese",
    "Mandarin",
    "Marathi",
    "Nepali",
    "Norwegian",
    "Nzema",
    "Ojibwa",
    "Oriya",
    "Other",
    "Panjabi/Punjabi",
    "Persian",
    "Polish",
    "Portuguese",
    "Pushto",
    "Quechua",
    "Romanian",
    "Russian",
    "Samoan",
    "Serbian",
    "Sesotho",
    "Sindhi",
    "Sinhala",
    "Sinhalese",
    "Slovak",
    "Slovenian",
    "Soga",
    "Somalian",
    "Spanish",
    "Swahili",
    "Swatow",
    "Swedish",
    "Tagalog",
    "Taiwanese",
    "Tamil",
    "Telugu",
    "Thai",
    "Tigrigna",
    "Tiv",
    "Tok Pisin",
    "Tulu",
    "Turkish",
    "Ukrainian",
    "Urdu",
    "Vietnamese",
    "Visayan",
    "Welsh",
    "Xhosa",
    "Yiddish",
    "Yoruba",
    "Yugoslav",
    "Zulu"
]

provider_types = [
    "Dentist",
]

specialties = [
    "Adolescent Medicine",
    "Anatomical Pathology",
    "Anesthesiology",
    "Bacteriology",
    "Cardiac Surgery",
    "Cardiology",
    "Cardiothoracic Surgery",
    "Cardiovascular and Thoracic Surgery",
    "Child and Adolescent Psychiatry",
    "Clinical Immunology",
    "Clinical Immunology and Allergy",
    "Clinical Pharmacology",
    "Clinical Pharmacology and Toxicology",
    "Colorectal Surgery",
    "Community Medicine",
    "Critical Care Medicine",
    "Dermatology",
    "Developmental Paediatrics",
    "Diagnostic and Therapeutic Radiology",
    "Diagnostic Radiology",
    "Emergency Medicine",
    "Endocrinology and Metabolism",
    "Family Medicine",
    "Family Medicine (Emergency Medicine)",
    "Forensic Pathology",
    "Forensic Psychiatry",
    "Gastroenterology",
    "General Internal Medicine",
    "General Pathology",
    "General Surgery",
    "General Surgical Oncology",
    "Geriatric Medicine",
    "Geriatric Psychiatry",
    "Gynecologic Oncology",
    "Gynecologic Reproductive Endocrinology & Infertility",
    "Hematological Pathology",
    "Hematology",
    "Infectious Diseases",
    "Internal Medicine",
    "Laboratory Medicine",
    "Maternal Fetal Medicine",
    "Medical Biochemistry",
    "Medical Genetics",
    "Medical Microbiology",
    "Medical Oncology",
    "Neonatal-Perinatal Medicine",
    "Nephrology",
    "Neurology",
    "Neurology and Psychiatry",
    "Neuropathology",
    "Neuroradiology",
    "Neurosurgery",
    "Nuclear Medicine",
    "Obstetrics",
    "Obstetrics and Gynecology",
    "Occupational Medicine",
    "Ophthalmology",
    "Orthopedic Surgery",
    "Otolaryngology - Head and Neck Surgery",
    "Paediatric Cardiology",
    "Paediatric Emergency Medicine",
    "Paediatric Haematology/Oncology",
    "Paediatric Radiology",
    "Paediatric Surgery",
    "Pain Medicine",
    "Palliative Medicine",
    "Pathology and Bacteriology",
    "Pediatric General Surgery",
    "Pediatrics", 
    "Physical Medicine and Rehabilitation", 
    "Plastic Surgery", 
    "Psychiatry", 
    "Public Health", 
    "Public Health and Preventive Medicine", 
    "Radiation Oncology", 
    "Respirology", 
    "Rheumatology", 
    "Thoracic Surgery", 
    "Transfusion Medicine", 
    "Urology", 
    "Vascular Surgery"
]

for designation in designations:
    with app.app_context():
        db.session.add(DesignationModel(name=designation))
        db.session.commit()

for language in languages:
    with app.app_context():
        db.session.add(LanguageModel(name=language))
        db.session.commit()

for provider_type in provider_types:
    with app.app_context():
        db.session.add(ProviderTypeModel(name=provider_type))
        db.session.commit()

for specialty in specialties:
    with app.app_context():
        db.session.add(SpecialtyModel(name=specialty))
        db.session.commit()
