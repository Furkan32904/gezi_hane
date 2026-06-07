import streamlit as st
import requests

st.set_page_config(page_title="Gezi Hane", page_icon="🌍")
st.title("🌍 Gezi Hane")
st.write("Yapay Zeka Destekli Çok Dilli Gezi Rehberi Sistemi")

STRAPI_URL = "http://127.0.0.1:1337"

@st.cache_data(ttl=1) 
def veri_cek():
    url = f"{STRAPI_URL}/api/sehirs?populate[mekans][populate]=*"
    try:
        cevap = requests.get(url)
        if cevap.status_code == 200:
            return cevap.json().get("data", [])
        return []
    except Exception as e:
        st.error(f"API Bağlantı Hatası: {e}")
        return []

sehirler = veri_cek()

if not sehirler:
    st.warning("Henüz veri bulunmuyor.")
else:
    sehir_isimleri = [sehir["Ad"] for sehir in sehirler]
    secilen_sehir_adi = st.selectbox("Gezmek istediğiniz şehri seçin:", sehir_isimleri)
    secilen_sehir = next((s for s in sehirler if s["Ad"] == secilen_sehir_adi), None)

    if secilen_sehir:
        st.markdown(f"### 📍 {secilen_sehir['Ad']}, {secilen_sehir.get('Ulke', '')}")
        st.write(secilen_sehir.get("Kisa_Bilgi", ""))
        st.divider()
        
        mekanlar = secilen_sehir.get("mekans", [])
        
        for mekan in mekanlar:
            mekan_adi = mekan['Mekan_Adi']
            st.markdown(f"#### {mekan_adi} (⭐ {mekan.get('Puan', '-')})")
            
            # Dinamik Resim Üretimi
            prompt = f"{mekan_adi} in {secilen_sehir['Ad']} historical landmark"
            ai_resim_url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=400&nologo=true"
            st.image(ai_resim_url, use_container_width=True)
            
            # Açıklama Seçimi: Önce Türkçe olanı ara, yoksa İngilizce olanı yaz
            aciklama_tr = mekan.get("aciklama_tr") or mekan.get("Aciklama")
            if aciklama_tr and aciklama_tr != "0":
                st.write(aciklama_tr)
            else:
                st.write(mekan.get("aciklama_en", "Açıklama bulunamadı."))
                
            st.divider()