import requests
from deep_translator import GoogleTranslator

# --- AYARLAR ---
STRAPI_API_URL = "http://localhost:1337/api"

# Lütfen kopyaladığın uzun Token'ı aşağıdaki tırnakların arasına yapıştır:
STRAPI_TOKEN = "8bc766298c3ac0bf40a6cefe9e90a491364342733f0550c044ee8463361480c00bb18f1530d94b5e8dadbf74a6691a0df0b742c095bdc185e8b928f18581af64373ed6fdd6f0f2f5d8f3ae30f7a52cb5dfbffd05196f540e9a41b04f46f2cd6f2c9c361808b730a2e8f497e7150c571a06402f89d97d936d2528d50a668dece4" 

HEADERS = {
    "Authorization": f"Bearer {STRAPI_TOKEN}",
    "Content-Type": "application/json"
}

def gorsel_uret_ve_indir(mekan_adi, ingilizce_aciklama):
    print(f"🎨 '{mekan_adi}' için görsel üretiliyor...")
    prompt = f"A beautiful tourist landscape, highly detailed 4k photograph of {mekan_adi}. {ingilizce_aciklama[:100]}"
    image_url = f"https://image.pollinations.ai/prompt/{prompt}"
    
    response = requests.get(image_url)
    dosya_adi = f"{mekan_adi.replace(' ', '_').lower()}.jpg"
    
    with open(dosya_adi, "wb") as f:
        f.write(response.content)
    print(f"✅ Görsel indirildi: {dosya_adi}")
    return dosya_adi

def veriyi_hazirla(mekan_adi, turkce_aciklama, puan):
    print(f"🔄 '{mekan_adi}' işleniyor...")
    translator = GoogleTranslator(source='tr', target='en')
    ingilizce_aciklama = translator.translate(turkce_aciklama)
    print("✅ İngilizce çeviri tamamlandı.")
    
    gorsel_dosyasi = gorsel_uret_ve_indir(mekan_adi, ingilizce_aciklama)
    
    return {
        "mekan_adi": mekan_adi,
        "aciklama_tr": turkce_aciklama,
        "aciklama_en": ingilizce_aciklama,
        "puan": puan,
        "gorsel_yolu": gorsel_dosyasi
    }

# --- STRAPI ENTEGRASYONU ---

def strapi_gorsel_yukle(dosya_yolu):
    """Görseli Strapi Media Library'ye yükler ve ID'sini döner."""
    url = f"http://localhost:1337/api/upload"
    headers_upload = {"Authorization": f"Bearer {STRAPI_TOKEN}"}
    
    print("⏳ Görsel Strapi Media Library'ye yükleniyor...")
    with open(dosya_yolu, 'rb') as f:
        files = {'files': (dosya_yolu, f, 'image/jpeg')}
        response = requests.post(url, headers=headers_upload, files=files)
        
    # BURAYI GÜNCELLEDİK: Artık 200 ve 201 kodlarının ikisini de başarı kabul ediyoruz
    if response.status_code in [200, 201]:
        image_id = response.json()[0]['id']
        print(f"✅ Görsel başarıyla yüklendi! (Görsel ID: {image_id})")
        return image_id
    else:
        print("❌ Görsel yükleme hatası:", response.text)
        return None

def strapi_mekan_kaydet(veri, image_id):
    """Verileri Strapi'ye Türkçe ve İngilizce dillerinde ayrı ayrı kaydeder."""
    url = f"{STRAPI_API_URL}/mekans"
    
    # 1. AŞAMA: Varsayılan dil (Türkçe) kaydı
    payload_tr = {
        "data": {
            "Mekan_Adi": veri["mekan_adi"],
            "Aciklama": veri["aciklama_tr"],
            "Puan": veri["puan"],
            "Kapak_Resmi": image_id
        }
    }
    
    print("⏳ Türkçe veriler veritabanına kaydediliyor...")
    response_tr = requests.post(url, headers=HEADERS, json=payload_tr)
    
    if response_tr.status_code in [200, 201]:
        # STRAPI v5 GÜNCELLEMESİ: 'id' yerine 'documentId' yakalıyoruz
        document_id = response_tr.json()['data']['documentId']
        print(f"✅ Türkçe kayıt başarılı! (Document ID: {document_id})")
        
        # 2. AŞAMA: İngilizce çeviriyi sisteme ekleme (Strapi v5 PUT metodu)
        url_en = f"{STRAPI_API_URL}/mekans/{document_id}?locale=en"
        payload_en = {
            "data": {
                "Mekan_Adi": veri["mekan_adi"], 
                "Aciklama": veri["aciklama_en"],
                "Puan": veri["puan"],
                "Kapak_Resmi": image_id
            }
        }
        
        print("⏳ İngilizce çeviri sisteme ekleniyor...")
        # Yeni dil eklemek için PUT isteği atıyoruz
        response_en = requests.put(url_en, headers=HEADERS, json=payload_en)
        
        if response_en.status_code in [200, 201]:
            print("🎉 BÜTÜN İŞLEMLER BAŞARIYLA TAMAMLANDI!")
        else:
            print("❌ İngilizce kayıt hatası:", response_en.text)
            
    else:
        print("❌ Türkçe kayıt hatası:", response_tr.text)

