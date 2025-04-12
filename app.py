import os
import random
import string
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from functools import wraps

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Ana sunucu URL'si
ANA_SUNUCU_URL = "deneme1-nj20.onrender.com"  # Ana sunucunun URL'sini buraya ekleyin

# API Bridge için şifre anahtarı
API_ANAHTAR = "akilli_ev_gizli_anahtar"

# OTP kodu için session değişkeni
otp_kodlari = {}

# Email yapılandırması
EMAIL_KULLANICI = "herdemerasmus@gmail.com"
EMAIL_SIFRE = "kmop hzuo yoqp ztnr"
EMAIL_ALICI = "hidayete369@gmail.com"

# Oturum kontrolü için decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'kullanici_adi' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ana sayfa
@app.route('/')
def index():
    return redirect(url_for('login'))

# Login sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    hata = None
    if request.method == 'POST':
        kullanici_adi = request.form.get('kullanici_adi')
        sifre = request.form.get('sifre')
        
        if kullanici_adi == 'herdem' and sifre == '1940':
            # Tek kullanımlık şifre oluştur
            otp = ''.join(random.choices(string.digits, k=6))
            session['temp_kullanici'] = kullanici_adi
            otp_kodlari[kullanici_adi] = otp
            
            # E-posta gönder
            try:
                email_gonder(otp)
                return redirect(url_for('otp_dogrulama'))
            except Exception as e:
                hata = f"E-posta gönderirken hata oluştu: {str(e)}"
        else:
            hata = "Geçersiz kullanıcı adı veya şifre!"
    
    return render_template('login.html', hata=hata)

# OTP doğrulama sayfası
@app.route('/otp-dogrulama', methods=['GET', 'POST'])
def otp_dogrulama():
    hata = None
    if 'temp_kullanici' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        kullanici_otp = request.form.get('otp')
        kullanici_adi = session['temp_kullanici']
        
        if kullanici_adi in otp_kodlari and kullanici_otp == otp_kodlari[kullanici_adi]:
            session['kullanici_adi'] = kullanici_adi
            del otp_kodlari[kullanici_adi]
            return redirect(url_for('dashboard'))
        else:
            hata = "Geçersiz doğrulama kodu!"
    
    return render_template('otp_dogrulama.html', hata=hata)

# Dashboard sayfası
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Ana sunucudan verileri al
        yanit = requests.get(f"{ANA_SUNUCU_URL}/api/durum")
        if yanit.status_code == 200:
            veriler = yanit.json()
            return render_template('dashboard.html', veriler=veriler)
        else:
            hata = "Ana sunucudan veri alınamadı."
            return render_template('hata.html', hata=hata)
    except Exception as e:
        hata = f"Bağlantı hatası: {str(e)}"
        return render_template('hata.html', hata=hata)

# Veri güncelleme endpoint'i
@app.route('/guncelle', methods=['POST'])
@login_required
def veri_guncelle():
    try:
        # Formdan gelen verileri al
        veri = request.form.to_dict()
        
        # Boolean değerleri dönüştür
        boolean_alanlar = ['kapi_gelen', 'vantilator_gelen', 'pencere_gelen', 'ampul_gelen', 
                          'perde_gelen', 'isik_oto_gelen', 'sicaklik_oto_gelen']
        
        for alan in boolean_alanlar:
            if alan in veri:
                veri[alan] = veri[alan] == 'true'
            else:
                veri[alan] = False
        
        # Sayısal değerleri dönüştür
        numeric_alanlar = ['sicaklik_gelen', 'birinci_esik_gelen', 'ikinci_esik_gelen']
        for alan in numeric_alanlar:
            if alan in veri and veri[alan]:
                veri[alan] = float(veri[alan])
        
        # Ana sunucuya verileri gönder
        yanit = requests.post(f"{ANA_SUNUCU_URL}/api/alinan", json=veri)
        
        if yanit.status_code == 200:
            return jsonify({"durum": "başarılı", "mesaj": "Veriler güncellendi"})
        else:
            return jsonify({"durum": "hata", "mesaj": "Veriler güncellenemedi"})
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)})

# API Bridge
@app.route('/api/bridge', methods=['POST'])
def api_bridge():
    try:
        veri = request.get_json()
        
        # API anahtarını kontrol et
        if not veri or 'anahtar' not in veri or veri['anahtar'] != API_ANAHTAR:
            return jsonify({"durum": "hata", "mesaj": "Geçersiz API anahtarı"}), 401
        
        # Anahtarı verilden çıkar
        del veri['anahtar']
        
        # Ana sunucuya ilet
        yanit = requests.post(f"{ANA_SUNUCU_URL}/api/alinan", json=veri)
        
        if yanit.status_code == 200:
            return jsonify({"durum": "başarılı", "mesaj": "Veriler iletildi"})
        else:
            return jsonify({"durum": "hata", "mesaj": "Veriler iletilemedi"}), 500
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

# Çıkış yap
@app.route('/cikis')
def cikis():
    session.clear()
    return redirect(url_for('login'))

# E-posta gönderme fonksiyonu
def email_gonder(otp):
    mesaj = MIMEMultipart()
    mesaj['From'] = EMAIL_KULLANICI
    mesaj['To'] = EMAIL_ALICI
    mesaj['Subject'] = "Akıllı Ev Sistemi - Tek Kullanımlık Şifre"
    
    govde = f"""
    Merhaba,
    
    Akıllı Ev Sisteminize giriş yapmak için tek kullanımlık şifreniz: {otp}
    
    Bu kodu kimseyle paylaşmayın.
    
    Saygılarımızla,
    Akıllı Ev Sistemi
    """
    
    mesaj.attach(MIMEText(govde, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_KULLANICI, EMAIL_SIFRE)
        text = mesaj.as_string()
        server.sendmail(EMAIL_KULLANICI, EMAIL_ALICI, text)
        server.quit()
    except Exception as e:
        raise Exception(f"E-posta gönderme hatası: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
