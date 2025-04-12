document.addEventListener('DOMContentLoaded', function() {
    const kontrolForm = document.getElementById('kontrol-form');
    const kaydetBtn = document.getElementById('kaydet-btn');
    const yenileBtn = document.getElementById('yenile-btn');
    const bildirim = document.getElementById('bildirim');
    const bildirimMesaj = document.getElementById('bildirim-mesaj');
    
    // Form gönderme işlemi
    kontrolForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Form verilerini al
        const formData = new FormData(kontrolForm);
        const formObj = {};
        
        // Boolean değerler için düzenleme
        const checkboxes = kontrolForm.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            formObj[checkbox.name] = checkbox.checked ? 'true' : 'false';
        });
        
        // Diğer değerleri ekle
        const inputs = kontrolForm.querySelectorAll('input:not([type="checkbox"])');
        inputs.forEach(input => {
            formObj[input.name] = input.value;
        });
        
        // AJAX isteği ile verileri gönder
        fetch('/guncelle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(formObj)
        })
        .then(response => response.json())
        .then(data => {
            if (data.durum === 'başarılı') {
                bildirimiGoster('Değişiklikler başarıyla kaydedildi!', 'basarili');
                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                bildirimiGoster('Hata: ' + data.mesaj, 'hata');
            }
        })
        .catch(error => {
            bildirimiGoster('Bağlantı hatası: ' + error, 'hata');
        });
    });
    
    // Sayfayı yenileme butonu
    yenileBtn.addEventListener('click', function() {
        location.reload();
    });
    
    // Otomatik mod seçeneklerinin durumuna göre ilgili kontrolleri etkinleştir/devre dışı bırak
    const sicaklikOtoCheckbox = document.getElementById('sicaklik_oto_gelen');
    const isikOtoCheckbox = document.getElementById('isik_oto_gelen');
    
    function kontrolDurumlariniGuncelle() {
        // Sıcaklık oto modu açık ise
        if (sicaklikOtoCheckbox.checked) {
            document.getElementById('vantilator_gelen').disabled = true;
            document.getElementById('pencere_gelen').disabled = true;
        } else {
            document.getElementById('vantilator_gelen').disabled = false;
            document.getElementById('pencere_gelen').disabled = false;
        }
        
        // Işık oto modu açık ise
        if (isikOtoCheckbox.checked) {
            document.getElementById('ampul_gelen').disabled = true;
            document.getElementById('perde_gelen').disabled = true;
        } else {
            document.getElementById('ampul_gelen').disabled = false;
            document.getElementById('perde_gelen').disabled = false;
        }
    }
    
    // Sayfa yüklendiğinde durumları güncelle
    kontrolDurumlariniGuncelle();
    
    // Checkbox durumları değiştiğinde kontrolleri güncelle
    sicaklikOtoCheckbox.addEventListener('change', kontrolDurumlariniGuncelle);
    isikOtoCheckbox.addEventListener('change', kontrolDurumlariniGuncelle);
    
    // Bildirim gösterme fonksiyonu
    function bildirimiGoster(mesaj, tip) {
        bildirimMesaj.textContent = mesaj;
        bildirim.className = 'bildirim ' + tip;
        bildirim.style.display = 'block';
        
        // 5 saniye sonra bildirim kaybolsun
        setTimeout(() => {
            bildirim.style.display = 'none';
        }, 5000);
    }
    
    // Eşik değerleri kontrolü
    const birinciEsik = document.getElementById('birinci_esik_gelen');
    const ikinciEsik = document.getElementById('ikinci_esik_gelen');
    
    birinciEsik.addEventListener('change', function() {
        if (parseFloat(birinciEsik.value) >= parseFloat(ikinciEsik.value)) {
            bildirimiGoster('Birinci eşik değeri ikinci eşik değerinden küçük olmalıdır!', 'hata');
            birinciEsik.value = parseFloat(ikinciEsik.value) - 1;
        }
    });
    
    ikinciEsik.addEventListener('change', function() {
        if (parseFloat(ikinciEsik.value) <= parseFloat(birinciEsik.value)) {
            bildirimiGoster('İkinci eşik değeri birinci eşik değerinden büyük olmalıdır!', 'hata');
            ikinciEsik.value = parseFloat(birinciEsik.value) + 1;
        }
    });
});