# --- SİSTEMİ ÇALIŞTIRMA ---
if __name__ == "__main__":
    # 18 Mekanlık Dev Veritabanımız
    mekanlar_listesi = [
        {"sehir": "İstanbul", "mekan_adi": "Kız Kulesi", "puan": 4.8, "aciklama_tr": "İstanbul boğazının incisi, muhteşem manzaralı tarihi bir yapı."},
        {"sehir": "İstanbul", "mekan_adi": "Ayasofya", "puan": 4.9, "aciklama_tr": "Dünya mimarlık tarihinin günümüze kadar ayakta kalmış en önemli anıtlarından biri."},
        {"sehir": "İstanbul", "mekan_adi": "Kapalıçarşı", "puan": 4.7, "aciklama_tr": "Dünyanın en büyük ve en eski kapalı çarşılarından biri, alışverişin kalbi."},
        {"sehir": "Hatay", "mekan_adi": "Titus Tüneli", "puan": 4.6, "aciklama_tr": "Roma döneminde dağ delinerek yapılmış devasa bir mühendislik harikası."},
        {"sehir": "Hatay", "mekan_adi": "Habibi Neccar Camii", "puan": 4.8, "aciklama_tr": "Anadolu'da inşa edilen ilk camilerden biri olan tarihi ve manevi bir mekan."},
        {"sehir": "Hatay", "mekan_adi": "Hatay Arkeoloji Müzesi", "puan": 4.9, "aciklama_tr": "Eşsiz eserlere ev sahipliği yapan, dünyanın en büyük mozaik müzelerinden biri."},
        {"sehir": "Paris", "mekan_adi": "Eyfel Kulesi", "puan": 4.8, "aciklama_tr": "Paris'in ve dünyanın en tanınmış demir kulesi ve Fransa'nın sembolü."},
        {"sehir": "Paris", "mekan_adi": "Louvre Müzesi", "puan": 4.9, "aciklama_tr": "Mona Lisa tablosuna da ev sahipliği yapan devasa bir sanat ve tarih müzesi."},
        {"sehir": "Paris", "mekan_adi": "Notre Dame Katedrali", "puan": 4.7, "aciklama_tr": "Gotik mimarinin en muhteşem örneklerinden biri olan ikonik katedral."},
        {"sehir": "Nice", "mekan_adi": "Promenade des Anglais", "puan": 4.8, "aciklama_tr": "Akdeniz kıyısında uzanan, yürüyüş ve deniz havası için harika bir sahil yolu."},
        {"sehir": "Nice", "mekan_adi": "Colline du Château", "puan": 4.6, "aciklama_tr": "Tüm şehri ve meşhur melekler körfezini tepeden gören tarihi bir seyir parkı."},
        {"sehir": "Nice", "mekan_adi": "Vieux Nice (Eski Şehir)", "puan": 4.7, "aciklama_tr": "Dar sokakları, renkli evleri ve hareketli pazarlarıyla tarihi Nice bölgesi."},
        {"sehir": "Tokyo", "mekan_adi": "Tokyo Kulesi", "puan": 4.6, "aciklama_tr": "Şehrin muhteşem manzarasını sunan, Eyfel'den esinlenilmiş kırmızı-beyaz kule."},
        {"sehir": "Tokyo", "mekan_adi": "Senso-ji Tapınağı", "puan": 4.8, "aciklama_tr": "Geleneksel Japon mimarisini yansıtan Tokyo'nun en eski Budist tapınağı."},
        {"sehir": "Tokyo", "mekan_adi": "Shibuya Kavşağı", "puan": 4.7, "aciklama_tr": "Dünyanın en kalabalık ve enerjisi en yüksek meşhur yaya kavşağı."},
        {"sehir": "Kyoto", "mekan_adi": "Fushimi Inari Tapınağı", "puan": 4.9, "aciklama_tr": "Binlerce kırmızı Torii kapısıyla dağa doğru uzanan büyüleyici bir Şinto tapınağı."},
        {"sehir": "Kyoto", "mekan_adi": "Kinkaku-ji (Altın Köşk)", "puan": 4.8, "aciklama_tr": "Üst katları tamamen altın varakla kaplı, göl kenarındaki zen tapınağı."},
        {"sehir": "Kyoto", "mekan_adi": "Arashiyama Bambu Ormanı", "puan": 4.7, "aciklama_tr": "Devasa bambu ağaçları arasında yürüyüş yapabileceğiniz mistik ve huzur dolu bir yol."}
    ]

    print("\n--- GEZİ HANE TOPLU OTOMASYON BAŞLATILDI ---")
    
    import time
    from deep_translator import GoogleTranslator

    for mekan in mekanlar_listesi:
        print(f"\n🚀 Sıradaki Mekan İşleniyor: {mekan['mekan_adi']} ({mekan['sehir']})")
        
        # 1. İngilizceye Çeviri
        try:
            mekan["aciklama_en"] = GoogleTranslator(source='tr', target='en').translate(mekan["aciklama_tr"])
            print("✅ İngilizce çeviri tamamlandı.")
        except Exception as e:
            print(f"❌ Çeviri hatası: {e}")
            mekan["aciklama_en"] = mekan["aciklama_tr"] # Hata olursa boş kalmasın
            
        # 2. Strapi'ye Kaydetme (Görsel işlemi arayüzde yapıldığı için resim ID'sine None diyoruz)
        try:
            strapi_mekan_kaydet(mekan, None)
        except Exception as e:
            print(f"❌ Strapi kayıt hatası: {e}")
            
        # Sistemlerin nefes alması için 2 saniye mola
        time.sleep(2)
        
    print("\n🎉 BÜTÜN MEKANLAR BAŞARIYLA SİSTEME EKLENDİ!")